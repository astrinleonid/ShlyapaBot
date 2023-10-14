"## ChatGPT"
import openai
from tokens import tokens

openai_api_key = tokens['openai']

"### Class"

class ChatApp:
    def __init__(self, openai_api_key):
        # Setting the API key to use the OpenAI API
        openai.api_key = openai_api_key
        self.messages = []

    def chat(self, message, model="gpt-4"):
        self.messages.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model = model,
            messages=self.messages
        )
        self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
        return response["choices"][0]["message"]["content"]

    def new_chat(self):
        self.messages = []
        print(f"Chat reset, messages {self.messages}")



