import re
from datetime import datetime

# Tabela de taxas (por número de parcelas)
TAXAS_CARTAO = {
    1: 4.39, 2: 5.19, 3: 6.19, 4: 6.59, 5: 7.19, 6: 8.29,
    7: 9.19, 8: 9.99, 9: 10.29, 10: 10.88, 11: 11.99, 12: 12.52,
    13: 13.69, 14: 14.19, 15: 14.69, 16: 15.19, 17: 15.89, 18: 16.84
}

ADMIN_ID = 123456789  # ⛔️ Substitua pelo SEU ID se quiser limitar comandos como /limpar

comprovantes = []

def analisar_mensagem(texto, user_id=None):
    texto = texto.lower().strip()

    if texto == "ajuda":
        return (
            "📌 *Comandos disponíveis:*\n"
            "• `1000 pix` → Calcula com taxa PIX (0.2%)\n"
            "• `7899,99 10x` → Calcula com 10 parcelas no cartão\n"
            "• `✅` → Marca último comprovante como pago\n"
            "• `total que devo` → Mostra valor total pendente\n"
            "• `listar pendentes` → Lista todos os não pagos\n"
            "• `listar pagos` → Lista os pagos\n"
            "• `último comprovante` → Mostra o último enviado\n"
            "• `total geral` → Mostra total geral\n"
            "• `/limpar tudo` → Limpa TODOS os dados (admin)\n"
            "• `/corrigir valor` → Corrige valor do último (admin)\n"
        )

    if texto.startswith("/limpar") and user_id == ADMIN_ID:
        comprovantes.clear()
        return "🚨 Todos os comprovantes foram apagados."

    if texto.startswith("/corrigir valor") and user_id == ADMIN_ID:
        return "Digite o novo valor para substituir o anterior (ex: 4500,00 3x)"

    if texto.startswith("✅"):
        for c in reversed(comprovantes):
            if not c["pago"]:
                c["pago"] = True
                return f"✅ Marcado como pago: R$ {c['valor_liquido']:.2f}"
        return "Não há comprovantes pendentes."

    if texto == "total que devo":
        total = sum(c["valor_liquido"] for c in comprovantes if not c["pago"])
        return f"📌 Total que você deve ao lojista: R$ {total:.2f}"

    if texto == "listar pendentes":
        lista = [f"• R$ {c['valor_liquido']:.2f} - {c['parcelas']}x" for c in comprovantes if not c["pago"]]
        return "📋 *Pendentes:*\n" + "\n".join(lista) if lista else "✅ Nenhum comprovante pendente."

    if texto == "listar pagos":
        lista = [f"• R$ {c['valor_liquido']:.2f} - {c['parcelas']}x" for c in comprovantes if c["pago"]]
        return "📗 *Pagos:*\n" + "\n".join(lista) if lista else "📭 Nenhum comprovante marcado como pago."

    if texto == "último comprovante":
        if not comprovantes:
            return "Nenhum comprovante ainda."
        c = comprovantes[-1]
        return (
            f"📄 Último comprovante:\n"
            f"💰 R$ {c['valor_bruto']:.2f} - {c['parcelas']}x\n"
            f"📉 Taxa: {c['taxa']:.2f}%\n"
            f"✅ Líquido: R$ {c['valor_liquido']:.2f}"
        )

    if texto == "total geral":
        total = sum(c["valor_liquido"] for c in comprovantes)
        return f"📊 Total geral de todos os comprovantes: R$ {total:.2f}"

    try:
        valor_str = re.findall(r"[\d.,]+", texto)[0].replace(".", "").replace(",", ".")
        valor = float(valor_str)
        parcelas = 1

        if "pix" in texto:
            taxa = 0.2
        else:
            parcelas_match = re.search(r"(\d{1,2})x", texto)
            if parcelas_match:
                parcelas = int(parcelas_match.group(1))
            taxa = TAXAS_CARTAO.get(parcelas, 0)

        liquido = valor * (1 - taxa / 100)
        hora = datetime.now().strftime("%H:%M")

        comprovantes.append({
            "valor_bruto": valor,
            "parcelas": parcelas,
            "taxa": taxa,
            "valor_liquido": liquido,
            "pago": False,
            "hora": hora
        })

        return (
            f"📄 *Comprovante analisado:*\n"
            f"💰 Valor bruto: R$ {valor:.2f}\n"
            f"💳 Parcelas: {parcelas}x\n"
            f"⏰ Horário: {hora}\n"
            f"📉 Taxa aplicada: {taxa:.2f}%\n"
            f"✅ Valor líquido a pagar: R$ {liquido:.2f}"
        )

    except Exception as e:
        return f"⚠️ Erro ao interpretar o comprovante: {str(e)}"
