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
MELI_CLIENT_ID = "697990339549885"
MELI_CLIENT_SECRET = "xzKEHd0bTveL6gNW636CSGt2JqjEJgdL"
MELI_AFFILIATE_ID = "r20251127144407"

DESCONTO_MINIMO = 15
HORARIOS = ["08:00", "12:00", "15:00", "18:00", "21:00"]
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
meli_access_token = None

PRODUTOS_AMAZON = [
    {"asin": "B0DYVPCX34", "nome": "Smartphone Samsung Galaxy", "preco_original": 3499.00, "preco_atual": 2199.99},
    {"asin": "B098YHFT9S", "nome": "Multifuncional Epson EcoTank L3250 Colorida", "preco_original": 1379.00, "preco_atual": 1011.08},
    {"asin": "B0FPYXKBJG", "nome": "Celular Samsung Galaxy 256GB 50MP", "preco_original": 1899.00, "preco_atual": 1167.00},
    {"asin": "B0DXR7GNWJ", "nome": "Apple iPhone 16e 128GB", "preco_original": 5799.00, "preco_atual": 3460.54},
    {"asin": "B0FMFRFNWG", "nome": "Samsung Galaxy Lite 128GB Cinza", "preco_original": 3149.00, "preco_atual": 2336.68},
    {"asin": "B0FK1NJLXB", "nome": "JBL Boombox Bluetooth Lossless", "preco_original": 3199.00, "preco_atual": 2488.00},
    {"asin": "B0CVCLGV1W", "nome": "Smartwatch Samsung Galaxy Watch", "preco_original": 549.00, "preco_atual": 224.90},
    {"asin": "B0F5X6L24G", "nome": "Samsung Smart TV Crystal 4K 2025", "preco_original": 3799.99, "preco_atual": 3399.90},
    {"asin": "B07Y2G7VX5", "nome": "Headphone HV-H2002d com Microfone", "preco_original": 294.60, "preco_atual": 139.99},
    {"asin": "B0GH2SC1XG", "nome": "Smart TV TCL 55\" 4K Google Assistente", "preco_original": 3399.00, "preco_atual": 2569.48},
    {"asin": "B0FRJV1B75", "nome": "Monitor LG 43\" 4K Profissional Ultrafino", "preco_original": 1999.00, "preco_atual": 1791.22},
    {"asin": "B0FVBH3L33", "nome": "JBL Bluetooth Portátil Auracast", "preco_original": 559.00, "preco_atual": 450.00},
    {"asin": "B0DZK3M8GJ", "nome": "Apple iPad 2025 Wi-Fi 128GB", "preco_original": 4499.00, "preco_atual": 3799.00},
    {"asin": "B0CRTYZG5C", "nome": "Soundcore Fone Cancelamento de Ruído Bluetooth", "preco_original": 369.00, "preco_atual": 205.00},
    {"asin": "B09VCHQHZ6", "nome": "Processador AMD Ryzen 7 5700X", "preco_original": 2186.92, "preco_atual": 1149.99},
    {"asin": "B0CT922NH7", "nome": "JBL Soundbar Bluetooth Cinema Subwoofer", "preco_original": 1469.00, "preco_atual": 946.32},
    {"asin": "B0765KZ264", "nome": "Suporte Ergonômico Articulado para Monitor", "preco_original": 299.90, "preco_atual": 157.50},
    {"asin": "B0FPHYC9FQ", "nome": "Celular Samsung Galaxy 128GB Preto", "preco_original": 799.00, "preco_atual": 590.90},
]

CATEGORIAS_TECH_MELI = [
    "fone bluetooth", "smartwatch", "carregador turbo", "hub usb",
    "cabo usb-c", "mouse sem fio", "teclado bluetooth", "powerbank",
    "câmera ip wifi", "headset gamer", "notebook", "monitor",
    "ssd externo", "memoria ram", "controle xbox", "controle playstation",
    "caixa de som bluetooth", "webcam full hd", "microfone usb", "leitor de cartao"
]


def obter_token_meli():
    global meli_access_token
    try:
        url = "https://api.mercadolibre.com/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": MELI_CLIENT_ID,
            "client_secret": MELI_CLIENT_SECRET
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            meli_access_token = response.json().get("access_token")
            print(f"✅ Token MELI obtido!")
            return True
        else:
            print(f"❌ Erro token MELI: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
    return False


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


def gerar_link_afiliado_meli(permalink):
    try:
        if not meli_access_token:
            obter_token_meli()
        url = "https://api.mercadolibre.com/v1/affiliate/links"
        headers = {
            "Authorization": f"Bearer {meli_access_token}",
            "Content-Type": "application/json"
        }
        payload = {"url": permalink, "publisher_id": MELI_AFFILIATE_ID}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("short_url") or permalink
    except Exception as e:
        print(f"⚠️ Erro link afiliado: {e}")
    return f"{permalink}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}"


def buscar_meli():
    global meli_access_token
    try:
        if not meli_access_token:
            obter_token_meli()

        categorias = random.sample(CATEGORIAS_TECH_MELI, 3)
        for keyword in categorias:
            headers = {"Authorization": f"Bearer {meli_access_token}"} if meli_access_token else {}
            url = f"https://api.mercadolibre.com/sites/MLB/search?q={keyword}&category=MLB1648&sort=best_match&limit=20"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 401:
                obter_token_meli()
                headers = {"Authorization": f"Bearer {meli_access_token}"}
                response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                continue

            produtos = response.json().get("results", [])
            melhores = []

            for p in produtos:
                preco_atual = p.get("price", 0)
                preco_original = p.get("original_price") or 0
                desconto = calcular_desconto(preco_original, preco_atual)
                imagem = p.get("thumbnail", "").replace("I.jpg", "O.jpg")

                if desconto >= DESCONTO_MINIMO and preco_atual > 50:
                    melhores.append({
                        "titulo": p.get("title", "Produto Tech"),
                        "preco_atual": preco_atual,
                        "preco_original": preco_original,
                        "desconto": desconto,
                        "permalink": p.get("permalink", ""),
                        "imagem": imagem,
                        "loja": "Mercado Livre"
                    })

            if melhores:
                melhor = max(melhores, key=lambda x: x["desconto"])
                melhor["link"] = gerar_link_afiliado_meli(melhor["permalink"])
                return melhor

        # Fallback
        keyword = random.choice(CATEGORIAS_TECH_MELI)
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={keyword}&category=MLB1648&sort=best_match&limit=5"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            produtos = response.json().get("results", [])
            if produtos:
                p = produtos[0]
                preco_atual = p.get("price", 0)
                preco_original = p.get("original_price") or preco_atual
                permalink = p.get("permalink", "")
                return {
                    "titulo": p.get("title", "Produto Tech"),
                    "preco_atual": preco_atual,
                    "preco_original": preco_original,
                    "desconto": calcular_desconto(preco_original, preco_atual),
                    "link": gerar_link_afiliado_meli(permalink),
                    "imagem": p.get("thumbnail", "").replace("I.jpg", "O.jpg"),
                    "loja": "Mercado Livre"
                }
    except Exception as e:
        print(f"❌ Erro MELI: {e}")
    return None


def montar_mensagem(oferta):
    emoji_loja = {"Amazon": "📦", "Mercado Livre": "🛒"}
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

    sorteio = random.randint(1, 10)
    if sorteio <= 7:
        oferta = buscar_meli()
        if not oferta:
            oferta = buscar_amazon()
    else:
        oferta = buscar_amazon()
        if not oferta:
            oferta = buscar_meli()

    if oferta:
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
        print(f"✅ Postado [{oferta['loja']}]: {oferta['titulo'][:50]}...")
    else:
        print("⚠️  Nenhuma oferta encontrada")


def iniciar_agendamento():
    print("🚀 Iniciando bot...")
    obter_token_meli()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR atualizado!</b>\n\n"
        "✅ 18 produtos Amazon reais\n"
        "✅ Mercado Livre em tempo real\n"
        "✅ 5 postagens por dia\n\n"
        "⏰ 08h | 12h | 15h | 18h | 21h\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    postar_oferta()

    for horario in HORARIOS:
        schedule.every().day.at(horario).do(postar_oferta)
        print(f"⏰ Agendado para {horario}")

    schedule.every(5).hours.do(obter_token_meli)

    print(f"\n✅ Bot rodando! Postagens às: {', '.join(HORARIOS)}\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT")
    print("=" * 50)
    iniciar_agendamento()
