CASHBACK_BASE_RATE = 0.05          
VIP_BONUS_RATE = 0.10              
DOUBLE_CASHBACK_THRESHOLD = 500.0  


def calcular_cashback(
    valor_produto: float,
    percentual_desconto: float = 0.0,
    is_vip: bool = False
) -> dict:
    if valor_produto < 0:
        raise ValueError("O valor do produto não pode ser negativo.")
    if not (0 <= percentual_desconto < 100):
        raise ValueError("O percentual de desconto deve ser entre 0 e 99.99.")

    # ── Valor final após desconto 'base de cálculo do cashback' 
    desconto_aplicado = valor_produto * (percentual_desconto / 100)
    valor_final = valor_produto - desconto_aplicado

    # ── Cashback base '5% sobre o valor final' 
    cashback_base = valor_final * CASHBACK_BASE_RATE

    # ── Bônus VIP '+10% sobre o cashback base'
    if is_vip:
        cashback_pos_vip = cashback_base * (1 + VIP_BONUS_RATE)
    else:
        cashback_pos_vip = cashback_base

    # ── Regra de dobro para compras acima de R$ 500 
    #aplica sobre o cashback já calculado (inclusive VIP)
    dobro_aplicado = valor_final > DOUBLE_CASHBACK_THRESHOLD
    if dobro_aplicado:
        cashback_final = cashback_pos_vip * 2
    else:
        cashback_final = cashback_pos_vip

    # ── Monta descrição detalhada 
    detalhes = (
        f"Valor produto: R$ {valor_produto:.2f}\n"
        f"Desconto ({percentual_desconto:.0f}%): -R$ {desconto_aplicado:.2f}\n"
        f"Valor final (base): R$ {valor_final:.2f}\n"
        f"Cashback base (5%): R$ {cashback_base:.2f}\n"
    )
    if is_vip:
        detalhes += (
            f"Bônus VIP (+10% sobre cashback base): "
            f"R$ {cashback_base:.2f} × 1.10 = R$ {cashback_pos_vip:.2f}\n"
        )
    if dobro_aplicado:
        detalhes += (
            f"Regra dobro (valor final > R$ {DOUBLE_CASHBACK_THRESHOLD:.0f}): "
            f"R$ {cashback_pos_vip:.2f} × 2 = R$ {cashback_final:.2f}\n"
        )
    detalhes += f"Cashback final: R$ {cashback_final:.2f}"

    return {
        "valor_produto": valor_produto,
        "desconto_aplicado": round(desconto_aplicado, 2),
        "valor_final": round(valor_final, 2),
        "cashback_base": round(cashback_base, 2),
        "cashback_pos_vip": round(cashback_pos_vip, 2),
        "cashback_final": round(cashback_final, 2),
        "dobro_aplicado": dobro_aplicado,
        "is_vip": is_vip,
        "detalhes": detalhes,
    }


# ─── Demonstração dos cenários solicitados 
if __name__ == "__main__":
    separador = "=" * 60

    print(separador)
    print("CENÁRIO 2 — Cliente VIP | R$ 600 | Cupom 20% off")
    print(separador)
    r2 = calcular_cashback(valor_produto=600, percentual_desconto=20, is_vip=True)
    print(r2["detalhes"])

    print()
    print(separador)
    print("CENÁRIO 3 — Cliente normal | R$ 600 | Cupom 10% off")
    print(separador)
    r3 = calcular_cashback(valor_produto=600, percentual_desconto=10, is_vip=False)
    print(r3["detalhes"])

    print()
    print(separador)
    print("CENÁRIO 4 (Suporte) — Cliente VIP | R$ 600 | Cupom 15% off")
    print(separador)
    r4 = calcular_cashback(valor_produto=600, percentual_desconto=15, is_vip=True)
    print(r4["detalhes"])
