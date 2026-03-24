from src.config import Settings
from src.data_generation.completion_client import CompletionClient
from src.data_generation.generate_dataset import DatasetGenerationService
from src.data_generation.generate_profiles import ProfileGenerationService
from src.data_generation.dto import (
    AGE_GROUPS,
    ILLNESSES,
    WEEKDAYS,
    FreeTime,
    Macros,
    Program,
    ProgramMeta,
    ProgramResponse,
    ProgramTask,
    TaskDetail,
    TimeSlot,
    UserProfile,
)
from src.enums import Gender, Goal, Intensity, TaskType

__all__ = [
    "Settings",
    "CompletionClient",
    "ProfileGenerationService",
    "DatasetGenerationService",
    # input DTOs
    "UserProfile",
    "FreeTime",
    "TimeSlot",
    "Gender",
    "Goal",
    "Intensity",
    "ILLNESSES",
    "AGE_GROUPS",
    "WEEKDAYS",
    # output DTOs
    "ProgramResponse",
    "Program",
    "ProgramMeta",
    "ProgramTask",
    "TaskDetail",
    "TaskType",
    "Macros",
]
