from openai import OpenAI
from context_manager import Context
import httpx as httpx
import asyncio



class ChatGptService:
    client: OpenAI = None
    message_list: list = None

    def __init__(self, token):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = OpenAI(
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"),
            api_key=token)
        self.message_list = []
        ###
        # chat_context = Context('ruth', [])
        # self.message_list = self.message_list.append(self, chat_context.get())

    async def send_message_list(self) -> str:
        # completion = self.client.chat.completions.create(
        #     model="o4-mini-2025-04-16",  # gpt-3.5-turbo, gpt-4o,  gpt-4-turbo,    gpt-3.5-turbo,  GPT-4o mini
        #     messages=self.message_list,
        #     max_tokens=3000,
        #     temperature=0.9
        # )
        # message = completion.choices[0].message
        # self.message_list.append(message)
        # return message.content
        return "message content"

    def set_prompt(self, prompt_text: str) -> None:
        #self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})
        self.message_list.append({"role": "user", "content": message_text})
        print(self.send_message_list())
        return await self.send_message_list()

async def main():
    chat_context = Context('ruth', [])
    await chat_context.get()
    print(chat_context)




if __name__ == '__main__':
    asyncio.run(main())