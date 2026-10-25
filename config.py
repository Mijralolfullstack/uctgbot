import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}

BRAND = "Og'abek_UC"
SUPPORT = os.getenv("SUPPORT", "@dasturchi_HTML_CSS")

# Реквизиты для оплаты (задайте в .env)
CARD_NUMBER = os.getenv("CARD_NUMBER", "4073 4200 3294 1407")
CARD_HOLDER = os.getenv("CARD_HOLDER", "OZODA TURGUNOVA")
CLICK_NUMBER = os.getenv("CLICK_NUMBER", "+998 91 510 11 03")
USDT_WALLET = os.getenv("USDT_WALLET", "TRC20: T...")

# Пакеты UC -> цена в сумах (ПРИМЕРНЫЕ цены, поставьте свои)
PACKAGES = {
    60: 12_000,
    325: 62_000,
    660: 122_000,
    1800: 310_000,
    3850: 620_000,
    8100: 1_234_000,
}
POPULAR = {660, 1800}

# Цена 1 UC для произвольной суммы и оптовые скидки (от UC -> %)
PER_UC_UZS = 235
WHOLESALE = [(8100, 5), (3850, 3), (1800, 2)]
MIN_CUSTOM, MAX_CUSTOM = 60, 100_000

# Курсы относительно сума (примерные, обновляйте)
RATES = {"UZS": 1, "RUB": 0.0070, "USD": 0.000088}

# Промокоды -> скидка в %
PROMOS = {"PUBG5": 5, "MOGGER": 10}