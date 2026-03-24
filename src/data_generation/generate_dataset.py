import asyncio
import json

import aiohttp

from src.config import Settings
from src.data_generation.completion_client import SYSTEM_PROMPT, CompletionClient


class DatasetGenerationService:
    def __init__(self, settings: Settings, client: CompletionClient) -> None:
        self.settings = settings
        self.client = client

    def load_profiles(self, filename: str | None = None) -> list[dict]:
        path = filename or self.settings.PROFILES_FILE
        print(f"Loading profiles from {path}...")
        with open(path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        print(f"Loaded {len(profiles)} profiles")
        return profiles

    def save_dataset(self, dataset: list[dict], filename: str | None = None) -> None:
        path = filename or self.settings.DATASET_FILE
        with open(path, "w", encoding="utf-8") as f:
            for record in dataset:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Saved {len(dataset)} records to {path}")

    async def _generate(self, profiles: list[dict], count: int) -> list[dict]:
        semaphore = asyncio.Semaphore(self.settings.CONCURRENCY)
        connector = self.client.build_connector()

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self.client.complete(session, profile, semaphore)
                for profile in profiles[:count]
            ]
            print(
                f"Sending {len(tasks)} requests (max {self.settings.CONCURRENCY} concurrent)..."
            )
            results = await asyncio.gather(*tasks)

        dataset: list[dict] = []
        for i, program in enumerate(results):
            if program:
                dataset.append(
                    {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": json.dumps(profiles[i], ensure_ascii=False),
                            },
                            {
                                "role": "assistant",
                                "content": json.dumps(program, ensure_ascii=False),
                            },
                        ]
                    }
                )
                print(f"Processed profile {i + 1}")
            else:
                print(f"Skipped profile {i + 1} (failed)")

        return dataset

    def run(self, count: int | None = None) -> None:
        profiles = self.load_profiles()
        total = count if count is not None else len(profiles)
        print(f"Processing {total} profiles...")

        dataset = asyncio.run(self._generate(profiles, total))
        self.save_dataset(dataset)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate dataset from profiles")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of profiles to process (default: all profiles in the file)",
    )
    args = parser.parse_args()

    settings = Settings()
    client = CompletionClient(settings)
    service = DatasetGenerationService(settings, client)
    service.run(count=args.count)
