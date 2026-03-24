import json
import random
from datetime import datetime, time, timedelta
from typing import List

from src.config import Settings
from src.data_generation.dto import (
    AGE_GROUPS,
    ILLNESSES,
    WEEKDAYS,
    FreeTime,
    Gender,
    Goal,
    Intensity,
    TimeSlot,
    UserProfile,
)


class ProfileGenerationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_time_slot(self) -> TimeSlot:
        start_hour = random.randint(6, 21)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)

        duration_minutes = random.choice([30, 45, 60, 75, 90, 105, 120, 150, 180])
        end_datetime = datetime.combine(datetime.today(), start_time) + timedelta(
            minutes=duration_minutes
        )
        end_time = end_datetime.time()

        if end_time.hour >= 23:
            end_time = time(22, 45)

        return TimeSlot(
            start=start_time.strftime("%H:%M:%S"),
            end=end_time.strftime("%H:%M:%S"),
        )

    def generate_free_time(self) -> FreeTime:
        schedule: dict = {}
        for day in WEEKDAYS:
            num_slots = random.choices([0, 1, 2], weights=[0.2, 0.5, 0.3])[0]
            slots: List[TimeSlot] = []
            if num_slots > 0:
                attempts = 0
                while len(slots) < num_slots and attempts < 10:
                    new_slot = self.generate_time_slot()
                    overlap = any(
                        new_slot.start < existing.end and new_slot.end > existing.start
                        for existing in slots
                    )
                    if not overlap:
                        slots.append(new_slot)
                    attempts += 1
            schedule[day] = slots if slots else None
        return FreeTime(**schedule)

    def generate_illnesses(self) -> List[str]:
        if random.random() < 0.3:
            return []
        num_illnesses = random.randint(1, 3)
        return random.sample(ILLNESSES, num_illnesses)

    def generate_profile(self) -> UserProfile:
        return UserProfile(
            age=random.choice(AGE_GROUPS),
            gender=random.choice(list(Gender)),
            goal=random.choice(list(Goal)),
            intensity=random.choice(list(Intensity)),
            illnesses=self.generate_illnesses(),
            free_time=self.generate_free_time(),
        )

    def generate_profiles(self, count: int | None = None) -> List[UserProfile]:
        total = count if count is not None else self.settings.PROFILES_COUNT
        profiles: List[UserProfile] = []
        for i in range(total):
            if (i + 1) % 500 == 0:
                print(f"Generated {i + 1} profiles...")
            profiles.append(self.generate_profile())
        return profiles

    def save_to_json(
        self, profiles: List[UserProfile], filename: str | None = None
    ) -> None:
        path = filename or self.settings.PROFILES_FILE
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [p.model_dump(mode="json") for p in profiles],
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"Saved {len(profiles)} profiles to {path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate user profiles")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of profiles to generate (default: PROFILES_COUNT from settings)",
    )
    args = parser.parse_args()

    settings = Settings()
    service = ProfileGenerationService(settings)

    print("Starting profile generator...")
    profiles = service.generate_profiles(count=args.count)
    service.save_to_json(profiles)

    print("\nExample generated profile:")
    print(json.dumps(profiles[0].model_dump(mode="json"), ensure_ascii=False, indent=2))
