from collections import defaultdict

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, \
    InlineKeyboardMarkup

import keyboards as kb
from consts import products_names, product_descriptions, info, \
    RegistrationStateGroup, product_index, LoginStateGroup
# create_table - ненужный импорт
from db_engine import create_table, append_to_table, get_products, delete_line, \
    get_all_id, get_ordered_names, set_ordered, get_ordered_ids, clear_database

API = '5913091059:AAGpH1ZNaJGNtRxQSEpQSzb_LYMHNacz9U0'
bot = Bot(token=API)
data = defaultdict(dict)
tmp = defaultdict(dict)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def hi(message: Message):
    await bot.send_message(message.from_user.id,
                           'Привет, это магазин электроники',
                           reply_markup=kb.keyboard_menu)


@dp.callback_query_handler(lambda c: c.data == 'menu')
async def main_menu(callback_query: CallbackQuery):
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id,
                           'Главное меню.\n',
                           reply_markup=kb.keyboard_menu)


@dp.callback_query_handler(lambda c: c.data == 'catalog')
async def show_catalog(callback_query: CallbackQuery):
    await callback_query.message.delete()
    global product_index
    # [note] Проблемы с кодировкой файла (кажется такая же была на защите)
    with open('product_names.txt') as f:
        file_size = len(f.readlines())
    if product_index > file_size - 1:
        product_index = 0
    msg = products_names[product_index] + '\n\n' + product_descriptions[
        product_index]
    await bot.send_message(callback_query.from_user.id,
                           # photo=open(f'img/tovar{product_index + 1}.jpg', 'rb'),
                           f'Каталог товаров\n\n{msg}',
                           reply_markup=kb.keyboard_catalogue)


@dp.callback_query_handler(lambda c: c.data == 'next')
async def add_to_cart(callback_query: CallbackQuery):
    global product_index
    product_index += 1
    await show_catalog(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'back')
async def add_to_cart(callback_query: CallbackQuery):
    global product_index
    if product_index <= 0:
        product_index = 3
    product_index -= 1
    await show_catalog(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'add_to_cart')
async def add_to_cart(callback_query: CallbackQuery):
    await callback_query.message.delete()
    append_to_table(products_names[product_index],
                    callback_query.from_user.id, )
    await bot.send_message(callback_query.from_user.id,
                           f'Товар добавлен в корзину',
                           reply_markup=kb.keyboard_added_to_cart)


@dp.callback_query_handler(lambda c: c.data == 'cart')
async def show_cart(callback_query: CallbackQuery):
    await callback_query.message.delete()
    products = list(get_products(callback_query.from_user.id))
    if len(products) == 0:
        await bot.send_message(callback_query.from_user.id,
                               'Ваша корзина пуста.',
                               reply_markup=InlineKeyboardMarkup().add(
                                   kb.button_back))
    else:
        await bot.send_message(callback_query.from_user.id,
                               ('Ваши товары:\n' + '\n'.join(
                                   [f'{n + 1}. ' + i[0] for n, i in
                                    enumerate(products)])),
                               reply_markup=kb.keyboard_cart
                               )


@dp.callback_query_handler(lambda c: c.data == 'delete')
async def delete_product(callback_query: CallbackQuery):
    await callback_query.message.delete()
    buttons_delete = [
        InlineKeyboardButton(str(n + 1), callback_data=f'delete_button_{i[0]}')
        for n, i in enumerate(get_all_id())
    ]
    await bot.send_message(callback_query.from_user.id,
                           'Выбери товар, который хотите удалить',
                           reply_markup=InlineKeyboardMarkup(row_width=2).add(
                               *buttons_delete).add(kb.button_back)
                           )


@dp.callback_query_handler(lambda c: c.data == 'clear_cart')
async def clear_cart(callback_query: CallbackQuery):
    await callback_query.message.delete()
    clear_database()
    await bot.send_message(callback_query.from_user.id,
                           "Корзина была очищена",
                           reply_markup=kb.keyboard_ordered)


@dp.callback_query_handler(
    lambda c: c.data in [f'delete_button_{i[0]}' for i in get_all_id()])
async def delete_buttons(callback_query: CallbackQuery):
    await callback_query.message.delete()
    delete_line(int(callback_query.data[-1]))
    await bot.send_message(callback_query.from_user.id,
                           'Товар был удален!',
                           reply_markup=kb.keyboard_menu)


@dp.callback_query_handler(lambda c: c.data == 'order')
async def order(callback_query: CallbackQuery):
    await callback_query.message.delete()
    if data.get(callback_query.from_user.id):
        if data.get(callback_query.from_user.id).get('logged_in'):
            buttons_order = [
                InlineKeyboardButton(str(n + 1),
                                     callback_data=f'order_button_{i[0]}')
                for n, i in enumerate(get_all_id())
            ]
            await bot.send_message(callback_query.from_user.id,
                                   'Выберите товар, который хотите заказать',
                                   reply_markup=InlineKeyboardMarkup(
                                       row_width=2).add(
                                       *buttons_order).add(kb.button_back))
        else:
            await bot.send_message(callback_query.from_user.id,
                                   "Прежде чем заказать товар, вам "
                                   "необходимо войти",
                                   reply_markup=kb.keyboard_register)
    else:
        await bot.send_message(callback_query.from_user.id,
                               "Прежде чем заказать товар, вам "
                               "необходимо пройти регистрацию",
                               reply_markup=kb.keyboard_register)


@dp.callback_query_handler(
    lambda c: c.data in [f'order_button_{i[0]}' for i in get_all_id()])
async def order_buttons(callback_query: CallbackQuery):
    await callback_query.message.delete()
    set_ordered(True, callback_query.data[-1])
    await bot.send_message(callback_query.from_user.id,
                           "Ожидайте доставки товара!\nОтследить доставку можно в пункте меню 'Мои заказы'",
                           reply_markup=kb.keyboard_ordered)


@dp.callback_query_handler(lambda c: c.data == 'orders')
async def client_orders(callback_query: CallbackQuery):
    await callback_query.message.delete()
    msg = ''.join([str(i + 1) + '. ' + el[0] + '\n' for i, el in
                   enumerate(get_ordered_names())])
    await bot.send_message(callback_query.from_user.id,
                           f"Ваши заказы:\n{msg}",
                           reply_markup=kb.keyboard_orders
                           )


@dp.callback_query_handler(lambda c: c.data == 'cancel')
async def cancel_order(callback_query: CallbackQuery):
    await callback_query.message.delete()
    buttons_orders = [
        InlineKeyboardButton(str(n + 1), callback_data=f'cancel_order_{i[0]}')
        for n, i in enumerate(get_ordered_ids())
    ]
    await bot.send_message(callback_query.from_user.id,
                           'Выберите заказ, который хотите отменить',
                           reply_markup=InlineKeyboardMarkup(row_width=2).add(
                               *buttons_orders).add(kb.button_back)
                           )


@dp.callback_query_handler(
    lambda c: c.data in [f'cancel_order_{i[0]}' for i in get_ordered_ids()])
async def cancel_buttons_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()
    set_ordered(False, callback_query.data[-1])
    await bot.send_message(callback_query.from_user.id,
                           'Заказ был отменен',
                           reply_markup=kb.keyboard_menu
                           )


@dp.callback_query_handler(lambda c: c.data == 'info')
async def info_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()
    # Всё тот же вопрос - зачем эта переменная, если можно сразу info передавать?
    information = info
    await bot.send_message(callback_query.from_user.id,
                           information,
                           parse_mode='HTML',
                           reply_markup=InlineKeyboardMarkup(row_width=2).add(
                               kb.button_back)
                           )


@dp.callback_query_handler(lambda c: c.data == 'register')
async def register(callback_query: CallbackQuery):
    if data.get(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id,
                               'Вы уже зарегистрированы!',
                               reply_markup=InlineKeyboardMarkup()
                               .add(InlineKeyboardButton(
                                   'Войти',
                                   callback_data='login'
                               )).add(kb.button_back))
    else:
        await bot.send_message(callback_query.from_user.id,
                               "Введите ваш логин", )
        await RegistrationStateGroup.login_add.set()


@dp.message_handler(state=RegistrationStateGroup.login_add)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['login'] = message.text
    await message.answer('Введите ваше ФИО.')
    await RegistrationStateGroup.fio_add.set()


# В следующих 5-ти функциях state не нужен
@dp.message_handler(state=RegistrationStateGroup.fio_add)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['fio'] = message.text
    await message.answer('Введите почту.')
    await RegistrationStateGroup.email_add.set()


@dp.message_handler(state=RegistrationStateGroup.email_add)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['email'] = message.text
    await message.answer('Введите номер телефона.')
    await RegistrationStateGroup.phone_add.set()


@dp.message_handler(state=RegistrationStateGroup.phone_add)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['phone'] = message.text
    await message.answer('Введите пароль.')
    await RegistrationStateGroup.password.set()


@dp.message_handler(state=RegistrationStateGroup.password)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['pass_1'] = message.text
    await message.answer('Введите пароль повторно.')
    await RegistrationStateGroup.password_confirm.set()


@dp.message_handler(state=RegistrationStateGroup.password_confirm)
async def process_fio_add(message: Message, state: FSMContext):
    data[message.from_user.id]['pass_2'] = message.text
    if data.get(message.from_user.id).get('pass_1') != data.get(
            message.from_user.id).get('pass_2'):
        await message.answer(
            'Введенные пароли не совпадают!\nПопробуйте еще раз.\n\n'
            'Введите пароль.')
        await RegistrationStateGroup.password.set()
    else:
        data[message.from_user.id]['email'] = message.text
        await message.answer(f'Вы были успешно зарегистрированы!'
                             f'\n\nЛогин - {data.get(message.from_user.id)["login"]}'
                             f'\nФИО - {data.get(message.from_user.id)["fio"]}'
                             f'\nПочта - {data.get(message.from_user.id)["email"]}'
                             f'\nТелефон - {data.get(message.from_user.id)["phone"]}',
                             reply_markup=kb.keyboard_menu)
        await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'login')
async def log_in(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id,
                           'Введите логин.')
    await LoginStateGroup.login.set()


@dp.message_handler(state=LoginStateGroup.login)
async def login(message: Message, state: FSMContext):
    tmp[message.from_user.id]['login'] = message.text
    await message.answer('Введите пароль.')
    await LoginStateGroup.password.set()


@dp.message_handler(state=LoginStateGroup.password)
async def password(message: Message, state: FSMContext):
    # Как и говорил на защите - tmp не чистится, хотя после проверки логина и пароля данные уже не нужны
    tmp[message.from_user.id]['pass_1'] = message.text
    if data.get(message.from_user.id):
        if tmp.get(message.from_user.id).get('login') == data.get(message.from_user.id).get('login'):
            if tmp.get(message.from_user.id).get('pass_1') == data.get(message.from_user.id).get('pass_1'):
                data[message.from_user.id]['logged_in'] = True
                await message.answer("Вы успешно вошли в аккаунт!",
                                     reply_markup=kb.keyboard_menu)
                await state.finish()
            else:
                await message.answer('Вы ввели неверный пароль. '
                                     'Попробуйте еще раз\n\n'
                                     'Введите логин.')
                await LoginStateGroup.login.set()
        else:
            await message.answer('Вы ввели неверный логин. '
                                 'Попробуйте еще раз\n\n'
                                 'Введите логин.')
            await LoginStateGroup.login.set()
    else:
        await message.answer('Вы не зарегистрированы.',
                             reply_markup=InlineKeyboardMarkup()
                             .add(InlineKeyboardButton(
                                 'Зарегистрироваться',
                                 callback_data='register'
                             )).add(kb.button_back))
        await state.finish()


@dp.message_handler()
async def default_msg(message: Message):
    await message.delete()
    # [note] Debug-информацию либо надо было убрать перед коммитом, либо делать через логирование
    print(data.get(message.from_user.id))
    await bot.send_message(message.from_user.id,
                           'У меня нет на это ответа :(\nВыберите пункт из меню.',
                           reply_markup=kb.keyboard_menu)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
