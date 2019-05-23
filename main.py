from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler, CallbackQueryHandler, Filters
from io import BytesIO

import logging
import numpy as np
import os

import sys
sys.path.append("PNG-reindexing")
from functions import *

# get token from token.conf
TOKEN = open("config/token.conf", "r").read().strip()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
  update.message.reply_text('Hi! Send me an image as file and I will make an indexed PNG file with a ordered palette!')

def indexing(bot, update):

    if not update.message.photo and update.message.document:
        if "image" in update.message.document.mime_type:
            file = bot.getFile(update.message.document.file_id)
            file.download(update.message.document.file_name)
            img_name=update.message.document.file_name
            update.message.reply_text('Processing...'+img_name)
        else:
            update.message.reply_text('The file is not an image!')
    else:
        if update.message.photo:
            id_img = update.message.photo[-1].file_id
        else:
            update.message.reply_text('Send me an image as file and I will make an indexed PNG file with a ordered palette')
            return

        pic = bot.getFile(id_img)
        new_file = bot.get_file(pic.file_id)
        new_file.download('picture.jpg')
        img_name = "picture.jpg"
        update.message.reply_text('Processing...')

    if "png" not in img_name:
        pixs, _palette = generate_palette_indexed_pixels(img_name)
        write_image("img_1.png", pixs, _palette)
        source = png.Reader("img_1.png")
        width, height, pixels, metadata = source.read()
    else:
        source = png.Reader(img_name)
        width, height, pixels, metadata = source.read()

        # if "palette" not in metadata:
        pixs, _palette = generate_palette_indexed_pixels(img_name)
        write_image("img_1.png", pixs, _palette)
        source = png.Reader("img_1.png")
        width, height, pixels, metadata = source.read()

    # converting pixels hex bytearray into integer
    pixels_idx = []
    for s in pixels:
        pixels_idx.append([x for x in s])

    M = matrix_co_occurences(pixels_idx, metadata["palette"])
    T = space_color_distance(metadata["palette"])
    W = calculate_weights(M, T, pixels_idx, len(metadata["palette"]))
    best_path_vec = apply_ant_colony(metadata["palette"], W)

    new_palette, new_pixels_idx = convert_palette(best_path_vec, metadata["palette"], pixels_idx)
    write_image("img2.png", new_pixels_idx, new_palette)

    bot.send_document(chat_id=update.message.chat_id, document=open('img_1.png', 'rb'), caption="Old image converted to PNG with palette")
    bot.send_document(chat_id=update.message.chat_id, document=open('img2.png', 'rb'), caption="Image reindexed")

def main():
  updater = Updater(TOKEN)

  dp = updater.dispatcher

  dp.add_handler(MessageHandler(Filters.photo, indexing))
  dp.add_handler(MessageHandler(Filters.document, indexing))
  dp.add_handler(CommandHandler('start', start))
  dp.add_handler(CommandHandler('help', start))

  updater.start_polling()
  updater.idle()


if __name__ == '__main__':
    main()
