import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}

BRAND = "Og'abek_UC"
SUPPORT = os.getenv("SUPPORT", "@dasturchi_HTML_CSS")

# Реквизиты для оплаты (задайте в .env)
CARD_NUMBER = os.getenv("CARD_NUMBER", "0000 0000 0000 0000")
CARD_HOLDER = os.getenv("CARD_HOLDER", "NAME SURNAME")
CLICK_NUMBER = os.getenv("CLICK_NUMBER", "+998 90 000 00 00")
USDT_WALLET = os.getenv("USDT_WALLET", "TRC20: T...")

# Пакеты UC -> цена в сумах (ПРИМЕРНЫЕ цены, поставьте свои)
PACKAGES = {
    60: 12_000,
    325: 60_000,
    660: 120_000,
    1800: 289_500,
    3850: 580_000,
    8100: 1_155_000,
}
POPULAR = {660, 1800}

# Цена 1 UC для произвольной суммы и оптовые скидки (от UC -> %)
PER_UC_UZS = 235
WHOLESALE = [(8100, 5), (3850, 3), (1800, 2)]
MIN_CUSTOM, MAX_CUSTOM = 60, 100_000

# Курсы относительно сума (примерные, обновляйте)
RATES = {"UZS": 1, "RUB": 0.0070, "USD": 0.000078}

# Промокоды -> скидка в %
PROMOS = {"PUBG5": 5, "NEWSEASON": 7}