from enum import Enum


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


class TaskType(str, Enum):
    SPORT = "SPORT"
    MEDICATION = "MEDICATION"
    NUTRITION = "NUTRITION"
    HABIT = "HABIT"
    REST = "REST"
