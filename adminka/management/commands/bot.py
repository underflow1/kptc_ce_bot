import os
import uuid

from django.core.management.base import BaseCommand
from django.conf import settings
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

from adminka.models import Photo
from .helpers import SQLiteExtractor, logger


db_path = 'app.db'
sqlite_extractor = SQLiteExtractor(db_path)

load_dotenv()

CHOOSE_LOCATION_STAGE, ADD_PHOTO_STAGE = range(2)
LOCATIONS = ['Дубнинская', 'Никитский', 'СКО', 'Тиснум']

keyboard_locations_items = []
for location in LOCATIONS:
    keyboard_locations_items.append(
        InlineKeyboardButton("▫️" + location, callback_data=location)
    )
keyboard_cancel_item = InlineKeyboardButton("❌ Отменить", callback_data="end")
keyboard_locations_items.append(keyboard_cancel_item)


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
    user = update.message.from_user
    if not sqlite_extractor.check_user(user.id):
        logger.info(user)
        logger.info(f"Пользователь {user.id} не авторизован")
        bot.send_message(
            chat_id=update.message.chat.id,
            text="Пользователь не авторизован",
        )
        return ConversationHandler.END

    context.user_data['username'] = user.first_name
    logger.info(f"Пользователь {context.user_data['username']} начал разговор")

    reply_markup = InlineKeyboardMarkup(
        build_menu(keyboard_locations_items, n_cols=1)
    )

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

    keyboard = [[keyboard_cancel_item]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    cancel_choose_message = context.user_data['cancel_choose_message']
    bot.delete_message(
        chat_id=cancel_choose_message['chat_id'],
        message_id=cancel_choose_message['message_id']
    )

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
    logger.info(
        f"Пользователь {context.user_data['username']} \
        локация {context.user_data['location']}"
    )

    query = update.callback_query
    query.answer()

    keyboard = [[keyboard_cancel_item]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text="Добавляйте фото", reply_markup=reply_markup
    )

    return ADD_PHOTO_STAGE


def no_location(update, context):
    if context.user_data['added_count'] == 0:
        bot.delete_message(
            chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
        update.message.reply_text(
            text="❌ НЕ ВЫБРАН ОБЪЕКТ ❌",
        )
    return CHOOSE_LOCATION_STAGE


def photo(update, context):

    """Stores the photo and asks for a location."""
    if context.user_data['location_message']:
        message = context.user_data['location_message']
        bot.edit_message_text(
            chat_id=message['chat_id'],
            message_id=message['message_id'],
            text=message['text']
        )
        context.user_data['location_message'] = False

    if context.user_data['cancel_photo_message']:
        message = context.user_data['cancel_photo_message']
        bot.delete_message(
            chat_id=message['chat_id'],
            message_id=message['message_id']
        )

    context.user_data['added_count'] = context.user_data['added_count'] + 1

    logger.info(
        f"Пользователь {context.user_data['username']} локация {context.user_data['location']} добавлено фото {context.user_data['added_count']}"
    )

    filename = str(uuid.uuid4()) + '.jpg'
    photo_file = update.message.photo[-1].get_file()

    image_url = photo_file['file_path']
    image_filename = os.path.basename(image_url)
    image_tmpdir = str(uuid.uuid4())
    image_dst = os.path.join(settings.PHOTOS_URL, image_tmpdir, image_filename)
    logger.info(f'image_url is {image_url}')
    logger.info(f'image_filename is {image_filename}')
    logger.info(f'image_tmpdir is {image_tmpdir}')
    logger.info(f'image_dst is {image_dst}')

    from django.core.files import File  # you need this somewhere
    from django.core.files.temp import NamedTemporaryFile
    import requests

    r = requests.get(image_url)
    img_temp = NamedTemporaryFile(delete=True, dir='temp')
    img_temp.name = image_filename
    img_temp.write(r.content)
    img_temp.flush()

    # urllib.request.urlretrieve(photo_file['file_path']) # image_url is a URL to an image
    # urllib.request.urlretrieve(image_url, image_dst)

    # image = photo_file.download(f"photos/{filename}")
    photo_model = Photo()

    logger.info(f"File is {File(img_temp)}")
    logger.info(f"File type is {type(File(img_temp))}")

    photo_model.location = context.user_data['location']
    photo_model.user = context.user_data['username']
    photo_model.photo = File(img_temp)

    photo_model.save()

    logger.info(f"photo_model is {photo_model}")
    # img_temp.close()

    # photo_dict = {
    #     'filename': filename,
    #     'location': context.user_data['location'],
    #     'user': context.user_data['username']
    # }
    # sqlite_extractor.add_record(photo_dict, PhotoModel)

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
    cancel_photo_message = get_message_id(message)
    context.user_data['cancel_photo_message'] = cancel_photo_message

    return ADD_PHOTO_STAGE


def end(update, context):
    """Возвращает `ConversationHandler.END`, который говорит
    `ConversationHandler` что разговор окончен"""

    logger.info(
        f"Пользователь {context.user_data['username']} локация {context.user_data['location']}"
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


TOKEN = os.getenv("TOKEN")
bot = Bot(TOKEN)


class Command(BaseCommand):
  	# Используется как описание команды обычно
    help = 'Implemented to Django application telegram bot setup command'

    def handle(self, *args, **kwargs):
        # bot.enable_save_next_step_handlers(delay=2) # Сохранение обработчиков
        # bot.load_next_step_handlers()								# Загрузка обработчиков
        # bot.infinity_polling()											# Бесконечный цикл бота

# if __name__ == "__main__":


    # logger.info(1)




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
                    CallbackQueryHandler(location_choosed, pattern='^\w+$'),
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
