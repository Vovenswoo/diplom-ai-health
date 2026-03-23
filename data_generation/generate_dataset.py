import json
import os
import asyncio
import ssl
import aiohttp
import certifi
from dotenv import load_dotenv

# Загружаем API-ключ из .env
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("❌ OPENROUTER_API_KEY не найден в .env файле!")

print(f"✅ API ключ загружен: {api_key[:10]}...")

# Системный промпт из PDF (жёсткий)
SYSTEM_PROMPT = """
You are an advanced AI functioning as a World-Class Rehabilitation Physician, Sports Physiologist, and Elite Fitness Coach. Your sole objective is to generate a safe, science-backed, 1-month wellness plan based on the user's input profile.

STRICT MEDICAL SAFETY:
- The "illnesses" array has absolute priority.
- You MUST NOT include any exercises, movements, or dietary recommendations that are contraindicated.
- Explicitly list restrictions in "health_warnings".

STRICT TIME MANAGEMENT:
- Schedule tasks ONLY within the provided "free_time" slots.
- Task duration MUST NOT exceed the available time slot.

RECURRENCE & TASK LOGIC:
- Use iCalendar RRULE format (FREQ=DAILY or FREQ=WEEKLY;BYDAY=MO,WE,FR).
- Task types: "SPORT", "MEDICATION", "NUTRITION", "HABIT", "REST".
- If "is_instant": true, duration_minutes = 0.

OUTPUT FORMAT (JSON ONLY):
{
  "programm": {
    "meta": {
      "daily_calories": int,
      "macros": {"p": int, "f": int, "c": int},
      "health_warnings": [str],
      "focus": str
    },
    "tasks": [
      {
        "task": {
          "type": str,
          "title": str,
          "description": str,
          "is_instant": bool,
          "duration_minutes": int
        },
        "recurrence_rule": str,
        "time_of_day": str
      }
    ]
  }
}
"""

async def generate_program(session, profile: dict, semaphore, retries=3):
    """
    Асинхронно отправляет профиль в OpenRouter и возвращает программу
    """
    async with semaphore:  # Ограничиваем количество одновременных запросов
        for attempt in range(retries):
            try:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "AI Health Coach Dataset Generator"
                    },
                    json={
                        "model": "deepseek/deepseek-chat",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": json.dumps(profile, ensure_ascii=False)}
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # Очистка от возможных markdown-обёрток
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0]
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0]
                        
                        return json.loads(content)
                    
                    elif response.status == 429:
                        # Rate limit — ждём и повторяем
                        wait_time = 2 ** attempt  # 1, 2, 4 секунды
                        print(f"⚠️ Rate limit, ждём {wait_time} сек...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ HTTP {response.status}: {await response.text()}")
                        return None
                        
            except asyncio.TimeoutError:
                print(f"⏰ Таймаут, попытка {attempt + 1}/{retries}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ Ошибка: {e}, попытка {attempt + 1}/{retries}")
                await asyncio.sleep(1)
        
        print(f"❌ Не удалось обработать профиль после {retries} попыток")
        return None

async def generate_dataset(profiles, test_count, concurrency=5):
    """
    Асинхронно обрабатывает профили
    concurrency — количество одновременных запросов (чтобы не перегружать API)
    """
    # Создаём SSL-контекст с правильными сертификатами
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    semaphore = asyncio.Semaphore(concurrency)
    
    # Создаём сессию с правильным SSL
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i, profile in enumerate(profiles[:test_count]):
            print(f"📤 Добавлен профиль {i+1}/{test_count} в очередь")
            task = generate_program(session, profile, semaphore)
            tasks.append(task)
        
        print(f"🚀 Запуск {len(tasks)} асинхронных запросов (максимум {concurrency} одновременно)...")
        results = await asyncio.gather(*tasks)
        
        dataset = []
        for i, program in enumerate(results):
            if program:
                record = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(profiles[i], ensure_ascii=False)},
                        {"role": "assistant", "content": json.dumps(program, ensure_ascii=False)}
                    ]
                }
                dataset.append(record)
                print(f"✅ Обработан профиль {i+1}")
            else:
                print(f"❌ Пропущен профиль {i+1} (ошибка)")
        
        return dataset

def main():
    # Загружаем профили
    print("📂 Загрузка profiles.json...")
    with open("profiles.json", "r", encoding="utf-8") as f:
        profiles = json.load(f)
    
    print(f"✅ Загружено {len(profiles)} профилей")
    
    # Количество профилей для обработки
    # Для теста: 10, 50, 100
    # Для всех: len(profiles)
    test_count = 10
    print(f"🔄 Обрабатываю {test_count} профилей...")
    
    # Запускаем асинхронную обработку
    dataset = asyncio.run(generate_dataset(profiles, test_count, concurrency=5))
    
    # Сохраняем в dataset.jsonl
    with open("dataset.jsonl", "w", encoding="utf-8") as f:
        for record in dataset:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Сохранено {len(dataset)} записей в dataset.jsonl")

if __name__ == "__main__":
    main()