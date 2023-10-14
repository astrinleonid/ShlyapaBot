import random
import json
from chatGPTbackend import *
from tokens import tokens

## Shlyapa Dictionary Classes


class AliasWord:

  def __init__(self, word, definition, available_levels = None, level = None) :

    self.word = word
    self.definition = definition
    self.available_levels = available_levels
    self.level = level


  def set_level(self, level):

    if level in self.available_levels:
      self.level = level
      return True
    else:
      return False

class AliasDictionary:

  def __init__(self):
    self.words = []
    self.available_levels = ['elementary', 'easy', 'medium', 'hard', 'evil', 'any']
    self.set_of_words_to_display = {}
    self.chatGPT = ChatApp(openai_api_key)
    self.GPTmodel = tokens['gpt_model']

  def add_word(self, word, definition = None):
    if type(word) == str:
      word = AliasWord(word, definition)
    else:
      print("Got object")
    word.available_levels = self.available_levels
    if type(word.level) == type(None):
      word.level = 'any'
    self.words.append(word)
    print("Word added")

  def getWord(self, first=False, word=None):

    if first:
      tried_words = []
      self.chatGPT.new_chat()

    template = prompt_template(first, word)
    print(f"Template: {template}\n\n")
    response = self.chatGPT.chat(template, self.GPTmodel)
    print(f"Got response: {response}\n")
    result = parser(response)

    if result:
      return result
    else:
      print("No options")
      return False

  def list(self, level):
    if level == 'any':
      return [word.word for word in self.words ]
    else:
      return [word.word for word in self.words if word.level == level]

  def words_left(self, level = 'any', renew = False):

    if len(self.set_of_words_to_display) == 0 and renew:
      self.set_of_words_to_display = set(self.list(level))
    return len(self.set_of_words_to_display)

  def word_to_display(self):
    word = random.choice(list(self.set_of_words_to_display))
    self.set_of_words_to_display -= {word}
    # if len(self.set_of_words_to_display) == 0:
    #   self.set_of_words_to_display = None
    return word

  def find_word(self, target):
    for word in self.words:
      if word.word == target:
        return word.definition
    return False

  def to_json(self, file):
    temp_dict = []
    for word in self.words:
      temp_dict.append({'word': word.word,
                        'definition': word.definition,
                        'level': word.level})
    return json.dump(temp_dict, file)

  def from_json(self,file):
    records = json.load(file)
    for record in records:
      if not self.find_word(record['word']):
        self.words.append(AliasWord(**record))


  # def word_displayed(left):

"""## Shlyapa backend"""

def parser(text):
  # text = text.strip()
  if "вариантов нет" in text.lower() or "no more options" in text.lower() or "no options" in text.lower():
    return False

  text = text[text.find('### ')+4:]
  try:
    assert len(text) > 1

  except:
    print(f"Beginning error, response: {text}")
    return {'word' : 'ERROR', 'definition' : "ERROR"}

  content = text.split("####")
  try:
    assert len(content) == 2
  except:
    print("Error splitting, text:", text)
    return {'word' : 'ERROR', 'definition' : "ERROR"}

  word = content[0].strip()
  definition = content[1].strip()
  return {'word' : word.strip().lower(), 'definition' : definition.strip()}

def prompt_template_ru(first, word = ''):
  # excluded = f"Известно, что не имеется в виду ни одно из слов из списка: {', '.join(tried_words)}" if len(tried_words) > 0 else ''
  if first:
    return f"""
                  Я дам слово на русском языке, существительное в именительном падеже.
                  Вероятнее всего, слово написано с ошибками или опечаткам.
                  Твоя задача:
                  1) Предположить, какое слово имеется в виду, и дать его правильное написание. Предлагай только слова, которые есть в русском языке.
                  2) Дать краткое определение для наиболее употребимого заначения этого слова.
                  Дай ответ в формате markdown точно как указано: \n### <Корректное написание слова> \n#### <определение>.
                  Слово: {word}"""
  else:
    return """Спасибо, но имеется в виду другое слово.
                Предложи другой вариант. Не повторяй варианты, уже упоминавшиеся в этой дискуссии.
                Дай ответ в таком же формате. Если ты не можешь предложить другой вариант, ответь: вариантов нет."""

def prompt_template(first, word = ''):
  # excluded = f"Известно, что не имеется в виду ни одно из слов из списка: {', '.join(tried_words)}" if len(tried_words) > 0 else ''
  if first:
    return f"""   I'll give you a word in russian language.
                  The word may or may not be spelled correctly.
                  Your task is:
                  1) Suggest an option for the correct spelling of the word.
                  The option you suggest should be a noun in the nominative case, not a private name or geographical name,
                  existing in the Russian language
                  2) Give a definition in Russian of the most common meaning of the word you suggested
                  Your answer should be exactly in the following format:
                  \n### <correct spelling of the word> \n#### <definition of the word's meaning in Russian>
                  Word: {word}
            """
  else:
    return  """  Thanks, but I meant different word.
                Suggest another option. Do not repeat the words, already mentionet in this conversation.
                Give an answer in the same format.
                If you don't have any reasonable options to suggest, respond: no more options.
            """

def formatted_message(result):

  return f"""Слово : {result['word']}
Значение : {result['definition']}
Сохранить 1
Не сохранять 2
Другой вариант 3
Сохранить и дать еще вариант 4"""


