import logging
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
)

from dotenv import load_dotenv
load_dotenv()

# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s', level=logging.INFO
)
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"

logger = logging.getLogger(__name__)


LOCATIONS = ['Дубнинская', 'Никитский', 'СКО', 'Тиснум']
keyboard_locations_items = []
for location in LOCATIONS:
    keyboard_locations_items.append(InlineKeyboardButton("▫️" + location, callback_data=location))
keyboard_locations_items.append(InlineKeyboardButton("❌ Отменить", callback_data="end"))

keyboard_cancel_item = [InlineKeyboardButton("❌ Отменить", callback_data="end")]


CHOOSE_LOCATION_STAGE = 'choose_location_stage'
ADD_PHOTO_STAGE = 'add_photo_stage'


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
    """Вызывается по команде `/start`."""

    user = update.message.from_user
    context.user_data['username'] = user.first_name
    logger.info(f"Пользователь {context.user_data['username']} начал разговор")

    keyboard = [keyboard_locations_items]
    reply_markup = InlineKeyboardMarkup(build_menu(keyboard_locations_items, n_cols=1))

    message = update.message.reply_text(
        text="Выберите объект", reply_markup=reply_markup
    )

    cancel_choose_message = get_message_id(message)
    context.user_data['cancel_choose_message'] = cancel_choose_message
    context.user_data['added_count'] = 0
    context.user_data['cancel_photo_message'] = False
    context.user_data['location'] = False

    return CHOOSE_LOCATION_STAGE


def location_choosed(update, context):
    query = update.callback_query
    query.answer()

    context.user_data['location'] = query.data
    logger.info(f"Пользователь {context.user_data['username']} локация {context.user_data['location']}")


    keyboard = [keyboard_cancel_item]
    reply_markup = InlineKeyboardMarkup(keyboard)

    cancel_choose_message = context.user_data['cancel_choose_message']
    bot.delete_message(chat_id=cancel_choose_message['chat_id'], message_id=cancel_choose_message['message_id'])

    location_message_text = f"▪️ выбран объект {query.data}"
    message = bot.send_message(
        chat_id=query.message.chat.id,
        text=location_message_text + "\nДобавляйте фото",
        reply_markup=reply_markup
    )

    location_message = get_message_id(message)
    location_message['text'] = location_message_text
    context.user_data['location_message'] = location_message

    return ADD_PHOTO_STAGE


def repeat_photo(update, context):
    logger.info(f"Пользователь {context.user_data['username']} локация {context.user_data['location']}")

    query = update.callback_query
    query.answer()

    keyboard = [keyboard_cancel_item]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text=f"Добавляйте фото", reply_markup=reply_markup
    )

    return ADD_PHOTO_STAGE


def photo(update, context):
    if context.user_data['location_message']:
        message = context.user_data['location_message']
        bot.edit_message_text(chat_id=message['chat_id'], message_id=message['message_id'], text=message['text'])
        context.user_data['location_message'] = False

    if context.user_data['cancel_photo_message']:
        message = context.user_data['cancel_photo_message']
        bot.delete_message(chat_id=message['chat_id'], message_id=message['message_id'])

    context.user_data['added_count'] = context.user_data['added_count'] + 1

    logger.info(f"Пользователь {context.user_data['username']} \
локация {context.user_data['location']} \
добавлено фото {context.user_data['added_count']}")


    """Stores the photo and asks for a location."""
    user = update.message.from_user
    # print(update.message.photo)
    photo_file = update.message.photo[-1].get_file()
    photo_file.download("user_photo.jpg")
    # logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")


    keyboard = [
        [
            InlineKeyboardButton("✔️ Добавить еще!", callback_data="repeat_photo"),
            InlineKeyboardButton("❌ Закончить", callback_data="end"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = update.message.reply_text(text=f"▪️ добавлено {context.user_data['added_count']} фото.", reply_markup=reply_markup)
    cancel_photo_message = get_message_id(message)
    context.user_data['cancel_photo_message'] = cancel_photo_message

    return ADD_PHOTO_STAGE


def end(update, context):
    logger.info(f"Пользователь {context.user_data['username']} локация {context.user_data['location']}")
    """Возвращает `ConversationHandler.END`, который говорит
    `ConversationHandler` что разговор окончен"""
    query = update.callback_query
    query.answer()

    bot.editMessageReplyMarkup(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=None
    )
    # query.edit_message_text(text="Добавление завершено")

    bot.send_message(
        chat_id=query.message.chat.id,
        text="Чтобы повторить нажмите \n/start",
    )

    return ConversationHandler.END


if __name__ == "__main__":

    bot = Bot(os.getenv("TOKEN"))
    updater = Updater(os.getenv("TOKEN"))
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(Filters.text, start)
        ],
        states={ # словарь состояний разговора, возвращаемых callback функциями
            CHOOSE_LOCATION_STAGE: [
                CallbackQueryHandler(end, pattern='^end$'),
                CallbackQueryHandler(location_choosed, pattern='^\w+$'),
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
