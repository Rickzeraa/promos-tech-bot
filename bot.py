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
INTERVALO_MONITOR = 10  # minutos
HORAS_BLOQUEIO = 6      # horas sem repetir mesmo produto

HORARIOS_AMAZON = ["08:00", "12:00", "17:00", "21:00"]

HISTORICO_FILE = "historico.json"
POSTADOS_FILE = "relampagos_postados.json"
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
meli_token = None
historico_precos = {}

# Controle de postados — carregado do arquivo
postados = {}  # id -> {"timestamp": "...", "preco": 0.0}

CATEGORIAS_MELI = [
    "MLB1051", "MLB1648", "MLB1000", "MLB1144",
    "MLB1714", "MLB1039", "MLB1574", "MLB5726", "MLB1743",
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
            # Limpa entradas expiradas ao carregar
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
            print(f"✅ Postados: {len(postados)} ativos ({len(expirados)} expirados removidos)")
        else:
            postados = {}
    except:
        postados = {}


def salvar_postados():
    try:
        with open(POSTADOS_FILE, "w") as f:
            json.dump(postados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar: {e}")


def foi_postado(produto_id, preco_atual):
    """Verifica se produto foi postado recentemente. Retorna True se deve BLOQUEAR."""
    pid = str(produto_id)

    if pid not in postados:
        return False  # nunca postado — libera

    try:
        ts = datetime.strptime(postados[pid]["timestamp"], "%Y-%m-%d %H:%M:%S")
        horas_passadas = (datetime.now() - ts).total_seconds() / 3600

        if horas_passadas >= HORAS_BLOQUEIO:
            del postados[pid]  # expirou — remove e libera
            salvar_postados()
            return False

        preco_anterior = postados[pid].get("preco", 0)
        if preco_anterior > 0 and preco_atual < preco_anterior * 0.98:
            print(f"💥 Preço caiu! R${preco_anterior:.2f} → R${preco_atual:.2f}")
            return False  # preço caiu — libera

        print(f"⏭️ Bloqueado {pid[:15]} ({horas_passadas:.1f}h atrás)")
        return True  # bloqueia

    except Exception as e:
        print(f"⚠️ Erro verificação: {e}")
        del postados[pid]
        return False


def marcar_postado(produto_id, preco):
    pid = str(produto_id)
    postados[pid] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "preco": preco
    }
    salvar_postados()


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
            print("✅ Telegram OK")
        else:
            print(f"❌ Telegram: {r.json()}")
    except Exception as e:
        print(f"❌ Telegram erro: {e}")


# ============================================================
# UTILITÁRIOS
# ============================================================

def formatar_preco(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_desconto(original, atual):
    if original and atual and original > atual:
        return round(((original - atual) / original) * 100)
    return 0


def eh_boa_oferta(preco_original, preco_atual):
    """Regra por faixa de ticket"""
    if preco_atual < PRECO_MINIMO or not preco_original:
        return False
    desconto = calcular_desconto(preco_original, preco_atual)
    economia = preco_original - preco_atual

    if preco_atual < 300:
        return desconto >= 30
    elif preco_atual < 1000:
        return desconto >= 20 or economia >= 100
    else:
        return desconto >= 15 or economia >= 200


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
# MELI
# ============================================================

def buscar_meli():
    global meli_token
    if not meli_token:
        obter_token_meli()

    headers = {"Authorization": f"Bearer {meli_token}"}
    ofertas = []
    ids_vistos = set()

    cats = random.sample(CATEGORIAS_MELI, min(5, len(CATEGORIAS_MELI)))

    for cat_id in cats:
        try:
            r1 = requests.get(
                f"https://api.mercadolibre.com/highlights/MLB/category/{cat_id}",
                headers=headers, timeout=10
            )
            if r1.status_code == 401:
                obter_token_meli()
                headers = {"Authorization": f"Bearer {meli_token}"}
                r1 = requests.get(
                    f"https://api.mercadolibre.com/highlights/MLB/category/{cat_id}",
                    headers=headers, timeout=10
                )
            if r1.status_code != 200:
                continue

            catalog_ids = [i.get("id") for i in r1.json().get("content", []) if i.get("id")]

            for cat_produto_id in catalog_ids:
                if cat_produto_id in ids_vistos:
                    continue
                ids_vistos.add(cat_produto_id)

                try:
                    r_cat = requests.get(
                        f"https://api.mercadolibre.com/products/{cat_produto_id}",
                        headers=headers, timeout=10
                    )
                    nome = cat_produto_id
                    imagem = ""
                    if r_cat.status_code == 200:
                        d = r_cat.json()
                        nome = d.get("name", cat_produto_id)
                        pics = d.get("pictures", [])
                        if pics:
                            imagem = pics[0].get("url", "")

                    r2 = requests.get(
                        f"https://api.mercadolibre.com/products/{cat_produto_id}/items",
                        headers=headers, timeout=10
                    )
                    if r2.status_code != 200:
                        continue

                    items = [i for i in r2.json().get("results", []) if i.get("price", 0) > 0]
                    if not items:
                        continue

                    item = min(items, key=lambda x: x["price"])
                    preco_atual = item["price"]
                    preco_original = item.get("original_price") or 0

                    if not eh_boa_oferta(preco_original, preco_atual):
                        continue

                    minimo = eh_minimo_historico(cat_produto_id, nome, preco_atual)
                    desconto = calcular_desconto(preco_original, preco_atual)
                    link = f"https://www.mercadolivre.com.br/p/{cat_produto_id}?matt_tool=23829216&matt_word={MELI_AFFILIATE_ID}"

                    ofertas.append({
                        "id": cat_produto_id,
                        "titulo": nome,
                        "preco_atual": preco_atual,
                        "preco_original": preco_original,
                        "desconto": desconto,
                        "economia": (preco_original - preco_atual) if preco_original else 0,
                        "link": link,
                        "imagem": imagem,
                        "loja": "Mercado Livre",
                        "minimo_historico": minimo
                    })

                except:
                    continue
        except:
            continue

    print(f"📦 MELI: {len(ofertas)} ofertas encontradas")
    return ofertas


# ============================================================
# MENSAGEM
# ============================================================

def montar_mensagem(oferta):
    emoji = {"Amazon": "📦", "Mercado Livre": "🛒"}
    titulo = oferta["titulo"][:80] + "..." if len(oferta["titulo"]) > 80 else oferta["titulo"]

    if oferta.get("minimo_historico"):
        msg = "🚨 <b>MÍNIMO HISTÓRICO!</b> 🚨\n\n⚠️ <b>MENOR PREÇO JÁ REGISTRADO!</b>\n\n"
    else:
        msg = "⚡⚡ <b>ALERTA RELÂMPAGO!</b> ⚡⚡\n\n🔥 <b>OFERTA IMPERDÍVEL!</b>\n\n"

    msg += f"{emoji.get(oferta['loja'], '🏪')} <b>{oferta['loja']}</b>\n\n"
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
        msg += "⏰ <b>Menor preço já visto!</b>\n\n"
    else:
        msg += "⚡ <b>Por tempo limitado!</b>\n\n"

    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += "📢 @promostechbr01 | Promos Tech BR"
    return msg


# ============================================================
# MONITOR MELI
# ============================================================

def monitorar_meli():
    print(f"\n⚡ [{datetime.now().strftime('%H:%M')}] Verificando ofertas MELI...")

    ofertas = buscar_meli()

    # Filtra apenas as não postadas recentemente
    novas = []
    ids_nesta_rodada = set()

    for o in ofertas:
        pid = str(o["id"])
        if pid in ids_nesta_rodada:
            continue  # evita duplicata na mesma lista
        if not foi_postado(pid, o["preco_atual"]):
            novas.append(o)
            ids_nesta_rodada.add(pid)

    if not novas:
        print("✅ Nenhuma oferta nova")
        return

    # Ordena: mínimo histórico primeiro, depois maior desconto
    novas.sort(key=lambda x: (x["minimo_historico"], x["desconto"]), reverse=True)

    print(f"🚨 {len(novas)} oferta(s) nova(s) para postar!")

    for oferta in novas:
        pid = str(oferta["id"])
        # Verifica UMA VEZ MAIS antes de postar (proteção extra)
        if foi_postado(pid, oferta["preco_atual"]):
            print(f"⏭️ Pulando {pid[:15]} — já postado")
            continue
        mensagem = montar_mensagem(oferta)
        enviar_telegram(mensagem, oferta.get("imagem"))
        marcar_postado(pid, oferta["preco_atual"])
        print(f"✅ Postado: {oferta['titulo'][:40]}")
        time.sleep(60)  # 1 min entre posts


# ============================================================
# AMAZON
# ============================================================

def postar_amazon():
    print(f"\n📦 [{datetime.now().strftime('%H:%M')}] Postando Amazon...")
    amazon_ja_postados = [pid for pid in postados if pid.startswith("B0") or len(pid) == 10]
    disponiveis = [p for p in PRODUTOS_AMAZON if p["asin"] not in amazon_ja_postados]
    if not disponiveis:
        disponiveis = PRODUTOS_AMAZON

    produto = random.choice(disponiveis)
    desconto = calcular_desconto(produto["preco_original"], produto["preco_atual"])
    oferta = {
        "titulo": produto["nome"],
        "preco_atual": produto["preco_atual"],
        "preco_original": produto["preco_original"],
        "desconto": desconto,
        "economia": produto["preco_original"] - produto["preco_atual"],
        "link": f"https://www.amazon.com.br/dp/{produto['asin']}?tag={AMAZON_PARTNER_TAG}",
        "imagem": None,
        "loja": "Amazon",
        "minimo_historico": False
    }

    msg = f"🔥 <b>OFERTA DO DIA!</b>\n\n"
    msg += f"📦 <b>Amazon</b>\n\n"
    msg += f"📱 <b>{produto['nome']}</b>\n\n"
    msg += f"<s>{formatar_preco(produto['preco_original'])}</s>\n"
    msg += f"💰 <b>Por apenas {formatar_preco(produto['preco_atual'])}</b>\n"
    msg += f"📉 <b>{desconto}% de desconto!</b>\n"
    msg += f"💵 <b>Economia de {formatar_preco(produto['preco_original'] - produto['preco_atual'])}!</b>\n\n"
    msg += f"⚡ <b>Por tempo limitado!</b>\n\n"
    msg += f"🔗 <a href='{oferta['link']}'>👉 CLIQUE AQUI PARA COMPRAR</a>\n\n"
    msg += "📢 @promostechbr01 | Promos Tech BR"

    enviar_telegram(msg)
    marcar_postado(produto["asin"], produto["preco_atual"])
    print(f"✅ Amazon: {produto['nome'][:40]}")


# ============================================================
# MAIN
# ============================================================

def iniciar():
    print("🚀 Iniciando bot...")
    carregar_dados()
    obter_token_meli()

    enviar_telegram(
        "🤖 <b>Bot Promos Tech BR — Online!</b>\n\n"
        "📦 Amazon: 08h | 12h | 17h | 21h\n"
        "⚡ Monitor MELI: a cada 10 minutos\n"
        "🚨 Mínimo histórico ativo\n\n"
        "📢 @promostechbr01 | Promos Tech BR"
    )

    for horario in HORARIOS_AMAZON:
        schedule.every().day.at(horario).do(postar_amazon)
        print(f"⏰ Amazon: {horario}")

    schedule.every(INTERVALO_MONITOR).minutes.do(monitorar_meli)
    schedule.every(5).hours.do(obter_token_meli)

    # Roda imediatamente ao iniciar
    postar_amazon()
    monitorar_meli()

    print(f"\n✅ Bot rodando!\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PROMOS TECH BR BOT")
    print("=" * 50)
    iniciar()
