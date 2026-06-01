# 🤖 Promos Tech BR Bot

Bot automático de ofertas de tecnologia para Telegram.

## Configuração

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais no bot.py
Abra o arquivo `bot.py` e edite o bloco de configurações:

```python
TELEGRAM_TOKEN = "seu_token_aqui"
TELEGRAM_CHANNEL = "@promostechbr01"
AMAZON_ACCESS_KEY = "sua_access_key"
AMAZON_SECRET_KEY = "sua_secret_key"
AMAZON_PARTNER_TAG = "digitalvaiven-20"
SHOPEE_AFFILIATE_ID = "18375371047"
```

### 3. Obter chaves da Amazon PA-API
1. Acesse: https://affiliate-program.amazon.com.br/assoc_credentials/home
2. Crie credenciais de API
3. Copie Access Key e Secret Key

### 4. Rodar o bot
```bash
python bot.py
```

## Horários de postagem
- 12:00 — Almoço
- 18:00 — Saída do trabalho  
- 21:00 — Prime time

## Deploy no Railway
1. Crie conta em railway.app
2. Conecte seu GitHub
3. Suba esta pasta como repositório
4. O Railway detecta automaticamente e roda

## Estrutura
```
promos_tech_bot/
├── bot.py          # Código principal
├── requirements.txt # Dependências
├── railway.toml    # Config do Railway
└── README.md       # Este arquivo
```
