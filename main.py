import json
import logging
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import bitrix
import os
import dotenv

import location_service

dotenv.load_dotenv()
messages_to_user = json.load(open('messages.json', 'r', encoding='UTF-8'))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv('TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def get_response_text(user_data):
    response = "Спасибо за заполнение формы!\n\n"
    response += "Имя: {}\n".format(user_data.get('name'))
    response += "Телефон: {}\n".format(user_data.get('phone'))
    response += "ИНН организации: {}\n".format(user_data.get('inn'))
    response += "Месторасположение: {}\n".format(user_data.get('location'))
    response += "Объем отходов: {}\n".format(user_data.get('volume'))
    response += "Накопление отходов: {}\n".format(user_data.get('waste_type'))
    response += "Погрузка отходов: {}\n".format(user_data.get('loading'))
    response += "Ограничения в доступе: {}\n".format(user_data.get('transport_restrictions'))
    response += "Срочность работ: {}\n".format(user_data.get('urgency'))
    return response

class UserForm(StatesGroup):
    name = State()
    phone = State()
    inn = State()
    location = State()
    volume = State()
    waste_type = State()
    loading = State()
    transport_restrictions = State()
    urgency = State()
    urgency_fast = State()


# Обработчик команды /start
@dp.message_handler(lambda m: m.text == '/start' or m.text == 'Оставить новую заявку')
async def cmd_start(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(message.from_user.first_name))
    await message.answer(messages_to_user['q1'], reply_markup=markup)
    await UserForm.name.set()


# Обработчик состояния 'name'
@dp.message_handler(state=UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('Отправить номер телефона', request_contact=True))
    await state.update_data(name=name)
    await message.answer(messages_to_user['q2'], reply_markup=markup)
    await UserForm.phone.set()


# Обработчик состояния 'phone'
@dp.message_handler(state=UserForm.phone, content_types=['contact', 'text'])
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact is None:
        phone = message.text
    else:
        phone = str(message.contact.phone_number)

    result = re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone)
    if not result:
        return await message.reply(messages_to_user['incorrect_value'] + "\n" + messages_to_user['q2'])
    await state.update_data(phone=phone)

    markup = types.ReplyKeyboardRemove()
    await message.answer(messages_to_user['q3'], reply_markup=markup)
    await UserForm.inn.set()


# Обработчик состояния 'inn'
@dp.message_handler(state=UserForm.inn)
async def process_inn(message: types.Message, state: FSMContext):
    inn = message.text
    if not inn.isdigit():
        return await message.reply(messages_to_user['incorrect_value'] + '\n' + messages_to_user['q3'])
    await state.update_data(inn=inn)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('Отправить текущее местоположение', request_location=True))
    await message.answer(messages_to_user['q4'], reply_markup=markup)
    await UserForm.location.set()


# Обработчик состояния 'location'
@dp.message_handler(state=UserForm.location, content_types=['text', 'location'])
async def process_location(message: types.Message, state: FSMContext):
    if message.location is None:
        location = message.text
    else:
        location = location_service.get_address(message.location.latitude, message.location.longitude)

    await state.update_data(location=location)

    markup = types.ReplyKeyboardRemove()
    await message.answer(messages_to_user['q5'], reply_markup=markup)
    await UserForm.volume.set()


# Обработчик состояния 'volume'
@dp.message_handler(state=UserForm.volume)
async def process_volume(message: types.Message, state: FSMContext):
    volume = message.text
    if not volume.replace('.', '').replace(',', '').isdigit():
        return await message.reply(messages_to_user['incorrect_value'] + '\n' + messages_to_user['q5'])
    await state.update_data(volume=volume)
    await message.answer(messages_to_user['q6'])
    await UserForm.waste_type.set()


# Обработчик состояния 'waste_type'
@dp.message_handler(state=UserForm.waste_type)
async def process_waste_type(message: types.Message, state: FSMContext):
    waste_type = message.text
    await state.update_data(waste_type=waste_type)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Самостоятельно"), KeyboardButton('Подрядчик'))
    await message.answer(messages_to_user['q7'], reply_markup=markup)
    await UserForm.loading.set()


# Обработчик состояния 'loading'
@dp.message_handler(state=UserForm.loading)
async def process_loading(message: types.Message, state: FSMContext):
    loading = message.text
    if loading != 'Самостоятельно' and loading != 'Подрядчик':
        return await message.reply(messages_to_user['incorrect_value'] + '\n' + messages_to_user['q7'])
    await state.update_data(loading=loading)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Ограничений нет"))
    await message.answer(messages_to_user['q8'], reply_markup=markup)
    await UserForm.transport_restrictions.set()


# Обработчик состояния 'transport_restrictions'
@dp.message_handler(state=UserForm.transport_restrictions)
async def process_transport_restrictions(message: types.Message, state: FSMContext):
    transport_restrictions = message.text
    await state.update_data(transport_restrictions=transport_restrictions)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Срочно"), KeyboardButton("Не срочно"))
    await message.answer(messages_to_user['q9'], reply_markup=markup)
    await UserForm.urgency.set()


# Обработчик состояния 'urgency'
@dp.message_handler(state=UserForm.urgency)
async def process_urgency(message: types.Message, state: FSMContext):
    urgency = message.text


    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Оставить новую заявку"))
    if urgency != 'Срочно' and urgency != 'Не срочно':
        await UserForm.urgency_fast.set()
        return await message.reply(messages_to_user['incorrect_value'] + '\n' + messages_to_user['q9'], reply_markup=markup)

    if urgency == 'Срочно':
        await UserForm.urgency_fast.set()
        return await message.answer(messages_to_user['q9_2'])
    await state.update_data(urgency=urgency)
    user_data = await state.get_data()
    bitrix.send_data_to_bitrix24(user_data)
    response = get_response_text(user_data)
    await message.answer(response, reply_markup=markup)
    await state.finish()



@dp.message_handler(state=UserForm.urgency_fast)
async def process_urgency_2(message: types.Message, state: FSMContext):
    urgency = message.text
    await state.update_data(urgency=urgency)
    user_data = await state.get_data()
    bitrix.send_data_to_bitrix24(user_data)
    response = get_response_text(user_data)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Оставить новую заявку"))
    await message.answer(response, reply_markup=markup)
    await bot.send_message(630033075, "Новая срочная заявка!\n" + response)
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
