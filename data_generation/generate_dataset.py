import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем API-ключ из .env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Системный промпт из твоего PDF (строгий)
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

def generate_program(profile: dict) -> dict:
    """Отправляет профиль в DeepSeek и возвращает программу"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(profile, ensure_ascii=False)}
            ],
            temperature=0.3
        )
        # Извлекаем JSON из ответа
        content = response.choices[0].message.content
        # Убираем возможные markdown обертки
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return None

def main():
    # Загружаем профили
    print("📂 Загрузка profiles.json...")
    with open("profiles.json", "r", encoding="utf-8") as f:
        profiles = json.load(f)
    
    print(f"✅ Загружено {len(profiles)} профилей")
    
    # Для теста берем первые 10 профилей
    # Потом изменишь на len(profiles) для всех 5000
    test_count = 10
    print(f"🔄 Обрабатываю {test_count} профилей для теста...")
    
    dataset = []
    for i, profile in enumerate(profiles[:test_count]):
        print(f"   {i+1}/{test_count}...")
        
        program = generate_program(profile)
        if program:
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(profile, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(program, ensure_ascii=False)}
                ]
            }
            dataset.append(record)
    
    # Сохраняем в dataset.jsonl
    with open("dataset.jsonl", "w", encoding="utf-8") as f:
        for record in dataset:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Сохранено {len(dataset)} записей в dataset.jsonl")

if __name__ == "__main__":
    main()