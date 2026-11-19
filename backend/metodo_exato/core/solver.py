import numpy as np
import pulp as p

from .solution import BiObjectiveSolution

# Teto por resolução: o CBC costuma levar frações de segundo em cada uma
TEMPO_LIMITE_S = 10


class SemSolucaoOtima(RuntimeError):
    """O solver não provou uma solução ótima (modelo inviável ou tempo esgotado)."""


class BiObjectiveSolver:
    def __init__(self, problem):
        self.problem = problem

    def solve(self, objective_builder):
        model, variables = self.problem.build_model()

        f1, f2 = self.problem.objectives(variables)

        objective_builder(model, f1, f2)  # Construção da função objetivo

        model.solve(p.PULP_CBC_CMD(msg=0, timeLimit=TEMPO_LIMITE_S))

        if model.status != p.LpStatusOptimal or model.sol_status != p.LpSolutionOptimal:
            raise SemSolucaoOtima(p.LpStatus[model.status])

        return self._extract_solution(variables, f1, f2)

    def _extract_solution(self, variables, f1, f2):
        solution_vars = dict()
        for vars_name in variables.keys():
            solution_vars[vars_name] = np.array([p.value(v) for v in variables[vars_name].values()], ndmin=2).T

        f = np.array([[p.value(f1)], [p.value(f2)]])

        solution_vars["f"] = f

        return BiObjectiveSolution(solution_vars)
