import numpy as np

from ..core.solver import BiObjectiveSolver, SemSolucaoOtima
from ..methods.epsilon_constraint import EpsilonContraint
from ..methods.lexicographic import LexicographicMethod


class EpsilonContraintRunner:
    def __init__(self, problem):
        self.problem = problem
        self.solver = BiObjectiveSolver(problem)
        self.pontos_ignorados = 0

    def _run_epsilon_contraint(self, epsilons, rho):
        solutions = []

        for epsilon in epsilons:
            method = EpsilonContraint(epsilon=epsilon, rho=rho)
            try:
                solutions.append(self.solver.solve(method))
            except SemSolucaoOtima:
                # Um ponto intermediário sem ótimo provado não invalida os demais
                self.pontos_ignorados += 1

        return solutions

    def run(self, N=20, rho=0.5):
        sol_f1 = self.solver.solve(LexicographicMethod(0.9999))
        sol_f2 = self.solver.solve(LexicographicMethod(0.0001))

        solutions = self._run_epsilon_contraint(
            epsilons=np.linspace(sol_f2.f2, sol_f1.f2, N, endpoint=False)[1:],
            rho=rho,
        )

        solutions.append(sol_f1)
        solutions.append(sol_f2)

        return solutions
