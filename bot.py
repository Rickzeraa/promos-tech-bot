import requests
import schedule
import time
import random
import json
import os
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = "8111527242:AAH2Bq-QgIgy8BsYVmgwAE-fs22WWGId9zE"
TELEGRAM_CHANNEL = "@promostechbr01"

AMAZON_PARTNER_TAG = "digitalvaiven-20"
MELI_AFFILIATE_ID = "r20251127144407"

DESCONTO_MINIMO_PERCENT = 15
ECONOMIA_MINIMA_REAIS = 30
PRECO_MINIMO = 50

RELAMPAGO_PERCENT = 20
RELAMPAGO_REAIS = 100
RELAMPAGO_TICKET_ALTO_PRECO_MIN = 200
RELAMPAGO_TICKET_ALTO_PERCENT = 20

HORARIOS_BLOCOS = ["08:00", "12:00", "17:00", "21:00"]
POSTS_POR_BLOCO = 6
INTERVALO_MINUTOS = 10
INTERVALO_RELAMPAGO = 30

HISTORICO_FILE = "historico.json"
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
historico_precos = {}
ultimo_relampago_id = None

HEADERS_MELI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

PRODUTOS_AMAZON = [
    {"asin": "B0DYVPCX34", "nome": "Smartphone Samsung Galaxy", "preco_original": 3499.00, "preco_atual": 2199.99},
    {"asin": "B098YHFT9S", "nome": "Multifuncional Epson EcoTank L3250", "preco_original": 1379.00, "preco_atual": 1011.08},
    {"asin": "B0FPYXKBJG", "nome": "Celular Samsung Galaxy 256GB 50MP", "preco_original": 1899.00, "preco_atual": 1167.00},
    {"asin": "B0DXR7GNWJ", "nome": "Apple iPhone 16e 128GB", "preco_original": 5799.00, "preco_atual": 3460.54},
    {"asin": "B0FMFRFNWG", "nome": "Samsung Galaxy Lite 128GB", "preco_original": 3149.00, "preco_atual": 2336.68},
    {"asin": "B0FK1NJLXB", "nome": "JBL Boombox Bluetooth Lossless", "preco_original": 3199.00, "preco_atual": 2488.00},
    {"asin": "B0CVCLGV1W", "nome": "Smartwatch Samsung Galaxy Watch", "preco_original": 549.00, "preco_atual": 224.90},
    {"asin": "B0F5X6L24G", "nome": "Samsung Smart TV Crystal 4K 2025", "preco_original": 3799.99, "preco_atual": 3399.90},
    {"asin": "B07Y2G7VX5", "nome": "Headphone HV-H2002d com Microfone", "preco_original": 294.60, "preco_atual": 139.99},
    {"asin": "B0GH2SC1XG", "nome": "Smart TV TCL 55\" 4K Google", "preco_original": 3399.00, "preco_atual": 2569.48},
    {"asin": "B0FRJV1B75", "nome": "Monitor LG 43\" 4K Profissional", "preco_original": 1999.00, "preco_atual": 1791.22},
    {"asin": "B0FVBH3L33", "nome": "JBL Bluetooth Portátil Auracast", "preco_original": 559.00, "preco_atual": 450.00},
    {"asin": "B0DZK3M8GJ", "nome": "Apple iPad 2025 Wi-Fi 128GB", "preco_original": 4499.00, "preco_atual": 3799.00},
    {"asin": "B0CRTYZG5C", "nome": "Soundcore Fone Cancelamento de Ruído", "preco_original": 369.00, "preco_atual": 205.00},
    {"asin": "B09VCHQHZ6", "nome": "Processador AMD Ryzen 7 5700X", "preco_original": 2186.92, "preco_atual": 1149.99},
    {"asin": "B0CT922NH7", "nome": "JBL Soundbar Cinema Subwoofer", "preco_original": 1469.00, "preco_atual": 946.32},
    {"asin": "B0765KZ264", "nome": "Suporte Ergonômico para Monitor", "preco_original": 299.90, "preco_atual": 157.50},
    {"asin": "B0FPHYC9FQ", "nome": "Celular Samsung Galaxy 128GB Preto", "preco_original": 799.00, "preco_atual": 590.90},
]

CATEGORIAS_TECH_MELI = [
    "fone bluetooth", "smartwatch", "carregador turbo", "hub usb",
    "cabo usb-c", "mouse sem fio", "teclado bluetooth", "powerbank",
    "camera ip wifi", "headset gamer", "notebook", "monitor",
    "ssd externo", "controle xbox", "controle playstation",
    "caixa de som bluetooth", "webcam", "microfone usb",
    "samsung galaxy", "iphone", "tablet", "processador"
]


# ============================================================
# HISTÓRICO
# ============================================================

def carregar_historico():
    global historico_precos
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, "r") as f:
                historico_precos = json.load(f)
            print(f"✅ Histórico: {len(historico_precos)} produtos")
        else:
            historico_precos = {}
    except:
        historico_precos = {}


def salvar_historico():
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico_precos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro histórico: {e}")


def verificar_minimo_historico(produto_id, titulo, preco_atual):
    global historico_precos
    produto_id = str(produto_id)
    eh_minimo = False

    if produto_id in historico_precos:
        minimo_anterior = historico_precos[produto_id]["minimo"]
        if preco_atual < minimo_anterior:
            eh_minimo = True
            historico_precos[produto_id]["minimo"] = preco_atual
            historico_precos[produto_id]["data_minimo"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            print(f"🚨 MÍNIMO HISTÓRICO: {titulo[:40]}")
    else:
        historico_precos[produto_id] = {
            "titulo": titulo[:60],
            "minimo": preco_atual,
            "data_minimo": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    historico_precos[produto_id]["ultimo_preco"] = preco_atual
    historico_precos[produto_id]["ultima_verificacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    salvar_historico()
    return eh_minimo


# ============================================================
# TELEGRAM
# ============================================================

def enviar_telegram(mensagem, imagem_url=None):
    try:
        if imagem_url:
            url = f"{TELEGRAM_API}/sendPhoto"
            payload = {"chat_id": TELEGRAM_CHANNEL, "photo": imagem_url, "caption": mensagem, "parse_mode": "HTML"}
        else:
            url = f"{TELEGRAM_API}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHANNEL, "text": mensagem, "parse_mode": "HTML"}

        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get("ok"):
            print(f"✅ Mensagem enviada!")
        else:
            print(f"❌ Erro Telegram: {result}")
    except Exception as e:
        print(f"❌ Erro: {e}")


# ============================================================
# UTILITÁRIOS
# ============================================================

def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_desconto(original, atual):
    if original and atual and original > atual:
        return round(((original - atual) / original) * 100)
    return 0


def vale_postar(preco_original, preco_atual):
    """
    Post normal dispara se QUALQUER UMA:
    - Desconto >= 15%
    - OU economia >= R$30
    """
    if preco_atual < PRECO_MINIMO:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = (preco_original - preco_atual) if preco_original else 0
    return desconto >= DESCONTO_MINIMO_PERCENT or economia >= ECONOMIA_MINIMA_REAIS


def eh_relampago(preco_original, preco_atual):
    """
    Relâmpago dispara se as TRÊS condições forem verdadeiras:
    - Produto >= R$200
    - Economia >= R$100
    - Desconto >= 20%
    """
    if not preco_original:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual
    return (
        preco_atual >= 200 and
        economia >= 100 and
        desconto >= 20
    )


# ============================================================
# MELI — SEM TOKEN (API pública)
# ============================================================

def gerar_link_meli(permalink):
    """Gera link de afiliado no formato correto do MELI"""
    return f"{permalink}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}&matt_source=telegram"


def buscar_meli(apenas_relampago=False):
    global ultimo_relampago_id

    try:
        categorias = random.sample(CATEGORIAS_TECH_MELI, 5)
        candidatos = []

        for keyword in categorias:
            keyword_encoded = keyword.replace(" ", "+")
            url = f"https://api.mercadolibre.com/sites/MLB/search?q={keyword_encoded}&sort=best_match&limit=20"

            try:
                response = requests.get(url, headers=HEADERS_MELI, timeout=15)
            except:
                continue

            if response.status_code != 200:
                print(f"⚠️ MELI status {response.status_code} para '{keyword}'")
                continue

            produtos = response.json().get("results", [])

            for p in produtos:
                preco_atual = p.get("price", 0)
                preco_original = p.get("original_price") or 0
                produto_id = p.get("id", "")
                titulo = p.get("title", "Produto Tech")
                imagem = p.get("thumbnail", "").replace("I.jpg", "O.jpg")
                permalink = p.get("permalink", "")

                if preco_atual < PRECO_MINIMO or not preco_original:
                    continue

                desconto = calcular_desconto(preco_original, preco_atual)
                relampago = eh_relampago(preco_original, preco_atual)
                minimo = verificar_minimo_historico(produto_id, titulo, preco_atual)

                oferta = {
                    "id": produto_id,
                    "titulo": titulo,
                    "preco_atual": preco_atual,
                    "preco_original": preco_original,
                    "desconto": desconto,
                    "economia": preco_original - preco_atual,
                    "link": gerar_link_meli(permalink),
                    "imagem": imagem,
                    "loja": "Mercado Livre",
                    "relampago": relampago,
                    "minimo_historico": minimo
                }

                if apenas_relampago:
                    if (relampago or minimo) and produto_id != ultimo_relampago_id:
                        candidatos.append(oferta)
                else:
                    if vale_postar(preco_original, preco_atual):
                        candidatos.append(oferta)

        if candidatos:
            candidatos.sort(key=lambda x: (x["minimo_historico"], x["relampago"], x["desconto"]), reverse=True)
            melhor = candidatos[0]
            if apenas_relampago:
                ultimo_relampago_id = melhor["id"]
            return melhor

        # Fallback: qualquer produto tech sem filtro de desconto
        if not apenas_relampago:
            keyword = random.choice(CATEGORIAS_TECH_MELI).replace(" ", "+")
            url = f"https://api.mercadolibre.com/sites/MLB/search?q={keyword}&sort=best_match&limit=5"
            response = requests.get(url, headers=HEADERS_MELI, timeout=15)
            if response.status_code == 200:
                produtos = response.json().get("results", [])
                if produtos:
                    p = produtos[0]
                    preco_atual = p.get("price", 0)
                    preco_original = p.get("original_price") or preco_atual
                    return {
                        "titulo": p.get("title", "Produto Tech"),
                        "preco_atual": preco_atual,
                        "preco_original": preco_original,
                        "desconto": calcular_desconto(preco_original, preco_atual),
                        "economia": preco_original - preco_atual,
                        "link": gerar_link_meli(p.get("permalink", "")),
                        "imagem": p.get("thumbnail", "").replace("I.jpg", "O.jpg"),
                        "loja": "Mercado Livre",
                        "relampago": False,
                        "minimo_historico": False
                    }

    except Exception as e:
        print(f"❌ Erro MELI: {e}")
    return None


# ============================================================
# AMAZON
# ============================================================

def buscar_amazon(excluir_asins=[]):
    try:
        disponiveis = [p for p in PRODUTOS_AMAZON if p["asin"] not in excluir_asins]
        if not disponiveis:
            disponiveis = PRODUTOS_AMAZON

        produto = random.choice(disponiveis)
        return {
            "titulo": produto["nome"],
            "preco_atual": produto["preco_atual"],
            "preco_original": produto["preco_original"],
            "desconto": calcular_desconto(produto["preco_original"], produto["preco_atual"]),
            "economia": produto["preco_original"] - produto["preco_atual"],
            "link": f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}",
            "imagem": None,
            "loja": "Amazon",
            "relampago": False,
            "minimo_historico": False,
            "asin": produto["asin"]
        }
    except Exception as e:
        print(f"❌ Erro Amazon: {e}")
    return None


# ============================================================
# MENSAGEM
# ============================================================

def montar_mensagem(oferta):
    emoji_loja = {"Amazon": "📦", "Mercado Livre": "🛒"}
    loja_emoji = emoji_loja.get(oferta["loja"], "🏪")
    titulo = oferta["titulo"][:80] + "..." if len(oferta["titulo"]) > 80 else oferta["titulo"]

    if oferta.get("minimo_historico"):
        msg = "🚨 <b>MÍNIMO HISTÓRICO!</b> 🚨\n\n⚠️ <b>MENOR PREÇO JÁ REGISTRADO!</b>\n\n"
    elif oferta.get("relampago"):
        msg = "⚡⚡ <b>ALERTA RELÂMPAGO!</b> ⚡⚡\n\n🔥 <b>OFERTA ABSURDA — CORRE!</b>\n\n"
    else:
        msg = "🔥 <b>OFERTA DO DIA!</b>\n\n"

    msg += f"{loja_emoji} <b>{oferta['loja']}</b>\n\n"
    msg += f"📱 <b>{titulo}</b>\n\n"

    if oferta.get("preco_original") and oferta["preco_original"] > oferta["preco_atual"]:
        msg += f"<s>{formatar_preco(oferta['preco_original'])}</s>\n"
        msg += f"💰 <b>Por apenas {formatar_preco(oferta['preco_atual'])}</b>\n"
        msg += f"📉 <b>{oferta['desconto']}% de desconto!</b>\n"
        if oferta.get("economia", 0) > 0:
            msg += f"💵 <b>Economia de {formatar_preco(oferta['economia'])}!</b>\n\n"
        else:
            msg += "\n"
    else:
        msg += f"💰 <b>{formatar_preco(oferta['preco_atual'])}</b>\n\n"

    if oferta.get("minimo_historico"):
        msg += "⏰ <b>Menor preço já visto! Pode acabar a qualquer momento!</b>\n\n"
    elif oferta.get("relampago"):
        msg += "⏰ <b>Por tempo MUITO limitado!</b>\n\n"
    else:
        msg += "⚡ <b>Por tempo limitado!</b>\n\n"

    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += "📢 @promostechbr01 | Promos Tech BR"

    return msg


# ============================================================
# POSTAGEM
# ============================================================

def postar_bloco():
    print(f"\n🎯 [{datetime.now().strftime('%H:%M')}] Iniciando bloco de {POSTS_POR_BLOCO} posts!")
    amazon_usados = []

    for i in range(POSTS_POR_BLOCO):
        print(f"\n📨 Post {i+1}/{POSTS_POR_BLOCO}")

        sorteio = random.randint(1, 10)

        if sorteio <= 7:
            oferta = buscar_meli()
            if not oferta:
                print("⚠️ MELI falhou, usando Amazon")
                oferta = buscar_amazon(amazon_usados)
        else:
            oferta = buscar_amazon(amazon_usados)

        if oferta:
            if oferta.get("asin"):
                amazon_usados.append(oferta["asin"])
            mensagem = montar_mensagem(oferta)
            enviar_telegram(mensagem, oferta.get("imagem"))
            print(f"✅ [{oferta['loja']}]: {oferta['titulo'][:40]}...")

        if i < POSTS_POR_BLOCO - 1:
            print(f"⏳ Aguardando {INTERVALO_MINUTOS} minutos...")
            time.sleep(INTERVALO_MINUTOS * 60)


def verificar_relampago():
    print(f"\n⚡ [{datetime.now().strftime('%H:%M')}] Verificando relâmpagos...")
    oferta = buscar_meli(apenas_relampago=True)
    if oferta:
        print(f"🚨 RELÂMPAGO: {oferta['titulo'][:40]}")
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
    else:
        print("✅ Nenhum relâmpago")


# ============================================================
# MAIN
# ============================================================

def iniciar_agendamento():
    print("🚀 Iniciando bot...")
    carregar_historico()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR — Sistema Completo!</b>\n\n"
        "✅ Mercado Livre corrigido\n"
        "✅ Amazon com 18 produtos\n"
        "✅ Blocos de 6 posts\n"
        "⚡ Alerta Relâmpago ativo\n"
        "🚨 Detector de Mínimo Histórico ativo\n\n"
        "⏰ Blocos: 08h | 12h | 17h | 21h\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    # Posta um bloco imediatamente para testar
    postar_bloco()

    for horario in HORARIOS_BLOCOS:
        schedule.every().day.at(horario).do(postar_bloco)
        print(f"⏰ Bloco agendado para {horario}")

    schedule.every(INTERVALO_RELAMPAGO).minutes.do(verificar_relampago)
    print(f"⚡ Relâmpago a cada {INTERVALO_RELAMPAGO} minutos")

    print(f"\n✅ Bot rodando!\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT")
    print("=" * 50)
    iniciar_agendamento()
