import logging
import httpx
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from src.config import Settings
from src.data_generation.models import UserProfile 

settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Health AI Assistant API",
    description="API для генерации персонализированных планов оздоровления"
)

class PlanResponse(BaseModel):
    status: str
    plan: Dict[str, Any]

@app.post("/generate-plan", response_model=PlanResponse)
async def generate_health_plan(profile: UserProfile):
    logger.info(f"Запрос на генерацию для пользователя. Возраст: {profile.age}")

    system_prompt = (
        "Ты — врач-реабилитолог. Твоя задача — генерировать программы оздоровления "
        "строго в формате JSON. Обязательно указывай противопоказания в health_warnings."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": profile.model_dump_json()}
        ],
        "temperature": 0.3
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.LOCAL_MODEL_URL, 
                json=payload, 
                timeout=120.0 
            )
            
        if response.status_code != 200:
            logger.error(f"Ошибка от llama.cpp: {response.text}")
            raise HTTPException(status_code=500, detail="Ошибка локальной модели")

        raw_content = response.json()["choices"][0]["message"]["content"]
        plan_data = json.loads(raw_content)

        return PlanResponse(status="success", plan=plan_data)

    except json.JSONDecodeError:
        logger.error("Модель вернула невалидный JSON")
        raise HTTPException(status_code=500, detail="Ошибка генерации структуры ответа")
    except httpx.ReadTimeout:
        logger.error("Модель не успела ответить за отведенное время")
        raise HTTPException(status_code=504, detail="Модель слишком долго думала")
    except Exception as e:
        logger.error(f"Внутренняя ошибка API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
