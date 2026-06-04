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

# Regras post normal
DESCONTO_MINIMO_PERCENT = 15
ECONOMIA_MINIMA_REAIS = 30
PRECO_MINIMO = 50

# Regras relâmpago
RELAMPAGO_PRECO_MIN = 200
RELAMPAGO_ECONOMIA_MIN = 100
RELAMPAGO_DESCONTO_MIN = 20

# Blocos agendados
HORARIOS_BLOCOS = ["08:00", "12:00", "17:00", "21:00"]
POSTS_POR_BLOCO = 6
INTERVALO_POSTS_BLOCO = 10  # minutos

# Monitor contínuo de relâmpagos
INTERVALO_MONITOR = 5  # minutos

HISTORICO_FILE = "historico.json"
RELAMPAGOS_POSTADOS_FILE = "relampagos_postados.json"
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
meli_token = None
historico_precos = {}
relampagos_postados = {}  # id -> timestamp

CATEGORIAS_MELI = [
    "MLB1648", "MLB1051", "MLB1000", "MLB1144",
    "MLB1714", "MLB1743", "MLB1748", "MLB5726"
]

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
    {"asin": "B0GH2SC1XG", "nome": "Smart TV TCL 55 4K Google", "preco_original": 3399.00, "preco_atual": 2569.48},
    {"asin": "B0FRJV1B75", "nome": "Monitor LG 43 4K Profissional", "preco_original": 1999.00, "preco_atual": 1791.22},
    {"asin": "B0FVBH3L33", "nome": "JBL Bluetooth Portátil Auracast", "preco_original": 559.00, "preco_atual": 450.00},
    {"asin": "B0DZK3M8GJ", "nome": "Apple iPad 2025 Wi-Fi 128GB", "preco_original": 4499.00, "preco_atual": 3799.00},
    {"asin": "B0CRTYZG5C", "nome": "Soundcore Fone Cancelamento de Ruído", "preco_original": 369.00, "preco_atual": 205.00},
    {"asin": "B09VCHQHZ6", "nome": "Processador AMD Ryzen 7 5700X", "preco_original": 2186.92, "preco_atual": 1149.99},
    {"asin": "B0CT922NH7", "nome": "JBL Soundbar Cinema Subwoofer", "preco_original": 1469.00, "preco_atual": 946.32},
    {"asin": "B0765KZ264", "nome": "Suporte Ergonômico para Monitor", "preco_original": 299.90, "preco_atual": 157.50},
    {"asin": "B0FPHYC9FQ", "nome": "Celular Samsung Galaxy 128GB Preto", "preco_original": 799.00, "preco_atual": 590.90},
]


# ============================================================
# TOKEN MELI
# ============================================================

def obter_token_meli():
    global meli_token
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", json={
            "grant_type": "client_credentials",
            "client_id": MELI_CLIENT_ID,
            "client_secret": MELI_CLIENT_SECRET
        }, timeout=10)
        if r.status_code == 200:
            meli_token = r.json().get("access_token")
            print("✅ Token MELI obtido!")
            return True
    except Exception as e:
        print(f"❌ Erro token: {e}")
    return False


# ============================================================
# HISTÓRICO E CONTROLE DE RELÂMPAGOS
# ============================================================

def carregar_historico():
    global historico_precos, relampagos_postados
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, "r") as f:
                historico_precos = json.load(f)
            print(f"✅ Histórico: {len(historico_precos)} produtos")
        else:
            historico_precos = {}

        if os.path.exists(RELAMPAGOS_POSTADOS_FILE):
            with open(RELAMPAGOS_POSTADOS_FILE, "r") as f:
                relampagos_postados = json.load(f)
        else:
            relampagos_postados = {}
    except:
        historico_precos = {}
        relampagos_postados = {}


def salvar_historico():
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico_precos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro histórico: {e}")


def salvar_relampagos():
    try:
        with open(RELAMPAGOS_POSTADOS_FILE, "w") as f:
            json.dump(relampagos_postados, f, ensure_ascii=False, indent=2)
    except:
        pass


def ja_postado_recentemente(produto_id, preco_atual, horas=6):
    """
    Usa dicionário em memória para controle confiável.
    Não repete se mesmo preço e menos de 6 horas.
    Se preço caiu, posta imediatamente.
    """
    produto_id = str(produto_id)
    
    if produto_id not in relampagos_postados:
        return False

    dados = relampagos_postados[produto_id]
    ultima_vez = dados["timestamp"]
    diferenca = (datetime.now() - ultima_vez).total_seconds() / 3600

    if diferenca >= horas:
        print(f"⏰ {produto_id} — passou {horas}h, pode postar novamente")
        return False

    ultimo_preco = dados.get("preco", 0)
    if preco_atual < ultimo_preco * 0.99:  # margem de 1% para variações mínimas
        print(f"💥 Preço caiu! Era R${ultimo_preco} agora R${preco_atual} — postando!")
        return False

    print(f"⏭️ Ignorando {produto_id} — já postado há {diferenca:.1f}h com mesmo preço")
    return True


def marcar_como_postado(produto_id, preco):
    relampagos_postados[str(produto_id)] = {
        "timestamp": datetime.now(),  # datetime object para cálculo preciso
        "preco": preco
    }
    print(f"📝 Marcado: {produto_id} | R${preco} | {datetime.now().strftime('%H:%M')}")


def verificar_minimo_historico(produto_id, titulo, preco_atual):
    global historico_precos
    produto_id = str(produto_id)
    eh_minimo = False
    if produto_id in historico_precos:
        if preco_atual < historico_precos[produto_id]["minimo"]:
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
        if response.json().get("ok"):
            print("✅ Enviado!")
        else:
            print(f"❌ Telegram: {response.json()}")
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


def vale_postar_normal(preco_original, preco_atual):
    if preco_atual < PRECO_MINIMO:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = (preco_original - preco_atual) if preco_original else 0
    return desconto >= DESCONTO_MINIMO_PERCENT or economia >= ECONOMIA_MINIMA_REAIS


def eh_relampago(preco_original, preco_atual):
    if not preco_original:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual
    return (
        preco_atual >= RELAMPAGO_PRECO_MIN and
        economia >= RELAMPAGO_ECONOMIA_MIN and
        desconto >= RELAMPAGO_DESCONTO_MIN
    )


# ============================================================
# MELI
# ============================================================

def buscar_todos_meli():
    """Busca todos os produtos disponíveis no MELI e retorna lista completa"""
    global meli_token

    if not meli_token:
        obter_token_meli()

    headers = {"Authorization": f"Bearer {meli_token}"}
    todos = []

    cats = random.sample(CATEGORIAS_MELI, min(4, len(CATEGORIAS_MELI)))

    for cat in cats:
        try:
            r1 = requests.get(
                f"https://api.mercadolibre.com/highlights/MLB/category/{cat}",
                headers=headers, timeout=10
            )
            if r1.status_code == 401:
                obter_token_meli()
                headers = {"Authorization": f"Bearer {meli_token}"}
                r1 = requests.get(
                    f"https://api.mercadolibre.com/highlights/MLB/category/{cat}",
                    headers=headers, timeout=10
                )
            if r1.status_code != 200:
                continue

            catalog_ids = [item.get("id") for item in r1.json().get("content", []) if item.get("id")][:4]

            for cat_id in catalog_ids:
                try:
                    r_cat = requests.get(
                        f"https://api.mercadolibre.com/products/{cat_id}",
                        headers=headers, timeout=10
                    )
                    nome = cat_id
                    imagem = ""
                    if r_cat.status_code == 200:
                        cat_data = r_cat.json()
                        nome = cat_data.get("name", cat_id)
                        pics = cat_data.get("pictures", [])
                        if pics:
                            imagem = pics[0].get("url", "")

                    r2 = requests.get(
                        f"https://api.mercadolibre.com/products/{cat_id}/items",
                        headers=headers, timeout=10
                    )
                    if r2.status_code != 200:
                        continue

                    items = [i for i in r2.json().get("results", []) if i.get("price", 0) > 0]
                    if not items:
                        continue

                    item_mais_barato = min(items, key=lambda x: x["price"])
                    preco_atual = item_mais_barato["price"]
                    preco_original = item_mais_barato.get("original_price") or 0

                    link = f"https://www.mercadolivre.com.br/p/{cat_id}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}"
                    minimo = verificar_minimo_historico(cat_id, nome, preco_atual)
                    relampago = eh_relampago(preco_original, preco_atual)

                    todos.append({
                        "id": cat_id,
                        "titulo": nome,
                        "preco_atual": preco_atual,
                        "preco_original": preco_original,
                        "desconto": calcular_desconto(preco_original, preco_atual),
                        "economia": (preco_original - preco_atual) if preco_original else 0,
                        "link": link,
                        "imagem": imagem,
                        "loja": "Mercado Livre",
                        "relampago": relampago,
                        "minimo_historico": minimo
                    })

                except Exception as e:
                    continue

        except Exception as e:
            continue

    return todos


def buscar_meli_normal():
    """Para blocos agendados — pega melhor oferta normal"""
    todos = buscar_todos_meli()
    candidatos = [p for p in todos if vale_postar_normal(p["preco_original"], p["preco_atual"])]
    if candidatos:
        candidatos.sort(key=lambda x: x["desconto"], reverse=True)
        return candidatos[0]
    if todos:
        return todos[0]
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
    except:
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
# MONITOR CONTÍNUO DE RELÂMPAGOS
# ============================================================

def monitorar_relampagos():
    """Roda a cada 5 minutos — posta TODOS os relâmpagos encontrados"""
    print(f"\n⚡ [{datetime.now().strftime('%H:%M')}] Monitorando relâmpagos...")

    todos = buscar_todos_meli()
    relampagos = [
        p for p in todos
        if (p["relampago"] or p["minimo_historico"])
        and not ja_postado_recentemente(str(p["id"]), p["preco_atual"], horas=6)
    ]

    if not relampagos:
        print("✅ Nenhum relâmpago no momento")
        return

    print(f"🚨 {len(relampagos)} relâmpago(s) encontrado(s)!")

    # Ordena por prioridade: mínimo histórico > relâmpago > desconto
    relampagos.sort(key=lambda x: (x["minimo_historico"], x["relampago"], x["desconto"]), reverse=True)

    for oferta in relampagos:
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
        marcar_como_postado(str(oferta["id"]), oferta["preco_atual"])
        print(f"⚡ Postado: {oferta['titulo'][:50]}")
        time.sleep(60)  # 1 minuto entre cada relâmpago


# ============================================================
# BLOCOS AGENDADOS
# ============================================================

def postar_bloco():
    print(f"\n🎯 [{datetime.now().strftime('%H:%M')}] Bloco de {POSTS_POR_BLOCO} posts!")
    amazon_usados = []

    for i in range(POSTS_POR_BLOCO):
        print(f"\n📨 Post {i+1}/{POSTS_POR_BLOCO}")
        sorteio = random.randint(1, 10)

        if sorteio <= 7:
            oferta = buscar_meli_normal()
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

        if i < POSTS_POR_BLOCO - 1:
            print(f"⏳ Aguardando {INTERVALO_POSTS_BLOCO} minutos (monitorando relâmpagos)...")
            segundos_totais = INTERVALO_POSTS_BLOCO * 60
            segundos_passados = 0
            ultima_verificacao = 0
            while segundos_passados < segundos_totais:
                time.sleep(30)
                segundos_passados += 30
                ultima_verificacao += 30
                # Verifica relâmpago a cada 5 minutos
                # A regra de 6 horas + mudança de preço já evita duplicatas
                if ultima_verificacao >= 300:
                    monitorar_relampagos()
                    ultima_verificacao = 0


# ============================================================
# MAIN
# ============================================================

def iniciar_agendamento():
    print("🚀 Iniciando bot...")
    carregar_historico()
    obter_token_meli()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR — Monitor Ativo!</b>\n\n"
        "✅ Mercado Livre funcionando\n"
        "✅ Amazon com 18 produtos\n"
        "✅ Blocos de 6 posts: 08h | 12h | 17h | 21h\n"
        "⚡ Monitor relâmpago a cada 5 minutos\n"
        "🚨 Mínimo histórico ativo\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    # Blocos agendados
    for horario in HORARIOS_BLOCOS:
        schedule.every().day.at(horario).do(postar_bloco)
        print(f"⏰ Bloco: {horario}")

    # Monitor contínuo de relâmpagos
    schedule.every(INTERVALO_MONITOR).minutes.do(monitorar_relampagos)
    print(f"⚡ Monitor relâmpago: a cada {INTERVALO_MONITOR} minutos")

    # Renova token
    schedule.every(5).hours.do(obter_token_meli)

    # Posta um bloco inicial para testar
    postar_bloco()

    print(f"\n✅ Bot rodando!\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT")
    print("=" * 50)
    iniciar_agendamento()
