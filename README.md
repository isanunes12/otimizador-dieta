# Otimizador de Dieta por Algoritmo Genético (PHDI)

Sistema web para otimizar dietas com um Algoritmo Genético: maximiza o PHDI respeitando meta calórica,
custo e aceitabilidade cultural de cada UF e faixa de renda (banco INA). Cada execução também roda um
método exato (ε-restrição com PuLP/CBC), que maximiza PHDI e aceitabilidade e mostra a fronteira de
Pareto em uma seção separada.

- **Backend:** Python + Flask (`backend/`)
- **Frontend:** React + TypeScript + Vite (`frontend/`)
- **Banco e login:** Firebase (Firestore + Authentication)
- **Execução:** Docker Compose

## 1. Configurar o Firebase (uma vez só)

No [Console do Firebase](https://console.firebase.google.com), no seu projeto:

1. **Authentication → Sign-in method →** ative **E-mail/senha**.
2. **Firestore Database →** crie o banco (se ainda não existir).
3. **Firestore → Regras →** cole o conteúdo de `firestore.rules` e publique.
   O frontend nunca acessa o Firestore direto; só a API (que usa o Admin SDK).
4. **Configurações do projeto → Contas de serviço → Gerar nova chave privada.**
   Salve o arquivo como `secrets/serviceAccountKey.json`.
   ⚠️ Nunca coloque esse arquivo dentro de `backend/` nem suba para o GitHub.
5. **Configurações do projeto → Geral →** copie a **Chave de API da Web**.

## 2. Configurar o projeto

Copie `.env.example` para `.env` (na raiz) e preencha:

```
FIREBASE_WEB_API_KEY=a-chave-de-api-da-web
FLASK_DEBUG=1
```

## 3. Rodar

```
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:5000/api/health

Crie uma conta na tela inicial e faça sua primeira execução.

## Estrutura

```
backend/
  app.py              rotas da API (extratos, otimizar, histórico)
  auth.py             valida o token do Firebase Auth enviado pelo frontend
  estratos.py         lê o CSV do INA e monta os 17 componentes por UF/faixa
  ga_engine.py        valida parâmetros, roda o AG com semente e monta o resultado
  Classe*.py          núcleo do algoritmo genético
  exact_engine.py     roda o método exato e monta o resultado para a API
  metodo_exato/       modelo matemático, solver e dados do método exato
frontend/src/
  App.tsx             navegação (nova execução, histórico, detalhe)
  components/         formulário, resultado, gráficos, histórico, login
  services/           chamadas à API e login (Firebase Auth via REST)
secrets/              chave da conta de serviço (fora do Git e da imagem Docker)
firestore.rules       regras do Firestore (bloqueia acesso direto do cliente)
```

## API

| Método | Rota | Login | Descrição |
|---|---|---|---|
| GET | `/api/strata` | não | lista os 109 extratos (UF × faixa de renda) |
| GET | `/api/strata/<uf>/<faixa>` | não | limites e preços dos 17 componentes |
| POST | `/api/optimize` | sim | roda o AG e o método exato e salva no histórico do usuário |
| GET | `/api/runs` | sim | histórico do usuário |
| GET | `/api/runs/<id>` | sim | detalhe com convergência geração a geração |
| DELETE | `/api/runs/<id>` | sim | exclui uma execução |

Os dados ficam em `users/{uid}/runs/{id}` no Firestore. Como cada usuário só acessa a própria
subcoleção, um usuário não consegue ler as execuções de outro.

Exemplo de corpo do `POST /api/optimize`:

```json
{
  "name": "MG faixa 2",
  "uf": 31,
  "faixa": 2,
  "params": { "generations": 100, "population_size": 100, "crossover_rate": 0.8,
              "mutation_rate": 0.1, "target_calories": 2000, "target_cost": 20, "seed": 42 },
  "adjustments": [{ "phdi_index": 12, "max_kcal": 150 }]
}
```

## Reprodutibilidade

Toda execução guarda a **semente aleatória** (`seed`). A mesma semente, com os mesmos parâmetros
e o mesmo extrato, gera exatamente o mesmo resultado. Para repetir uma execução, use
"Repetir com estes parâmetros" na tela de resultado.

## Limites

- Gerações ≤ 2000, população ≤ 2000 e gerações × população ≤ 500.000.
  Para referência, 500 × 500 leva cerca de 17 s.
- A execução é síncrona: a requisição fica aberta até o AG terminar.
