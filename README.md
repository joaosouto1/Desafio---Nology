# Programa de Cashback — Guia de Entrega e Deploy

## Arquivos entregues

| Arquivo                  | Descrição                                          |
|--------------------------|----------------------------------------------------|
| `cashback.py`            | Módulo Python com engine de cálculo (questão 1)    |
| `api.py`                 | Backend FastAPI com banco Postgres (questão 5)     |
| `frontend_index.html`    | Frontend estático (questão 5)                      |
| `cashback_respostas.docx`| Respostas das questões 2, 3 e 4 em Word            |
| `README.md`              | Este arquivo                                       |

---

## Regras de negócio implementadas

1. **Cashback base**: 5% sobre o valor final da compra (após descontos) — *Doc 1*
2. **Bônus VIP**: +10% adicional sobre o cashback base → `base × 1.10` — *Doc 1*
3. **Dobro**: compras com valor final > R$ 500 = cashback dobrado (todos os clientes) — *Doc 2*
4. **Ordem de cálculo**: base → VIP → dobro — *Doc 3*

---

## Questão 1 — Código Python

```bash
python cashback.py
```

Demonstra automaticamente os 3 cenários (questões 2, 3 e 4).

---

## Questão 5 — Deploy do App

### Backend (FastAPI + PostgreSQL)

#### Pré-requisitos
```bash
pip install fastapi uvicorn psycopg2-binary
```

#### Banco de dados (PostgreSQL)
```sql
CREATE DATABASE cashback_db;
```
A tabela é criada automaticamente ao iniciar a API.

#### Configuração
Defina a variável de ambiente antes de rodar:
```bash
export DATABASE_URL="postgresql://user:senha@host:5432/cashback_db"
```

#### Rodar localmente
```bash
uvicorn api:app --reload --port 8000
```

#### Endpoints
| Método | URL          | Descrição                                  |
|--------|--------------|--------------------------------------------|
| POST   | `/calcular`  | Calcula cashback e registra no banco por IP |
| GET    | `/historico` | Retorna histórico do IP solicitante         |
| GET    | `/health`    | Health check                               |

#### Exemplo de chamada (POST /calcular)
```bash
curl -X POST http://localhost:8000/calcular \
  -H "Content-Type: application/json" \
  -d '{"tipo_cliente":"vip","valor_produto":600,"desconto_percent":20}'
```

---

### Frontend (HTML estático)

O arquivo `frontend_index.html` é 100% estático — basta abrir no navegador ou servir via qualquer servidor web/CDN (Netlify, Vercel, GitHub Pages, S3, etc.).

Para uso com o backend real, edite a constante `API_URL` no `<script>` do HTML:
```javascript
const API_URL = 'https://sua-api.exemplo.com';
```

#### Deploy gratuito sugerido
- **Frontend**: [Netlify Drop](https://app.netlify.com/drop) — arraste o HTML
- **Backend**: [Railway](https://railway.app) ou [Render](https://render.com) — suporte nativo a FastAPI + Postgres

---

## MySQL (alternativa ao PostgreSQL)

Substitua em `api.py`:
```python
# pip install mysql-connector-python
import mysql.connector
conn = mysql.connector.connect(host=..., user=..., password=..., database=...)
```
O SQL DDL é compatível — substitua `SERIAL` por `INT AUTO_INCREMENT`.

---

## Arquitetura

```
┌─────────────────────┐        POST /calcular        ┌──────────────────┐
│  Frontend estático  │ ─────────────────────────── ▶│  FastAPI (api.py)│
│  (HTML/JS puro)     │ ◀─────────────────────────── │  Python backend  │
└─────────────────────┘       JSON response           └────────┬─────────┘
                                                               │ INSERT/SELECT
                                                      ┌────────▼─────────┐
                                                      │  PostgreSQL DB   │
                                                      │  tabela: consultas│
                                                      └──────────────────┘
```
