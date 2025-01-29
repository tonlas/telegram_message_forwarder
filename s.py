from telethon import TelegramClient
from datetime import datetime, timezone
import random
import asyncio
from telethon.errors import FloodWaitError, ChatForwardsRestrictedError
import os
from dotenv import load_dotenv
import time

# Ваши параметры
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
destination_channel_id = os.getenv("DESTINATION_CHANNEL")  # Укажите ID канала для пересылки
keywords = os.getenv("KEYWORDS").split(",")  # Ваши ключевые слова
phone = os.getenv("PHONE")


def sleep_delay():
    min_delay = 0
    max_delay = 1
    delay = random.uniform(min_delay, max_delay)
    return delay


client = TelegramClient('my_session', api_id, api_hash)


async def main():
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
        messages = [] # Список для хранения текстов сообщений, чтобы избежать дублирования
        async for dialog in client.iter_dialogs():

            # Пропускаем канал назначения
            if dialog.id == destination_channel_id:
                print(f"Пропускаем канал назначения: {dialog.name} (ID: {dialog.id})")
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
                        # Не пересылаем дубликаты
                        if message.text in messages:
                            print("Такое сообщение уже есть в пуле")
                            continue
                        messages.append(message.text)
                        print(f"Найдено сообщение: {message.text[:50]}...")
                        # Пересылаем сообщение
                        try:
                            await client.forward_messages(destination_channel_id, message)
                        except ChatForwardsRestrictedError:
                            # Если пересылка запрещена, отправляем ссылку на сообщение
                            link = f"https://t.me/c/{dialog.id}/{message.id}"
                            await client.send_message(destination_channel_id, link)

    except FloodWaitError as e:
        print('Have to sleep', e.seconds, 'seconds')
        time.sleep(e.seconds)
    elapsed_time = time.time() - start_time

    print(
        f"Time - {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}, processed channels:{channel_counter}, messages {message_counter}")


asyncio.run(main())
