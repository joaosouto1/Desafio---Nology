import os
from datetime import datetime

import psycopg2
import psycopg2.pool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# ── Config 
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/cashback_db"
)

app = FastAPI(title="Cashback API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Regras de negócio 
CASHBACK_BASE_RATE      = 0.05   
VIP_BONUS_RATE          = 0.10   
DOUBLE_CASHBACK_THRESHOLD = 500.0  


# ── DB helpers 
def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    #Cria a tabela de consultas se não existir.
    ddl = """
    CREATE TABLE IF NOT EXISTS consultas (
        id          SERIAL PRIMARY KEY,
        ip_usuario  VARCHAR(45)   NOT NULL,
        tipo_cliente VARCHAR(10)  NOT NULL,   -- 'normal' | 'vip'
        valor_produto NUMERIC(12,2) NOT NULL,
        desconto_perc NUMERIC(5,2)  NOT NULL DEFAULT 0,
        valor_final   NUMERIC(12,2) NOT NULL,
        cashback      NUMERIC(12,2) NOT NULL,
        criado_em     TIMESTAMP    NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_consultas_ip ON consultas(ip_usuario);
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


# ── Schemas 
class CalcularRequest(BaseModel):
    tipo_cliente:     str   # "normal" | "vip"
    valor_produto:    float
    desconto_percent: float = 0.0

    @field_validator("tipo_cliente")
    @classmethod
    def validar_tipo(cls, v):
        if v.lower() not in ("normal", "vip"):
            raise ValueError("tipo_cliente deve ser 'normal' ou 'vip'")
        return v.lower()

    @field_validator("valor_produto")
    @classmethod
    def validar_valor(cls, v):
        if v <= 0:
            raise ValueError("valor_produto deve ser maior que zero")
        return v

    @field_validator("desconto_percent")
    @classmethod
    def validar_desconto(cls, v):
        if not (0 <= v < 100):
            raise ValueError("desconto_percent deve estar entre 0 e 99.99")
        return v


# ── Engine de cálculo (espelho do cashback.py) 
def calcular_cashback(tipo: str, valor: float, desconto: float) -> dict:
    """
    Aplica as regras de negócio documentadas:
      Doc 1: base=5%, VIP=+10% sobre base
      Doc 2: valor_final>500 → dobro
      Doc 3: ordem base → VIP → dobro
    """
    desconto_val = valor * (desconto / 100)
    valor_final  = valor - desconto_val

    cash_base = valor_final * CASHBACK_BASE_RATE

    is_vip = (tipo == "vip")
    cash_vip = cash_base * (1 + VIP_BONUS_RATE) if is_vip else cash_base

    dobro = valor_final > DOUBLE_CASHBACK_THRESHOLD
    cash_final = cash_vip * 2 if dobro else cash_vip

    return {
        "valor_final":  round(valor_final,  2),
        "cash_base":    round(cash_base,    2),
        "cash_vip":     round(cash_vip,     2),
        "cash_final":   round(cash_final,   2),
        "dobro":        dobro,
        "is_vip":       is_vip,
    }


# ── Endpoints 
@app.post("/calcular")
def calcular(req: CalcularRequest, request: Request):
    """Calcula cashback, persiste no banco e retorna o resultado."""
    ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    res = calcular_cashback(req.tipo_cliente, req.valor_produto, req.desconto_percent)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO consultas
                    (ip_usuario, tipo_cliente, valor_produto, desconto_perc, valor_final, cashback)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (ip, req.tipo_cliente, req.valor_produto,
                 req.desconto_percent, res["valor_final"], res["cash_final"])
            )
        conn.commit()
    finally:
        conn.close()

    return {
        "tipo_cliente":   req.tipo_cliente,
        "valor_produto":  req.valor_produto,
        "desconto_perc":  req.desconto_percent,
        "valor_final":    res["valor_final"],
        "cashback_base":  res["cash_base"],
        "cashback_vip":   res["cash_vip"] if res["is_vip"] else None,
        "dobro_aplicado": res["dobro"],
        "cashback_final": res["cash_final"],
        "ip_registrado":  ip,
    }


@app.get("/historico")
def historico(request: Request):
    #Retorna as últimas 50 consultas do IP que faz a requisição.
    ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tipo_cliente, valor_produto, desconto_perc,
                       valor_final, cashback, criado_em
                FROM consultas
                WHERE ip_usuario = %s
                ORDER BY criado_em DESC
                LIMIT 50
                """,
                (ip,)
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return {
        "ip": ip,
        "total": len(rows),
        "consultas": [
            {
                "tipo_cliente":   r[0],
                "valor_produto":  float(r[1]),
                "desconto_perc":  float(r[2]),
                "valor_final":    float(r[3]),
                "cashback":       float(r[4]),
                "data":           r[5].isoformat(),
            }
            for r in rows
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
