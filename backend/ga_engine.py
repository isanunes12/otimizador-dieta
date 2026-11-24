"""
Ponte entre a API Flask e as classes do Algoritmo Genético.

- valida e normaliza os parâmetros recebidos do frontend;
- executa o AG com semente aleatória (reprodutibilidade);
- devolve a melhor dieta e o histórico de convergência (elite de cada geração).
"""
import math
import random
import threading
import time
from typing import Any, Dict, List, Optional

from metodo_ag import AlgoritmoGenetico, Ferramentas

# O AG usa o módulo global `random`; o lock garante que execuções simultâneas
# não embaralhem a semente umas das outras.
_LOCK_AG = threading.Lock()

# Limites de segurança: evitam que uma requisição trave o servidor
LIMITE_GERACOES = 2000
LIMITE_POPULACAO = 2000
LIMITE_AVALIACOES = 500_000  # gerações x população


class ErroValidacao(ValueError):
    """Erro de entrada do usuário (vira HTTP 400)."""


class FerramentasLeves(Ferramentas):
    """Igual a Ferramentas, mas não guarda todas as dietas de todas as gerações (só as elites)."""

    def armazena_populacao(self, populacao) -> None:  # noqa: D401
        return None


def _num(params: Dict[str, Any], chave: str, padrao, tipo, minimo, maximo):
    valor = params.get(chave, padrao)
    try:
        valor = tipo(valor)
    except (TypeError, ValueError):
        raise ErroValidacao(f"Parâmetro '{chave}' inválido")
    if isinstance(valor, float) and not math.isfinite(valor):
        raise ErroValidacao(f"Parâmetro '{chave}' inválido")
    if not (minimo <= valor <= maximo):
        raise ErroValidacao(f"Parâmetro '{chave}' deve estar entre {minimo} e {maximo}")
    return valor


def valida_parametros(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    params = params or {}
    p = {
        "generations": _num(params, "generations", 100, int, 1, LIMITE_GERACOES),
        "population_size": _num(params, "population_size", 100, int, 4, LIMITE_POPULACAO),
        "crossover_rate": _num(params, "crossover_rate", 0.8, float, 0.0, 1.0),
        "mutation_rate": _num(params, "mutation_rate", 0.1, float, 0.0, 1.0),
        "target_calories": _num(params, "target_calories", 2000.0, float, 500.0, 6000.0),
        "target_cost": _num(params, "target_cost", 20.0, float, 0.01, 10000.0),
        "elite_ratio": _num(params, "elite_ratio", 0.01, float, 0.0, 0.5),
        "tournament_ratio": _num(params, "tournament_ratio", 0.02, float, 0.0, 1.0),
        "tournament_upset": _num(params, "tournament_upset", 0.05, float, 0.0, 1.0),
        "blx_alpha": _num(params, "blx_alpha", 0.5, float, 0.0, 2.0),
        "blx_beta": _num(params, "blx_beta", 0.25, float, 0.0, 2.0),
    }
    if p["generations"] * p["population_size"] > LIMITE_AVALIACOES:
        raise ErroValidacao(f"Gerações x população não pode passar de {LIMITE_AVALIACOES:,}".replace(",", "."))

    seed = params.get("seed")
    if seed in (None, ""):
        seed = random.SystemRandom().randint(1, 2**31 - 1)
    p["seed"] = _num({"seed": seed}, "seed", 0, int, 0, 2**31 - 1)
    return p


def aplica_ajustes(grupos: List[dict], ajustes: Optional[List[dict]]) -> List[dict]:
    """Sobrescreve limites/preço de componentes específicos com valores informados pelo usuário."""
    grupos = [dict(g) for g in grupos]
    campos = ["min_kcal", "max_kcal", "cultural_min", "cultural_max", "price_per_kcal"]
    for ajuste in ajustes or []:
        idx = ajuste.get("phdi_index")
        if not isinstance(idx, int) or not (0 <= idx < len(grupos)):
            raise ErroValidacao("Ajuste com phdi_index inválido")
        for campo in campos:
            if campo in ajuste and ajuste[campo] is not None:
                grupos[idx][campo] = _num(ajuste, campo, 0, float, 0.0, 100000.0)
        grupos[idx]["adjusted"] = True

    for g in grupos:
        if g["min_kcal"] > g["max_kcal"]:
            raise ErroValidacao(f"{g['name_pt']}: mínimo de kcal maior que o máximo")
    if grupos[3]["max_kcal"] <= 0:
        raise ErroValidacao("Vegetais (total) precisa ter máximo de kcal maior que zero")
    return grupos


def avisos(grupos: List[dict]) -> List[str]:
    """Inconsistências dos dados que não impedem a execução, mas devem ser mostradas ao usuário."""
    saida = []
    for g in grupos:
        if g["cultural_min"] > g["cultural_max"]:
            saida.append(
                f"{g['name_pt']}: mínimo cultural ({g['cultural_min']:.1f} kcal) maior que o máximo cultural "
                f"({g['cultural_max']:.1f} kcal); qualquer valor deste componente será penalizado."
            )
    return saida


def _r(valor, casas=4):
    return None if valor is None else round(float(valor), casas)


def executa_ag(params: Dict[str, Any], grupos: List[dict]) -> Dict[str, Any]:
    """Roda o AG. `params` deve vir de valida_parametros e `grupos` de aplica_ajustes."""
    pop = params["population_size"]
    ferramentas = FerramentasLeves()
    ag = AlgoritmoGenetico(
        numero_geracoes=params["generations"],
        tamanho_populacao=pop,
        taxa_cruzamento=params["crossover_rate"],
        taxa_mutacao=params["mutation_rate"],
        numero_elites=max(1, math.ceil(params["elite_ratio"] * pop)),
        numero_participantes_torneio=max(2, min(pop, math.ceil(params["tournament_ratio"] * pop))),
        probabilidade_upset_torneio=params["tournament_upset"],
        alfa_cruzamento=params["blx_alpha"],
        beta_cruzamento=params["blx_beta"],
        is_maximizacao=True,
    )

    consumo = [{"minimo": g["min_kcal"], "maximo": g["max_kcal"]} for g in grupos]
    cultural = [{"minimo": g["cultural_min"], "maximo": g["cultural_max"]} for g in grupos]
    precos = [g["price_per_kcal"] for g in grupos]

    with _LOCK_AG:
        random.seed(params["seed"])
        inicio = time.perf_counter()
        ag.algoritmo_genetico(
            ferramentas=ferramentas,
            alvo_calorico=params["target_calories"],
            custo_alvo=params["target_cost"],
            consumo_min_max_componentes=consumo,
            valores_componentes=precos,
            limites_aceitabilidade_cultural=cultural,
        )
        duracao = time.perf_counter() - inicio

    historico = [
        {
            "generation": i,
            "fo": _r(d.pontuacao_fo),
            "phdi": _r(d.pontuacao_phdi),
            "penalty_total": _r(d.penalizacao_aplicada or 0.0),
            "penalty_calories": _r(d.penalizacao_calorias or 0.0),
            "penalty_cost": _r(d.penalizacao_custo or 0.0),
            "penalty_cultural": _r(d.penalizacao_aceitabilidade or 0.0),
            "calories": _r(d.calorias_totais, 2),
            "cost": _r(d.custo_total),
        }
        for i, d in enumerate(ferramentas.historico_elites)
    ]

    melhor = ferramentas.historico_elites[-1]
    gr = melhor.grupos_alimentares
    itens = []
    for i, grupo in enumerate(gr):
        calorias = grupo.calorias
        if grupo.nome == "Vegetables":
            # "Outros vegetais" = vegetais totais - DGV - REV (é o que entra no custo)
            outros = grupo.calorias - (gr[10].calorias + gr[11].calorias)
        else:
            outros = None
        itens.append({
            "phdi_index": i,
            "group": grupo.nome,
            "group_pt": grupos[i]["name_pt"],
            "calories": _r(calorias, 2),
            "other_vegetables_calories": _r(outros, 2),
            "percentage": _r(grupo.percentual_calorico or 0.0, 2),
            "phdi_score": _r(grupo.pontuacao_phdi, 2) if grupo.pontuacao_phdi is not None else None,
            "cost": _r((outros if outros is not None else calorias) * grupos[i]["price_per_kcal"]),
            "cultural_min": _r(grupos[i]["cultural_min"], 2),
            "cultural_max": _r(grupos[i]["cultural_max"], 2),
            "is_penalized": bool(grupo.penalizado),
            "penalty": _r(grupo.penalizacao_aplicada or 0.0),
        })

    return {
        "summary": {
            "fitness": _r(melhor.pontuacao_fo, 2),
            "phdi_total": _r(melhor.pontuacao_phdi, 2),
            "total_calories": _r(melhor.calorias_totais, 2),
            "total_cost": _r(melhor.custo_total, 2),
            "is_penalized": bool(melhor.penalizado),
            "penalty_total": _r(melhor.penalizacao_aplicada or 0.0),
            "penalty_calories": _r(melhor.penalizacao_calorias or 0.0),
            "penalty_cost": _r(melhor.penalizacao_custo or 0.0),
            "penalty_cultural": _r(melhor.penalizacao_aceitabilidade or 0.0),
            "duration_s": round(duracao, 3),
        },
        "items": itens,
        "history": historico,
        "warnings": avisos(grupos),
    }
