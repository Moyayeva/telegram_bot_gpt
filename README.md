# Constellation Telegram Bot
## Introduction
This project is a Telegram bot designed to process in Telegram some capabilities of GPT and offer useful features. 


### Installation
To set up this project locally, you'll need Python, pip, a Telegram bot token and OpenAI token. Follow these steps:

Clone the repository:
git clone https://github.com/Moyayeva/telegram_bot_gpt
cd telegram_bot_gpt
Install the required dependencies:
pip install -r requirements.txt
Configuration
Create a .env file in the root directory and add your Telegram bot token and OpenAI token:
```
CHATGPT_TOKEN = "<your OpenAI API token>"
BOT_TOKEN = "<your Telegram bot token>"
```

### Usage
To run the Telegram bot, execute:

python bot.py
Interact with your bot in Telegram to start and use hints that you will receive.

### Features
* **Random facts** from GPT 
* **Ask-Respond chat** for answering short questions
* **Famous persons** for conversation with GPT AI in the role of famous persons
* **Quiz** to check your erudition
* **Tokenizer** - count tokens in your text  for GPT models (does not spend API)
* **Fantazy translator** - translate text to (Dothraki, Klingon, and High Valyrian)

License
This project is licensed under the MIT License
