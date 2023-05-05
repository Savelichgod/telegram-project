from aiogram.dispatcher.filters.state import StatesGroup, State

# [note] Константы следует называть большими буквами
product_index = 0
with open('product_names.txt') as file:
    products_names = file.readlines()

product_descriptions = [
    f'Это очень крутой товар под названием {i[0].lower() + i[1:]}' for i in
    products_names]

info = (
    "<i>Amazon is guided by four principles: customer obsession rather than competitor focus, passion for"
    " invention, commitment to operational excellence, and long-term thinking. Amazon strives to be Earth’s"
    " most customer-centric company, Earth’s best employer, and Earth’s safest place to work. Customer "
    "reviews, 1-Click shopping, personalized recommendations, Prime, Fulfillment by Amazon, AWS, Kindle "
    "Direct Publishing, Kindle, Career Choice, Fire tablets, Fire TV, Amazon Echo, Alexa, Just Walk Out"
    " technology, Amazon Studios, and The Climate Pledge are some of the things pioneered by Amazon.</i>")


class RegistrationStateGroup(StatesGroup):
    fio_add = State()
    email_add = State()
    login_add = State()
    phone_add = State()
    password = State()
    password_confirm = State()


class LoginStateGroup(StatesGroup):
    login = State()
    password = State()
