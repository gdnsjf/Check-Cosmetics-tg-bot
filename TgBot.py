import logging
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import joblib
import pytesseract
from PIL import Image
import re
from io import BytesIO

# Применение nest_asyncio для избежания ошибки с event loop
nest_asyncio.apply()

# Логирование для отслеживания событий
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определение функции для токенизации ингредиентов
def custom_tokenizer(text):
    # Разбиваем текст по запятым
    tokens = re.split(r',\s*', text)
    return tokens

# Загрузка модели и векторизатора
model = joblib.load('cosmetic_safety_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

# Очистка и форматирование текста
def clean_and_format_text(text):
    text = text.lower()

    # Удаляем все до первого слова "aqua" или "water"
    match = re.search(r'\baqua|water\b', text)
    if match:
        text = text[match.start():]

    # Удаляем любые лишние символы кроме букв, цифр, запятых и пробелов
    text = re.sub(r'[^a-zA-Z0-9,\s\-]', '', text)

    # Убираем множественные пробелы и лишние запятые
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# Извлечение текста с изображения
def extract_text_from_image(image):
    img = Image.open(image)
    return pytesseract.image_to_string(img)

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь мне изображение состава, и я проверю его безопасность.')

# Обработка изображений
async def handle_image(update: Update, context: CallbackContext) -> None:
    photo = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO(await photo.download_as_bytearray())

    raw_text = extract_text_from_image(photo_bytes)
    clean_text = clean_and_format_text(raw_text)
    ingredients = custom_tokenizer(clean_text)

    total_ingredients = len(ingredients)
    rating_0_2 = 0
    rating_3_6 = 0
    rating_7_10 = 0

    result_message = "Результаты анализа продукта:\n"

    for ingredient in ingredients:
        ingredient_vector = vectorizer.transform([ingredient.strip()])
        prediction = model.predict(ingredient_vector)

        if prediction[0] == 2:
            result_message += f'⚠️ {ingredient.strip()} \n'
            rating_7_10 += 1
        elif prediction[0] == 1:
            result_message += f'🟡 {ingredient.strip()}\n'
            rating_3_6 += 1
        else:
            result_message += f'✅ {ingredient.strip()}\n'
            rating_0_2 += 1

    percent_0_2 = (rating_0_2 / total_ingredients) * 100
    percent_3_6 = (rating_3_6 / total_ingredients) * 100
    percent_7_10 = (rating_7_10 / total_ingredients) * 100

    if rating_7_10 > 0:
        result_message += "\n❌ Продукт содержит опасные ингредиенты и НЕ рекомендуется для покупки."
    elif percent_0_2 >= 80 and percent_3_6 <= 15:
        result_message += "\n✅ Продукт безопасен и РЕКОМЕНДУЕТСЯ для покупки."
    else:
        result_message += "\n⚠️ Продукт не соответствует требованиям безопасности и НЕ рекомендуется для покупки."

    await update.message.reply_text(result_message)
    await update.message.reply_text('Хотите проверить еще один продукт? Отправьте фото состава!')

# Логирование ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

# Основной запуск бота
async def main():
    TOKEN = "YOUR_BOT_TOKEN"
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
