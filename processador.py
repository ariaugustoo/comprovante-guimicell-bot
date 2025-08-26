import os
import requests
import re
from datetime import datetime

TOKEN = '8044957045:AAE8AmsmV3LYwqPUi6BXmp_I9ePgywg80IA'
GROUP_ID = '-1002122662652'

comprovantes = []

def enviar_mensagem(texto):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': GROUP_ID,
        'text': texto,
        'parse_mode': 'HTML'
    }
    requests.post(url, json=payload)

def extrair_info(texto):
    valor = None
    parcelas = 1
    tipo = 'PIX'
    
    valor_match = re.search(r'([\d\.,]+)', texto)
    if valor_match:
        valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
        try:
            valor = float(valor_str)
        except:
            pass

    if 'x' in texto.lower():
        tipo = 'CARTÃO'
        parcelas_match = re.search(r'(\d{1,2})x', texto.lower())
        if parcelas_match:
            parcelas = int(parcelas_match.group(1))

    elif 'pix' in texto.lower():
        tipo = 'PIX'
    
    return valor, tipo, parcelas

def calcular_taxa(valor, tipo, parcelas):
    if tipo == 'PIX':
        taxa = 0.002
    else:
        tabela_taxas = {
            1: 0.0439, 2: 0.0519, 3: 0.0619, 4: 0.0659,
            5: 0.0719, 6: 0.0829, 7: 0.0919, 8: 0.0999,
            9: 0.1029, 10: 0.1088, 11: 0.1199, 12: 0.1252,
            13: 0.1369, 14: 0.1419, 15: 0.1469, 16: 0.1519,
            17: 0.1589, 18: 0.1684
        }
        taxa = tabela_taxas.get(parcelas, 0.0439)
    
    valor_liquido = valor * (1 - taxa)
    return round(taxa * 100, 2), round(valor_liquido, 2)

def processar_mensagem(msg):
    if 'text' not in msg:
        return

    texto = msg['text'].lower()
    user = msg['from']['first_name']
    horario = datetime.now().strftime('%H:%M')
    
    if 'pix' in texto or 'x' in texto:
        valor, tipo, parcelas = extrair_info(texto)
        if valor:
            taxa_pct, valor_liq = calcular_taxa(valor, tipo, parcelas)
            comprovantes.append({
                'user': user,
                'valor': valor,
                'parcelas': parcelas,
                'horario': horario,
                'taxa': taxa_pct,
                'valor_liquido': valor_liq,
                'pago': False
            })

            resposta = (
                f"📄 <b>Comprovante analisado:</b>\n"
                f"💰 Valor bruto: R$ {valor:,.2f}\n"
                f"💳 Parcelas: {parcelas}x\n"
                f"⏰ Horário: {horario}\n"
                f"📉 Taxa aplicada: {taxa_pct}%\n"
                f"✅ Valor líquido a pagar: R$ {valor_liq:,.2f}"
            )
            enviar_mensagem(resposta)

    elif texto.strip() == 'total que devo':
        total = sum(c['valor_liquido'] for c in comprovantes if not c['pago'])
        enviar_mensagem(f"💸 <b>Total pendente:</b> R$ {total:,.2f}")

    elif texto.strip() == 'listar pendentes':
        pendentes = [c for c in comprovantes if not c['pago']]
        if not pendentes:
            enviar_mensagem("✅ Nenhum comprovante pendente.")
        else:
            mensagem = "📋 <b>Comprovantes Pendentes:</b>\n"
            for i, c in enumerate(pendentes, 1):
                mensagem += f"{i}. R$ {c['valor']:,.2f} - {c['parcelas']}x - {c['horario']}\n"
            enviar_mensagem(mensagem)

    elif texto.strip() == 'listar pagos':
        pagos = [c for c in comprovantes if c['pago']]
        if not pagos:
            enviar_mensagem("📁 Nenhum comprovante marcado como pago.")
        else:
            mensagem = "📁 <b>Comprovantes Pagos:</b>\n"
            for i, c in enumerate(pagos, 1):
                mensagem += f"{i}. R$ {c['valor']:,.2f} - {c['parcelas']}x - {c['horario']}\n"
            enviar_mensagem(mensagem)

    elif texto.strip() == 'último comprovante':
        if comprovantes:
            c = comprovantes[-1]
            status = "✅ Pago" if c['pago'] else "⏳ Pendente"
            mensagem = (
                f"📄 <b>Último comprovante:</b>\n"
                f"💰 R$ {c['valor']:,.2f} - {c['parcelas']}x\n"
                f"⏰ {c['horario']}\n"
                f"📉 Taxa: {c['taxa']}%\n"
                f"💵 Líquido: R$ {c['valor_liquido']:,.2f}\n"
                f"{status}"
            )
            enviar_mensagem(mensagem)
        else:
            enviar_mensagem("Nenhum comprovante registrado ainda.")

    elif texto.strip() == 'total geral':
        total = sum(c['valor_liquido'] for c in comprovantes)
        enviar_mensagem(f"📊 <b>Total geral (pagos + pendentes):</b> R$ {total:,.2f}")

    elif texto.strip() == '✅':
        for c in reversed(comprovantes):
            if not c['pago']:
                c['pago'] = True
                enviar_mensagem(f"✅ Comprovante de R$ {c['valor']:,.2f} marcado como pago.")
                break

    elif texto.strip() == 'ajuda':
        comandos = (
            "📘 <b>Comandos disponíveis:</b>\n"
            "➡️ <i>1234,56 pix</i> ou <i>1234,56 3x</i>\n"
            "✅ — marca último comprovante como pago\n"
            "🧾 <b>Consultar:</b>\n"
            "• total que devo\n"
            "• listar pendentes\n"
            "• listar pagos\n"
            "• último comprovante\n"
            "• total geral\n"
            "• ajuda"
        )
        enviar_mensagem(comandos)
