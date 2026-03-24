import asyncio
import json
import ssl

import aiohttp
import certifi

from pydantic import ValidationError

from src.config import Settings
from src.data_generation.dto import ProgramResponse

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


class CompletionClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def build_connector(self) -> aiohttp.TCPConnector:
        return aiohttp.TCPConnector(ssl=self._ssl_context)

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.HTTP_REFERER,
            "X-Title": self.settings.APP_TITLE,
        }

    def _build_payload(self, profile: dict) -> dict:
        return {
            "model": self.settings.MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(profile, ensure_ascii=False)},
            ],
            "temperature": self.settings.TEMPERATURE,
            "response_format": {"type": "json_object"},
        }

    def _strip_markdown(self, content: str) -> str:
        if "```json" in content:
            return content.split("```json")[1].split("```")[0]
        if "```" in content:
            return content.split("```")[1].split("```")[0]
        return content

    async def complete(
        self,
        session: aiohttp.ClientSession,
        profile: dict,
        semaphore: asyncio.Semaphore,
    ) -> dict | None:
        async with semaphore:
            for attempt in range(self.settings.MAX_RETRIES):
                try:
                    async with session.post(
                        self.settings.OPENROUTER_BASE_URL,
                        headers=self._build_headers(),
                        json=self._build_payload(profile),
                        timeout=aiohttp.ClientTimeout(
                            total=self.settings.REQUEST_TIMEOUT
                        ),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            raw = data["choices"][0]["message"]["content"]
                            parsed = json.loads(self._strip_markdown(raw))
                            return ProgramResponse.model_validate(parsed).model_dump(
                                mode="json"
                            )

                        if response.status == 429:
                            wait = 2**attempt
                            print(f"Rate limit hit, retrying in {wait}s...")
                            await asyncio.sleep(wait)
                            continue

                        print(f"HTTP {response.status}: {await response.text()}")
                        return None

                except asyncio.TimeoutError:
                    print(
                        f"Timeout on attempt {attempt + 1}/{self.settings.MAX_RETRIES}"
                    )
                    await asyncio.sleep(1)
                except ValidationError as exc:
                    print(
                        f"Response validation failed on attempt {attempt + 1}/{self.settings.MAX_RETRIES}: {exc}"
                    )
                    return None
                except Exception as exc:
                    print(
                        f"Error on attempt {attempt + 1}/{self.settings.MAX_RETRIES}: {exc}"
                    )
                    await asyncio.sleep(1)

        print(f"Failed to process profile after {self.settings.MAX_RETRIES} attempts")
        return None
