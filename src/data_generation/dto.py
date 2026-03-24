from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.enums import Gender, Goal, Intensity, TaskType


ILLNESSES: List[str] = [
    "degenerative_disc_disease",
    "postural_kyphosis",
    "early_varicose_veins",
    "insulin_resistance",
    "flat_feet",
    "stage_1_hypertension",
    "muscular_deconditioning",
]

AGE_GROUPS: List[str] = [
    "15-20",
    "25-30",
    "35-40",
    "45-50",
    "50-60",
]

WEEKDAYS: List[str] = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class TimeSlot(BaseModel):
    start: str = Field(..., description="Start time in HH:MM:SS format")
    end: str = Field(..., description="End time in HH:MM:SS format")

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        try:
            hour, minute, second = map(int, v.split(":"))
            if minute % 15 != 0:
                raise ValueError(f"Minutes must be a multiple of 15: {v}")
            if second != 0:
                raise ValueError(f"Seconds must be 0: {v}")
            return v
        except ValueError:
            raise
        except Exception:
            raise ValueError(f"Invalid time format: {v}")


class FreeTime(BaseModel):
    monday: Optional[List[TimeSlot]] = None
    tuesday: Optional[List[TimeSlot]] = None
    wednesday: Optional[List[TimeSlot]] = None
    thursday: Optional[List[TimeSlot]] = None
    friday: Optional[List[TimeSlot]] = None
    saturday: Optional[List[TimeSlot]] = None
    sunday: Optional[List[TimeSlot]] = None


class UserProfile(BaseModel):
    age: str = Field(..., description="Age group")
    gender: Gender = Field(..., description="Gender")
    goal: Goal = Field(..., description="Fitness goal")
    intensity: Intensity = Field(..., description="Training intensity")
    illnesses: List[str] = Field(
        default_factory=list, description="List of illnesses (up to 3)"
    )
    free_time: FreeTime = Field(..., description="Weekly free-time schedule")

    @field_validator("illnesses")
    @classmethod
    def validate_illnesses(cls, v: List[str]) -> List[str]:
        if len(v) > 3:
            raise ValueError("No more than 3 illnesses allowed")
        for illness in v:
            if illness not in ILLNESSES:
                raise ValueError(f"Illness '{illness}' is not in the allowed list")
        return v

    @field_validator("age")
    @classmethod
    def validate_age_group(cls, v: str) -> str:
        if v not in AGE_GROUPS:
            raise ValueError(f"Age group '{v}' does not exist")
        return v


# ==================================================
# AI OUTPUT DTOs
# ==================================================


class Macros(BaseModel):
    p: int = Field(..., ge=0, description="Protein (g)")
    f: int = Field(..., ge=0, description="Fat (g)")
    c: int = Field(..., ge=0, description="Carbohydrates (g)")


class ProgramMeta(BaseModel):
    daily_calories: int = Field(..., ge=0)
    macros: Macros
    health_warnings: List[str] = Field(default_factory=list)
    focus: str


class TaskDetail(BaseModel):
    type: TaskType
    title: str
    description: str
    is_instant: bool
    duration_minutes: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_instant_duration(self) -> "TaskDetail":
        if self.is_instant and self.duration_minutes != 0:
            raise ValueError("duration_minutes must be 0 when is_instant is True")
        return self


class ProgramTask(BaseModel):
    task: TaskDetail
    recurrence_rule: str = Field(..., description="iCalendar RRULE string")
    time_of_day: str = Field(..., description="HH:MM time string")


class Program(BaseModel):
    meta: ProgramMeta
    tasks: List[ProgramTask] = Field(default_factory=list)


class ProgramResponse(BaseModel):
    programm: Program
