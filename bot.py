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
MELI_CLIENT_ID = "697990339549885"
MELI_CLIENT_SECRET = "xzKEHd0bTveL6gNW636CSGt2JqjEJgdL"
MELI_AFFILIATE_ID = "r20251127144407"

# Regras de postagem normal
DESCONTO_MINIMO_PERCENT = 15
ECONOMIA_MINIMA_REAIS = 100
PRECO_MINIMO = 50

# Regras de alerta relâmpago
RELAMPAGO_PERCENT = 50
RELAMPAGO_REAIS = 500
RELAMPAGO_TICKET_ALTO_PERCENT = 30
RELAMPAGO_TICKET_ALTO_PRECO = 2000

# Blocos de postagem
HORARIOS_BLOCOS = ["08:00", "12:00", "17:00", "21:30"]
POSTS_POR_BLOCO = 6
INTERVALO_MINUTOS = 10

# Verificação de relâmpago a cada X minutos
INTERVALO_RELAMPAGO = 30

HISTORICO_FILE = "historico.json"
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
meli_access_token = None
historico_precos = {}
ultimo_relampago_id = None

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
    "câmera ip wifi", "headset gamer", "notebook", "monitor",
    "ssd externo", "memoria ram", "controle xbox", "controle playstation",
    "caixa de som bluetooth", "webcam full hd", "microfone usb",
    "samsung galaxy", "iphone", "tablet", "processador", "placa de video"
]


# ============================================================
# HISTÓRICO DE PREÇOS
# ============================================================

def carregar_historico():
    global historico_precos
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, "r") as f:
                historico_precos = json.load(f)
            print(f"✅ Histórico carregado: {len(historico_precos)} produtos")
        else:
            historico_precos = {}
            print("📝 Histórico novo criado")
    except Exception as e:
        print(f"⚠️ Erro ao carregar histórico: {e}")
        historico_precos = {}


def salvar_historico():
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico_precos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")


def verificar_minimo_historico(produto_id, titulo, preco_atual):
    """Verifica se é o menor preço já visto e atualiza histórico"""
    global historico_precos

    produto_id = str(produto_id)
    eh_minimo = False

    if produto_id in historico_precos:
        minimo_anterior = historico_precos[produto_id]["minimo"]
        if preco_atual < minimo_anterior:
            economia_vs_minimo = minimo_anterior - preco_atual
            percent_vs_minimo = round((economia_vs_minimo / minimo_anterior) * 100)
            eh_minimo = True
            print(f"🚨 MÍNIMO HISTÓRICO: {titulo[:40]} - Era R${minimo_anterior} agora R${preco_atual}")
            historico_precos[produto_id]["minimo"] = preco_atual
            historico_precos[produto_id]["data_minimo"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        # Primeiro registro
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


# ============================================================
# UTILITÁRIOS
# ============================================================

def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_desconto(original, atual):
    if original and atual and original > atual:
        return round(((original - atual) / original) * 100)
    return 0


def vale_postar_normal(preco_original, preco_atual):
    """Regra inteligente: % OU economia em R$"""
    if preco_atual < PRECO_MINIMO:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual if preco_original else 0
    return desconto >= DESCONTO_MINIMO_PERCENT or economia >= ECONOMIA_MINIMA_REAIS


def eh_relampago(preco_original, preco_atual):
    """Verifica se é uma oferta absurda"""
    if not preco_original:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual

    if desconto >= RELAMPAGO_PERCENT:
        return True
    if economia >= RELAMPAGO_REAIS:
        return True
    if preco_atual >= RELAMPAGO_TICKET_ALTO_PRECO and desconto >= RELAMPAGO_TICKET_ALTO_PERCENT:
        return True
    return False


# ============================================================
# MELI
# ============================================================

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
        print(f"❌ Erro token: {e}")
    return False


def gerar_link_afiliado_meli(permalink):
    try:
        if not meli_access_token:
            obter_token_meli()
        url = "https://api.mercadolibre.com/v1/affiliate/links"
        headers = {"Authorization": f"Bearer {meli_access_token}", "Content-Type": "application/json"}
        payload = {"url": permalink, "publisher_id": MELI_AFFILIATE_ID}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("short_url") or permalink
    except:
        pass
    return f"{permalink}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}"


def buscar_meli(apenas_relampago=False):
    global meli_access_token, ultimo_relampago_id

    try:
        if not meli_access_token:
            obter_token_meli()

        categorias = random.sample(CATEGORIAS_TECH_MELI, 5)
        candidatos = []

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
                economia = preco_original - preco_atual
                relampago = eh_relampago(preco_original, preco_atual)
                minimo = verificar_minimo_historico(produto_id, titulo, preco_atual)

                oferta = {
                    "id": produto_id,
                    "titulo": titulo,
                    "preco_atual": preco_atual,
                    "preco_original": preco_original,
                    "desconto": desconto,
                    "economia": economia,
                    "permalink": permalink,
                    "imagem": imagem,
                    "loja": "Mercado Livre",
                    "relampago": relampago,
                    "minimo_historico": minimo
                }

                if apenas_relampago:
                    if (relampago or minimo) and produto_id != ultimo_relampago_id:
                        candidatos.append(oferta)
                else:
                    if vale_postar_normal(preco_original, preco_atual):
                        candidatos.append(oferta)

        if candidatos:
            # Prioriza mínimo histórico > relâmpago > maior desconto
            candidatos.sort(key=lambda x: (x["minimo_historico"], x["relampago"], x["desconto"]), reverse=True)
            melhor = candidatos[0]
            melhor["link"] = gerar_link_afiliado_meli(melhor["permalink"])
            if apenas_relampago:
                ultimo_relampago_id = melhor["id"]
            return melhor

    except Exception as e:
        print(f"❌ Erro MELI: {e}")
    return None


# ============================================================
# AMAZON
# ============================================================

def buscar_amazon():
    try:
        produto = random.choice(PRODUTOS_AMAZON)
        desconto = calcular_desconto(produto["preco_original"], produto["preco_atual"])
        economia = produto["preco_original"] - produto["preco_atual"]

        if not vale_postar_normal(produto["preco_original"], produto["preco_atual"]):
            produto = max(PRODUTOS_AMAZON, key=lambda x: calcular_desconto(x["preco_original"], x["preco_atual"]))

        link = f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}"
        return {
            "titulo": produto["nome"],
            "preco_atual": produto["preco_atual"],
            "preco_original": produto["preco_original"],
            "desconto": calcular_desconto(produto["preco_original"], produto["preco_atual"]),
            "economia": produto["preco_original"] - produto["preco_atual"],
            "link": link,
            "imagem": None,
            "loja": "Amazon",
            "relampago": False,
            "minimo_historico": False
        }
    except Exception as e:
        print(f"❌ Erro Amazon: {e}")
    return None


# ============================================================
# MENSAGENS
# ============================================================

def montar_mensagem(oferta):
    emoji_loja = {"Amazon": "📦", "Mercado Livre": "🛒"}
    loja_emoji = emoji_loja.get(oferta["loja"], "🏪")
    titulo = oferta["titulo"][:80] + "..." if len(oferta["titulo"]) > 80 else oferta["titulo"]

    # Cabeçalho especial para relâmpago/mínimo histórico
    if oferta.get("minimo_historico"):
        msg = f"🚨 <b>MÍNIMO HISTÓRICO!</b> 🚨\n\n"
        msg += f"⚠️ <b>MENOR PREÇO JÁ REGISTRADO!</b>\n\n"
    elif oferta.get("relampago"):
        msg = f"⚡⚡ <b>ALERTA RELÂMPAGO!</b> ⚡⚡\n\n"
        msg += f"🔥 <b>OFERTA ABSURDA — CORRE!</b>\n\n"
    else:
        msg = f"🔥 <b>OFERTA DO DIA!</b>\n\n"

    msg += f"{loja_emoji} <b>{oferta['loja']}</b>\n\n"
    msg += f"📱 <b>{titulo}</b>\n\n"

    if oferta.get("preco_original") and oferta["preco_original"] > oferta["preco_atual"]:
        msg += f"<s>{formatar_preco(oferta['preco_original'])}</s>\n"
        msg += f"💰 <b>Por apenas {formatar_preco(oferta['preco_atual'])}</b>\n"
        msg += f"📉 <b>{oferta['desconto']}% de desconto!</b>\n"
        if oferta.get("economia", 0) > 0:
            msg += f"💵 <b>Você economiza {formatar_preco(oferta['economia'])}!</b>\n\n"
        else:
            msg += "\n"
    else:
        msg += f"💰 <b>{formatar_preco(oferta['preco_atual'])}</b>\n\n"

    if oferta.get("minimo_historico"):
        msg += f"⏰ <b>Menor preço já visto! Pode acabar a qualquer momento!</b>\n\n"
    elif oferta.get("relampago"):
        msg += f"⏰ <b>Por tempo MUITO limitado!</b>\n\n"
    else:
        msg += f"⚡ <b>Por tempo limitado!</b>\n\n"

    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += f"📢 @promostechbr01 | Promos Tech BR"

    return msg


# ============================================================
# POSTAGEM
# ============================================================

def postar_oferta():
    print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] Buscando oferta...")

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
        tipo = "🚨 MÍNIMO" if oferta.get("minimo_historico") else "⚡ RELÂMPAGO" if oferta.get("relampago") else "normal"
        print(f"✅ [{tipo}] [{oferta['loja']}]: {oferta['titulo'][:40]}...")
    else:
        print("⚠️ Nenhuma oferta encontrada")


def postar_bloco():
    """Posta 6 ofertas com intervalo de 10 minutos entre elas"""
    print(f"\n🎯 [{datetime.now().strftime('%H:%M')}] Iniciando bloco de {POSTS_POR_BLOCO} posts!")
    amazon_usados = []

    for i in range(POSTS_POR_BLOCO):
        print(f"\n📨 Post {i+1}/{POSTS_POR_BLOCO}")

        sorteio = random.randint(1, 10)
        if sorteio <= 7:
            oferta = buscar_meli()
            if not oferta:
                # Amazon sem repetir
                disponiveis = [p for p in PRODUTOS_AMAZON if p["asin"] not in amazon_usados]
                if not disponiveis:
                    amazon_usados = []
                    disponiveis = PRODUTOS_AMAZON
                produto = random.choice(disponiveis)
                amazon_usados.append(produto["asin"])
                oferta = {
                    "titulo": produto["nome"],
                    "preco_atual": produto["preco_atual"],
                    "preco_original": produto["preco_original"],
                    "desconto": calcular_desconto(produto["preco_original"], produto["preco_atual"]),
                    "economia": produto["preco_original"] - produto["preco_atual"],
                    "link": f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}",
                    "imagem": None,
                    "loja": "Amazon",
                    "relampago": False,
                    "minimo_historico": False
                }
        else:
            disponiveis = [p for p in PRODUTOS_AMAZON if p["asin"] not in amazon_usados]
            if not disponiveis:
                amazon_usados = []
                disponiveis = PRODUTOS_AMAZON
            produto = random.choice(disponiveis)
            amazon_usados.append(produto["asin"])
            oferta = {
                "titulo": produto["nome"],
                "preco_atual": produto["preco_atual"],
                "preco_original": produto["preco_original"],
                "desconto": calcular_desconto(produto["preco_original"], produto["preco_atual"]),
                "economia": produto["preco_original"] - produto["preco_atual"],
                "link": f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}",
                "imagem": None,
                "loja": "Amazon",
                "relampago": False,
                "minimo_historico": False
            }

        if oferta:
            mensagem = montar_mensagem(oferta)
            enviar_telegram(mensagem, oferta.get("imagem"))
            print(f"✅ [{oferta['loja']}]: {oferta['titulo'][:40]}...")

        # Aguarda 10 minutos entre posts (exceto no último)
        if i < POSTS_POR_BLOCO - 1:
            print(f"⏳ Aguardando {INTERVALO_MINUTOS} minutos...")
            time.sleep(INTERVALO_MINUTOS * 60)


def verificar_relampago():
    """Verifica a cada 30 minutos se apareceu oferta absurda"""
    print(f"\n⚡ [{datetime.now().strftime('%H:%M')}] Verificando ofertas relâmpago...")
    oferta = buscar_meli(apenas_relampago=True)

    if oferta:
        print(f"🚨 RELÂMPAGO ENCONTRADO: {oferta['titulo'][:40]}")
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
    else:
        print("✅ Nenhum relâmpago no momento")


# ============================================================
# MAIN
# ============================================================

def iniciar_agendamento():
    print("🚀 Iniciando bot...")
    carregar_historico()
    obter_token_meli()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR — Sistema Completo!</b>\n\n"
        "✅ Blocos de 6 posts por horário\n"
        "✅ Filtro inteligente por % e economia em R$\n"
        "⚡ Alerta Relâmpago ativo\n"
        "🚨 Detector de Mínimo Histórico ativo\n\n"
        "⏰ Blocos: 08h | 12h | 17h | 21h\n"
        "🔍 Verificação relâmpago a cada 30min\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    # Agenda blocos
    for horario in HORARIOS_BLOCOS:
        schedule.every().day.at(horario).do(postar_bloco)
        print(f"⏰ Bloco agendado para {horario}")

    # Agenda verificação de relâmpago
    schedule.every(INTERVALO_RELAMPAGO).minutes.do(verificar_relampago)
    print(f"⚡ Verificação relâmpago a cada {INTERVALO_RELAMPAGO} minutos")

    # Renova token MELI
    schedule.every(5).hours.do(obter_token_meli)

    print(f"\n✅ Bot rodando!\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT — SISTEMA COMPLETO")
    print("=" * 50)
    iniciar_agendamento()
