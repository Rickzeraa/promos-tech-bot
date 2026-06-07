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

PRECO_MINIMO = 50
INTERVALO_MONITOR = 3   # minutos
HORAS_BLOQUEIO = 6      # horas sem repetir mesmo produto
LIMITE_DIARIO = 500     # máximo de posts por dia

HORARIOS_AMAZON = ["08:00", "12:00", "17:00", "21:00"]

HISTORICO_FILE = "historico.json"
POSTADOS_FILE = "relampagos_postados.json"
CONTADOR_FILE = "contador_diario.json"
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
meli_token = None
historico_precos = {}
postados = {}
contador_hoje = {"data": "", "total": 0}

# Fontes de busca — cada uma com nome, tipo e parâmetros
FONTES_MELI = [
    # Abas especiais
    {"nome": "Ofertas Relâmpago",   "tipo": "relampago",    "params": "sort=best_discount&deal_ids=MLB_FLASH&limit=50"},
    {"nome": "Preços Imbatíveis",   "tipo": "imbativel",    "params": "sort=best_discount&deal_ids=MLB_UNBEATABLE&limit=50"},
    {"nome": "Todas as Ofertas",    "tipo": "oferta",       "params": "sort=best_discount&has_discount=true&limit=50"},
    # Categorias específicas
    {"nome": "Celulares",           "tipo": "categoria",    "params": "category=MLB1051&sort=best_discount&limit=50"},
    {"nome": "Notebooks",           "tipo": "categoria",    "params": "category=MLB1648&sort=best_discount&limit=50"},
    {"nome": "TVs",                 "tipo": "categoria",    "params": "category=MLB1144&sort=best_discount&limit=50"},
    {"nome": "Fones e Áudio",       "tipo": "categoria",    "params": "category=MLB1714&sort=best_discount&limit=50"},
    {"nome": "Smartwatches",        "tipo": "categoria",    "params": "category=MLB5726&sort=best_discount&limit=50"},
    {"nome": "Caixas de Som",       "tipo": "categoria",    "params": "category=MLB1000&sort=best_discount&limit=50"},
    {"nome": "Games",               "tipo": "categoria",    "params": "category=MLB1741&sort=best_discount&limit=50"},
    {"nome": "Informática",         "tipo": "categoria",    "params": "category=MLB1648&sort=best_discount&limit=50"},
    {"nome": "Eletrônicos",         "tipo": "categoria",    "params": "category=MLB1000&sort=best_discount&limit=50"},
    {"nome": "Câmeras e Foto",      "tipo": "categoria",    "params": "category=MLB1039&sort=best_discount&limit=50"},
    {"nome": "Esporte e Fitness",   "tipo": "categoria",    "params": "category=MLB1276&sort=best_discount&limit=50"},
    {"nome": "Perfumes",            "tipo": "categoria",    "params": "category=MLB1246&sort=best_discount&limit=50"},
    {"nome": "Eletrodomésticos",    "tipo": "categoria",    "params": "category=MLB5726&sort=best_discount&limit=50"},
    {"nome": "Figurinhas Copa",     "tipo": "categoria",    "params": "q=figurinha+copa+2026&sort=best_discount&limit=20"},
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
# CONTADOR DIÁRIO
# ============================================================

def carregar_contador():
    global contador_hoje
    try:
        if os.path.exists(CONTADOR_FILE):
            with open(CONTADOR_FILE, "r") as f:
                contador_hoje = json.load(f)
        hoje = datetime.now().strftime("%Y-%m-%d")
        if contador_hoje.get("data") != hoje:
            contador_hoje = {"data": hoje, "total": 0}
            salvar_contador()
        print(f"✅ Contador: {contador_hoje['total']}/{LIMITE_DIARIO} posts hoje")
    except:
        contador_hoje = {"data": datetime.now().strftime("%Y-%m-%d"), "total": 0}


def salvar_contador():
    try:
        with open(CONTADOR_FILE, "w") as f:
            json.dump(contador_hoje, f)
    except:
        pass


def incrementar_contador():
    global contador_hoje
    hoje = datetime.now().strftime("%Y-%m-%d")
    if contador_hoje.get("data") != hoje:
        contador_hoje = {"data": hoje, "total": 0}
    contador_hoje["total"] += 1
    salvar_contador()


def limite_atingido():
    hoje = datetime.now().strftime("%Y-%m-%d")
    if contador_hoje.get("data") != hoje:
        return False
    return contador_hoje["total"] >= LIMITE_DIARIO


# ============================================================
# PERSISTÊNCIA
# ============================================================

def carregar_dados():
    global historico_precos, postados
    try:
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, "r") as f:
                historico_precos = json.load(f)
            print(f"✅ Histórico: {len(historico_precos)} produtos")
    except:
        historico_precos = {}

    try:
        if os.path.exists(POSTADOS_FILE):
            with open(POSTADOS_FILE, "r") as f:
                postados = json.load(f)
            # Limpa expirados
            agora = datetime.now()
            expirados = []
            for pid, dados in postados.items():
                try:
                    ts = datetime.strptime(dados["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if (agora - ts).total_seconds() / 3600 >= HORAS_BLOQUEIO:
                        expirados.append(pid)
                except:
                    expirados.append(pid)
            for pid in expirados:
                del postados[pid]
            print(f"✅ Postados: {len(postados)} ativos")
        else:
            postados = {}
    except:
        postados = {}


def salvar_postados():
    try:
        with open(POSTADOS_FILE, "w") as f:
            json.dump(postados, f, ensure_ascii=False, indent=2)
    except:
        pass


def foi_postado(produto_id, preco_atual):
    pid = str(produto_id)
    if pid not in postados:
        return False
    try:
        ts = datetime.strptime(postados[pid]["timestamp"], "%Y-%m-%d %H:%M:%S")
        horas = (datetime.now() - ts).total_seconds() / 3600
        if horas >= HORAS_BLOQUEIO:
            del postados[pid]
            salvar_postados()
            return False
        preco_anterior = postados[pid].get("preco", 0)
        if preco_anterior > 0 and preco_atual < preco_anterior * 0.98:
            print(f"💥 Preço caiu! R${preco_anterior:.2f} → R${preco_atual:.2f}")
            return False
        return True
    except:
        del postados[pid]
        return False


def marcar_postado(produto_id, preco):
    pid = str(produto_id)
    postados[pid] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "preco": preco
    }
    salvar_postados()


def eh_minimo_historico(produto_id, titulo, preco_atual):
    pid = str(produto_id)
    eh_minimo = False
    if pid in historico_precos:
        if preco_atual < historico_precos[pid]["minimo"]:
            eh_minimo = True
            historico_precos[pid]["minimo"] = preco_atual
            historico_precos[pid]["data_minimo"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        historico_precos[pid] = {
            "titulo": titulo[:60],
            "minimo": preco_atual,
            "data_minimo": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    historico_precos[pid]["ultimo"] = preco_atual
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico_precos, f, ensure_ascii=False, indent=2)
    except:
        pass
    return eh_minimo


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
            print("✅ Token MELI OK")
            return True
    except Exception as e:
        print(f"❌ Token: {e}")
    return False


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
        r = requests.post(url, json=payload, timeout=10)
        if r.json().get("ok"):
            return True
        else:
            print(f"❌ Telegram: {r.json()}")
            return False
    except Exception as e:
        print(f"❌ Telegram: {e}")
        return False


# ============================================================
# UTILITÁRIOS
# ============================================================

def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_desconto(original, atual):
    if original and atual and original > atual:
        return round(((original - atual) / original) * 100)
    return 0


def tem_desconto_valido(preco_original, preco_atual):
    if preco_atual < PRECO_MINIMO or not preco_original:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual
    # Regra por faixa de ticket
    if preco_atual < 300:
        return desconto >= 15
    elif preco_atual < 1000:
        return desconto >= 10 or economia >= 50
    else:
        return desconto >= 8 or economia >= 100


# ============================================================
# MENSAGENS POR TIPO
# ============================================================

def montar_mensagem(oferta):
    tipo = oferta.get("tipo", "oferta")
    fonte = oferta.get("fonte", "Mercado Livre")
    titulo = oferta["titulo"][:80] + "..." if len(oferta["titulo"]) > 80 else oferta["titulo"]
    minimo = oferta.get("minimo_historico", False)

    # Cabeçalho por tipo
    if minimo:
        cabecalho = "🚨 <b>MÍNIMO HISTÓRICO!</b> 🚨\n\n⚠️ <b>MENOR PREÇO JÁ REGISTRADO!</b>"
        rodape = "⏰ <b>Menor preço já visto! Pode acabar a qualquer momento!</b>"
    elif tipo == "relampago":
        cabecalho = "⚡⚡ <b>OFERTA RELÂMPAGO!</b> ⚡⚡\n\n🔥 <b>POR TEMPO LIMITADÍSSIMO!</b>"
        rodape = "⏰ <b>Essa oferta pode acabar a qualquer momento!</b>"
    elif tipo == "imbativel":
        cabecalho = "💥 <b>PREÇO IMBATÍVEL!</b> 💥\n\n🏆 <b>MENOR PREÇO DO MERCADO!</b>"
        rodape = "🏆 <b>Menor preço disponível agora!</b>"
    elif tipo == "oferta":
        cabecalho = "🔥 <b>OFERTA DO DIA!</b>"
        rodape = "⚡ <b>Por tempo limitado!</b>"
    else:
        cabecalho = f"🔥 <b>OFERTA — {fonte.upper()}!</b>"
        rodape = "⚡ <b>Por tempo limitado!</b>"

    msg = f"{cabecalho}\n\n"
    msg += f"🛒 <b>Mercado Livre</b>"
    if tipo == "categoria":
        msg += f" — {fonte}"
    msg += f"\n\n📱 <b>{titulo}</b>\n\n"

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

    msg += f"{rodape}\n\n"
    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += "📢 @promostechbr01 | Promos Tech BR"

    return msg


def montar_mensagem_amazon(produto):
    desconto = calcular_desconto(produto["preco_original"], produto["preco_atual"])
    economia = produto["preco_original"] - produto["preco_atual"]
    link = f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}"

    msg = "🔥 <b>OFERTA DO DIA!</b>\n\n"
    msg += "📦 <b>Amazon</b>\n\n"
    msg += f"📱 <b>{produto['nome']}</b>\n\n"
    msg += f"<s>{formatar_preco(produto['preco_original'])}</s>\n"
    msg += f"💰 <b>Por apenas {formatar_preco(produto['preco_atual'])}</b>\n"
    msg += f"📉 <b>{desconto}% de desconto!</b>\n"
    msg += f"💵 <b>Economia de {formatar_preco(economia)}!</b>\n\n"
    msg += "⚡ <b>Por tempo limitado!</b>\n\n"
    msg += f"🔗 <a href='{link}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += "📢 @promostechbr01 | Promos Tech BR"

    return msg


# ============================================================
# BUSCA MELI
# ============================================================

def buscar_fonte(fonte, headers, ids_esta_rodada):
    """Busca produtos de uma fonte específica"""
    resultados = []
    try:
        url = f"https://api.mercadolibre.com/sites/MLB/search?{fonte['params']}"
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code == 401:
            obter_token_meli()
            headers["Authorization"] = f"Bearer {meli_token}"
            r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            return []

        produtos = r.json().get("results", [])

        for p in produtos:
            pid = str(p.get("id", ""))
            if not pid or pid in ids_esta_rodada:
                continue

            preco_atual = p.get("price", 0)
            preco_original = p.get("original_price", 0)
            titulo = p.get("title", "")
            permalink = p.get("permalink", "")
            imagem = p.get("thumbnail", "").replace("I.jpg", "O.jpg")

            if preco_atual < PRECO_MINIMO or not titulo:
                continue

            if not tem_desconto_valido(preco_original, preco_atual):
                continue

            desconto = calcular_desconto(preco_original, preco_atual)
            economia = (preco_original - preco_atual) if preco_original else 0
            link = f"{permalink}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}"
            minimo = eh_minimo_historico(pid, titulo, preco_atual)

            resultados.append({
                "id": pid,
                "titulo": titulo,
                "preco_atual": preco_atual,
                "preco_original": preco_original,
                "desconto": desconto,
                "economia": economia,
                "link": link,
                "imagem": imagem,
                "tipo": fonte["tipo"],
                "fonte": fonte["nome"],
                "minimo_historico": minimo
            })

    except Exception as e:
        print(f"⚠️ Erro {fonte['nome']}: {e}")

    return resultados


# ============================================================
# MONITOR PRINCIPAL
# ============================================================

def monitorar():
    global meli_token

    if limite_atingido():
        print(f"⛔ Limite diário de {LIMITE_DIARIO} posts atingido!")
        return

    print(f"\n🔍 [{datetime.now().strftime('%H:%M')}] Monitorando {len(FONTES_MELI)} fontes...")

    if not meli_token:
        obter_token_meli()

    headers = {"Authorization": f"Bearer {meli_token}"}
    ids_esta_rodada = set()
    todos_produtos = []

    # Embaralha fontes para variar a ordem
    fontes = FONTES_MELI.copy()
    random.shuffle(fontes)

    for fonte in fontes:
        if limite_atingido():
            break
        produtos = buscar_fonte(fonte, headers, ids_esta_rodada)
        for p in produtos:
            ids_esta_rodada.add(p["id"])
        todos_produtos.extend(produtos)
        print(f"  📂 {fonte['nome']}: {len(produtos)} produtos novos")

    # Filtra não postados
    novos = []
    ids_novos = set()
    for p in todos_produtos:
        pid = p["id"]
        if pid not in ids_novos and not foi_postado(pid, p["preco_atual"]):
            novos.append(p)
            ids_novos.add(pid)

    if not novos:
        print("✅ Nenhum produto novo")
        return

    # Ordena: mínimo histórico > relâmpago > imbatível > maior desconto
    prioridade = {"relampago": 3, "imbativel": 2, "oferta": 1, "categoria": 0}
    novos.sort(key=lambda x: (
        x["minimo_historico"],
        prioridade.get(x["tipo"], 0),
        x["desconto"]
    ), reverse=True)

    print(f"🚨 {len(novos)} produto(s) para postar!")

    for oferta in novos:
        if limite_atingido():
            print(f"⛔ Limite diário atingido!")
            break

        mensagem = montar_mensagem(oferta)
        if enviar_telegram(mensagem, oferta.get("imagem")):
            marcar_postado(oferta["id"], oferta["preco_atual"])
            incrementar_contador()
            tipo_label = oferta["tipo"].upper()
            print(f"✅ [{tipo_label}] {oferta['fonte']}: {oferta['titulo'][:40]}")
            time.sleep(30)  # 30 segundos entre posts


# ============================================================
# AMAZON
# ============================================================

def postar_amazon():
    if limite_atingido():
        return

    print(f"\n📦 [{datetime.now().strftime('%H:%M')}] Postando Amazon...")
    ja_postados = [pid for pid in postados if len(pid) == 10 and pid.startswith("B")]
    disponiveis = [p for p in PRODUTOS_AMAZON if p["asin"] not in ja_postados]
    if not disponiveis:
        disponiveis = PRODUTOS_AMAZON

    produto = random.choice(disponiveis)
    msg = montar_mensagem_amazon(produto)
    if enviar_telegram(msg):
        marcar_postado(produto["asin"], produto["preco_atual"])
        incrementar_contador()
        print(f"✅ Amazon: {produto['nome'][:40]}")


# ============================================================
# MAIN
# ============================================================

def iniciar():
    print("🚀 Iniciando bot...")
    carregar_dados()
    carregar_contador()
    obter_token_meli()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR — Sistema Amplo!</b>\n\n"
        f"📊 {len(FONTES_MELI)} fontes de busca ativas\n"
        "⚡ Ofertas Relâmpago\n"
        "💥 Preços Imbatíveis\n"
        "🔥 Todas as Ofertas\n"
        "📱 Celulares · Notebooks · TVs · Fones\n"
        "⌚ Smartwatches · Games · Informática\n"
        "📸 Câmeras · Fitness · Perfumes\n\n"
        f"🎯 Limite: {LIMITE_DIARIO} posts/dia\n"
        f"⏱️ Monitor: a cada {INTERVALO_MONITOR} min\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    for horario in HORARIOS_AMAZON:
        schedule.every().day.at(horario).do(postar_amazon)
        print(f"⏰ Amazon: {horario}")

    schedule.every(INTERVALO_MONITOR).minutes.do(monitorar)
    schedule.every(5).hours.do(obter_token_meli)
    schedule.every().day.at("00:00").do(carregar_contador)

    # Roda imediatamente
    postar_amazon()
    monitorar()

    print(f"\n✅ Bot rodando! Monitor a cada {INTERVALO_MONITOR} min\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT — SISTEMA AMPLO")
    print("=" * 50)
    iniciar()
