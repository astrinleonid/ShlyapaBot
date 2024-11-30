from chatGPTbackend import ChatApp

class Field:

    def __init__(self, content_string):

            self.parce_format(content_string)

    def parce_format(self, content_string):
            self.name = 'text_field'
            self.fieldtype = 'text'
            self.content = content_string.strip()

    def update_content(self, new_content):
        self.content = new_content

    def __str__(self):
        return self.content


class ResponseField(Field):

    def parce_format(self, content_string):
        if not (content_string.startswith('{') and content_string.endswith('}')):
            raise ValueError(f"ResponseField incorrect input {content_string}")
        fields = content_string.strip('{}').split(',', 4)
        assert len(fields) == 4, f"ResponseField format: name, type, marker, content, provided {content_string}"
        self.name = fields[0].strip()
        self.type = fields[1].strip()
        self.marker = fields[2].strip()
        self.content = fields[3].strip()

    def extract_content(self, content_string):
        if not content_string.startswith(self.marker):
            raise RuntimeError(f"Incorrect input string {content_string}. Field {self.name} has marker {self.marker}")
        self.content = content_string.removeprefix(self.marker).strip()
        return self.content


class FillInField(Field):

    def parce_format(self, content_string):
        if not (content_string.startswith('{') and content_string.endswith('}')):
            raise ValueError(f"ResponseField incorrect input {content_string}")
        fields = content_string.strip('{}').split(',', 2)
        assert len(fields) == 2, f"ResponseField format: name, type provided {content_string}"
        self.name = fields[0].strip()
        self.type = fields[1].strip()

FIELDCLASSESDICT = {
    'prompt' : FillInField,
    'response' : ResponseField
}

class ChatPrompt:

    def __init__(self, **kwargs):
        self.system = kwargs['system'] if 'system' in kwargs else ''
        self.model = kwargs['model'] if 'model' in kwargs else ''
        self.load_prompt_template(kwargs['template']) if 'template' in kwargs else []
        self.load_response_template(kwargs['response']) if 'response' in kwargs else []
        self.chat = ChatApp(**kwargs)

    def load_template_string(self, template_string, template_type = 'prompt'):
        result = []
        FillInFieldClass = FIELDCLASSESDICT[template_type]
        while len(template_string) > 0:
            current_field = ''
            while len(template_string) > 0 and template_string[0] != '{':
                current_field += template_string[0]
                if template_string[0] == "}":
                    raise ValueError("Field format mismatch")
                template_string = template_string[1:]
            result.append(Field(current_field))
            if len(template_string) == 0:
                break
            current_field = template_string[0]
            template_string = template_string[1:]
            while template_string[0] != '}':
                current_field += template_string[0]
                if template_string[0] == "{" or len(template_string) == 1:
                    raise ValueError(f"Field format mismatch, {template_string}")
                template_string = template_string[1:]
            current_field += template_string[0]
            template_string = template_string[1:]
            result.append(FillInFieldClass(current_field))
        return result


    def load_prompt_template(self, template_string):
        self.fields = self.load_template_string(template_string)

    def load_response_template(self, template_string):
        self.response_fields = self.load_template_string(template_string, template_type='response')

    def parse_response(self, gpt_response):
        markers = [field.marker for field in self.response_fields]
        field_strings = []
        for i, marker in enumerate(markers):
            pos = gpt_response.find(marker)
            if i == 0:
                gpt_response = gpt_response[pos:]
                continue
            if pos > 0:
                field_strings.append(gpt_response[:pos])
                gpt_response = gpt_response[pos:]
            else:
                return False
        for field, string in zip(self.response_fields, field_strings):
            field.get_content(string)

    def compose_prompt(self, **fields):
        for field in self.fields:
            if field.name in fields:
                field.update_content(fields[field.name])
        self.prompt = ' '.join([str(field) for field in self.fields])

    def start(self):
         if self.system == '':
            self.chat.new_chat()
         else:
             self.chat.new_chat(system = self.system)
         self.parse_response(self.chat.chat(self.prompt))


if __name__ == '__main__':

    ps = """Твоя задача помочь ученику вспомнить слово, 
      которое он слышал, но не запомнил. Ученик говорит, что слово 
      звучит похоже на {reminder, string}. 
      На вопрос о том, что слово значит или из какой оно области, ученик отвечает так: 
      {description, string}. """

    rs =  "Дай ответ в формате \n {word, string, ###, <слово>} \n {meaning, string, ####, <значение слова>}"

    word_chat = ChatPrompt(template = ps, response = rs)
    word_chat.compose_prompt(reminder = 'jgvjwvjdv', description = 'physics')
    print(word_chat.prompt)
    word_chat.start()
    print([str(field) for field in word_chat.response_fields])




