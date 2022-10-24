import os
import requests
import logging
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
)

from bot.models import Photo, User, Location


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

CHOOSE_LOCATION_STAGE, ADD_PHOTO_STAGE = range(2)
TOKEN = os.getenv("TOKEN")
bot = Bot(TOKEN)

keyboard_cancel_item = InlineKeyboardButton("❌ Отменить", callback_data="end")

def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def get_message_id(message):
    return {'chat_id': message.chat.id, 'message_id': message.message_id}


def start(update, context):
    '''Вход в бота, показ локаций'''
    # аутентификация и создание отсутствующего пользователя
    user = update.message.from_user
    user_model = User.get_user_by_user_id(user.id)
    if not user_model:
        user_model = User(
            user_id = user.id,
            username = user.username,
            first_name = user.first_name,
            last_name = user.last_name,
            language_code = user.language_code
        )
        user_model.save()
        logger.info(f'new user {user_model} created')

    # авторизация
    if not user_model.get_user_allowed_user_id(user.id):
        logger.info(f"Пользователь {user_model} не авторизован")
        bot.send_message(
            chat_id=update.message.chat.id,
            text="Пользователь не авторизован",
        )
        return ConversationHandler.END
    logger.info(f"Пользователь {user_model} начал разговор")

    keyboard_locations_items = []
    for location in Location.objects.all():
        keyboard_locations_items.append(
            InlineKeyboardButton("▫️" + str(location.name), callback_data=str(location.id))
        )
    keyboard_locations_items.append(keyboard_cancel_item)

    reply_markup = InlineKeyboardMarkup(
        build_menu(keyboard_locations_items, n_cols=1))
    message = update.message.reply_text(
        text="Выберите объект", reply_markup=reply_markup)
    start_message = get_message_id(message)

    # сохраним полученные данные
    context.user_data['user'] = user_model
    context.user_data['start_message'] = start_message
    context.user_data['added_count'] = 0
    context.user_data['photo_message'] = None
    context.user_data['location'] = None
    context.user_data['no_location_message'] = None

    return CHOOSE_LOCATION_STAGE


def location_choosed(update, context):
    '''Локация выбрана, загрузка фоток'''

    if context.user_data['no_location_message']:
        bot.delete_message(**context.user_data['no_location_message'])

    query = update.callback_query
    query.answer()
    location_model = Location.get_location_by_id(query.data)
    context.user_data['location'] = location_model
    logger.info(f"Пользователь {context.user_data['user']} выбрал локацию {location_model}")

    # подрихтуем сообщение о выборе локаций
    bot.delete_message(**context.user_data['start_message'])
    keyboard = [[keyboard_cancel_item]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = bot.send_message(
        chat_id=query.message.chat.id,
        text=f"▪️ выбран объект {location_model}\nДобавляйте фото",
        reply_markup=reply_markup
    )
    context.user_data['location_message'] = get_message_id(message)

    return ADD_PHOTO_STAGE


def repeat_photo(update, context):
    '''можно добавить фоток по нажатию кнопки Добавить еще,
    а можно и не нажимать и продолжать добавлять)))'''
    query = update.callback_query
    query.answer()
    keyboard = [[keyboard_cancel_item]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text="Добавляйте фото", reply_markup=reply_markup
    )

    return ADD_PHOTO_STAGE


def no_location(update, context):
    '''Удалять фотки если они отправлены до выбора локации'''
    bot.delete_message(
        chat_id=update.message.chat.id,
        message_id=update.message.message_id
    )

    if context.user_data['no_location_message']:
        bot.delete_message(**context.user_data['no_location_message'])

    message = update.message.reply_text(
        text="❌ НЕ ВЫБРАН ОБЪЕКТ ❌",)
    no_location_message = get_message_id(message)
    context.user_data['no_location_message'] = no_location_message

    return CHOOSE_LOCATION_STAGE


def photo(update, context):
    """Сохраняем фото и информацию о локации и пользователе в бд"""
    # прежде всего удалим предыдущее уведомление о том что фото добавлено
    if context.user_data['photo_message']:
        message = context.user_data['photo_message']
        bot.delete_message(
            chat_id=message['chat_id'],
            message_id=message['message_id']
        )

    # посчитаем количество добавленных фото
    context.user_data['added_count'] = context.user_data['added_count'] + 1

    logger.info(
        f"Пользователь {context.user_data['user']} добавил фото №{context.user_data['added_count']}"
    )

    image_url = update.message.photo[-1].get_file()['file_path']
    r = requests.get(image_url)
    img_temp = NamedTemporaryFile(delete=True, dir='temp')
    img_temp.name = os.path.basename(image_url)
    img_temp.write(r.content)
    img_temp.flush()

    photo_model = Photo()
    photo_model.location = context.user_data['location']
    photo_model.user = context.user_data['user']
    photo_model.photo = File(img_temp)
    photo_model.save()

    keyboard = [
        [
            InlineKeyboardButton(
                "✔️ Добавить еще!", callback_data="repeat_photo"
            ),
            InlineKeyboardButton("❌ Закончить", callback_data="end"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = update.message.reply_text(
        text=f"▪️ добавлено {context.user_data['added_count']} фото.",
        reply_markup=reply_markup
    )
    photo_message = get_message_id(message)
    context.user_data['photo_message'] = photo_message

    return ADD_PHOTO_STAGE


def end(update, context):
    """Возвращает `ConversationHandler.END`, который говорит
    `ConversationHandler` что разговор окончен"""

    logger.info(
        f"Пользователь {context.user_data['user']} закончил диалог"
    )

    query = update.callback_query
    query.answer()

    bot.editMessageReplyMarkup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=None
    )

    bot.send_message(
        chat_id=query.message.chat.id,
        text="Добавление завершено. \nЧтобы повторить нажмите \n/start",
    )

    return ConversationHandler.END


class Command(BaseCommand):
    # Используется как описание команды обычно
    def handle(self, *args, **kwargs):
        updater = Updater(TOKEN)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                MessageHandler(Filters.text, start)
            ],
            states={
                CHOOSE_LOCATION_STAGE: [
                    CallbackQueryHandler(end, pattern='^end$'),
                    # CallbackQueryHandler(location_choosed, pattern='^\w+$'),
                    CallbackQueryHandler(location_choosed, pattern='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
                    MessageHandler(Filters.photo, no_location),
                ],
                ADD_PHOTO_STAGE: [
                    MessageHandler(Filters.photo, photo),
                    CallbackQueryHandler(repeat_photo, pattern='^repeat_photo$'),
                    CallbackQueryHandler(end, pattern='^end$'),
                ]
            },
            fallbacks=[CommandHandler('start', start)],
        )

        dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()
