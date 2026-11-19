"""
Leitura dos extratos (UF x faixa de renda) do banco INA e montagem dos
limites dos 17 componentes do PHDI usados pelo Algoritmo Genético.

O CSV é estático e pequeno, então é carregado uma única vez em memória.
"""
import os
from functools import lru_cache
from typing import Dict, List

import pandas as pd

_DIR = os.path.dirname(os.path.abspath(__file__))
# Consumo (percentis), preços e metas por extrato
CAMINHO_CSV = os.path.join(_DIR, "banco_INA_estratificado_ag.csv")
# Limites de aceitabilidade cultural (os mesmos do método exato e da tabela da orientadora):
# % nacionais de kcal (Brasil) multiplicadas pelas kcal do PHDI de cada extrato
CAMINHO_CSV_ACEITABILIDADE = os.path.join(_DIR, "metodo_exato", "data", "banco_INA_new_aceptability.csv")

# Versão dos limites, gravada em cada execução para separar resultados antigos dos novos
VERSAO_LIMITES = "aceitabilidade-tabela-orientadora-2026-11"

UFS: Dict[int, str] = {
    11: "Rondônia", 12: "Acre", 13: "Amazonas", 14: "Roraima", 15: "Pará", 16: "Amapá", 17: "Tocantins",
    21: "Maranhão", 22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte", 25: "Paraíba", 26: "Pernambuco",
    27: "Alagoas", 28: "Sergipe", 29: "Bahia", 31: "Minas Gerais", 32: "Espírito Santo", 33: "Rio de Janeiro",
    35: "São Paulo", 41: "Paraná", 42: "Santa Catarina", 43: "Rio Grande do Sul", 50: "Mato Grosso do Sul",
    51: "Mato Grosso", 52: "Goiás", 53: "Distrito Federal", 99: "Brasil",
}

FAIXAS: Dict[int, str] = {
    1: "Faixa 1 (menor renda)", 2: "Faixa 2", 3: "Faixa 3", 4: "Faixa 4 (maior renda)", 99: "Todas as faixas",
}

# Nome usado internamente pelo AG (não alterar: ClasseAlgoritmoGenetico depende deles) e nome de exibição
NOMES_GRUPOS = [
    ("Nuts and peanuts", "Nozes e amendoim"),
    ("Legumes", "Leguminosas"),
    ("Fruits", "Frutas"),
    ("Vegetables", "Vegetais (total)"),
    ("Whole cereals", "Cereais integrais"),
    ("Eggs", "Ovos"),
    ("Fish and seafood", "Peixes e frutos do mar"),
    ("Tubers and potatoes", "Tubérculos e batatas"),
    ("Dairy", "Laticínios"),
    ("Vegetable oils", "Óleos vegetais"),
    ("DGV", "Vegetais verde-escuros (DGV)"),
    ("REV", "Vegetais vermelho-alaranjados (REV)"),
    ("Red meat", "Carne vermelha"),
    ("Chicken and substitutes", "Frango e substitutos"),
    ("Animal fats", "Gordura animal"),
    ("Added sugars", "Açúcares de adição"),
    ("Cereais Refinados", "Cereais refinados"),
]

# Componentes com consumo fixo (coluna "Fixo" da tabela): nozes, cereais integrais, peixes e DGV.
# O valor em kcal é % nacional x kcal do PHDI do extrato. Nozes, cereais integrais e peixes já vêm
# calculados no CSV de aceitabilidade; DGV não está nele, então usamos o % da tabela.
FIXOS = (0, 4, 6, 10)
PERC_FIXO_DGV = 0.11          # % das kcal totais
PERC_MAX_CULTURAL_REV = 0.71  # REV: limite cultural 0 a 0,71% das kcal totais

# índice do componente no AG -> nome da coluna no CSV de aceitabilidade
CHAVES_ACEITABILIDADE = {
    0: "nozes_amendoim", 1: "leguminosas", 2: "frutas", 3: "veg_totais", 4: "cereais_integrais",
    5: "ovos", 6: "peixes", 7: "batatas_tuber", 8: "laticinios", 9: "oleos_insat",
    12: "carne_vermelha", 13: "aves_frango", 14: "gord_animal", 15: "acucares", 16: "cereais_refinados",
}


@lru_cache(maxsize=1)
def _df() -> pd.DataFrame:
    return pd.read_csv(CAMINHO_CSV)


@lru_cache(maxsize=1)
def _df_aceitabilidade() -> pd.DataFrame:
    df = pd.read_csv(CAMINHO_CSV_ACEITABILIDADE)
    # Nesse CSV a linha do Brasil tem a faixa vazia; no app ela é a faixa 99
    df["faixa_renda_per_capita"] = df["faixa_renda_per_capita"].fillna(99).astype(int)
    return df


def lista_extratos() -> List[dict]:
    df = _df()
    saida = []
    for _, linha in df[["uf", "faixa_renda_per_capita"]].iterrows():
        uf, faixa = int(linha["uf"]), int(linha["faixa_renda_per_capita"])
        saida.append({
            "uf": uf,
            "uf_nome": UFS.get(uf, str(uf)),
            "faixa": faixa,
            "faixa_nome": FAIXAS.get(faixa, str(faixa)),
            **metas_do_extrato(uf, faixa),
        })
    saida.sort(key=lambda e: (e["uf"] != 99, e["uf_nome"], e["faixa"]))
    return saida


def _linha(uf: int, faixa: int, df: pd.DataFrame = None) -> pd.Series:
    df = _df() if df is None else df
    sel = df[(df["uf"] == uf) & (df["faixa_renda_per_capita"] == faixa)]
    if sel.empty:
        raise KeyError(f"Extrato UF={uf} faixa={faixa} não existe no banco INA")
    return sel.iloc[0]


def metas_do_extrato(uf: int, faixa: int) -> dict:
    """Metas padrão = consumo e custo atuais da população (as mesmas usadas pelo método exato)."""
    l = _linha(uf, faixa)
    return {
        "target_calories": round(float(l["kcal_consumo_phdi"]), 1),
        "target_cost": round(float(l["preco_total_phdi"]), 2),
    }


def grupos_do_extrato(uf: int, faixa: int) -> List[dict]:
    """Retorna os 17 componentes com limites de consumo, limites culturais e preço por kcal."""
    l = _linha(uf, faixa)
    f = lambda col: float(l[col])

    a = _linha(uf, faixa, _df_aceitabilidade())
    kcal_phdi = float(l["kcal_consumo_phdi"])

    # Intervalo de busca do AG (min_kcal, max_kcal) e preço por kcal: dados de consumo do extrato
    busca = {
        1: (f("p5_leguminosas_kcal"), f("p95_leguminosas_kcal"), f("preco_leguminosas_por_kcal")),
        2: (f("p5_frutas_kcal"), f("p95_frutas_kcal"), f("preco_frutas_por_kcal")),
        3: (f("p5_veg_total_kcal"), f("p95_veg_total_kcal"), f("preco_veg_outros_por_kcal")),
        5: (f("p5_ovos_kcal"), f("p95_ovos_kcal"), f("preco_ovos_por_kcal")),
        7: (f("p5_batatas_tuber_kcal"), f("p95_batatas_tuber_kcal"), f("preco_batatas_tuber_por_kcal")),
        8: (f("p5_laticinios_kcal"), f("p95_laticinios_kcal"), f("preco_laticinios_por_kcal")),
        9: (f("p5_oleos_insat_kcal"), f("p95_oleos_insat_kcal"), f("preco_oleos_insat_por_kcal")),
        11: (f("p5_veg_vermelho_kcal"), f("p95_veg_vermelho_kcal"), f("preco_veg_vermelho_por_kcal")),
        # Moderação: o AG não passa do consumo médio atual
        12: (f("p5_carne_vermelha_kcal"), f("kcal_totais_carne_vermelha"), f("preco_carne_vermelha_por_kcal")),
        13: (f("p5_aves_frango_kcal"), f("kcal_totais_aves_frango"), f("preco_aves_frango_por_kcal")),
        14: (f("p5_gord_animal_kcal"), f("kcal_totais_gord_animal"), f("preco_gord_animal_por_kcal")),
        15: (f("p5_acucares_kcal"), f("kcal_totais_acucares"), f("preco_acucares_por_kcal")),
        16: (0.0, f("kcal_totais_cereais_refinados"), f("preco_cereais_refinados_por_kcal")),
    }
    precos_fixos = {
        0: f("preco_nozes_amendoim_por_kcal"),
        4: f("preco_cereais_integrais_por_kcal"),
        6: f("preco_peixes_por_kcal"),
        10: f("preco_veg_verde_por_kcal"),
    }

    # Limites de aceitabilidade cultural (tabela da orientadora / CSV do método exato)
    cultural = {
        i: (float(a[f"aceitabilidade_limite_inferior_{k}"]), float(a[f"aceitabilidade_limite_superior_{k}"]))
        for i, k in CHAVES_ACEITABILIDADE.items()
    }
    cultural[10] = (PERC_FIXO_DGV / 100 * kcal_phdi,) * 2
    cultural[11] = (0.0, PERC_MAX_CULTURAL_REV / 100 * kcal_phdi)

    especificacao = {}
    for idx in range(len(NOMES_GRUPOS)):
        cmn, cmx = cultural[idx]
        if idx in FIXOS:
            # consumo fixo: o AG não varia este componente
            especificacao[idx] = (cmn, cmn, cmn, cmn, precos_fixos[idx])
        else:
            mn, mx, preco = busca[idx]
            especificacao[idx] = (mn, mx, cmn, cmx, preco)

    grupos = []
    for idx, (nome, nome_pt) in enumerate(NOMES_GRUPOS):
        mn, mx, cmn, cmx, preco = especificacao[idx]
        grupos.append({
            "phdi_index": idx,
            "name": nome,
            "name_pt": nome_pt,
            "fixed": idx in FIXOS,
            "min_kcal": mn,
            "max_kcal": mx,
            "cultural_min": cmn,
            "cultural_max": cmx,
            "price_per_kcal": preco,
        })
    return grupos
