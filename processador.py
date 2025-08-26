def processar_comprovante(texto):
    try:
        texto = texto.lower().replace("r$", "").replace(" ", "")
        texto = texto.replace(",", ".")
        valor = None
        parcelas = 1
        taxa = 0.0

        if "pix" in texto:
            valor = float(texto.replace("pix", ""))
            taxa = 0.2
        elif "x" in texto:
            partes = texto.split("x")
            valor = float(partes[0])
            parcelas = int(partes[1])
            tabela = {
                1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59,
                5: 7.19, 6: 8.29, 7: 9.19, 8: 9.99, 9: 10.29,
                10: 10.88, 11: 11.99, 12: 12.52, 13: 13.69, 14: 14.19,
                15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
            }
            taxa = tabela.get(parcelas, 0)
        else:
            return None

        valor_liquido = valor * (1 - taxa / 100)

        return {
            "valor_bruto": f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "parcelas": parcelas,
            "taxa": taxa,
            "valor_liquido": round(valor_liquido, 2),
            "pago": False
        }

    except Exception as e:
        print("Erro ao processar:", e)
        return None

