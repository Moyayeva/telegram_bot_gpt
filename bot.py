from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler
import logging
from gpt import ChatGptService
from util import (load_message, load_prompt, send_text, send_image, show_main_menu,send_html,
                  default_callback_handler, send_text_buttons, tokenize)
from credentials import CHATGPT_TOKEN, BOT_TOKEN
from telegram.error import Conflict, NetworkError
from telegram.ext import MessageHandler, filters

# Налаштування базового логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Створення екземпляру сервісу ChatGPT, використовуючи токен з середовища/облікових даних
chat_gpt = ChatGptService(CHATGPT_TOKEN)

# Створення додатку Telegram, використовуючи BOT_TOKEN з середовища/облікових даних
app = ApplicationBuilder().token(BOT_TOKEN).build()

"""
 Глобальні змінні (меню)
"""

quiz_score = 0
quiz_questions = 0
personalities = {
        'talk_cobain': 'Курт Кобейн 🎸',
        'talk_einstein': 'Альберт Ейнштейн 👅',
        'talk_nietzsche': 'Фрідріх Ніцше 📚',
        'talk_lovelace': 'Ада Лавлейс 📃',
        'talk_tolkien': 'Дж.Р.Р. Толкін 🧙‍♂️',
        'start': 'Закінчити 🏁'
    }
# Створюємо кнопки для вибору тем квізу
topics = {
    'quiz_AI': 'ШІ ✨',
    'quiz_code': 'Програмування 👩‍💻',
    'quiz_philosophy': 'Філософія 🪶',
    'quiz_psy': 'Психологія 𝚿',
    'quiz_neuro': 'Нейронауки 🧠',
    'quiz_neuronet': 'Нейромережні архітектури 🕸️',
    'quiz_cyber': 'Історія кібернетики 🦾',
    'quiz_ethics': 'Етика ⚖️️'
    }
# Створюємо кнопки для вибору способів токенізації
enc = {
    'token_cl100k_base': 'GPT-3.5,GPT-4',
    'token_o200k_base': 'GPT-4o, GPT-5, OpenAI-o3 ect.',
    'start': 'Закінчити 🏁'
}
# Створюємо кнопки для вибору мови
langs = {
    'translate_klingon': 'Клингон 🖖',
    'translate_dothraki': 'Дотракійська  🐎',
    'translate_valyrian': 'Висока валірійська 💍'
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення всіх попередніх станів розмови
    context.user_data.clear()

    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 😊',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'token': 'Обрахувати кількість токенів (OpenAI) 🧮',
        'translate': 'Перекласти текст 📚'
    })

# Обробник команди /random для отримання випадкового факту
async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'random')

    # Відправляємо повідомлення про очікування відповіді від ChatGPT
    message = await send_text(update, context, "🔍 Шукаю цікавий факт для вас...")

    try:
        # Завантажуємо заздалегідь підготовлений промпт для випадкового факту
        prompt = load_prompt('random')

        # Запитуємо ChatGPT
        fact = await chat_gpt.send_question(prompt, "Розкажи мені цікавий факт")
        logger.info(f"lof fact: {fact}")
        # Створюємо кнопки для взаємодії
        buttons = {
            'random': 'Хочу ще факт 🔄',
            'start': 'Закінчити 🏁'
        }

        # Видаляємо повідомлення про очікування
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)

        # Надсилаємо випадковий факт з кнопками
        await send_text_buttons(update, context, f"📚 *Випадковий факт:*\n\n{fact}", buttons)

    except Exception as e:
        logger.error(f"Помилка при отриманні випадкового факту: {e}")
        await send_text(update, context, "😔 На жаль, виникла помилка при отриманні факту. Спробуйте ще раз пізніше.")
        # Видаляємо повідомлення про очікування в разі помилки
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)

# Користувацький обробник колбеків для кнопок випадкових фактів
async def random_fact_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на колбек

    # Отримуємо дані з колбеку
    data = query.data

    if data == 'random':
        # Якщо натиснуто кнопку "Хочу ще факт"
        await random_fact(update, context)
    elif data == 'start':
        # Якщо натиснуто кнопку "Закінчити"
        await start(update, context)

# Обробник команди /gpt для взаємодії з ChatGPT
async def gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення попередніх станів розмови, але збереження основного стану для GPT
    # Видаляємо всі ключі, крім нових, які ми встановлюємо
    context.user_data.clear()

    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'gpt')

    # Завантажуємо заздалегідь підготовлений промпт для GPT
    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)  # Це повністю скидає історію повідомлень у сервісі ChatGPT
    chat_gpt.set_prompt(load_prompt('gpt'))

    # Надсилаємо повідомлення з інструкцією
    await send_text(update, context, "😊 Задайте питання, і я відповім на нього.\nПросто надішліть текстове повідомлення.")

    # Зберігаємо стан розмови в контексті користувача
    context.user_data['conversation_state'] = 'gpt'

# Обробник команди /talk для діалогу з відомими особистостями
async def talk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення попередніх станів розмови
    context.user_data.clear()

    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'talk')

    context.user_data['conversation_state'] = 'talk'
    # Надсилаємо повідомлення з вибором особистості
    await send_text_buttons(update, context, "👤 Виберіть особистість, з якою ви хочете поспілкуватися:", personalities)

# Окремий обробник для інтерпретації випадкових повідомлень користувача
async def interpret_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """
    Аналізує випадковий текст від користувача і намагається визначити намір.
    Повертає True, якщо намір визначено та оброблено, False - якщо не вдалося визначити намір.
    """
    # Аналізуємо текст повідомлення для визначення можливого наміру
    message_text_lower = message_text.lower()

    # Перевірка на схожість до команд/функцій
    if any(keyword in message_text_lower for keyword in ['факт', 'цікав', 'random', 'випадков']):
        await send_text(update, context, "🧠 Схоже, ви цікавитесь випадковими фактами! Зараз покажу вам один...")
        await random_fact(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['gpt', 'чат', 'питання', 'запита', 'дізнатися']):
        await send_text(update, context, "😊 Схоже, у вас є питання! Із радістю відповім на нього!..")
        await gpt_handler(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['розмов', 'говори', 'спілкува', 'особист', 'talk']):
        await send_text(update, context, "👤 Схоже, ви хочете поговорити з відомою особистістю! Зараз покажу вам доступні варіанти...")
        await talk_handler(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['квіз', 'грати', 'вікторин', 'quiz']):
        await send_text(update, context, "❓ Схоже, ви хочете взяти участь у квізі! Зараз покажу вам доступні теми...")
        await talk_handler(update, context)
        return True
    # Якщо не вдалося визначити намір, повертаємо False
    return False

# Обробник для відображення кумедної відповіді, коли намір не визначено
async def show_funny_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показує випадкову кумедну відповідь, коли не вдається визначити намір користувача."""
    import random

    # Випадкові кумедні відповіді, якщо наміри не визначені
    funny_responses = [
        "🤔 Хмм... Цікаво, але я не зрозумів, що саме ви хочете. Може спробуєте одну з команд з меню?",
        "🧐 Дуже цікаве повідомлення! Але мені потрібні чіткіші інструкції. Ось доступні команди:",
        "😅 Ой, здається, ви мене застали зненацька! Я вмію багато чого, але мені потрібна конкретна команда:",
        "🤖 *перезавантажується* Вибачте, мої алгоритми не розпізнали це як команду. Ось що я точно вмію:",
        "🦄 Це повідомлення таке ж загадкове, як єдиноріг у дикій природі! Спробуйте одну з цих команд:",
        "🕵️ Я намагаюся зрозуміти ваше повідомлення... Але краще скористайтесь однією з команд:",
        "🎲 О! Випадкове повідомлення! Я теж вмію бути випадковим, але краще використовуйте команди:",
        "📱 *натискає уявні кнопки* Гм, не спрацювало. Може спробуємо ці команди?",
        "🌈 Це повідомлення прекрасне, як веселка! Але для повноцінного спілкування спробуйте:",
        "🤓 Згідно з моїми розрахунками, це повідомлення не відповідає жодній з моїх команд. Ось вони:",
    ]

    # Додаткові підказки для покращення взаємодії
    hints = [
        "Спробуйте команду /gpt, щоб задати питання",
        "Використайте /random для отримання цікавого факту",
        "Команда /talk дозволить вам поспілкуватися з відомою особистістю",
        "Не знаєте, що обрати? Почніть з /start",
    ]

    # Формуємо повідомлення з кумедною відповіддю та підказкою
    response = f"{random.choice(funny_responses)}\n\n💡 *Підказка:* {random.choice(hints)}"
    await send_text(update, context, response)

    # Показуємо основне меню
    await start(update, context)


# Обробник повідомлень для взаємодії з GPT та відомими особистостями
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, buttons=None):
    # Отримуємо текст повідомлення від користувача
    message_text = update.message.text

    # Перевіряємо поточний стан розмови
    conversation_state = context.user_data.get('conversation_state')

    # Якщо стан розмови не визначено (випадкове повідомлення)
    if not conversation_state:
        # Спробуємо інтерпретувати намір користувача
        intent_recognized = await interpret_random_input(update, context, message_text)

        # Якщо намір не визначено, показуємо кумедну відповідь
        if not intent_recognized:
            await show_funny_response(update, context)

        return

    if conversation_state == 'gpt':
        # Обробка питання до ChatGPT
        # Відправляємо повідомлення про очікування відповіді
        waiting_message = await send_text(update, context, "🔍 Обробляю ваше питання...")

        try:
            # Надсилаємо запит до ChatGPT
            response = await chat_gpt.add_message(message_text)

            # Видаляємо повідомлення про очікування
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

            # Надсилаємо відповідь користувачу
            await send_text(update, context, f"😊 *Відповідь ChatGPT:*\n\n{response}")

        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "😔 На жаль, виникла помилка при отриманні відповіді. Спробуйте ще раз пізніше.")
            # Видаляємо повідомлення про очікування в разі помилки
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

    elif conversation_state == 'talk':
        # Обробка повідомлення для діалогу з обраною особистістю
        # Отримуємо обрану особистість
        waiting_message = await send_text(update, context, "Дайте трохи подумати, будь ласка...")
        personality = context.user_data.get('selected_personality')

        if not personality:
            await send_text(update, context, "😕 Будь ласка, спочатку виберіть особистість для розмови за допомогою команди /talk")
            return

        try:
            # Надсилаємо запит до ChatGPT з промптом обраної особистості
            response = await chat_gpt.add_message(message_text)

            # Створюємо кнопку "Закінчити"
            buttons = {'start': 'Закінчити 🏁'}

            # Надсилаємо відповідь користувачу з кнопкою
            await send_text_buttons(update, context, f"👤 {personalities[personality]}:\n\n{response}", buttons)
            # Видаляємо повідомлення про очікування
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "😔 На жаль, виникла помилка при отриманні відповіді. Спробуйте ще раз пізніше.")
            # Видаляємо повідомлення про очікування в разі помилки
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

    elif conversation_state == 'quiz':
        # Обробка відповіді на питання квізу
        # Отримуємо обрану тему
        topic = context.user_data.get('selected_topic')
        if not topic:
            await send_text(update, context,
                            "😕 Будь ласка, спочатку виберіть тему квізу за допомогою команди /quiz")
            return
        selected_topic = topics[topic]

        # Відправляємо повідомлення про очікування відповіді
        waiting_message = await send_text(update, context, "📝 Обробляю вашу відповідь...")
        print(waiting_message)
        try:
             # # Надсилаємо запит до ChatGPT з промптом quiz
             # response = await chat_gpt.add_message(message_text)

             # quiz_state = 'question'
             # if quiz_state == 'question':
             #    quiz_state = 'answer'
             # Видаляємо повідомлення про очікування

             await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
             # Надсилаємо відповідь до ChatGPT
             response = await chat_gpt.add_message(message_text)

             buttons = {
                 topic: 'Ще! 🤩',
                 'quiz': 'Змінити тему 🔄',
                 'start': 'Закінчити 🏁'
             }
             global quiz_score
             global quiz_questions
             quiz_questions += 1
             if response == "Правильно!":
                 quiz_score += 1

             await send_text_buttons(update, context, f"❓Аналіз вашої відповіді за темою *{selected_topic}*:\n\n{response} Ваш рахунок: {quiz_score} з {quiz_questions}",buttons)

        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context,
                            "😔 На жаль, виникла помилка при отриманні відповіді. Спробуйте ще раз пізніше.")
            # Видаляємо повідомлення про очікування в разі помилки
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
    elif conversation_state == 'token':
        # Обробка тексту для токенізації
        # Отримуємо обрану систему токенізації
        data = context.user_data.get('selected_enc')
        selected_enc = data.replace('token_', '')

        if not selected_enc:
            await send_text(update, context,
                            "😕 Будь ласка, спочатку виберіть спосіб кодування за допомогою команди /token")
            return

        # Відправляємо повідомлення про очікування відповіді
        waiting_message = await send_text(update, context, "📝 Обробляю ваш текст...")

        try:
             # Надсилаємо запит до ChatGPT з промптом quiz
             token_num = tokenize(message_text, selected_enc)
             buttons = {
                 'start': 'Закінчити 🏁',
                 'token': 'Змінити спосіб кодування 🔄'
             }
             await send_text_buttons(update, context,
                                     f"Ваш текст містить *{token_num}* токенів в кодуванні *{selected_enc}*",
                                     buttons)

             # Видаляємо повідомлення про очікування
             await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        except Exception as e:
             logger.error(f"Помилка при підрахунку токенів: {e}")
             await send_text(update, context,
                             "😔 На жаль, виникла помилка при підрахунку токенів. Спробуйте ще раз пізніше.")
             # Видаляємо повідомлення про очікування
             await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

    elif conversation_state == 'translate':
        # Обробка повідомлення для перекладача
        # Отримуємо обрану мову
        waiting_message = await send_text(update, context, "Дайте трохи подумати, будь ласка...")
        lang = context.user_data.get('selected_lang')

        if not lang:
            await send_text(update, context, "😕 Будь ласка, спочатку виберіть мову перекладу за допомогою команди /translate")
            return

        try:
            # Надсилаємо запит до ChatGPT з промптом обраної особистості
            response = await chat_gpt.add_message(message_text)

            # Створюємо кнопку "Закінчити"
            buttons = {
                'translate': 'Змінити мову 🔄',
                'start': 'Закінчити 🏁'
            }
            lang_lable = langs[lang].lower()
            # Надсилаємо відповідь користувачу з кнопкою
            await send_text_buttons(update, context, f"Переклад вашого тексту на таку мову: *{lang_lable}*\n\n{response}", buttons)
            # Видаляємо повідомлення про очікування
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "😔 На жаль, виникла помилка при отриманні відповіді. Спробуйте ще раз пізніше.")
            # Видаляємо повідомлення про очікування в разі помилки
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

# Обробник колбеків для діалогу з відомими особистостями
async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на колбек

    # Отримуємо дані з колбеку
    data = query.data

    # Якщо натиснуто кнопку "Закінчити"
    if data == 'start':
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('selected_personality', None)
        await start(update, context)
        return

    # Перевіряємо, чи це вибір особистості
    if data.startswith('talk_'):
        # Очищаємо попередні дані користувача перед вибором нової особистості
        context.user_data.clear()

        # Зберігаємо обрану особистість
        context.user_data['selected_personality'] = data
        context.user_data['conversation_state'] = 'talk'

        # Завантажуємо промпт для обраної особистості
        prompt = load_prompt(data)
        chat_gpt.set_prompt(prompt)  # Це повністю скидає історію повідомлень у сервісі ChatGPT

        # Надсилаємо повідомлення про початок розмови з вибраною особистістю
        # Надсилаємо зображення обраної особистості
        await send_image(update, context, data)

        # Надсилаємо повідомлення з інструкцією та кнопкою "Закінчити"
        buttons = {
            'start': 'Закінчити 🏁'
            }
        await send_text_buttons(update, context, f"👤 Ваш співрозмовник – *{personalities[data]}*. Надішліть повідомлення, щоб отримати відповідь.", buttons)

# Обробник команди /quiz для участі у квізі
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення попередніх станів розмови
    context.user_data.clear()

    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'quiz')
    context.user_data['conversation_state'] = 'quiz'
    # Надсилаємо повідомлення з вибором теми
    await send_text_buttons(update, context, "Виберіть тему квізу:", topics)

# Обробник колбеків для квізу
async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на колбек

    # Отримуємо дані з колбеку
    data = query.data

    # Якщо натиснуто кнопку "Закінчити"
    if data == 'start':
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('selected_topic', None)
        await start(update, context)
        global quiz_score
        global quiz_questions
        quiz_score = 0
        quiz_questions = 0
        return

    # Перевіряємо, чи це вибір теми
    if data.startswith('quiz_'):
        # Відправляємо повідомлення про очікування відповіді
        waiting_message = await send_text(update, context, "📝 Готую для вас цікаве питання...")

        # Зберігаємо обрану тему
        context.user_data['selected_topic'] = data
        context.user_data['conversation_state'] = 'quiz'

        # Завантажуємо промпт для квізу
        prompt = load_prompt('quiz')
        chat_gpt.set_prompt(prompt)  # Це повністю скидає історію повідомлень у сервісі ChatGPT
        try:
            # Надсилаємо промпт і тему до ChatGPT
            quiz_question = await chat_gpt.add_message(data)

            # Видаляємо повідомлення про очікування
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

            # Надсилаємо питання користувачу
            await send_text(update, context, f"❓ *КВІЗ*\n\nПитання квіз за темою *{topics[data]}*\n\n{quiz_question}")

        except Exception as e:
            logger.error(f"Помилка при отриманні питання від ChatGPT: {e}")
            await send_text(update, context, "😔 На жаль, виникла помилка при отриманні питання. Спробуйте ще раз пізніше.")
            # Видаляємо повідомлення про очікування в разі помилки
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)

# Обробник команди /token для участі розрахунку токенів
async def token_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення попередніх станів розмови
    context.user_data.clear()

    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'token')
    context.user_data['conversation_state'] = 'token'

    # Надсилаємо повідомлення з вибором способу токенізації
    await send_text_buttons(update, context, "Хочете знати, скільки API-токенів «з'їсть» той чи інший інпут?\nДавайте порахуємо! Оберіть спосіб кодування:", enc)

# Обробник колбеків токенайзера
async def token_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на колбек

    # Отримуємо дані з колбеку
    data = query.data
    # Якщо натиснуто кнопку "Закінчити"
    if data == 'start':
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('selected_enc', None)
        await start(update, context)
        return

    # Перевіряємо, чи це вибір способу кодування
    if data.startswith('token_'):
        # Очищаємо попередні дані користувача перед вибором нового способу кодування
        context.user_data.clear()

        # Зберігаємо обраний спосіб кодування
        context.user_data['selected_enc'] = data
        context.user_data['conversation_state'] = 'token'
        selected_enc = data.replace('token_', '')
        # Надсилаємо повідомлення з інструкцією.
        await send_html(update, context, f"Ви обрали спосіб кодування <b>{selected_enc}</b>. Будь ласка, надішліть текст, який необхідно обрахувати.")

# Обробник команди /translate для перекладача
async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищення попередніх станів розмови
    context.user_data.clear()

    # Надсилаємо заздалегідь підготовлене зображення
    await send_image(update, context, 'translate')
    context.user_data['conversation_state'] = 'translate'

    # Надсилаємо повідомлення з вибором теми
    await send_text_buttons(update, context,
                            "Хочете написати любовного листа високою валірійською чи допис на клінгоні?\nНаш перекладач вам допоможе!\n\nБудь ласка, оберіть мову:",
                            langs)


# Обробник колбеків перекладача
async def translate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обов'язково відповідаємо на колбек

    # Отримуємо дані з колбеку
    data = query.data
    # Якщо натиснуто кнопку "Закінчити"
    if data == 'start':
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('selected_enc', None)
        await start(update, context)
        return


    # Перевіряємо, чи це вибір способу кодування
    if data.startswith('translate_'):
        # Очищаємо попередні дані користувача перед вибором нового способу кодування
        context.user_data.clear()

        # Зберігаємо обраний спосіб кодування
        context.user_data['selected_lang'] = data
        context.user_data['conversation_state'] = 'translate'

        selected_lang = data.replace('translate_', '')

        # Завантажуємо промпт для обраної особистості
        prompt = load_prompt('translate').replace('lang', selected_lang)
        chat_gpt.set_prompt(prompt)  # Це повністю скидає історію повідомлень у сервісі ChatGPT
        lang_lable = langs[data].lower()
        # Надсилаємо повідомлення з інструкцією.
        await send_html(update, context,
                        f"Ви обрали мову перекладу: <b>{lang_lable}</b>.\n\nБудь ласка, надішліть текст, який необхідно перекласти!")


#Обробник помилок для бота
async def error_handler(update, context):
    logger.error(f"Помилка під час обробки оновлення: {context.error}")
    if isinstance(context.error, Conflict):
        logger.error("Конфлікт: інший екземпляр цього бота вже запущено. Переконайтесь, що працює лише один екземпляр.")
    elif isinstance(context.error, NetworkError):
        logger.error(f"Помилка мережі: {context.error}")

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt_handler))
app.add_handler(CommandHandler('talk', talk_handler))
app.add_handler(CommandHandler('quiz', quiz_handler))
app.add_handler(CommandHandler('token', token_handler))
app.add_handler(CommandHandler('translate', translate_handler))

# Зареєструвати обробник колбеку для кнопок випадкових фактів
app.add_handler(CallbackQueryHandler(random_fact_button_handler, pattern='^(random|start)$'))

# Зареєструвати обробник колбеку для кнопок в діалозі з відомими особистостями
app.add_handler(CallbackQueryHandler(talk_button_handler, pattern='^(talk_cobain|talk_einstein|talk_nietzsche|talk_lovelace|talk_tolkien|start)$'))

# Зареєструвати обробник колбеку для кнопок в діалозі з відомими особистостями
app.add_handler(CallbackQueryHandler(quiz_button_handler, pattern='^(quiz_AI|quiz_code|quiz_philosophy|quiz_psy|quiz_neuro|quiz_neuronet|quiz_cyber|quiz_ethics|start)$'))
app.add_handler(CallbackQueryHandler(quiz_handler, pattern='^(quiz)$'))
app.add_handler(CallbackQueryHandler(token_button_handler, pattern='^(token_cl100k_base|token_o200k_base|start)$'))
app.add_handler(CallbackQueryHandler(token_handler, pattern='^(token)$'))
app.add_handler(CallbackQueryHandler(translate_handler, pattern='^(translate)$'))
app.add_handler(CallbackQueryHandler(translate_button_handler, pattern='^(translate_valyrian|translate_dothraki|translate_klingon|start)$'))

# Зареєструвати обробник текстових повідомлень
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# Зареєструвати обробник колбеку для інших кнопок
app.add_handler(CallbackQueryHandler(default_callback_handler))

# Додавання обробника помилок
# app.add_error_handler(error_handler)

# Запуск бота з налаштуваннями для запобігання конфліктів
app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
