import json
from enum import Enum
import pandas as pd
import pulp as p
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ObjectiveMode(Enum):
    MONO_OBJETIVO = "mono_objetivo"
    PHDI = "phdi"
    ACEITABILIDADE = "aceitabilidade"


class ConstraintMode(Enum):
    NONE = "none"
    FIX_PHDI = "fix_phdi"
    FIX_ACEITABILIDADE = "fix_aceitabilidade"


class DietOptimizationProblem:
    def __init__(
        self,
        objective_mode: ObjectiveMode,
        constraint_mode: ConstraintMode = ConstraintMode.NONE,
        constraint_value: float = None,
        M: float = 1000,
        row_index: int = -1,
        row_uf_renda: list = []
    ):
        with open(DATA_DIR / "componentes_phdi.json", "r", encoding="utf-8") as f:
            self.componentes_phdi = json.load(f)

        with open(DATA_DIR / "grupos_alimentares.json", "r", encoding="utf-8") as f:
            self.grupos_alimentares = json.load(f)

        with open(DATA_DIR / "limites_medios.json", "r", encoding="utf-8") as f:
            self.limites_medios = json.load(f)

        self.df_INA = pd.read_csv(DATA_DIR / "banco_INA_new_aceptability.csv")
        # self.df_INA = pd.read_csv("data/banco_INA_estratificado_ag.csv")

        if row_index != -1 and row_index < len(self.df_INA):
            self.df_INA = self.df_INA.iloc[[row_index]]
        elif len(row_uf_renda) == 2:
            self.df_INA = self.df_INA[self.df_INA["uf"] == row_uf_renda[0]]
            self.df_INA = self.df_INA[self.df_INA["faixa_renda_per_capita"] == row_uf_renda[1]]
        else:
            raise IndexError("problems with row_index or row_uf_renda")

        self.row = self.df_INA.iloc[0]
        self.caloria_alvo = self.row['kcal_consumo_phdi']
        self.preco_alvo = self.row['preco_total_phdi']
        self.M = M
        self.objective_mode = objective_mode
        self.constraint_mode = constraint_mode
        self.constraint_value = constraint_value

        # Validação antecipada
        if constraint_mode is not ConstraintMode.NONE and constraint_value is None:
            raise ValueError("constraint_value is required when constraint_mode is set.")


    def _suffix(self, alimento: str) -> str:
        return {
            'nozes_amendoim': 'nozes',
            'aves_frango': 'frango',
            'cereais_integrais': 'cereais_int',
            'batatas_tuber': 'batatas',
        }.get(alimento, alimento)


    def build_model(self) -> tuple:
        model = p.LpProblem("Diet_Optimization_Problem", p.LpMaximize)
        variables = self._build_variables()
        self._add_constraints(model, variables)
        # Somente adiciona o objetivo se não for escalarizar para mono-objetivo
        if self.objective_mode != ObjectiveMode.MONO_OBJETIVO:
            self._add_objective(model, variables)
        
        return model, variables

    def objectives(self, variables):
        f1 = self._objective_f1(variables)
        f2 = self._objective_f2(variables)

        return f1, f2

    def _build_variables(self) -> dict:
        x, s, b, d_minus, d_plus = {}, {}, {}, {}, {}

        for index, alimento in enumerate(self.grupos_alimentares):
            suffix = self._suffix(alimento)
            
            if alimento != "cereais_refinados":
                s[alimento] = p.LpVariable(f"s_{alimento}", lowBound=0, upBound=10)

            x[alimento] = p.LpVariable(
                f"x_{alimento}",
                lowBound=self.row[f"p5_{alimento}_kcal"],
                upBound=self.row[f"p95_{alimento}_kcal"]
            )

            d_minus[alimento] = p.LpVariable(f"d_minus_{alimento}", lowBound=0)
            d_plus[alimento] = p.LpVariable(f"d_plus_{alimento}", lowBound=0)

            if index >= 5 and index <= 13:
                b[alimento] = p.LpVariable(f"b_{alimento}", cat="Binary")

        return {'x': x, 's': s, 'b': b, 'd_minus': d_minus, 'd_plus': d_plus}


    def _add_constraints(self, model: p.LpProblem, variables: dict):
        x = variables['x']
        s = variables['s']
        b = variables['b']
        d_minus = variables['d_minus']
        d_plus = variables['d_plus']

        for index, alimento in enumerate(self.grupos_alimentares):
            # p25 = self.row[f'p25_{alimento}_kcal']
            # p75 = self.row[f'p75_{alimento}_kcal']
            limite_inferior_aceitabilidade = self.row[f'aceitabilidade_limite_inferior_{alimento}']
            limite_superior_aceitabilidade = self.row[f'aceitabilidade_limite_superior_{alimento}']
            portion = (x[alimento] / self.caloria_alvo) * 100

            # Aceitabilidade cultural
            model += x[alimento] + d_minus[alimento] >= limite_inferior_aceitabilidade, f"Min_Cultural_{alimento}"
            model += x[alimento] - d_plus[alimento] <= limite_superior_aceitabilidade, f"Max_Cultural_{alimento}"

            # Restrições PHDI por grupo
            if 0 <= index <= 4:
                model += s[alimento] <= 10 * (portion / self.componentes_phdi[index]['limite']), f"Subida_{alimento}"

            elif 5 <= index <= 9:
                limite_otimo = self.componentes_phdi[index]['limite_otimo']
                limite_superior = self.componentes_phdi[index]['limite_superior']

                if limite_superior == limite_otimo:
                    raise ValueError(f"limite_superior == limite_otimo para {alimento}, divisão por zero.")

                model += s[alimento] <= 10 * (portion / limite_otimo), f"Subida_{alimento}"
                model += (
                    s[alimento] <= 10 * ((limite_superior - portion) / (limite_superior - limite_otimo)) + (self.M * b[alimento])
                ), f"Descida_{alimento}"
                model += s[alimento] <= 10 * (1 - b[alimento]), f"Corte_Zero_{alimento}"

            elif 10 <= index <= 13:
                model += (
                    s[alimento] <= 10 * (1 - (portion / self.componentes_phdi[index]['limite'])) + (self.M * b[alimento])
                ), f"Descida_{alimento}"
                model += s[alimento] <= 10 * (1 - b[alimento]), f"Corte_Zero_{alimento}"

        # Restrições gerais
        model += p.lpSum([x[alimento] for alimento in self.grupos_alimentares]) == self.caloria_alvo, "Isocalorica"
        model += p.lpSum([x[alimento] * self.row[f"preco_{alimento}_por_kcal"] for alimento in self.grupos_alimentares]) <= self.preco_alvo, "Acessivel"
        
        # Restrição de conflito (lexicográfico)
        epsilon = 1e-5
        if self.constraint_mode is ConstraintMode.FIX_PHDI:
            model += self._objective_f1(variables) >= self.constraint_value - epsilon, "Fix_PHDI"
        elif self.constraint_mode is ConstraintMode.FIX_ACEITABILIDADE:
            model += self._objective_f2(variables) >= self.constraint_value - epsilon, "Fix_Aceitabilidade"


    def _add_objective(self, model: p.LpProblem, variables: dict):
        if self.objective_mode is ObjectiveMode.PHDI:
            model += self._objective_f1(variables)
        elif self.objective_mode is ObjectiveMode.ACEITABILIDADE:
            model += self._objective_f2(variables)


    def _objective_f1(self, variables: dict) -> p.LpAffineExpression:
        s = variables['s']
        return p.lpSum([s[alimento] for alimento in self.grupos_alimentares if alimento != "cereais_refinados"])


    def _objective_f2(self, variables: dict) -> p.LpAffineExpression:
        d_minus = variables['d_minus']
        d_plus = variables['d_plus']
        objetivos_ac = []

        for alimento in self.grupos_alimentares:
            suffix = self._suffix(alimento)
            min_kcal = self.row[f"p5_{alimento}_kcal"]
            max_kcal = self.row[f"p95_{alimento}_kcal"]
            # p25 = self.row[f'p25_{alimento}_kcal']
            # p75 = self.row[f'p75_{alimento}_kcal']
            limite_inferior_aceitabilidade = self.row[f'aceitabilidade_limite_inferior_{alimento}']
            limite_superior_aceitabilidade = self.row[f'aceitabilidade_limite_superior_{alimento}']

            max_desvio_min = limite_inferior_aceitabilidade - min_kcal
            max_desvio_plus = max_kcal - limite_superior_aceitabilidade

            penalidade = p.LpAffineExpression()
            if max_desvio_min > 0:
                penalidade += 10 * (d_minus[alimento] / max_desvio_min)
            if max_desvio_plus > 0:
                penalidade += 10 * (d_plus[alimento] / max_desvio_plus)
            
            objetivos_ac.append(10.0 - penalidade)

        return p.lpSum(objetivos_ac)