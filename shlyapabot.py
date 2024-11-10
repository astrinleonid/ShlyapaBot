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


telegram_token = tokens['telegram']

model = tokens['gpt_model']
available_models = {}
w_dict = {}
dict_file = 'shlyapaSave.json'

"""# Bot"""


BOT_INTERVAL = 3
BOT_TIMEOUT = 5

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
error_message = f"Bot started at {dt_string}"
markup_dict_option = {"Сохранить": "option0",
               "Не сохранять": "option1",
               "Еще вариант": "option2",
               "Сохранить и еще вариант": "option3"}

markup_dict_saved = {"Редактировать": "option5",
               "Удалить": "option6",
               "Уровень сложности": "option7"}

markup_dict_reminder = {"Coxpaнить слово": "option0",
                        "Не сохранять" : "option1",
                        "Уточнить значение" : "option8"}

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

            To register: /user
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

    @bot.message_handler(commands=['model'])
    def get_model(message):
        global available_models
        print("List models")
        chat_id = message.chat.id
        if chat_id not in w_dict:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь")

        bot.send_message(chat_id, f'Current model: {w_dict[chat_id].get_model()}', parse_mode='html')
        models = w_dict[chat_id].list_models()
        all_models = '\n'
        for i, model_name in enumerate(models):
            if model_name[:3] == 'gpt':
                all_models += f"{i + 1} {model_name}\n"
                available_models[i + 1] = model_name
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
        def list_to_html_table(data):
            # Start the table
            html = "<table border='1'>\n"

            # Loop through rows
            for row in data:
                html += "  <tr>\n"
                # Loop through columns
                for item in row:
                    html += f"    <td>{item}</td>\n"
                html += "  </tr>\n"

            # End the table
            html += "</table>"
            return html

        chat_id = message.chat.id
        log_message = f"Сохраняю словари в файл {dict_file}"
        print(log_message)
        save_dict = {chat_id : {'name' : user.username, 'words' : user.pack()} for chat_id, user in w_dict.items() }
        with open(dict_file, 'w') as file:
          json.dump(save_dict,file)

        list_of_words = [[word.word for word in user.words] for chat_id, user in w_dict.items()]
        html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>Table</title>\n</head>\n<body>\n{list_to_html_table(list_of_words)}\n</body>\n</html>"
        print(html)
        with open("shlyapaSave.html", 'w') as file:
            file.write(html)

        bot.send_message(message.chat.id, log_message)

    @bot.message_handler(commands=['load'])
    def load_file(message):
        chat_id = message.chat.id
        if chat_id not in w_dict:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь")
        with open(dict_file, 'r') as file:
          w_dict[chat_id].from_json(file)
        log_message = f"Загружено {len(w_dict[chat_id].words)} слов. \nПоказать список: /list"
        bot.send_message(message.chat.id, log_message)

    @bot.message_handler(commands=['user'])
    def register_user(message):
        teleg_ID = message.chat.username
        bot.send_message(message.chat.id, f"Введите свое имя и фамилию пожалуйста, или отправьте 1 чтобы использовать {teleg_ID}")
        name = bot.reply_to(message, f'Имя:', parse_mode='html')
        bot.register_next_step_handler(name, register_user)

    @bot.message_handler(commands=['list'])
    def output_word_list(message):
        if message.chat_id not in w_dict:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь")
        send_word_list(message.chat.id)

    @bot.message_handler(commands=['remind'])
    def register_user(message):
        if message.chat.id not in w_dict:
            teleg_ID = message.chat.username
            print(f"User {teleg_ID} is not registered yet")
            bot.send_message(message.chat.id,
                             f"Давайте сначала вас зарегистрируем. Введите свое имя и фамилию пожалуйста, или отправьте 1 чтобы использовать {teleg_ID}")
            name = bot.reply_to(message, f'Имя:', parse_mode='html')
            bot.register_next_step_handler(name, register_user)
            return
        teleg_ID = message.chat.username
        bot.send_message(message.chat.id, 'Давайте попробуем вспомнить слово. Пример: На что похоже? вазетка или варьетка Из какой области? что-то связанное с фотографией. Ответ бота: Возможно, вы имеете в виду слово "виньетка". В фотографии виньетка — это эффект, при котором края изображения затемнены или размытие по сравнению с центром, что помогает сосредоточить внимание на центральной части фотографии.')
        reminder1 = bot.reply_to(message, f'На что похоже слово, которое вы хотите вспомнить?:', parse_mode='html')
        bot.register_next_step_handler(reminder1, remind_word1)

    @bot.message_handler(content_types=['text'])
    def get_user_text(message):
        print("Incoming text")
        print(message.text)
        chat_id = message.chat.id

        if chat_id not in w_dict:
            teleg_ID = message.chat.username
            bot.send_message(message.chat.id,
                             f"Давайте сначала вас зарегистрируем. Введите свое имя и фамилию пожалуйста, или отправьте 1 чтобы использовать {teleg_ID}")
            name = bot.reply_to(message, f'Имя:', parse_mode='html')
            bot.register_next_step_handler(name, register_user)

        elif w_dict[chat_id].get_mode() == "shlyapa":
          result = w_dict[chat_id].getWord(first = True, word = message.text)

          if result:
            temp_words[message.chat.id] = AliasWord(**result)
            send_option_menu(message.chat.id, formatted_message(result), markup_dict_option)


    def send_option_menu(chat_id, prompt, markup_dict):

      markup = types.InlineKeyboardMarkup(row_width=1)

      items = []
      for command, callback in markup_dict.items():
        items.append(types.InlineKeyboardButton(command, callback_data=callback))

      markup.add(*items)

      bot.send_message(chat_id, prompt, reply_markup=markup)

    def send_word_list(chat_id, level = 'any', number = 7):

      markup = types.InlineKeyboardMarkup(row_width=1)
      bot.send_message(chat_id, f"{w_dict[chat_id].get_name()} ваши слова:")
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
        print(f"Processing callback: {call.data}")
        if call.data.startswith('option'):
          if call.data[-1] == '0' :
              print(temp_words[chat_id])
              w_dict[chat_id].add_word(temp_words[chat_id])
              bot.send_message(chat_id, "Слово добавлено в словарь")
              send_word_list(chat_id)
              print(f"Chat ID: {chat_id}")
          if call.data[-1] == '3':
              print(temp_words[chat_id])
              w_dict[chat_id].add_word(temp_words[chat_id])
              bot.send_message(chat_id, "Слово добавлено в словарь")
          if call.data[-1] == '1':
              send_word_list(chat_id)
          if call.data[-1] == '2' or call.data[-1] == '3':
              result = w_dict[chat_id].getWord( first = False)

              if result:
                temp_words[chat_id] = AliasWord(**result)
                send_option_menu(chat_id, formatted_message(result), markup_dict_option)
              else:
                bot.send_message(chat_id, "Больше вариантов нет")
          if call.data[-1] == '5':
              print("processing option 5")
              bot.send_message(chat_id, "Это пока не реализовано")
          if call.data[-1] == '6':
              w_dict[chat_id].delete_word()
              bot.send_message(chat_id, "Слово удалено")
          if call.data[-1] == '7':
              bot.send_message(chat_id, "Это пока не реализовано")
          if call.data[-1] == '8':
              bot.send_message(chat_id, "ОК, пожалуйста, расскажите подробнее про слово, которое вы имеете в виду")
              bot.register_next_step_handler()

        elif call.data.startswith('word'):
          if chat_id not in w_dict:
              bot.send_message(chat_id, "Словарь пуст или слово не найдено\n Загрузить словарь из файла: /load")
              return
          word = w_dict[chat_id].find_word(call.data[5:])
          send_option_menu(chat_id, formatted_message({'word': word.word, 'definition': word.definition}), markup_dict_saved)

        elif call.data.startswith('more'):
          send_word_list(chat_id)

    def register_user(message):
        name = message.text.strip()
        if name == '1':
            name = message.chat.username

        for user in w_dict:
            if name == user.get_name():
                bot.send_message(message.chat.id, "Такое имя в системе уже есть, если это вы, то зайдите, пожалуйста, с того же эккаунта, что и в прошлый раз, или зарегистрируйтесь заново под другим именем")
        w_dict[message.chat.id] = AliasDictionary(name)
        bot.send_message(message.chat.id, f"Прекрасно, {name}, теперь давайте писать слова. Просто напишите слово, или пошлите /remind чтобы бот помог вам вспомнить слово")

    def remind_word1(message):
        w_dict[message.chat.id].set_reminder(similars = message.text)
        print(f"Performing reminder step 2")
        bot.reply_to(message, "Из какой области это слово, или примерное значение", parse_mode = 'html')
        bot.register_next_step_handler(message, remind_word2)

    def remind_word2(message):
        w_dict[message.chat.id].set_reminder(meaning = message.text)
        reply = w_dict[message.chat.id].get_reminder()
        if reply:
            temp_words[message.chat.id] = AliasWord(**reply)
            send_option_menu(message.chat.id, f"{reply['word']} {reply['definition']}", markup_dict_reminder)
        else:
            bot.send_message(message.chat.id, f"К сожалению, не понимаю, что за слово вы имеете в виду")

    def remind_word3(message):
        prompt = f"""Ученик имел в виду другое слово, 
        вот его уточнение: {message.text}. 
        Предложи вариант исходя из подсказок, которые ученик дал раньше, 
        и уточнения.
        Дай ответ в таком же формате. 
        Если подхлдящих вариантов не нашлось, 
        ответь:  вариантов нет"""
        reply = w_dict[message.chat.id].get_reminder(prompt)
        if reply:
            temp_words[message.chat.id] = AliasWord(**reply)
            send_option_menu(message.chat.id, f"{reply['word']} {reply['definition']}", markup_dict_reminder)
        else:
            bot.send_message(message.chat.id, f"К сожалению, не понимаю, что за слово вы имеете в виду")

    def change_model(message):

        try:
            num = int(message.text)
            if num in available_models:
                model = available_models[num]
                print(f"Setting model to {model}")
                w_dict[message.chat.id].set_model(model)
        except:
            pass
        bot.send_message(message.chat.id, f'Current model: {model}', parse_mode='html')

    def get_user_mode(id):
        global user_modes
        if id not in user_modes:
            user_modes[id] = default_mode
        return user_modes[id]

if __name__ == '__main__':

    bot_polling(telegram_token)
