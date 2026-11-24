from typing import List, Optional, Dict

class GrupoAlimentar:
    """
    Representa um grupo de alimentos com suas propriedades nutricionais e pontuações no cálculo do PHDI.
    
    Atributos:
        nome (str): Nome do grupo alimentar (ex: "Frutas", "Verduras").
        valor_componente (float, opcional): Valor monetário por kcal.
        calorias (float, opcional): Quantidade total de calorias do grupo.
        percentual_calorico (float, opcional): Percentual que o grupo representa no total calórico.
        pontuacao_fo (float, opcional): Pontuação no cálculo da pontuação final.
        pontuacao_phdi (float, opcional): Pontuação específica para o índice PHDI.
        penalizado (bool): Indica se o grupo recebeu penalização.
        penalizacao_aplicada (float, opcional): Valor da penalização aplicada, se houver.
    """

    def __init__(self, nome, valor_componente: Optional[float] = None, calorias: Optional[float] = None):
        """
        Inicializa um novo grupo alimentar.
        
        Args:
            nome (str): Nome identificador do grupo alimentar
            valor_componente (float, opcional): Valor por kcal.
            calorias (float, opcional): Quantidade de calorias do grupo alimentar.
        """
        self.nome = nome
        self.valor_componente = valor_componente # Valor por kcal
        self.calorias = calorias
        self.percentual_calorico = None
        self.pontuacao_fo = None
        self.pontuacao_phdi = None
        self.penalizado = False
        self.penalizacao_aplicada = None
        self.porcentagem_penalizacao = None

    def __str__(self):
        """
        Retorna uma representação em string do objeto para facilitar a visualização.
        
        Returns:
            str: String formatada com todas as propriedades relevantes do grupo
        """
        return f'{self.nome} = Calorias: {self.calorias}, Percentual Calórico: {self.percentual_calorico}, Pontuação PHDI: {self.pontuacao_phdi}, Pontuação FO: {self.pontuacao_fo}, Penalizado?: {self.penalizado}, Penalização aplicada: {self.penalizacao_aplicada}'

    def copia(self):
        """
        Cria uma cópia independente (deep copy) do objeto GrupoAlimentar.
        
        Retorna:
            GrupoAlimentar: Nova instância com os mesmos valores dos atributos
        """
        copia_grupo = GrupoAlimentar(self.nome)
        copia_grupo.valor_componente = self.valor_componente
        copia_grupo.calorias = self.calorias
        copia_grupo.percentual_calorico = self.percentual_calorico
        copia_grupo.pontuacao_fo = self.pontuacao_fo
        copia_grupo.pontuacao_phdi = self.pontuacao_phdi
        copia_grupo.penalizado = self.penalizado
        copia_grupo.penalizacao_aplicada = self.penalizacao_aplicada
        copia_grupo.porcentagem_penalizacao = self.porcentagem_penalizacao

        return copia_grupo

    def reset(self) -> None:
        """
        Reseta os atributos calculados do grupo para seus valores padrão.
        Mantém apenas nome e valor_componente, que são propriedades básicas.
        
        Útil para reiniciar cálculos sem perder a definição original do grupo.
        """
        self.calorias = None
        self.percentual_calorico = None
        self.pontuacao_phdi = None
        self.pontuacao_fo = None
        self.penalizado = False
        self.penalizacao_aplicada = None
        self.porcentagem_penalizacao = None
