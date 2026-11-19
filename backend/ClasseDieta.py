from typing import List, Optional, Dict
from ClasseGrupoAlimentar import GrupoAlimentar

class Dieta:
    """
    Representa uma dieta completa com múltiplos grupos alimentares e suas métricas agregadas.
    
    Atributos:
        grupos_alimentares (List[GrupoAlimentar]): Lista de grupos que compõem a dieta.
        alvo_calorico (float, opcional): Meta calórica desejada para a dieta.
        custo_alvo (float, opcional): Meta de custo máximo desejado.
        calorias_totais (float, opcional): Soma das calorias de todos os grupos.
        custo_total (float): Custo total calculado da dieta.
        pontuacao_phdi (float, opcional): Pontuação total da dieta no índice PHDI.
        pontuacao_fo (float, opcional): Pontuação total no cálculo FO.
        penalizado (bool): Indica se a dieta como um todo foi penalizada.
        penalizacao_aplicada (float, opcional): Valor total da penalização aplicada.
        penalizacao_aceitabilidade (float): Valor total da penalização por Aceitabilidade Cultural.
    """

    def __init__(self, grupos_alimentares: List[GrupoAlimentar], alvo_calorico: Optional[float] = None, custo_alvo: Optional[float] = None) -> None:
        """
        Inicializa uma nova dieta com grupos alimentares e metas opcionais.
        
        Args:
            grupos_alimentares (List[GrupoAlimentar]): Lista de grupos que compõem a dieta
            alvo_calorico (float, opcional): Meta de calorias diárias desejadas
            custo_alvo (float, opcional): Meta de custo máximo permitidosuperior': 30.7},    #9

            # Componente Proporção (grupos 10-11): DGV e REV, relacionados ao grupo dos vegetais    
            {'grupo': 'DGV', 'limite_inferior': 0.0, 'limite_otimo' : 29.5, 'limite_superior': 100.0},              #10
            {'grupo': 'REV', 'limite_inferior': 0.0, 'limite_otimo' : 38.5, 'limite_superior': 100.0},              #11

        """
        self.grupos_alimentares = grupos_alimentares
        self.alvo_calorico = alvo_calorico
        self.custo_alvo = custo_alvo
        self.calorias_totais = None
        self.custo_total = None
        self.pontuacao_phdi = None
        self.pontuacao_fo = None
        self.penalizado = False
        self.penalizacao_aplicada = None # Engloba todas as penalizações
        self.penalizacao_calorias = None
        self.penalizacao_custo = None
        self.penalizacao_aceitabilidade = None

    def calcular_calorias_totais(self) -> None:
        """
        Calcula e armazena o total de calorias da dieta somando todos os grupos.
        
        Nota: DGV e REV não entram na soma de calorias, pois são componentes de razão relacionados aos Vegetais
        """
        if self.calorias_totais is None:  #Caso uma dieta que não tenha sofrido nenhuma alteração na ultima geração (Exemplo: elites), não irá ser calculada
            self.calorias_totais = 0
            for grupo in self.grupos_alimentares:
                # DGV e REV não colaboram com as calorias da dieta, suas calorias são em relação aos vegetais.
                if grupo.nome != 'DGV' and grupo.nome != 'REV':
                    self.calorias_totais += grupo.calorias

        #if self.calorias_totais is None:
        #    self.calorias_totais = sum(grupo.calorias or 0 for grupo in self.grupos_alimentares) # Soma as calorias de cada grupo, tratando None como 0
        
    def calcular_percentual_calorico(self) -> None:        
        """
        Calcula o percentual calórico de cada grupo em relação ao total da dieta.
        
        Pré-condição: calorias_totais deve ter sido calculado previamente.
        Caso contrário, pode gerar erro de divisão por zero ou resultados incorretos.
        """
        #Caso uma dieta que não tenha sofrido nenhuma alteração na ultima geração (Exemplo: elites), ainda assim ocorrerá o cálculo das porcentagens 
        if self.calorias_totais is not None: 
            for grupo in self.grupos_alimentares:
                if grupo.nome != 'DGV' and grupo.nome != 'REV':
                    grupo.percentual_calorico = grupo.calorias / self.calorias_totais * 100
                else:
                    # Os grupos DGV e REV estão relacionados apenas aos vegetais
                    grupo.percentual_calorico = grupo.calorias / self.grupos_alimentares[3].calorias * 100

        #if self.calorias_totais is not None:
        #    for grupo in self.grupos_alimentares:
        #        grupo.percentual_calorico = grupo.calorias / self.calorias_totais * 100

    def calcular_custo_dieta(self) -> None:        
        """
        Calcula o custo total da dieta baseado nas calorias e valor por componente de cada grupo.
        
        Nota: Este método acumula no atributo custo_total, podendo somar múltiplas vezes
        se chamado repetidamente. Use o reset() para realizar novas somas. 
        """ 

        if self.custo_total is None: # Evita que o custo seja calculado mais de uma vez para a mesma dieta 
            self.custo_total = 0
            for grupo in self.grupos_alimentares:
                if grupo.nome == 'Vegetables': # Os vegetais são compostos de DGV, REV e Outros Vegetais, logo a soma dos valores no grupo dos vegetais deve refletir somente aos Outros Vegetais, tendo em vista que DGV e REV possuem valores diferentes.
                    calorias_outros_vegetais = grupo.calorias - (self.grupos_alimentares[10].calorias + self.grupos_alimentares[11].calorias)
                    self.custo_total += calorias_outros_vegetais * grupo.valor_componente
                else:        
                    self.custo_total += grupo.calorias * grupo.valor_componente

        #for grupo in self.grupos_alimentares:
        #    self.custo_total += grupo.calorias * grupo.valor_componente

    def __str__(self) -> str:
        """
        Retorna uma representação detalhada da dieta em formato string.
        
        Returns:
            str: String formatada com resumo da dieta e detalhes de cada grupo alimentar
        """
        string = f'Dieta: Calorias totais: {self.calorias_totais}, Custo total: {self.custo_total}, Pontuação PHDI: {self.pontuacao_phdi}, Pontuação FO: {self.pontuacao_fo}, Penalizado?: {self.penalizado}, Penalizacao aplicada: {self.penalizacao_aplicada}'
        for grupo_alimentar in self.grupos_alimentares:
           string += f'\n   {grupo_alimentar}'
        return string

    def reset(self) -> None:
        self.calorias_totais = None
        self.custo_total = None
        self.pontuacao_phdi = None
        self.pontuacao_fo = None
        self.penalizado = False
        self.penalizacao_aplicada = None
        self.penalizacao_calorias = None
        self.penalizacao_custo = None
        self.penalizacao_aceitabilidade = None
    
    def copia(self):
        """
        Cria uma cópia independente (deep copy) da dieta, incluindo cópias independentes de todos os grupos.
        
        Retorna:
            Dieta: Nova instância com valores idênticos mas independentes
            
        Nota: Usa o método copia() de cada GrupoAlimentar para garantir independência.
        """
        copia_dieta = Dieta([grupo.copia() for grupo in self.grupos_alimentares])
        copia_dieta.alvo_calorico = self.alvo_calorico
        copia_dieta.custo_alvo = self.custo_alvo
        copia_dieta.calorias_totais = self.calorias_totais
        copia_dieta.custo_total = self.custo_total
        copia_dieta.pontuacao_phdi = self.pontuacao_phdi
        copia_dieta.pontuacao_fo = self.pontuacao_fo
        copia_dieta.penalizado = self.penalizado
        copia_dieta.penalizacao_aplicada = self.penalizacao_aplicada
        copia_dieta.penalizacao_calorias = self.penalizacao_calorias
        copia_dieta.penalizacao_custo = self.penalizacao_custo
        copia_dieta.penalizacao_aceitabilidade = self.penalizacao_aceitabilidade

        return copia_dieta