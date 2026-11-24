import pandas as pd
from typing import List, Optional, Dict
from ClasseDieta import Dieta
#from ClasseAlgoritmoGenetico import AlgoritmoGenetico
import os

class Ferramentas:
    """
    Ferramentas de apoio para armazenamento e exportação de dados do algoritmo genético.
    
    Atributos:
        historico_dietas (List[Dieta]): Histórico completo de todas as dietas avaliadas
        historico_elites (List[Dieta]): Histórico das melhores dietas de cada geração
    """

    def __init__(self):
        """
        Inicializa os históricos de armazenamento de dados.
        """
        self.historico_dietas: List[Dieta] = []
        self.historico_elites: List[Dieta] = []

    def armazena_populacao(self, populacao: List['Dieta']) -> None:
        """
        Armazena uma população completa de dietas no histórico geral.
        
        Args:
            populacao: Lista de objetos Dieta a serem armazenados
            
        Nota: Utilizado para rastrear todas as dietas avaliadas durante a execução.
        Pode consumir muita memória em execuções longas ou com populações grandes.
        """
        #Desempacota a lista e adiciona item por item no histórico, mais eficiente que append
        self.historico_dietas.extend(populacao) 

    def armazena_elites(self, elites: List['Dieta']) -> None:
        """
        Armazena a melhor dieta (elite) de uma geração no histórico de elites.
        
        Args:
            elites: Lista de dietas de elite (geralmente ordenadas do melhor para o pior)
            
        Nota: Assume que a primeira dieta da lista é a melhor (elite principal).
        Armazena apenas a elite principal.
        """

        self.historico_elites.append(elites[0])

    def gera_csv_elites_execucao(self, 
                                    nome_arquivo: str, 
                                    uf: str,
                                    faixa_renda: str,
                                    execucao: int,
                                    conjunto: int,
                                    ag: 'AlgoritmoGenetico',
                                    tempo_execucao: float) -> None:
        """
        Gera um arquivo CSV com o histórico completo das elites de todas as gerações.
        
        Args:
            nome_arquivo: Caminho e nome do arquivo CSV de saída
            uf: Unidade Federativa (estado) para identificação do contexto
            faixa_renda: Faixa de renda da população alvo
            execucao: Número da execução do algoritmo (para múltiplas execuções)
            conjunto: Identificador do conjunto de parâmetros/teste
            ag: Instância do AlgoritmoGenetico com parâmetros de configuração
            
        Nota: Cria um arquivo novo ou acrescenta a um existente, permitindo consolidação
        de múltiplas execuções. Útil para análise da evolução do algoritmo ao longo das gerações.
        """

        from ClasseAlgoritmoGenetico import AlgoritmoGenetico

        dados = []

        # Processa cada elite armazenada no histórico
        for i, dieta in enumerate(self.historico_elites):
            # Cria dicionário com todos os dados relevantes da elite da geração i
            linha = {
                # Infos Extrato
                'UF': uf,
                'Faixa de Renda': faixa_renda,
                'Alvo Calorico': dieta.alvo_calorico,
                'Custo Alvo': dieta.custo_alvo,

                # Parâmetros e configuração do Algoritmo Genético
                'Conjunto': conjunto,
                'Execucao': execucao,
                'Tempo de Execucao (s)': tempo_execucao,
                'Geracao': i,
                'Numero de Individuos': ag.tamanho_populacao,
                'Numero de Geracoes': ag.numero_geracoes,
                'Taxa de Cruzamento': ag.taxa_cruzamento,
                'Taxa de Mutacao': ag.taxa_mutacao,
                'Proporcao de Elites': ag.numero_elites/ag.tamanho_populacao, # Armazena a proporção de elites em relação ao tamanho da população
                'Proporcao de Participantes por Torneio': ag.numero_participantes_torneio/ag.tamanho_populacao, # Armazena a proporção de participantes por torneio em relação ao tamanho da população
                'Probabilidade de Upset no Torneio': ag.probabilidade_upset_torneio,
                'Alfa Cruzamento': ag.alfa_cruzamento,
                'Beta Cruzamento': ag.beta_cruzamento,
                
                # Infos Dieta
                #'Componentes KCAL': [grupo.calorias for grupo in dieta.grupos_alimentares],
                #"Componentes % Calorico": [grupo.percentual_calorico for grupo in dieta.grupos_alimentares],
                #'Calorias Totais': dieta.calorias_totais,
                #'Custo Total': dieta.custo_total,                
                #'Penalizado': dieta.penalizado,
                #'Penalizacao Aplicada': dieta.penalizacao_aplicada,
                #'Pontuacao PHDI': dieta.pontuacao_phdi,
                #'Pontuacao FO': dieta.pontuacao_fo
            }
            
            # Adiciona colunas individuais para cada grupo alimentar
            for grupo in dieta.grupos_alimentares:
                # Remove espaços e caracteres especiais para criar nome de coluna válido
                nome_coluna_safe = grupo.nome.replace(' ', '_').replace('(', '').replace(')', '').lower()
                
                # Coluna para calorias (ex: nuts_and_peanuts_kcal)
                linha[f'{nome_coluna_safe}_kcal'] = grupo.calorias
                
                # Coluna para percentual calórico (ex: nuts_and_peanuts_perc)
                linha[f'{nome_coluna_safe}_perc'] = grupo.percentual_calorico
                
                # Coluna para pontuação PHDI (ex: nuts_and_peanuts_phdi)
                linha[f'{nome_coluna_safe}_phdi'] = grupo.pontuacao_phdi
                
                # Coluna para pontuação FO (ex: nuts_and_peanuts_fo)
                linha[f'{nome_coluna_safe}_fo'] = grupo.pontuacao_fo
                
                # Coluna para penalização (ex: nuts_and_peanuts_penalizado)
                linha[f'{nome_coluna_safe}_penalizado'] = grupo.penalizado
                linha[f'{nome_coluna_safe}_porcentagem_penalização'] = grupo.porcentagem_penalizacao
                linha[f'{nome_coluna_safe}_penalizacao'] = grupo.penalizacao_aplicada

            linha[f'Calorias Totais'] = dieta.calorias_totais
            linha[f'Custo Total'] = dieta.custo_total                
            linha[f'Dieta Penalizada?'] = dieta.penalizado
            linha[f'Penalizacao Aplicada'] = dieta.penalizacao_aplicada
            linha[f'Penalizacao por Calorias'] = dieta.penalizacao_calorias
            linha[f'Penalizacao por Custo'] = dieta.penalizacao_custo
            linha[f'Penalizacao por Aceitabilidade Aplicada'] = dieta.penalizacao_aceitabilidade
            linha[f'Pontuacao PHDI'] = dieta.pontuacao_phdi
            linha[f'Pontuacao FO'] = dieta.pontuacao_fo
            
            dados.append(linha)
            
        # Verifica se o arquivo já existe para decidir entre criar ou acrescentar
        if not os.path.exists(nome_arquivo):
            # Cria o arquivo novo
            df = pd.DataFrame(dados)
            df.to_csv(nome_arquivo, index=False)
        else:
            # Acrescenta ao existente
            df = pd.DataFrame(dados)
            df.to_csv(nome_arquivo, mode='a', index=False, header=False)
    
    def gera_csv_resultado_execucao(self, 
                 nome_arquivo: str, 
                 uf: str,
                 faixa_renda: str,
                 execucao: int,
                 conjunto: int,
                 ag: 'AlgoritmoGenetico', 
                 tempo_execucao: float) -> None:
        """
        Gera um arquivo CSV com apenas o resultado final (última elite) da execução.
        
        Args:
            nome_arquivo: Caminho e nome do arquivo CSV de saída
            uf: Unidade Federativa (estado)
            faixa_renda: Faixa de renda da população
            execucao: Número da execução
            conjunto: Identificador do conjunto de parâmetros
            ag: Instância do AlgoritmoGenetico
            
        Nota: Útil para consolidar apenas os resultados finais de múltiplas execuções,
        criando um dataset mais enxeto para análise comparativa.
        """
        from ClasseAlgoritmoGenetico import AlgoritmoGenetico
        
        # Obtém a melhor dieta da última geração (resultado final)
        dieta = self.historico_elites[-1]

        linha = {
            # Infos Extrato
            'UF': uf,
            'Faixa de Renda': faixa_renda,
            'Alvo Calorico': dieta.alvo_calorico,
            'Custo Alvo': dieta.custo_alvo,

            # Parâmetros do Algoritmo Genético
            'Conjunto': conjunto,
            'Execucao': execucao,
            'Tempo de Execucao (s)': tempo_execucao,
            'Numero de Individuos': ag.tamanho_populacao,
            'Numero de Geracoes': ag.numero_geracoes,
            'Taxa de Cruzamento': ag.taxa_cruzamento,
            'Taxa de Mutacao': ag.taxa_mutacao,
            'Proporcao de Elites': ag.numero_elites/ag.tamanho_populacao, # Armazena a proporção de elites em relação ao tamanho da população
            'Proporcao de Participantes por Torneio': ag.numero_participantes_torneio/ag.tamanho_populacao, # Armazena a proporção de participantes por torneio em relação ao tamanho da população
            'Probabilidade de Upset no Torneio': ag.probabilidade_upset_torneio,
            'Alfa Cruzamento': ag.alfa_cruzamento,
            'Beta Cruzamento': ag.beta_cruzamento,
            
            # Infos Dieta
            #'Componentes KCAL': [grupo.calorias for grupo in dieta.grupos_alimentares],
            #"Componentes % Calorico": [grupo.percentual_calorico for grupo in dieta.grupos_alimentares],
            #'Calorias Totais': dieta.calorias_totais,
            #'Custo Total': dieta.custo_total,            
            #'Penalizado': dieta.penalizado,
            #'Penalizacao Aplicada': dieta.penalizacao_aplicada,
            #'Pontuacao PHDI': dieta.pontuacao_phdi,
            #'Pontuacao FO': dieta.pontuacao_fo
        }        
        
        # Adiciona colunas individuais para cada grupo alimentar
        for grupo in dieta.grupos_alimentares:
            # Remove espaços e caracteres especiais para criar nome de coluna válido
            nome_coluna_safe = grupo.nome.replace(' ', '_').replace('(', '').replace(')', '').lower()
            
            # Coluna para calorias (ex: nuts_and_peanuts_kcal)
            linha[f'{nome_coluna_safe}_kcal'] = grupo.calorias
            
            # Coluna para percentual calórico (ex: nuts_and_peanuts_perc)
            linha[f'{nome_coluna_safe}_perc'] = grupo.percentual_calorico
            
            # Coluna para pontuação PHDI (ex: nuts_and_peanuts_phdi)
            linha[f'{nome_coluna_safe}_phdi'] = grupo.pontuacao_phdi
            
            # Coluna para pontuação FO (ex: nuts_and_peanuts_fo)
            linha[f'{nome_coluna_safe}_fo'] = grupo.pontuacao_fo
            
            # Coluna para penalização (ex: nuts_and_peanuts_penalizado)
            linha[f'{nome_coluna_safe}_penalizado'] = grupo.penalizado
            linha[f'{nome_coluna_safe}_porcentagem_penalização'] = grupo.porcentagem_penalizacao
            linha[f'{nome_coluna_safe}_penalizacao'] = grupo.penalizacao_aplicada

        linha[f'Calorias Totais'] = dieta.calorias_totais
        linha[f'Custo Total'] = dieta.custo_total                
        linha[f'Dieta Penalizada?'] = dieta.penalizado
        linha[f'Penalizacao Aplicada'] = dieta.penalizacao_aplicada
        linha[f'Penalizacao por Calorias'] = dieta.penalizacao_calorias
        linha[f'Penalizacao por Custo'] = dieta.penalizacao_custo
        linha[f'Penalizacao por Aceitabilidade Aplicada'] = dieta.penalizacao_aceitabilidade
        linha[f'Pontuacao PHDI'] = dieta.pontuacao_phdi
        linha[f'Pontuacao FO'] = dieta.pontuacao_fo

        
        # Verifica existência do arquivo para decidir criação ou acréscimo
        if not os.path.exists(nome_arquivo):
            # Primeira execução: cria arquivo com cabeçalho
            # Nota: linha é envolvida em lista para criar DataFrame com uma única linha
            df = pd.DataFrame([linha])
            df.to_csv(nome_arquivo, index=False)
        else:
            # Acrescenta ao existente
            df = pd.DataFrame([linha])
            df.to_csv(nome_arquivo, mode='a', index=False, header=False)