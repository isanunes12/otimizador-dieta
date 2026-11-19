class BiObjectiveSolution:
    '''
        Interface de uma solução (padroniza a saída)
    '''
    def __init__(self, solution_vars):
        self.solution_vars = solution_vars

    @property
    def f1(self):
        return self.solution_vars['f'][0, 0]
    
    @property
    def f2(self):
        return self.solution_vars['f'][1, 0]