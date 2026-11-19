import pulp as p

class EpsilonContraint:
    def __init__(self, epsilon, rho):
        self.epsilon = epsilon
        self.rho = rho
    
    def __call__(self, model, f1, f2):
        '''
            Existe teoremas que me permitem afirmar que se o problema garante
            soluções ótimas únicas, então não importa a função objetivo escolhida
            para ser minimizada. Pois, toda solução encontrada com a função
            minimizada escolhida pode ser obtida por qualquer outra.
        '''
         
        # Adicional Contraint
        model += f2 >= self.epsilon

        # Objective Function
        model += f1 + (self.rho * f2)