from __future__ import annotations
from aiogram.enums import ParseMode
import asyncio 
import html
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties

from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db
from config import *

router = Router()
LINE = "━━━━━━━━━━━━━━━━━━"
METHODS = {"click": "📱 Click / Uzum / Payme", "card": "💳 Банковская карта", "usdt": "🪙 USDT (TRC20)"}


class Order(StatesGroup):
    player_id = State()
    custom = State()
    promo = State()
    receipt = State()


# ---------- helpers ----------
def money(uzs: int, cur: str) -> str:
    if cur == "UZS":
        return f"{uzs:,}".replace(",", " ") + " so'm"
    v = uzs * RATES[cur]
    if cur == "RUB":
        return f"{round(v):,}".replace(",", " ") + " ₽"
    return f"${v:,.2f}"


def total_uzs(uc: int, promo: str | None) -> int:
    if uc in PACKAGES:
        price, disc = PACKAGES[uc], 0
    else:
        price = uc * PER_UC_UZS
        disc = next((p for amount, p in WHOLESALE if uc >= amount), 0)
    if promo:
        disc += PROMOS[promo]
    return round(price * (100 - disc) / 100 / 100) * 100


def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for row in rows:
        b.row(*[__import__("aiogram").types.InlineKeyboardButton(text=t, callback_data=d) for t, d in row])
    return b.as_markup()


async def show(cb: CallbackQuery, text: str, markup: InlineKeyboardMarkup):
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await cb.message.answer(text, reply_markup=markup)
    await cb.answer()


def menu_kb():
    return kb([
        [("🛒 Пакеты UC", "packs"), ("🧮 Калькулятор", "calc")],
        [("💳 Способы оплаты", "pays"), ("❓ FAQ", "faq")],
        [("🌐 Валюта", "cur"), ("🆘 Поддержка", "support")],
    ])


MENU_TEXT = (
    f"⚡ <b>{BRAND}</b>\n<i>Automated PUBG Mobile Top-Up</i>\n{LINE}\n"
    "Мгновенное пополнение UC по Player ID.\n"
    "Оплата: Click, карта, USDT.\n\n"
    "🔒 Пароли от аккаунта <b>не нужны</b> — только ID игрока.\n"
    f"🆘 Поддержка 24/7: {SUPPORT}"
)


# ---------- menu ----------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(MENU_TEXT, reply_markup=menu_kb())


@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, MENU_TEXT, menu_kb())


@router.callback_query(F.data == "support")
async def support(cb: CallbackQuery):
    await show(cb, f"🆘 <b>Поддержка</b>\n{LINE}\nОпечатались в ID, нужен статус заказа или есть вопрос?\nПишите: {SUPPORT}",
               kb([[("⬅️ Меню", "menu")]]))


@router.callback_query(F.data == "faq")
async def faq(cb: CallbackQuery):
    await show(cb,
        f"❓ <b>FAQ</b>\n{LINE}\n"
        "<b>Как оплатить?</b>\nВыберите пакет → введите ID → выберите способ оплаты → "
        "переведите точную сумму и отправьте чек (фото) в бот.\n\n"
        "<b>Сколько ждать?</b>\nПосле проверки чека UC приходят на ваш ID.\n\n"
        f"<b>Ошибся в ID?</b>\nСразу пишите в поддержку: {SUPPORT}",
        kb([[("⬅️ Меню", "menu")]]))


@router.callback_query(F.data == "pays")
async def pays(cb: CallbackQuery):
    await show(cb,
        f"💳 <b>Способы оплаты</b>\n{LINE}\n"
        "📱 <b>Click / Uzum / Payme</b> — без лишней комиссии\n"
        "💳 <b>Банковская карта</b> — перевод на карту\n"
        "🪙 <b>USDT (TRC20)</b> — криптоплатёж\n\n"
        "Реквизиты покажу при оформлении заказа.",
        kb([[("🛒 К пакетам", "packs")], [("⬅️ Меню", "menu")]]))


# ---------- currency ----------
@router.callback_query(F.data == "cur")
async def cur(cb: CallbackQuery):
    now = await db.get_currency(cb.from_user.id)
    rows = [[(("✅ " if c == now else "") + c, f"setcur:{c}") for c in RATES]]
    await show(cb, f"🌐 <b>Валюта цен</b>\n{LINE}\nТекущая: <b>{now}</b>", kb(rows + [[("⬅️ Меню", "menu")]]))


@router.callback_query(F.data.startswith("setcur:"))
async def setcur(cb: CallbackQuery):
    await db.set_currency(cb.from_user.id, cb.data.split(":")[1])
    await cur(cb)


# ---------- packages ----------
@router.callback_query(F.data == "packs")
async def packs(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    c = await db.get_currency(cb.from_user.id)
    rows, row = [], []
    for uc, price in PACKAGES.items():
        fire = "🔥 " if uc in POPULAR else "💎 "
        row.append((f"{fire}{uc} UC · {money(price, c)}", f"pk:{uc}"))
        if len(row) == 1:
            rows.append(row); row = []
    rows += [[("🧮 Свой объём UC", "calc")], [("⬅️ Меню", "menu")]]
    await show(cb, f"🛒 <b>Выберите пакет UC</b>\n{LINE}\n🔥 — популярное. Цены в <b>{c}</b>.", kb(rows))


@router.callback_query(F.data.startswith("pk:"))
async def pick(cb: CallbackQuery, state: FSMContext):
    await state.update_data(uc=int(cb.data[3:]), promo=None)
    await ask_id(cb, state)


async def ask_id(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Order.player_id)
    d = await state.get_data()
    await show(cb, f"🎮 <b>Шаг 1 из 3 — Player ID</b>\n{LINE}\nПакет: <b>{d['uc']} UC</b>\n\n"
               "Отправьте числовой ID из профиля PUBG Mobile\n(например <code>5182947261</code>).",
               kb([[("❌ Отмена", "menu")]]))


# ---------- calculator ----------
@router.callback_query(F.data == "calc")
async def calc(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Order.custom)
    await show(cb, f"🧮 <b>Калькулятор UC</b>\n{LINE}\nВведите нужное количество UC "
               f"({MIN_CUSTOM}–{MAX_CUSTOM}).\nОптовая скидка: " +
               ", ".join(f"от {a} UC −{p}%" for a, p in reversed(WHOLESALE)),
               kb([[("⬅️ Меню", "menu")]]))


@router.message(Order.custom)
async def calc_amount(m: Message, state: FSMContext):
    if not (m.text or "").strip().isdigit() or not MIN_CUSTOM <= int(m.text) <= MAX_CUSTOM:
        return await m.answer(f"Введите число от {MIN_CUSTOM} до {MAX_CUSTOM}.")
    uc = int(m.text)
    c = await db.get_currency(m.from_user.id)
    await state.update_data(uc=uc, promo=None)
    await state.set_state(Order.player_id)
    await m.answer(f"🧮 <b>{uc} UC</b> = <b>{money(total_uzs(uc, None), c)}</b>\n{LINE}\n"
                   "🎮 Теперь отправьте ваш Player ID.", reply_markup=kb([[("❌ Отмена", "menu")]]))


# ---------- checkout ----------
async def checkout(m: Message, state: FSMContext, uid: int):
    d = await state.get_data()
    c = await db.get_currency(uid)
    promo = f"\n🎟 Промокод: <b>{d['promo']}</b> (−{PROMOS[d['promo']]}%)" if d.get("promo") else ""
    await state.set_state(Order.promo)  # ждём промокод, но кнопки оплаты работают в любом состоянии
    await m.answer(
        f"🧾 <b>Шаг 2 из 3 — Оплата</b>\n{LINE}\n"
        f"💎 Пакет: <b>{d['uc']} UC</b>\n🎮 Player ID: <code>{d['player_id']}</code>{promo}\n"
        f"💰 К оплате: <b>{money(total_uzs(d['uc'], d.get('promo')), c)}</b>\n{LINE}\n"
        "Выберите способ оплаты. Есть промокод — просто отправьте его сообщением.",
        reply_markup=kb([[(t, f"pay:{k}")] for k, t in METHODS.items()] + [[("❌ Отмена", "menu")]]))


@router.message(Order.player_id)
async def got_id(m: Message, state: FSMContext):
    pid = (m.text or "").strip()
    if not pid.isdigit() or not 7 <= len(pid) <= 12:
        return await m.answer("⚠️ ID должен состоять из 7–12 цифр. Попробуйте ещё раз.")
    await state.update_data(player_id=pid)
    await checkout(m, state, m.from_user.id)


@router.message(Order.promo)
async def got_promo(m: Message, state: FSMContext):
    code = (m.text or "").strip().upper()
    if code not in PROMOS:
        return await m.answer("❌ Такого промокода нет. Выберите способ оплаты или попробуйте другой код.")
    await state.update_data(promo=code)
    await m.answer(f"✅ Промокод применён: −{PROMOS[code]}%")
    await checkout(m, state, m.from_user.id)


@router.callback_query(F.data.startswith("pay:"))
async def pay(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if "player_id" not in d:
        return await cb.answer("Сессия устарела, начните заново: /start", show_alert=True)
    method = cb.data[4:]
    c = await db.get_currency(cb.from_user.id)
    amount = total_uzs(d["uc"], d.get("promo"))
    await state.update_data(method=method, amount=amount)
    await state.set_state(Order.receipt)
    if method == "card":
        details, sum_text = f"<code>{CARD_NUMBER}</code>\n{html.escape(CARD_HOLDER)}", money(amount, "UZS")
    elif method == "click":
        details, sum_text = f"Номер: <code>{CLICK_NUMBER}</code>", money(amount, "UZS")
    else:
        details, sum_text = f"<code>{USDT_WALLET}</code>", money(amount, "USD")
    await show(cb,
        f"💳 <b>Шаг 3 из 3 — Перевод</b>\n{LINE}\n{METHODS[method]}\n{details}\n\n"
        f"Сумма: <b>{sum_text}</b>\n{LINE}\n"
        "После перевода отправьте <b>фото чека</b> в этот чат 📸",
        kb([[("❌ Отмена", "menu")]]))


@router.message(Order.receipt, F.photo)
async def got_receipt(m: Message, state: FSMContext, bot: Bot):
    d = await state.get_data()
    oid = await db.create_order(m.from_user.id, m.from_user.username, d["player_id"],
                                d["uc"], d["amount"], d["method"], d.get("promo"))
    await state.clear()
    await m.answer(f"✅ <b>Заказ #{oid} принят</b>\n{LINE}\nПроверяем оплату, обычно это несколько минут. "
                   "Я напишу, как только UC будут отправлены.", reply_markup=kb([[("⬅️ Меню", "menu")]]))
    user = f"@{m.from_user.username}" if m.from_user.username else f"id {m.from_user.id}"
    caption = (f"🆕 <b>Заказ #{oid}</b>\n👤 {html.escape(user)}\n🎮 <code>{d['player_id']}</code>\n"
               f"💎 {d['uc']} UC\n💰 {money(d['amount'], 'UZS')}\n💳 {METHODS[d['method']]}\n"
               f"🎟 {d.get('promo') or '—'}")
    for admin in ADMIN_IDS:
        await bot.send_photo(admin, m.photo[-1].file_id, caption=caption,
                             reply_markup=kb([[("✅ Оплата пришла", f"adm:ok:{oid}"), ("❌ Отклонить", f"adm:no:{oid}")]]))


@router.message(Order.receipt)
async def need_photo(m: Message):
    await m.answer("📸 Отправьте чек именно <b>фото</b>, либо нажмите «Отмена».")


# ---------- admin ----------
@router.callback_query(F.data.startswith("adm:"))
async def admin_action(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id not in ADMIN_IDS:
        return await cb.answer("Нет доступа", show_alert=True)
    _, act, oid = cb.data.split(":")
    order = await db.get_order(int(oid))
    if not order:
        return await cb.answer("Заказ не найден")
    texts = {
        "ok": ("paid", "✅ Оплата подтверждена", f"✅ Оплата по заказу #{oid} подтверждена. Отправляем UC на ID {order['player_id']}…",
               kb([[("📦 UC отправлены", f"adm:done:{oid}")]])),
        "done": ("done", "📦 Выполнен", f"🎉 Заказ #{oid} выполнен! {order['uc']} UC отправлены на ID {order['player_id']}. Приятной игры!", None),
        "no": ("rejected", "❌ Отклонён", f"❌ Заказ #{oid} отклонён: оплата не найдена. Если это ошибка, напишите {SUPPORT}", None),
    }
    status, label, user_msg, markup = texts[act]
    await db.set_status(int(oid), status)
    await cb.message.edit_caption(caption=f"{cb.message.caption}\n\n<b>{label}</b>", reply_markup=markup)
    await bot.send_message(order["user_id"], user_msg)
    await cb.answer(label)


@router.message(Command("admin"))
async def admin_panel(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    rows = await db.stats()
    lines = [f"{s}: {n} шт · {money(total, 'UZS')}" for s, n, total in rows] or ["Заказов пока нет"]
    await m.answer("📊 <b>Статистика</b>\n" + "\n".join(lines))


async def main():
    logging.basicConfig(level=logging.INFO)
    await db.init()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())