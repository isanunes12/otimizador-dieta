"""
Ponte entre a API Flask e o método exato (ε-restrição bi-objetivo em `metodo_exato/`).

Maximiza PHDI e aceitabilidade cultural e devolve as soluções da fronteira de Pareto.
Uma falha aqui nunca derruba a execução: o erro volta em `status`/`message`, e o resultado
do Algoritmo Genético continua sendo salvo e exibido.
"""
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List

import pandas as pd

from metodo_exato.core.solver import SemSolucaoOtima
from metodo_exato.problems.diet_optimization_model import DATA_DIR, DietOptimizationProblem, ObjectiveMode
from metodo_exato.runners.epsilon_contraint_runner import EpsilonContraintRunner

log = logging.getLogger("dieta-ag")

NUMERO_PONTOS = 20
RHO = 0.5

NOMES_PT = {
    "nozes_amendoim": "Nozes e amendoim",
    "leguminosas": "Leguminosas",
    "frutas": "Frutas",
    "veg_totais": "Vegetais (total)",
    "cereais_integrais": "Cereais integrais",
    "ovos": "Ovos",
    "peixes": "Peixes e frutos do mar",
    "batatas_tuber": "Tubérculos e batatas",
    "laticinios": "Laticínios",
    "oleos_insat": "Óleos vegetais",
    "carne_vermelha": "Carne vermelha",
    "aves_frango": "Frango e substitutos",
    "gord_animal": "Gordura animal",
    "acucares": "Açúcares de adição",
    "cereais_refinados": "Cereais refinados",
}


@lru_cache(maxsize=1)
def _indices_por_extrato() -> Dict[tuple, int]:
    # No CSV do método exato, a linha do Brasil tem faixa vazia; no app ela é a faixa 99
    df = pd.read_csv(DATA_DIR / "banco_INA_new_aceptability.csv")
    faixas = df["faixa_renda_per_capita"].fillna(99).astype(int)
    return {(int(uf), int(f)): i for i, (uf, f) in enumerate(zip(df["uf"], faixas))}


def _r(valor, casas=4) -> float:
    return round(float(valor or 0.0), casas)


def _unicas_ordenadas(solucoes) -> List[Any]:
    """Remove pontos repetidos e ordena do maior para o menor PHDI."""
    por_phdi = {}
    for s in solucoes:
        por_phdi.setdefault(float(s.f1), s)
    return sorted(por_phdi.values(), key=lambda s: s.f1, reverse=True)


def _monta_solucao(sol, problema: DietOptimizationProblem) -> Dict[str, Any]:
    linha = problema.row
    grupos = problema.grupos_alimentares
    variaveis = sol.solution_vars
    x = variaveis["x"][:, 0]
    d_menos = variaveis["d_minus"][:, 0]
    d_mais = variaveis["d_plus"][:, 0]
    # `s` não tem o componente cereais_refinados (não pontua no PHDI)
    notas = dict(zip([g for g in grupos if g != "cereais_refinados"], variaveis["s"][:, 0]))

    total_kcal = float(sum(x))
    itens = []
    custo_total = 0.0
    for j, grupo in enumerate(grupos):
        minimo = float(linha[f"p5_{grupo}_kcal"])
        maximo = float(linha[f"p95_{grupo}_kcal"])
        ac_inf = float(linha[f"aceitabilidade_limite_inferior_{grupo}"])
        ac_sup = float(linha[f"aceitabilidade_limite_superior_{grupo}"])
        desvio_inf, desvio_sup = float(d_menos[j]), float(d_mais[j])

        penalidade = 0.0
        if ac_inf - minimo > 0:
            penalidade += 10 * desvio_inf / (ac_inf - minimo)
        if maximo - ac_sup > 0:
            penalidade += 10 * desvio_sup / (maximo - ac_sup)

        custo = float(x[j]) * float(linha[f"preco_{grupo}_por_kcal"])
        custo_total += custo
        itens.append({
            "key": grupo,
            "group_pt": NOMES_PT[grupo],
            "calories": _r(x[j], 2),
            "percentage": _r(x[j] / total_kcal * 100 if total_kcal > 0 else 0, 2),
            "phdi_score": _r(notas[grupo], 2) if grupo in notas else None,
            "acceptability_score": _r(10.0 - penalidade, 2),
            "acceptability_min": _r(ac_inf, 2),
            "acceptability_max": _r(ac_sup, 2),
            "gap_lower": _r(desvio_inf, 2),
            "gap_upper": _r(desvio_sup, 2),
            "cost": _r(custo),
        })

    return {
        "phdi": _r(sol.f1),
        "acceptability": _r(sol.f2),
        "total_calories": _r(total_kcal, 2),
        "total_cost": _r(custo_total, 2),
        "items": itens,
    }


def _erro(mensagem: str) -> Dict[str, Any]:
    return {"status": "error", "message": mensagem}


def executa_exato(uf: int, faixa: int) -> Dict[str, Any]:
    """Resolve o modelo para o extrato com os dados e as metas do próprio método exato."""
    indice = _indices_por_extrato().get((uf, faixa))
    if indice is None:
        return _erro(f"O método exato não tem dados para o extrato UF={uf}, faixa={faixa}.")

    try:
        problema = DietOptimizationProblem(objective_mode=ObjectiveMode.MONO_OBJETIVO, row_index=indice)
        executor = EpsilonContraintRunner(problema)
        inicio = time.perf_counter()
        solucoes = executor.run(N=NUMERO_PONTOS, rho=RHO)
        duracao = time.perf_counter() - inicio

        return {
            "status": "ok",
            "method": "epsilon_constraint",
            "epsilon_points": NUMERO_PONTOS,
            "rho": RHO,
            "target_calories": _r(problema.caloria_alvo, 2),
            "target_cost": _r(problema.preco_alvo, 2),
            "duration_s": round(duracao, 3),
            "skipped_points": executor.pontos_ignorados,
            "solutions": [_monta_solucao(s, problema) for s in _unicas_ordenadas(solucoes)],
        }
    except SemSolucaoOtima as e:
        log.warning("Método exato sem solução ótima para UF=%s faixa=%s: %s", uf, faixa, e)
        return _erro("O solver não encontrou uma solução ótima para este extrato.")
    except Exception:
        log.exception("Falha no método exato para UF=%s faixa=%s", uf, faixa)
        return _erro("Não foi possível executar o método exato.")
