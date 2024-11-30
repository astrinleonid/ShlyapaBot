"## ChatGPT"
from openai import OpenAI, api_key
from tokens import tokens


"### Class"

class ChatApp:
    def __init__(self, **kwargs):
        # Setting the API key to use the OpenAI API
        self.client = OpenAI(api_key=tokens['openai'])
        self.model = kwargs['model'] if 'model' in kwargs else tokens['gpt_model'][0]
        self.messages = []

    def chat(self, message, **kwargs):
        self.messages.append({"role": "user", "content": message})
        model = kwargs['model'] if 'model' in kwargs else self.model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages
            )
        ai_resp = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_resp})
        return ai_resp

    def new_chat(self, **kwargs):
        self.messages = []
        if 'system' in kwargs:
            self.messages.append({"role": "system", "content" : kwargs['system']})
        print(f"Chat reset, messages {self.messages}")
    def list_models(self):
        """Lists all available GPT models."""
        return tokens['gpt_model']

    def set_model(self, model):
        print(f"Setting model to {model}")
        assert model in tokens['gpt_model'], f"Incorrect model provided {model}"
        print("Model found")
        self.model = model
        print(f"Model set to {self.model}")

def test_chat_class():
    chat = ChatApp(model="gpt-4")
    print(chat.chat("What do you think about Trump being elected a president?"))
    print(chat.chat("What other candidates can you name?"))

    # List available models
    chat.list_models()

if __name__ == "__main__":
    test_chat_class()