# -*- coding: utf-8 -*-

#Installations and imports

import pickle
import os
import sys



import json
import requests
import telebot

import platform
import pathlib
import time
from datetime import datetime


# import whisper

from telebot import types
from tokens import tokens
from shlyapaBackend import *

"""# Classes and functions"""

"""##File and variable loads"""

# voice_transcription_model = whisper.load_model("small")
# with open('/content/drive/MyDrive/10root/whisper_model.pkl', 'rb') as file:
#     voice_transcription_model = pickle.load(file)

# with open('config.json') as token_file:
#     tokens = json.load(token_file)



telegram_token = tokens['telegram']

model = tokens['gpt_model']
available_models = {}
w_dict = {}
dict_file = 'temp.json'

"""# Bot"""


BOT_INTERVAL = 3
BOT_TIMEOUT = 5

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
error_message = f"Bot started at {dt_string}"


def bot_polling(token=telegram_token):
    global error_message
    bot = None
    print("Starting bot polling now")
    while True:
        try:
            print("New bot instance started")
            bot = telebot.TeleBot(token)  # Generate new bot instance
            botactions(bot)  # If bot is used as a global variable, remove bot as an input param
            bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex:  # Error in polling
            print("Bot polling failed, restarting in {}sec. Error:\n{}".format(BOT_TIMEOUT, ex))
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            error_message += f"\n\nCrash at {dt_string} Error message: {ex}"
            bot.stop_polling()
            time.sleep(BOT_TIMEOUT)
        else:  # Clean exit
            bot.stop_polling()
            print("Bot polling loop finished")
            break  # End loop



default_mode = 'words_for_shlyapa'
user_modes = {}
temp_words = {}

def botactions(bot):
    # @bot.message_handler(commands=['new_chat'])
    # def new_chat(message):
    #     chatGPT.new_chat()
    #     bot.send_message(message.chat.id, "Start a new conversation", parse_mode='html')

    @bot.message_handler(commands=['start'])
    def start(message):
        greeting = """
            <b>Welcome to the ShlyapaIsrael chatbot</b>

            To change chatGPT model: /model
            To add word: type or say
            To list saved words: /list
      """
        bot.send_message(message.chat.id, greeting, parse_mode='html')


    @bot.message_handler(commands=['mode'])
    def get_mode(message):
        global user_modes
        print("Change mode")

        mode = get_user_mode(message.chat.id)

        bot.send_message(message.chat.id, f'Current mode: {mode}', parse_mode='html')
        sent = bot.reply_to(message,
                            f'Modes available:<b>\n1  chatgpt\n2  speech_to_text\n3  parrot\n4  words_for_shlyapa</b>\nTo change mode send mode number, or send 0 to pass',
                            parse_mode='html')
        bot.register_next_step_handler(sent, change_mode)
        print("Mode changed")

    @bot.message_handler(commands=['model'])
    def get_model(message):
        global available_models
        print("List models")
        chat_id = message.chat.id
        if chat_id not in w_dict:
            w_dict[chat_id] = AliasDictionary()

        bot.send_message(chat_id, f'Current model: {w_dict[chat_id].GPTmodel}', parse_mode='html')
        models = openai.Model.list()
        all_models = '\n'
        for i, model_name in enumerate(models.data):
            if model_name.id[:3] == 'gpt':
                all_models += f"{i + 1} {model_name.id}\n"
                available_models[i + 1] = model_name.id
        bot.send_message(message.chat.id, f'Available models: {all_models}', parse_mode='html')
        sent = bot.reply_to(message, f'To change model, reply with model number, else reply with 0', parse_mode='html')
        bot.register_next_step_handler(sent, change_model)

    @bot.message_handler(commands=['crash'])
    def crash_bot(message):

        bot.send_message(message.chat.id, f'Crashing')
        int('kjwnkjn')

    @bot.message_handler(commands=['log'])
    def crash_log(message):

        bot.send_message(message.chat.id, error_message)

    @bot.message_handler(commands=['save'])
    def save_file(message):
        chat_id = message.chat.id
        log_message = f"Сохраняю {w_dict[chat_id].words_left(level = 'any', renew = False)} слов"
        print(log_message)
        with open(dict_file, 'w') as file:
          w_dict[chat_id].to_json(file)
        bot.send_message(message.chat.id, log_message)

    @bot.message_handler(commands=['load'])
    def load_file(message):
        chat_id = message.chat.id
        if chat_id not in w_dict:
            w_dict[chat_id] = AliasDictionary()
        with open(dict_file, 'r') as file:
          w_dict[chat_id].from_json(file)
        log_message = f"Загружено {len(w_dict[chat_id].words)} слов"
        bot.send_message(message.chat.id, log_message)

    @bot.message_handler(commands=['list'])
    def output_word_list(message):
        send_word_list(message.chat.id)

    @bot.message_handler(content_types=['text'])
    def get_user_text(message):
        print("Incoming text")
        print(message.text)
        chat_id = message.chat.id
        if chat_id not in w_dict:
            w_dict[chat_id] = AliasDictionary()
        mode = get_user_mode(chat_id)
        if mode == 'words_for_shlyapa':
          result = w_dict[chat_id].getWord(first = True, word = message.text)

          if result:
            temp_words[message.chat.id] = AliasWord(**result)
            send_option_menu(message.chat.id, formatted_message(result))




    # @bot.message_handler(content_types=['voice'])
    # def get_user_voice(message):
    #     print("Incoming voice")
    #     file_id = message.voice.file_id
    #     file_name = f'voice_{file_id}.ogg'
    #     # Download the voice message file
    #     download_voice_file(file_id, file_name)
    #     print('File saved')
    #     result = voice_transcription_model.transcribe('voice_prompt.wav')
    #     prompt = " ".join([segment['text'] for segment in result['segments']])
    #     print(prompt)
    #
    #     mode = get_user_mode(message.chat.id)
    #
    #     if mode == "speech_to_text":
    #         bot.send_message(message.chat.id, prompt, parse_mode='html')
    #     else:
    #         output_file = return_voice_response(prompt, mode)
    #         # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
    #         audio = open(output_file, 'rb')
    #         bot.send_audio(message.chat.id, audio)

    def change_mode(message):
        global user_modes
        input = message.text
        modes = ['chatgpt', 'speech_to_text', 'parrot', 'words_for_shlyapa']
        try:
            num = int(input) - 1
            if num in range(4):
                user_modes[message.chat.id] = modes[num]
        except:
            pass
        bot.send_message(message.chat.id, f'Current mode: {user_modes[message.chat.id]}', parse_mode='html')

    def send_option_menu(chat_id, prompt):

      markup = types.InlineKeyboardMarkup(row_width=1)

      item1 = types.InlineKeyboardButton("Сохранить", callback_data="option_0")
      item2 = types.InlineKeyboardButton("Не сохранять", callback_data="option_1")
      item3 = types.InlineKeyboardButton("Еще вариант", callback_data="option_2")
      item4 = types.InlineKeyboardButton("Сохранить и еще вариант", callback_data="option_3")

      markup.add(item1, item2, item3, item4)

      bot.send_message(chat_id, prompt, reply_markup=markup)

    def send_word_list(chat_id, level = 'any', number = 7):

      markup = types.InlineKeyboardMarkup(row_width=1)
      list_of_words = []
      if chat_id not in w_dict:
          bot.send_message(chat_id, "Словарь пуст\n Добавьте слова или загрузите из файла: /load")
          return
      for i in range(min(number, w_dict[chat_id].words_left(level, renew = True))):
          word = w_dict[chat_id].word_to_display()
          list_of_words.append(word)
          print(f"Add word to the list: {word}\n")

      print(w_dict[chat_id].words_left(level))

      items = []
      for word in list_of_words:
        items.append(types.InlineKeyboardButton(word, callback_data = "word_" + word))

      if w_dict[chat_id].words_left(level) > 0:
        items.append(types.InlineKeyboardButton('*** Еще ***', callback_data = 'more'))

      print(f"\n{len(items)}Items added to the list")
      markup.add(*items)

      bot.send_message(chat_id, '***', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
      if call.message:
        chat_id = call.message.chat.id
        # bot.send_message(chat_id, call.data)
        if call.data.startswith('option'):
          if call.data[-1] == '0' or call.data[-1] == '3':
              print(temp_words[chat_id])
              w_dict[chat_id].add_word(temp_words[chat_id])
              bot.send_message(chat_id, "Слово добавлено в словарь")
          elif call.data[-1] == '1':
              return True
          if call.data[-1] == '2' or call.data[-1] == '3':
              result = w_dict[chat_id].getWord( first = False)

              if result:
                temp_words[chat_id] = AliasWord(**result)
                send_option_menu(chat_id, formatted_message(result))
              else:
                bot.send_message(chat_id, "Больше вариантов нет")

        elif call.data.startswith('word'):
          if chat_id not in w_dict:
              bot.send_message(chat_id, "Словарь пуст\n Добавьте слова или загрузите из файла: /load")
              return
          word = w_dict[chat_id].find_word(call.data[5:])
          bot.send_message(chat_id, word)

        elif call.data.startswith('more'):
          send_word_list(chat_id)

    def change_model(message):

        try:
            num = int(message.text)
            if num in available_models:
                model = available_models[num]
                print(model)
                w_dict[message.chat.id].GPTmodel = model
        except:
            pass
        bot.send_message(message.chat.id, f'Current model: {model}', parse_mode='html')

    # def download_voice_file(file_id, file_name, output_file='voice_prompt.wav'):
    #     file_path = bot.get_file(file_id).file_path
    #     file_url = f'https://api.telegram.org/file/bot{telegram_token}/{file_path}'
    #     response = requests.get(file_url)
    #     # print(response)
    #     with open(file_name, 'wb') as f:
    #         f.write(response.content)
    #     # audio = AudioSegment.from_file(file_name, ffprobe=ffprobe_path)
    #     audio = AudioSegment.from_file(file_name)
    #     audio.export(output_file, format='wav')

    def get_user_mode(id):
        global user_modes
        if id not in user_modes:
            user_modes[id] = default_mode
        return user_modes[id]

if __name__ == '__main__':

    bot_polling(telegram_token)
