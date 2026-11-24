from ClasseDieta import Dieta
from ClasseGrupoAlimentar import GrupoAlimentar
from ClasseFerramentas import Ferramentas
from typing import List, Optional, Dict
import random

# Váriaveis globais
"""
Dicionário global com a definição completa dos grupos alimentares do PHDI.
"""
COMPONENTES_PHDI = [            
            # Componente de Adequação (grupos 0-4): quanto mais, melhor, até o limite
            {'grupo': 'Nuts and peanuts', 'limite': 11.6},                                                          #0
            {'grupo': 'Legumes', 'limite': 11.3},                                                                   #1
            {'grupo': 'Fruits', 'limite': 5.0},                                                                     #2
            {'grupo': 'Vegetables', 'limite': 3.1},                                                                 #3
            {'grupo': 'Whole cereals', 'limite': 32.4},                                                             #4

            # Componente Ótimo (grupos 5-9): faixa ótima entre mínimo e máximo
            {'grupo': 'Eggs', 'limite_inferior': 0.0, 'limite_otimo' : 0.8, 'limite_superior': 1.5},                #5
            {'grupo': 'Fish and seafood', 'limite_inferior': 0.0, 'limite_otimo' : 1.6, 'limite_superior': 5.7},    #6
            {'grupo': 'Tubers and potatoes', 'limite_inferior': 0.0, 'limite_otimo' : 1.6, 'limite_superior': 3.1}, #7
            {'grupo': 'Dairy', 'limite_inferior': 0.0, 'limite_otimo' : 6.1, 'limite_superior': 12.2},              #8
            {'grupo': 'Vegetable oils', 'limite_inferior': 0.0, 'limite_otimo' : 16.5, 'limite_superior': 30.7},    #9

            # Componente Proporção (grupos 10-11): DGV e REV, relacionados ao grupo dos vegetais    
            {'grupo': 'DGV', 'limite_inferior': 0.0, 'limite_otimo' : 29.5, 'limite_superior': 100.0},              #10
            {'grupo': 'REV', 'limite_inferior': 0.0, 'limite_otimo' : 38.5, 'limite_superior': 100.0},              #11

            # Componente Moderação (grupos 12-15): quanto menos, melhor
            {'grupo': 'Red meat', 'limite': 2.4},                                                                   #12
            {'grupo': 'Chicken and substitutes', 'limite': 5.0},                                                    #13
            {'grupo': 'Animal fats', 'limite': 1.4},                                                                #14
            {'grupo': 'Added sugars', 'limite': 4.8},                                                               #15
            {'grupo': 'Cereais Refinados'}                                                                          #16
        ]
 

class AlgoritmoGenetico:
    """
    Implementa um algoritmo genético para otimização de dietas considerando múltiplos critérios.
    
    Atributos:
        numero_geracoes (int): Número máximo de gerações a serem executadas.
        tamanho_populacao (int): Número de indivíduos (dietas) na população.
        taxa_cruzamento (float): Probabilidade de ocorrer cruzamento entre pais [0, 1].
        taxa_mutacao (float): Probabilidade de mutação em cada gene [0, 1].
        numero_elites (int): Número de melhores indivíduos que sobrevivem sem alterações.
        numero_participantes_torneio (int): Número de competidores em cada torneio.
        probabilidade_upset_torneio (float): Chance de indivíduo pior vencer um confronto [0, 1].
        alfa_cruzamento (float): Parâmetro de expansão para lado inferior (melhor pai) no cruzamento BLX.
        beta_cruzamento (float): Parâmetro de expansão para lado superior (pior pai) no cruzamento BLX.
        is_maximizacao (bool): True se o problema é de maximização, False para minimização
    """

    def __init__(self,
                 numero_geracoes: int,
                 tamanho_populacao: int,
                 taxa_cruzamento: float,
                 taxa_mutacao: float,
                 numero_elites: int,
                 numero_participantes_torneio: int,
                 probabilidade_upset_torneio: float,
                 alfa_cruzamento: float,
                 beta_cruzamento: float,
                 is_maximizacao: bool) -> None:
        """
        Inicializa os parâmetros do algoritmo genético.
        
        Args:
            numero_geracoes: Número de iterações do algoritmo
            tamanho_populacao: Tamanho da população em cada geração
            taxa_cruzamento: Probabilidade de cruzamento entre indivíduos
            taxa_mutacao: Probabilidade de mutação em cada gene
            numero_elites: Número de melhores indivíduos preservados
            numero_participantes_torneio: Competidores por torneio
            probabilidade_upset_torneio: Chance de vitória do pior indivíduo
            alfa_cruzamento: Fator de expansão inferior (melhor pai) no cruzamento BLX
            beta_cruzamento: Fator de expansão superior (pior pai) no cruzamento BLX
            is_maximizacao: True para maximizar fitness, False para minimizar
        """
        self.numero_geracoes = numero_geracoes
        self.tamanho_populacao = tamanho_populacao
        self.taxa_cruzamento = taxa_cruzamento
        self.taxa_mutacao = taxa_mutacao
        self.numero_elites = numero_elites
        self.numero_participantes_torneio = numero_participantes_torneio
        self.probabilidade_upset_torneio = probabilidade_upset_torneio
        self.alfa_cruzamento = alfa_cruzamento
        self.beta_cruzamento = beta_cruzamento
        self.is_maximizacao = is_maximizacao

    @staticmethod
    def verifica_aceitabilidade_cultural(grupo_alimentar: GrupoAlimentar, limites_aceitabilidade_cultural: Dict[str, float]) -> float:
        """
        Verifica se o componente ultrapassou os limites de aceitabilidade cultural quando o consumo está fora dos limites.
        
        Args:
            grupo_alimentar: Grupo alimentar a ser avaliado.
            limites_aceitabilidade_cultural: Dicionário com limites mínimo e máximo de aceitação.
        """   
        #Returns:
        #    float: Percentual que ultrapassou os limites.
            
        #Nota: O percentual é limitado a 100%.

        # Verifica se está abaixo do mínimo aceitável
        if grupo_alimentar.calorias < limites_aceitabilidade_cultural['minimo']:
            grupo_alimentar.porcentagem_penalizacao = abs(grupo_alimentar.calorias - limites_aceitabilidade_cultural['minimo']) / limites_aceitabilidade_cultural['minimo']           
            return #percentual
        
        # Verifica se está acima do máximo aceitável
        elif grupo_alimentar.calorias > limites_aceitabilidade_cultural['maximo']:
            if limites_aceitabilidade_cultural['maximo'] == 0: # Evita divisão por zero, caso o limite máximo seja zero
                grupo_alimentar.porcentagem_penalizacao = abs(grupo_alimentar.calorias - 0.000001) / 0.000001
                return #percentual
            else:
                grupo_alimentar.porcentagem_penalizacao = abs(grupo_alimentar.calorias - limites_aceitabilidade_cultural['maximo']) / limites_aceitabilidade_cultural['maximo']               
                return #percentual
        else:  # Dentro dos limites aceitáveis, sem penalização
            grupo_alimentar.porcentagem_penalizacao = 0.0
            return #0.0

    @staticmethod
    def funcao_objetivo(dieta: Dieta, limites_aceitabilidade_cultural: Dict[str, float]) -> None:
        """
        Avalia a qualidade de uma dieta calculando a pontuação PHDI e aplicando penalizações.
        
        Args:
            dieta: Dieta a ser avaliada
            limites_aceitabilidade_cultural: Limites culturais para cada grupo alimentar
        """      

        pontuacao_total = 0
        penalizacao_total = 0        
        percentuais_ultrapassados_aceitabilidade = []  # Para armazenar os percentuais de ultrapassagem de aceitabilidade cultural de cada grupo penalizado 

        for i, grupo_alimentar in enumerate(dieta.grupos_alimentares):

            # Componentes de Adequação (grupos 0-4)
            if i in range(5):
                # Pontuação proporcional até o limite máximo (máx 10 pontos)
                pontuacao = min(10, (grupo_alimentar.percentual_calorico / COMPONENTES_PHDI[i]['limite'] * 10)) # Calcula a pontuação do grupo alimentar
                grupo_alimentar.pontuacao_phdi = pontuacao
                pontuacao_total += pontuacao

                # Verifica se o componente ultrapassa a aceitabilidade cultural
                AlgoritmoGenetico.verifica_aceitabilidade_cultural(grupo_alimentar, limites_aceitabilidade_cultural[i])
                    
            # Componentes Ótimos (grupos 5-9)
            if i in range(5, 10):
                pontuacao = None

                # Dentro da faixa ideal: pontuação crescente até o ótimo
                if COMPONENTES_PHDI[i]['limite_inferior'] <= grupo_alimentar.percentual_calorico <= COMPONENTES_PHDI[i]['limite_otimo']:
                    pontuacao = (grupo_alimentar.percentual_calorico) / (COMPONENTES_PHDI[i]['limite_otimo']) * 10
                
                # Acima do ótimo mas abaixo do máximo: pontuação decrescente
                elif grupo_alimentar.percentual_calorico <= COMPONENTES_PHDI[i]['limite_superior']:
                    pontuacao = 10 - (grupo_alimentar.percentual_calorico - COMPONENTES_PHDI[i]['limite_otimo']) / (COMPONENTES_PHDI[i]['limite_superior'] - COMPONENTES_PHDI[i]['limite_otimo']) * 10
                
                # Acima do máximo: pontuação zero
                else:
                    pontuacao = 0.0

                grupo_alimentar.pontuacao_phdi = pontuacao
                pontuacao_total += pontuacao
                
                # Verifica se o componente ultrapassa a aceitabilidade cultural
                AlgoritmoGenetico.verifica_aceitabilidade_cultural(grupo_alimentar, limites_aceitabilidade_cultural[i])

            # Componentes de Proporção (grupos 10-11)
            if i in range(10, 12): # Se são os grupos de proporção
                pontuacao = None

                # Dentro da faixa ideal: pontuação crescente (máx 5 pontos)
                if COMPONENTES_PHDI[i]['limite_inferior'] <= grupo_alimentar.percentual_calorico <= COMPONENTES_PHDI[i]['limite_otimo']:
                    pontuacao = (grupo_alimentar.percentual_calorico) / (COMPONENTES_PHDI[i]['limite_otimo']) * 5
                
                # Acima do ótimo: pontuação decrescente
                else:
                    pontuacao = 5 - (grupo_alimentar.percentual_calorico - COMPONENTES_PHDI[i]['limite_otimo']) / (COMPONENTES_PHDI[i]['limite_superior'] - COMPONENTES_PHDI[i]['limite_otimo']) * 5

                grupo_alimentar.pontuacao_phdi = pontuacao
                pontuacao_total += pontuacao

                # Verifica se o componente ultrapassa a aceitabilidade cultural
                AlgoritmoGenetico.verifica_aceitabilidade_cultural(grupo_alimentar, limites_aceitabilidade_cultural[i])

            # Componentes de Moderação (grupos 12-15)
            if i in range(12, 16):
                pontuacao = None
                # Acima do limite recomendado: pontuação zero
                if grupo_alimentar.percentual_calorico >= COMPONENTES_PHDI[i]['limite']:
                    pontuacao = 0.0
                
                # Abaixo do limite: pontuação decrescente com o consumo
                else:
                    pontuacao = 10 - (grupo_alimentar.percentual_calorico / COMPONENTES_PHDI[i]['limite'] * 10)
                grupo_alimentar.pontuacao_phdi = pontuacao
                pontuacao_total += pontuacao

                # Verifica se o componente ultrapassa a aceitabilidade cultural
                AlgoritmoGenetico.verifica_aceitabilidade_cultural(grupo_alimentar, limites_aceitabilidade_cultural[i])
            
            if i == 16: # Cereais Refinados
                # Verifica se o componente ultrapassa a aceitabilidade cultural
                AlgoritmoGenetico.verifica_aceitabilidade_cultural(grupo_alimentar, limites_aceitabilidade_cultural[i])

        # Penaliza dietas que não são isocalóricas proporcionalmente ao excesso em relação ao alvo. Ex: 2500 - 2000 / 2000 = 0.25
        # if dieta.calorias_totais < (dieta.alvo_calorico * 0.95): # Permite uma margem de 5% para variações calóricas, sem penalização
        #     percentual_calorico_excedente = abs(dieta.calorias_totais - (dieta.alvo_calorico * 0.95)) / (dieta.alvo_calorico * 0.95)
        #     penalizacao = percentual_calorico_excedente * pontuacao_total        
        #     penalizacao_total += penalizacao
        #     dieta.penalizacao_calorias = penalizacao

        # if dieta.calorias_totais > (dieta.alvo_calorico * 1.05): # Permite uma margem de 5% para variações calóricas, sem penalização
        #     percentual_calorico_excedente = abs(dieta.calorias_totais - (dieta.alvo_calorico * 1.05)) / (dieta.alvo_calorico * 1.05)
        #     penalizacao = percentual_calorico_excedente * pontuacao_total        
        #     penalizacao_total += penalizacao
        #     dieta.penalizacao_calorias = penalizacao

        if dieta.calorias_totais != dieta.alvo_calorico:
            percentual_calorico_excedente = abs(dieta.calorias_totais - dieta.alvo_calorico) / dieta.alvo_calorico
            penalizacao = percentual_calorico_excedente * pontuacao_total        
            penalizacao_total += penalizacao
            dieta.penalizacao_calorias = penalizacao

        # Penaliza dietas que não atingem o custo alvo proporcionalmente ao déficit/excedente em relação ao alvo.        
        #if dieta.custo_total < (dieta.custo_alvo * 0.95): # Permite uma margem de 5% para variações de custo, sem penalização
        #    percentual_custo_excedente = abs(dieta.custo_total - (dieta.custo_alvo * 0.95)) / (dieta.custo_alvo * 0.95)
        #    penalizacao = percentual_custo_excedente * pontuacao_total
        #    penalizacao_total += penalizacao
        #    dieta.penalizacao_custo = penalizacao

        #if dieta.custo_total > (dieta.custo_alvo * 1.05): # Permite uma margem de 5% para variações de custo, sem penalização
        #    percentual_custo_excedente = abs(dieta.custo_total - (dieta.custo_alvo * 1.05)) / (dieta.custo_alvo * 1.05)
        #    penalizacao = percentual_custo_excedente * pontuacao_total
        #    penalizacao_total += penalizacao
        #    dieta.penalizacao_custo = penalizacao

        if dieta.custo_total > dieta.custo_alvo:            
            percentual_custo_excedente = abs(dieta.custo_total - dieta.custo_alvo) / dieta.custo_alvo
            penalizacao = percentual_custo_excedente * pontuacao_total
            penalizacao_total += penalizacao
            dieta.penalizacao_custo = penalizacao
        
        # Penaliza dietas que ultrapassaram os limites de aceitabilidade cultural em seus componentes proporcionalmente ao percentual de ultrapassagem / 16. Ex: Se um grupo ultrapassou o limite em 20%, a penalização será 20% da pontuação total da dieta dividida por 16.
        penalizacao_aceitabilidade = 0
        for grupo_alimentar in dieta.grupos_alimentares:
            if grupo_alimentar.porcentagem_penalizacao > 0.0:
                penalizacao = (grupo_alimentar.porcentagem_penalizacao * pontuacao_total) / 17
                penalizacao_total += penalizacao
                penalizacao_aceitabilidade += penalizacao
                grupo_alimentar.penalizado = True               
                grupo_alimentar.penalizacao_aplicada = penalizacao
                
            else:
                grupo_alimentar.penalizado = False
                
        dieta.penalizacao_aceitabilidade = penalizacao_aceitabilidade

        if penalizacao_total > 0:
            dieta.penalizado = True
            dieta.penalizacao_aplicada = penalizacao_total

        # Pontuação final da dieta (pode ser negativa se penalizações forem grandes)
        dieta.pontuacao_fo = pontuacao_total - penalizacao_total
        dieta.pontuacao_phdi = pontuacao_total

    def avaliacao_dietas(self, populacao: List[Dieta], limites_aceitabilidade_cultural: List[Dict[str, float]]) -> None:
        """
        Avalia uma população de dietas calculando suas pontuações e aplicando penalizações por aceitabilidade cultural.
        
        Args:
            populacao: Lista de dietas a serem avaliadas.
            limites_aceitabilidade_cultural: Limites culturais para cada grupo.
            
        Nota: Apenas avalia dietas que ainda não possuem pontuação calculada.
        """
        
        # Seleciona apenas as dietas que precisam de avaliação
        dietas_para_avaliar = [dieta for dieta in populacao if dieta.pontuacao_fo is None]

        if not dietas_para_avaliar:
            return  # Todas já avaliadas, não precisa rodar nada

        for dieta in dietas_para_avaliar:
            self.funcao_objetivo(dieta, limites_aceitabilidade_cultural)

    def cria_populacao_inicial(self, alvo_calorico: float, 
                               custo_alvo: float, 
                               consumo_min_max_componentes: List[Dict[str,float]],
                               valores_componentes: List[float]) -> List[Dieta]:
        
        """
        Cria população inicial aleatória dentro dos limites de consumo especificados.
        Nota: Os componentes DGV e REV terão suas calorias geradas em relação aos Vegetais.
        
        Args:
            alvo_calorico: Meta calórica das dietas
            custo_alvo: Meta de custo das dietas
            consumo_min_max_componentes: Limites mínimo e máximo para cada grupo
            valores_componentes: Valor por kcal de cada grupo alimentar
            
        Returns:
            List[Dieta]: População inicial de dietas aleatórias
        """
        
        populacao: List[Dieta] = []

        for i in range(self.tamanho_populacao):
            grupos: List[GrupoAlimentar] = []

            for j in range(17):
                grupos.append(GrupoAlimentar(nome= COMPONENTES_PHDI[j]['grupo']))
                grupos[j].valor_componente = valores_componentes[j]
                
                if grupos[j].nome in ['Nuts and peanuts', 'Whole cereals', 'Fish and seafood', 'DGV']:  # DGV e REV serão calculados depois
                    grupos[j].calorias = consumo_min_max_componentes[j]['maximo']  # Atribui o valor para os grupos com valores fixos
                else:
                    grupos[j].calorias = random.uniform(consumo_min_max_componentes[j]['minimo'], consumo_min_max_componentes[j]['maximo'])                

            # DGV e REV receberão porcentagens das calorias dos Vegetais
            percentual1 = random.uniform(0, 1)
            percentual2 = random.uniform(0, 1 - percentual1)

            if random.uniform(0, 1) <= 0.5:
                #grupos[10].calorias = grupos[3].calorias * percentual1 # DGV possui valor fixo agora
                grupos[11].calorias = grupos[3].calorias * percentual2   
            else:
                #grupos[10].calorias = grupos[3].calorias * percentual2 # DGV possui valor fixo agora
                grupos[11].calorias = grupos[3].calorias * percentual1           

            populacao.append(Dieta(grupos_alimentares= grupos, alvo_calorico= alvo_calorico, custo_alvo= custo_alvo))            
            populacao[i].alvo_calorico = alvo_calorico
            populacao[i].custo_alvo = custo_alvo

        return populacao

    def torneio_chaveado(self, populacao: List[Dieta]) -> List[Dieta]:
        """
        Realiza a seleção por torneio em formato de chaveamento (mata-mata).

        Nesse tipo de seleção, indivíduos são agrupados em torneios eliminatórios com partidas
        1 contra 1. É possível simular "upsets", onde um indivíduo pior pode vencer um confronto com certa probabilidade.

        Args:
            populacao: Lista de dietas para seleção
            
        Returns:
            List[Dieta]: Lista de pais selecionados
            
        Nota: Permite "upsets" onde indivíduos piores podem vencer com certa probabilidade
        """

        def proxima_potencia_de_dois(x: int) -> int:
            """Retorna a próxima potência de 2 maior ou igual a x (para completar os brackets)."""
            return 1 << (x - 1).bit_length()

        def partida(a: Dieta, b: Dieta) -> Dieta:
            """
            Realiza uma partida entre duas dietas com possibilidade de upset.
            
            Returns:
                Dieta: Vencedor do confronto
            """
            if a is None: return b  # Bye para b
            if b is None: return a  # Bye para a

            # Define quem é o melhor e o pior, de acordo com o objetivo
            if self.is_maximizacao:
                melhor, pior = (a, b) if a.pontuacao_fo >= b.pontuacao_fo else (b, a)
            else:
                melhor, pior = (a, b) if a.pontuacao_fo <= b.pontuacao_fo else (b, a)

            # Verifica se haverá upset
            if self.probabilidade_upset_torneio > 0 and random.random() < self.probabilidade_upset_torneio:
                return pior

            return melhor

        pais: List[Dieta] = []  # Lista de pais selecionados

        # Seleciona pais até completar o tamanho da população
        while len(pais) < self.tamanho_populacao:
            # 1) Seleciona competidores aleatórios para o bracket
            competidores = random.sample(populacao, self.numero_participantes_torneio)

            # 2) Define o tamanho do chaveamento como próxima potência de dois
            chaveamento = proxima_potencia_de_dois(self.numero_participantes_torneio)
            n_byes = chaveamento - self.numero_participantes_torneio

            # 3) Ordena os competidores por pontuacao_fo (melhores primeiros)
            competidores.sort(key=lambda ind: ind.pontuacao_fo, reverse= self.is_maximizacao) # Se o problema for de maximização, a lista vai ser ordenada em ordem decrescente

            # 4) Adiciona os byes (None) ao final dos slots
            slots = competidores + [None] * n_byes

            # 5) Executa as rodadas do torneio até sobrar 1 vencedor
            while len(slots) > 1:
                proxima_rodada = []
                for i in range(0, len(slots), 2):
                    vencedor = partida(slots[i], slots[i+1])
                    proxima_rodada.append(vencedor)
                slots = proxima_rodada

            # 6) O vencedor do torneio é adicionado aos pais
            pais.append(slots[0])

        return pais

    def cruzamento_blx_alfa_beta(self, pais: List[Dieta], consumo_min_max_componentes: List[Dict[str, float]]) -> List[Dieta]:
        """
        Realiza cruzamento BLX-α-β entre pares de pais.

        O método gera novos genes dentro de uma faixa expandida baseada nos genes dos pais,
        controlada pelos parâmetros alfa e beta. O cruzamento ocorre com uma probabilidade
        definida pela taxa de cruzamento.

        Se o problema for de minimização, o pai com menor pontuacao_fo lidera o cruzamento.
        Se for de maximização, o pai com maior pontuacao_fo lidera o cruzamento.

        Nota: Os componentes DGV e REV tem seu novo valor calórico definidos após cálculos a no máximo 50% das calorias dos Vegetais.
        Args:
            pais: Lista de pais selecionados
            consumo_min_max_componentes: Limites de consumo para cada grupo
            
        Returns:
            List[Dieta]: Filhos gerados pelo cruzamento                    
        """

        filhos: List[Dieta] = []
        
        # Processa pares de pais
        for i in range(0, self.tamanho_populacao, 2):
            pai_1 = pais[i]
            pai_2 = pais[i + 1]

            # Decide se ocorre cruzamento baseado na taxa
            if random.uniform(0, 1) <= self.taxa_cruzamento:
                grupos_alimentares_filho_1: List[GrupoAlimentar] = []
                grupos_alimentares_filho_2: List[GrupoAlimentar] = []

                # Decide a ordem dos pais com base no fitness
                if (self.is_maximizacao and pai_1.pontuacao_fo >= pai_2.pontuacao_fo) or (not self.is_maximizacao and pai_1.pontuacao_fo <= pai_2.pontuacao_fo):
                    melhor, pior = pai_1, pai_2
                else:
                    melhor, pior = pai_2, pai_1

                
                # Faz o cruzamento gene a gene
                for j, (grupo_alimentar_melhor, grupo_alimentar_pior) in enumerate(zip(melhor.grupos_alimentares, pior.grupos_alimentares)):
                    distancia = abs(grupo_alimentar_melhor.calorias - grupo_alimentar_pior.calorias)
                    
                    calorias_filho_1 = None
                    calorias_filho_2 = None

                    if grupo_alimentar_melhor.nome in ['Nuts and peanuts', 'Whole cereals', 'Fish and seafood', 'DGV']: #Verifica se o grupo da vez é um dos que tem valores fixos para evitar realizar contas
                        grupos_alimentares_filho_1.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= grupo_alimentar_melhor.calorias))
                        grupos_alimentares_filho_2.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= grupo_alimentar_melhor.calorias))
                        continue  # Pula para o próximo grupo, sem cruzamento
                    
                    else:

                        # Determina limites do intervalo de cruzamento
                        if grupo_alimentar_melhor.calorias <= grupo_alimentar_pior.calorias:
                            min_val = grupo_alimentar_melhor.calorias - (self.alfa_cruzamento * distancia)
                            max_val = grupo_alimentar_pior.calorias + (self.beta_cruzamento * distancia)
                        else:
                            min_val = grupo_alimentar_pior.calorias - (self.beta_cruzamento * distancia)
                            max_val = grupo_alimentar_melhor.calorias + (self.alfa_cruzamento * distancia)

                        # Garante que valores estejam dentro dos limites permitidos
                        if min_val < consumo_min_max_componentes[j]['minimo']:
                            min_val = consumo_min_max_componentes[j]['minimo']    

                        if max_val > consumo_min_max_componentes[j]['maximo']:
                            max_val = consumo_min_max_componentes[j]['maximo']           

                        # Tratamento especial para o grupo REV
                        if grupo_alimentar_melhor.nome == 'REV':
                            calorias_filho_1 = random.uniform(min_val, max_val) 
                            if calorias_filho_1 > grupos_alimentares_filho_1[3].calorias / 2:  # 50% de Vegetables
                                calorias_filho_1 = grupos_alimentares_filho_1[3].calorias / 2

                            calorias_filho_2 = random.uniform(min_val, max_val)
                            if calorias_filho_2 > grupos_alimentares_filho_2[3].calorias / 2:  # 50% de Vegetables
                                calorias_filho_2 = grupos_alimentares_filho_2[3].calorias / 2

                            grupos_alimentares_filho_1.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= calorias_filho_1))
                            grupos_alimentares_filho_2.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= calorias_filho_2))
                        
                        # Cruzamento normal para outros grupos
                        else:   
                            grupos_alimentares_filho_1.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= random.uniform(min_val, max_val)))
                            grupos_alimentares_filho_2.append(GrupoAlimentar(nome= grupo_alimentar_melhor.nome, valor_componente= grupo_alimentar_melhor.valor_componente, calorias= random.uniform(min_val, max_val)))

                # Cria filhos com os grupos gerados
                filhos.append(Dieta(grupos_alimentares= grupos_alimentares_filho_1, alvo_calorico= pai_1.alvo_calorico, custo_alvo= pai_1.custo_alvo))
                filhos.append(Dieta(grupos_alimentares= grupos_alimentares_filho_2, alvo_calorico= pai_2.alvo_calorico, custo_alvo= pai_2.custo_alvo))

            else:
                # Caso não ocorra cruzamento, copia os pais diretamente
                filhos.append(pai_1.copia())
                filhos.append(pai_2.copia())

        return filhos

    def mutacao_aleatoria(self, populacao: List[Dieta], 
                          consumo_min_max_componentes: List[Dict[str,float]]) -> None:
        """
        Aplica mutação aleatória em cada gene das dietas.
        Nota: Os componentes DGV e REV serão mutados se, e somente se, os vegetais sofrerem mutação.
        
        Args:
            populacao: Lista de dietas a sofrer mutação
            consumo_min_max_componentes: Limites para os novos valores
            
        Nota: Cada grupo alimentar tem chance independente de sofrer mutação
        """
        for dieta in populacao:
            vegetais_mutou = False
            dieta_mutou = False

            for i, grupo in enumerate(dieta.grupos_alimentares):

                if grupo.nome not in ['Nuts and peanuts', 'Whole cereals', 'Fish and seafood', 'DGV', 'REV']: #Verifica se o grupo da vez é um dos que tem valores fixos para evitar realizar contas, (REV só está na lista para evitar um if a mais, ele não é classificado como fixo)
                    # Verifica se ocorre mutação neste gene
                    if random.uniform(0, 1) <= self.taxa_mutacao:  
                        if grupo.nome == 'Vegetables':
                            vegetais_mutou = True
                        # Reseta o grupo e atribui novo valor aleatório
                        dieta_mutou = True
                        grupo.reset()
                        grupo.calorias = random.uniform(consumo_min_max_componentes[i]['minimo'], consumo_min_max_componentes[i]['maximo'])
            
            # Reseta alguns atributos da dieta para que na virada da geração, eles sejam recalculados 
            if dieta_mutou:
                dieta.reset()

            if vegetais_mutou:
                #print(len(dieta.grupos_alimentares))
                dieta.grupos_alimentares[11].reset()
                
                # DGV e REV receberão porcentagens das calorias dos Vegetais
                percentual1 = random.uniform(0, 1)
                percentual2 = random.uniform(0, 1 - percentual1)

                if random.uniform(0, 1) <= 0.5:
                    #dieta.grupos_alimentares[10].calorias = dieta.grupos_alimentares[3].calorias * percentual1 # DGV possui valor fixo agora
                    dieta.grupos_alimentares[11].calorias = dieta.grupos_alimentares[3].calorias * percentual2   
                else:
                    #dieta.grupos_alimentares[10].calorias = dieta.grupos_alimentares[3].calorias * percentual2 # DGV possui valor fixo agora
                    dieta.grupos_alimentares[11].calorias = dieta.grupos_alimentares[3].calorias * percentual1   

    def elitismo(self, populacao: List[Dieta]) -> List[Dieta]:
        """
        Seleciona os melhores indivíduos da população para preservação.
        
        Args:
            populacao: População atual
            
        Returns:
            List[Dieta]: Indivíduos de elite selecionados
        """
        # Ordena população por fitness
        populacao_ordenada = sorted(
            populacao,
            key=lambda ind: ind.pontuacao_fo,
            reverse=self.is_maximizacao
        )

        # Seleciona os primeiros 'numero_elites' indivíduos da população ordenada
        elites = [populacao_ordenada[i] for i in range(self.numero_elites)]

        return elites
    
    def nova_geracao(self, elites: List[Dieta], filhos_mutados: List[Dieta]) -> List[Dieta]:
        """
        Combina elites e filhos mutados para formar nova geração.
        
        Args:
            elites: Indivíduos de elite preservados
            filhos_mutados: Filhos após mutação
            
        Returns:
            List[Dieta]: Nova população completa
        """
        nova_populacao = elites.copy()
        numero_faltante = self.tamanho_populacao - len(elites)

        # Adiciona os filhos mutados até completar o tamanho da população
        nova_populacao.extend(filhos_mutados[:numero_faltante])

        return nova_populacao
       
    def algoritmo_genetico(self,
                           ferramentas: Ferramentas,
                           alvo_calorico: float,
                           custo_alvo: float,
                           consumo_min_max_componentes: List[Dict[str,float]],
                           valores_componentes: List[float],
                           limites_aceitabilidade_cultural: List[Dict[str, float]]
                           ) -> None:        
        """
        Executa o fluxo principal do algoritmo genético.
        
        Args:
            ferramentas: Objeto para armazenamento de dados e utilidades
            alvo_calorico: Meta calórica das dietas
            custo_alvo: Meta de custo das dietas
            consumo_min_max_componentes: Limites de consumo por grupo
            valores_componentes: Valor por kcal de cada grupo
            limites_aceitabilidade_cultural: Limites culturais por grupo
            
        Nota: Este método executa o ciclo completo do algoritmo genético por N gerações
        """
        
        def atualiza_dietas(populacao: List[Dieta]) -> None:
            """Atualiza cálculos agregados de todas as dietas."""
            for dieta in populacao:
                dieta.calcular_calorias_totais()
                dieta.calcular_percentual_calorico()
                dieta.calcular_custo_dieta()
        
        # Inicialização da população
        populacao: List[Dieta] = []        
        populacao = self.cria_populacao_inicial(alvo_calorico= alvo_calorico, 
                                                custo_alvo= custo_alvo,
                                                consumo_min_max_componentes= consumo_min_max_componentes, 
                                                valores_componentes= valores_componentes)

        # atualiza_dietas(populacao= populacao)

        # print('\n\n--- Populacao Inicial ---\n\n')
        # for dieta in populacao:            
        #     print('\n')
        #     print(dieta)

        # Loop principal de gerações
        for i in range(self.numero_geracoes):          

            # Atualiza cálculos das dietas
            atualiza_dietas(populacao= populacao)
            
            # Avaliação da população
            self.avaliacao_dietas(populacao= populacao, limites_aceitabilidade_cultural= limites_aceitabilidade_cultural)
            
            # print('\n\n--- Populacao Pós Avaliação ---\n\n')
            # for dieta in populacao:                
            #     print('\n')
            #     print(dieta)

            # Armazena dados da geração atual
            ferramentas.armazena_populacao(populacao= populacao)
            
            # Seleção por torneio
            pais = self.torneio_chaveado(populacao= populacao)
            
            # print('\n\n--- Pais ---\n\n')
            # for dieta in pais:              
            #     print('\n')
            #     print(dieta)

            # Cruzamento
            filhos = self.cruzamento_blx_alfa_beta(pais= pais, consumo_min_max_componentes= consumo_min_max_componentes)
            
            # print('\n\n--- Filhos ---\n\n')
            # for dieta in filhos:         
            #     print('\n')
            #     print(dieta.alvo_calorico)
            #     print(dieta)            
            
            # Mutação
            self.mutacao_aleatoria(populacao= filhos,
                                   consumo_min_max_componentes= consumo_min_max_componentes)
            
            # print('\n\n--- Filhos Pós Mutação ---\n\n')
            # for dieta in filhos:                
            #     print('\n')
            #     print(dieta)

            # Seleção de elites
            elites = self.elitismo(populacao= populacao)
            
            # print('\n\n--- Elites ---\n\n')
            # for dieta in elites:
            #     print('\n')                
            #     print(dieta)

            # Armazena elites
            ferramentas.armazena_elites(elites= elites)

            # Formação da nova geração
            populacao = self.nova_geracao(elites= elites, filhos_mutados= filhos)
            
            # print('\n\n--- Nova População ---\n\n')
            # for dieta in populacao:               
            #     print('\n')
            #     print(dieta)
