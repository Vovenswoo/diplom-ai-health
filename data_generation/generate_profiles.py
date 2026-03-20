import json
import random
from datetime import datetime, time, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

# ==================================================
# ENUMS
# ==================================================

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Goal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTAIN_FITNESS = "maintain_fitness"
    GENERAL_HEALTH = "general_health"
    REHABILITATION = "rehabilitation"

class Intensity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

# Список болезней (окончательный)
ILLNESSES = [
    "degenerative_disc_disease",
    "postural_kyphosis",
    "early_varicose_veins",
    "insulin_resistance",
    "flat_feet",
    "stage_1_hypertension",
    "muscular_deconditioning"
]

# Возрастные группы
AGE_GROUPS = [
    "15-20",
    "25-30",
    "35-40",
    "45-50",
    "50-60"
]

# Дни недели
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# ==================================================
# PYDANTIC МОДЕЛИ
# ==================================================

class TimeSlot(BaseModel):
    start: str = Field(..., description="Время начала в формате HH:MM:SS")
    end: str = Field(..., description="Время окончания в формате HH:MM:SS")
    
    @field_validator("start", "end")
    def validate_time_format(cls, v):
        try:
            hour, minute, second = map(int, v.split(":"))
            if minute % 15 != 0:
                raise ValueError(f"Минуты должны быть кратны 15: {v}")
            if second != 0:
                raise ValueError(f"Секунды должны быть 0: {v}")
            return v
        except Exception:
            raise ValueError(f"Неверный формат времени: {v}")

class FreeTime(BaseModel):
    monday: Optional[List[TimeSlot]] = None
    tuesday: Optional[List[TimeSlot]] = None
    wednesday: Optional[List[TimeSlot]] = None
    thursday: Optional[List[TimeSlot]] = None
    friday: Optional[List[TimeSlot]] = None
    saturday: Optional[List[TimeSlot]] = None
    sunday: Optional[List[TimeSlot]] = None

class UserProfile(BaseModel):
    age: str = Field(..., description="Возрастная группа")
    gender: Gender = Field(..., description="Пол")
    goal: Goal = Field(..., description="Цель")
    intensity: Intensity = Field(..., description="Интенсивность")
    illnesses: List[str] = Field(default_factory=list, description="Список болезней (1-3)")
    free_time: FreeTime = Field(..., description="Расписание свободного времени")
    
    @field_validator("illnesses")
    def validate_illnesses(cls, v):
        if len(v) > 3:
            raise ValueError("Не более 3 болезней")
        for illness in v:
            if illness not in ILLNESSES:
                raise ValueError(f"Болезнь {illness} не входит в разрешенный список")
        return v
    
    @field_validator("age")
    def validate_age_group(cls, v):
        if v not in AGE_GROUPS:
            raise ValueError(f"Возрастная группа {v} не существует")
        return v

# ==================================================
# ГЕНЕРАТОРЫ
# ==================================================

def generate_time_slot() -> TimeSlot:
    start_hour = random.randint(6, 21)
    start_minute = random.choice([0, 15, 30, 45])
    start_time = time(start_hour, start_minute)
    
    duration_minutes = random.choice([30, 45, 60, 75, 90, 105, 120, 150, 180])
    
    end_datetime = datetime.combine(datetime.today(), start_time) + timedelta(minutes=duration_minutes)
    end_time = end_datetime.time()
    
    if end_time.hour >= 23:
        end_time = time(22, 45)
    
    return TimeSlot(
        start=start_time.strftime("%H:%M:%S"),
        end=end_time.strftime("%H:%M:%S")
    )

def generate_free_time() -> FreeTime:
    schedule = {}
    for day in WEEKDAYS:
        num_slots = random.choices([0, 1, 2], weights=[0.2, 0.5, 0.3])[0]
        slots = []
        if num_slots > 0:
            attempts = 0
            while len(slots) < num_slots and attempts < 10:
                new_slot = generate_time_slot()
                overlap = False
                for existing in slots:
                    if new_slot.start < existing.end and new_slot.end > existing.start:
                        overlap = True
                        break
                if not overlap:
                    slots.append(new_slot)
                attempts += 1
        schedule[day] = slots if slots else None
    
    return FreeTime(**schedule)

def generate_illnesses() -> List[str]:
    if random.random() < 0.3:
        return []
    num_illnesses = random.randint(1, 3)
    return random.sample(ILLNESSES, num_illnesses)

def generate_user_profile() -> UserProfile:
    return UserProfile(
        age=random.choice(AGE_GROUPS),
        gender=random.choice([Gender.MALE, Gender.FEMALE]),
        goal=random.choice(list(Goal)),
        intensity=random.choice(list(Intensity)),
        illnesses=generate_illnesses(),
        free_time=generate_free_time()
    )

def generate_profiles(count: int = 5000) -> List[UserProfile]:
    profiles = []
    for i in range(count):
        if (i + 1) % 500 == 0:
            print(f"Сгенерировано {i + 1} профилей...")
        profiles.append(generate_user_profile())
    return profiles

def save_profiles_to_json(profiles: List[UserProfile], filename: str = "profiles.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([p.model_dump(mode="json") for p in profiles], f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено {len(profiles)} профилей в {filename}")

if __name__ == "__main__":
    print("🚀 Запуск генератора профилей...")
    profiles = generate_profiles(5000)
    save_profiles_to_json(profiles, "profiles.json")
    print("\n📋 Пример сгенерированного профиля:")
    print(json.dumps(profiles[0].model_dump(mode="json"), ensure_ascii=False, indent=2))