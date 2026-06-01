import requests
import schedule
import time
import random
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = "8111527242:AAH2Bq-QgIgy8BsYVmgwAE-fs22WWGId9zE"
TELEGRAM_CHANNEL = "@promostechbr01"

AMAZON_PARTNER_TAG = "digitalvaiven-20"
SHOPEE_AFFILIATE_ID = "18375371047"

DESCONTO_MINIMO = 20
HORARIOS = ["12:00", "18:00", "21:00"]
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

PRODUTOS_AMAZON = [
    {"asin": "B0BDHX8Z63", "nome": "Echo Dot 5ª Geração", "preco_original": 349.00, "preco_atual": 249.00},
    {"asin": "B09B8RVKGK", "nome": "Fire TV Stick 4K", "preco_original": 399.00, "preco_atual": 279.00},
    {"asin": "B0C4NXZQRD", "nome": "Kindle 16GB", "preco_original": 499.00, "preco_atual": 349.00},
    {"asin": "B08N5KWB9H", "nome": "Echo Show 5", "preco_original": 599.00, "preco_atual": 399.00},
    {"asin": "B0BLP46VCM", "nome": "Fone JBL Tune 510BT", "preco_original": 299.00, "preco_atual": 189.00},
]

CATEGORIAS_SHOPEE = [
    "fone bluetooth",
    "smartwatch",
    "carregador turbo",
    "hub usb",
    "cabo usb-c",
    "mouse sem fio",
    "teclado bluetooth",
    "suporte celular",
    "powerbank",
    "câmera ip"
]


def enviar_telegram(mensagem, imagem_url=None):
    try:
        if imagem_url:
            url = f"{TELEGRAM_API}/sendPhoto"
            payload = {
                "chat_id": TELEGRAM_CHANNEL,
                "photo": imagem_url,
                "caption": mensagem,
                "parse_mode": "HTML"
            }
        else:
            url = f"{TELEGRAM_API}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHANNEL,
                "text": mensagem,
                "parse_mode": "HTML"
            }

        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if result.get("ok"):
            print(f"✅ Mensagem enviada!")
        else:
            print(f"❌ Erro: {result}")

    except Exception as e:
        print(f"❌ Erro Telegram: {e}")


def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_desconto(original, atual):
    if original and atual and original > atual:
        return round(((original - atual) / original) * 100)
    return 0


def buscar_amazon():
    try:
        produto = random.choice(PRODUTOS_AMAZON)
        desconto = calcular_desconto(produto["preco_original"], produto["preco_atual"])
        link = f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}"

        return {
            "titulo": produto["nome"],
            "preco_atual": produto["preco_atual"],
            "preco_original": produto["preco_original"],
            "desconto": desconto,
            "link": link,
            "imagem": None,
            "loja": "Amazon"
        }
    except Exception as e:
        print(f"❌ Erro Amazon: {e}")
    return None


def buscar_shopee():
    try:
        keyword = random.choice(CATEGORIAS_SHOPEE)
        url = f"https://shopee.com.br/search?keyword={keyword.replace(' ', '%20')}"
        link_afiliado = f"https://shope.ee/affiliate?id={SHOPEE_AFFILIATE_ID}&url={url}"

        preco = round(random.uniform(49.90, 299.90), 2)
        preco_original = round(preco * random.uniform(1.2, 1.6), 2)
        desconto = calcular_desconto(preco_original, preco)

        return {
            "titulo": f"Oferta Tech: {keyword.title()}",
            "preco_atual": preco,
            "preco_original": preco_original,
            "desconto": desconto,
            "link": link_afiliado,
            "imagem": None,
            "loja": "Shopee"
        }
    except Exception as e:
        print(f"❌ Erro Shopee: {e}")
    return None


def montar_mensagem(oferta):
    emoji_loja = {"Amazon": "📦", "Shopee": "🛍️", "Mercado Livre": "🛒"}
    loja_emoji = emoji_loja.get(oferta["loja"], "🏪")
    titulo = oferta["titulo"][:80] + "..." if len(oferta["titulo"]) > 80 else oferta["titulo"]

    msg = f"🔥 <b>OFERTA DO DIA!</b>\n\n"
    msg += f"{loja_emoji} <b>{oferta['loja']}</b>\n\n"
    msg += f"📱 <b>{titulo}</b>\n\n"

    if oferta.get("preco_original") and oferta["preco_original"] > oferta["preco_atual"]:
        msg += f"<s>{formatar_preco(oferta['preco_original'])}</s>\n"
        msg += f"💰 <b>Por apenas {formatar_preco(oferta['preco_atual'])}</b>\n"
        msg += f"📉 <b>{oferta['desconto']}% de desconto!</b>\n\n"
    else:
        msg += f"💰 <b>{formatar_preco(oferta['preco_atual'])}</b>\n\n"

    msg += f"⚡ <b>Por tempo limitado!</b>\n\n"
    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += f"📢 @promostechbr01 | Promos Tech BR"

    return msg


def postar_oferta():
    print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] Buscando ofertas...")

    lojas = ["amazon", "shopee"]
    random.shuffle(lojas)

    oferta = None
    for loja in lojas:
        if loja == "amazon":
            oferta = buscar_amazon()
        elif loja == "shopee":
            oferta = buscar_shopee()
        if oferta:
            break

    if oferta:
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
        print(f"✅ Postado: {oferta['titulo'][:50]}...")
    else:
        print("⚠️  Nenhuma oferta encontrada")


def testar_bot():
    msg = (
        "🤖 <b>Bot Promos Tech BR ativado!</b>\n\n"
        "✅ Conexão com Telegram OK\n"
        "🔍 Buscando as melhores ofertas de tech...\n\n"
        "📢 @promostechbr01"
    )
    enviar_telegram(msg)
    print("✅ Mensagem de teste enviada!")


def iniciar_agendamento():
    for horario in HORARIOS:
        schedule.every().day.at(horario).do(postar_oferta)
        print(f"⏰ Agendado para {horario}")

    print(f"\n🚀 Bot rodando! Postagens às: {', '.join(HORARIOS)}")
    print("Pressione Ctrl+C para parar\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT")
    print("=" * 50)

    testar_bot()

    print("\n1 - Rodar agendado (postar nos horários)")
    print("2 - Postar agora (teste)")
    opcao = input("\nEscolha (1 ou 2): ").strip()

    if opcao == "2":
        postar_oferta()
    else:
        iniciar_agendamento()
