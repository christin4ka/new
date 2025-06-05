
import asyncio
import logging
import aiohttp
import random

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)

TOKEN = ""

# Инициализация
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
form_router = Router()
dp.include_router(form_router)

# ------------------- ЗАГЛУШКА ВЗАИМОДЕЙСТВИЯ С ОСНОВНОЙ СИСТЕМОЙ --------------------
# Вместо этого сделай вызов к API своей системы

async def check_user_in_system(contact: str) -> bool:
    """
    Проверяет, существует ли пользователь с email/телефоном contact в основной системе.
    Для примера всегда возвращает True.
    """
    # Здесь делаем запрос к API
    # Например:
    # async with aiohttp.ClientSession() as session:
    #    async with session.post("https://api.yoursystem.ru/check_user", json={"contact": contact}) as resp:
    #        data = await resp.json()
    #        return data["exists"]

    # Заглушка
    return True

async def send_code_to_system(contact: str) -> str:
    """
    Отправляет запрос в основную систему, чтобы получить код подтверждения.
    Для примера генерируем рандомный код.
    """
    code = f"{random.randint(1000, 9999)}"
    # Здесь надо отправить этот код в систему для показа пользователю
    # или отправить пользователю email/SMS (в зависимости от требований)
    print(f"[DEBUG] Отправлен код {code} для {contact} в систему")
    return code

# БД
buildings_data = {
    "Корпус А": {
        "Этаж 1": ["Помещение 101", "Помещение 102"],
        "Этаж 2": ["Помещение 201", "Помещение 202"]
    },
    "Корпус Б": {
        "Этаж 1": ["Помещение 103", "Помещение 104"],
        "Этаж 3": ["Помещение 301", "Помещение 302"]
    }
}

inventory_data = {
    "123456": {
        "наименование": "Ноутбук Lenovo",
        "местоположение": "Корпус А, этаж 2, каб. 204",
        "ответственный": "Иванов И.И.",
        "состояние": "Рабочее"
    },
    "654321": {
        "наименование": "Принтер HP",
        "местоположение": "Корпус Б, этаж 1, каб. 101",
        "ответственный": "Петров П.П.",
        "состояние": "На ремонте"
    }
}

#FSM-состояния
class Registration(StatesGroup):
    waiting_for_contact = State()
    waiting_for_code = State()

class SearchByInventory(StatesGroup):
    waiting_for_number = State()

#Временное хранение кода для пользователя
user_codes = {}

# Обработчики
@form_router.message(CommandStart( "start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать!\n\n"
        "Для начала регистрации введите ваш email или номер телефона:"
    )
    await state.set_state(Registration.waiting_for_contact)

@form_router.message(Registration.waiting_for_contact)
async def process_contact(message: Message, state: FSMContext):
    contact = message.text.strip()
    exists = await check_user_in_system(contact)
    if not exists:
        await message.answer("Пользователь с таким email или телефоном не найден. Попробуйте еще раз.")
        return
    code = await send_code_to_system(contact)
    user_codes[message.from_user.id] = code
    await message.answer("Код подтверждения отправлен в систему. Пожалуйста, введите этот код для завершения регистрации:")
    await state.set_state(Registration.waiting_for_code)
    # Сохраняем контакт в state, если надо
    await state.update_data(contact=contact)


    # --- Объявляем функцию show_main_menu ДО использования ---
async def show_main_menu(message: Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="Просмотр корпусов и помещений", callback_data="menu_view_buildings"),
        InlineKeyboardButton(text="Поиск по инвентарному номеру", callback_data="menu_search_inventory")
    )
    await message.answer("Главное меню:", reply_markup=kb)

# --- Затем идут обработчики, которые вызывают show_main_menu ---
@form_router.message(Registration.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    input_code = message.text.strip()
    real_code = user_codes.get(message.from_user.id)
    if input_code == real_code:
        await message.answer("Регистрация успешна! Добро пожаловать в главное меню.")
        await state.clear()
        await show_main_menu(message)  
    else:
        await message.answer("Неверный код. Попробуйте еще раз.")


    # --- Объявляем функцию show_main_menu ДО использования ---
async def show_main_menu(message: Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="Просмотр корпусов и помещений", callback_data="menu_view_buildings"),
        InlineKeyboardButton(text="Поиск по инвентарному номеру", callback_data="menu_search_inventory")
    )
    await message.answer("Главное меню:", reply_markup=kb)

# --- Затем идут обработчики, которые вызывают show_main_menu ---
@form_router.message(Registration.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    input_code = message.text.strip()
    real_code = user_codes.get(message.from_user.id)
    if input_code == real_code:
        await message.answer("Регистрация успешна! Добро пожаловать в главное меню.")
        await state.clear()
        await show_main_menu(message)  
    else:
        await message.answer("Неверный код. Попробуйте еще раз.")


@form_router.message(Command("view_buildings_or_rooms"))
async def view_buildings_handler(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    for building in buildings_data:
        builder.add(InlineKeyboardButton(text=building, callback_data=f"building:{building}"))
    await message.answer("Выберите корпус:", reply_markup=builder.as_markup())

@form_router.callback_query(lambda c: c.data.startswith("building:"))
async def handle_building_choice(callback: CallbackQuery) -> None:
    building = callback.data.split(":", 1)[1]
    floors = buildings_data.get(building, {})
    builder = InlineKeyboardBuilder()
    for floor in floors:
        builder.add(InlineKeyboardButton(text=floor, callback_data=f"floor:{building}:{floor}"))
    await callback.message.edit_text(f"Вы выбрали: {building}\n\n Выберите этаж:", reply_markup=builder.as_markup())

@form_router.callback_query(lambda c: c.data.startswith("floor:"))
async def handle_floor_choice(callback: CallbackQuery) -> None:
    _, building, floor = callback.data.split(":")
    rooms = buildings_data[building][floor]
    builder = InlineKeyboardBuilder()
    for room in rooms:
        builder.add(InlineKeyboardButton(text=room, callback_data=f"room:{building}:{floor}:{room}"))
    await callback.message.edit_text(f"Корпус: {building}\nЭтаж: {floor}\n\n Выберите помещение:", reply_markup=builder.as_markup())

@form_router.callback_query(lambda c: c.data.startswith("room:"))
async def handle_room_choice(callback: CallbackQuery) -> None:
    _, building, floor, room = callback.data.split(":")
    await callback.message.edit_text(f"Вы выбрали:\nКорпус: {building}\nЭтаж: {floor}\nПомещение: {room}")

@form_router.message(Command("search_by_inventory_number"))
async def start_inventory_search(message: Message, state) -> None:
    await message.answer("Введите инвентарный номер:")
    await state.set_state(SearchByInventory.waiting_for_number)

@form_router.message(SearchByInventory.waiting_for_number)
async def process_inventory_number(message: Message, state) -> None:
    number = message.text.strip()
    item = inventory_data.get(number)
    if item:
        await message.answer(
            f"Найден объект:\n"
            f"Наименование: {item['наименование']}\n"
            f"Местоположение: {item['местоположение']}\n"
            f"Ответственный: {item['ответственный']}\n"
            f"Состояние: {item['состояние']}"
        )
    else:
        await message.answer("Объект с таким номером не найден. Проверьте номер и попробуйте снова.")
    await state.clear()

@form_router.message(Command("help"))
async def cmd_help(message: Message):
    await show_main_menu(message)

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
