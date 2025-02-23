from telethon import TelegramClient
from datetime import datetime, timezone
import random
import asyncio
from telethon.errors import FloodWaitError, ChatForwardsRestrictedError
import os
from dotenv import load_dotenv
import time
import re
import logging

# Ваши параметры
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE")
destination_channel_id = os.getenv("DESTINATION_CHANNEL")  # Укажите ID канала для пересылки
keywords = os.getenv("KEYWORDS").split(",")  # Ваши ключевые слова
excluded_channels = os.getenv("EXCLUDED_CHANNELS").split(",")  # Список каналов, которые нужно пропустить
stop_words = os.getenv("STOPWORDS").split(",")  # Список стоп-слов
user_nicks = os.getenv("USER").split(",")  # Список ников пользователей для упоминаний


def sleep_delay():
    min_delay = 0
    max_delay = 1
    delay = random.uniform(min_delay, max_delay)
    return delay


def contains_stop_words(text):
    text_lower = text.lower()
    return any(stop_word.lower() in text_lower for stop_word in
               stop_words)


client = TelegramClient('my_session', api_id, api_hash)

logging.basicConfig(
    filename='script.log',
    level=logging.INFO,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
)


async def main():
    try:
        print(stop_words)
        print(keywords)
        start_time = time.time()
        channel_counter = 0
        message_counter = 0
        await client.start(phone)
        try:
            # Получаем дату и время последнего сообщения в целевом канале
            last_message = await client.get_messages(destination_channel_id, limit=1)
            if last_message:
                last_post_time = last_message[0].date
            else:
                last_post_time = datetime(1970, 1, 1, tzinfo=timezone.utc)  # Если сообщений нет, берём древнюю дату

            print(f"Дата последнего поста в целевом канале: {last_post_time}")
            messages = []  # Список для хранения текстов сообщений, чтобы избежать дублирования
            stopped_messages = []
            async for dialog in client.iter_dialogs():

                # Пропускаем канал назначения
                if dialog.id == destination_channel_id:
                    print(f"Пропускаем канал назначения: {dialog.name} (ID: {dialog.id})")
                    continue
                # Пропускаем каналы из списка
                if str(dialog.id) in excluded_channels:
                    print(f"Пропускаем канал из списка: {dialog.name} (ID: {dialog.id})")
                    continue
                # Обрабатываем только каналы
                if dialog.is_channel and not dialog.is_group:
                    print(f"Читаем канал: {dialog.name} (ID: {dialog.id})")

                    # Рандомная задержка перед обработкой диалога
                    await asyncio.sleep(sleep_delay())
                    channel_counter += 1

                    # Перебираем сообщения в канале
                    async for message in client.iter_messages(entity=dialog.id, wait_time=2):
                        message_counter += 1
                        # Прекращаем обработку, если сообщение старше последнего поста
                        if message.date <= last_post_time:
                            break

                        # Проверяем ключевые слова
                        if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
                            if contains_stop_words(message.text):
                                print(f"В сообщении {message.text} стоп-слово!!!")
                                stopped_messages.append(message.text)
                            nick_in_message = any(user_nick.lower() in message.text.lower() for user_nick in user_nicks)

                            # Проверяем наличие непроходимых слов
                            if not any(stop_word.lower() in message.text.lower() for stop_word in
                                       stop_words) or nick_in_message:
                                # Не пересылаем дубликаты
                                if message.text in messages:
                                    print("Такое сообщение уже есть в пуле")
                                    continue
                                messages.append(message.text)
                                print(f"Найдено сообщение: {message.text[:50]}...")
                                # Если что-то выигрываем, то помечаем ключевым словом
                                if nick_in_message:
                                    await client.send_message(destination_channel_id, "Хубабуба")
                                # Пересылаем сообщение
                                try:
                                    await client.forward_messages(destination_channel_id, message)
                                except ChatForwardsRestrictedError:
                                    # Если пересылка запрещена, отправляем ссылку на сообщение
                                    link = f"https://t.me/c/{dialog.id}/{message.id}"
                                    await client.send_message(destination_channel_id, f"{link} in {dialog.name}")
            #logging.info(f"Прошедшие сообщения:\n\n\n")
            #for msg in messages:
            #    logging.info(f"{msg}\n")
            logging.info(f"Непрошедшие:\n\n\n")
            for msg in stopped_messages:
                logging.info(f"{msg}\n")
        except FloodWaitError as e:
            print('Have to sleep', e.seconds, 'seconds')
            time.sleep(e.seconds)
        elapsed_time = time.time() - start_time

        print(
            f"Time - {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}, processed channels:{channel_counter}, messages {message_counter}")


    except Exception as e:
        logging.error("Ошибка!", exc_info=true)


asyncio.run(main())
