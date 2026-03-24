# AI Health Coach — Dataset Generator

Generates a fine-tuning dataset of personalised 1-month wellness plans.
Each record pairs a randomly generated user profile (input) with an AI-produced programme (output).

## Project structure

```
src/
  config.py                        # Pydantic settings (reads .env)
  enums.py                         # Shared enums: Gender, Goal, Intensity, TaskType
  data_generation/
    dto.py                         # Input and output Pydantic models
    completion_client.py           # OpenRouter API client + system prompt
    generate_profiles.py           # ProfileGenerationService
    generate_dataset.py            # DatasetGenerationService
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_key_here
```

Optional overrides (all have defaults):

```env
MODEL=deepseek/deepseek-chat
TEMPERATURE=0.3
CONCURRENCY=50
MAX_RETRIES=3
REQUEST_TIMEOUT=60
PROFILES_COUNT=5000
PROFILES_FILE=src/data_generation/profiles.json
DATASET_FILE=src/data_generation/dataset.jsonl
```

## Make commands

All commands must be run from the **project root**.

### `generate-profiles`

Generates random user profiles and saves them to `PROFILES_FILE`.

```bash
# Generate the default number of profiles (PROFILES_COUNT from settings, default 5000)
make generate-profiles

# Generate a specific number of profiles
make generate-profiles COUNT=100
```

### `generate-dataset`

Reads profiles from `PROFILES_FILE`, sends each one to the AI, and saves the
resulting fine-tuning records to `DATASET_FILE` in JSONL format.

```bash
# Process all profiles in the file
make generate-dataset

# Process only the first N profiles
make generate-dataset COUNT=10
```

### Typical workflow

```bash
make generate-profiles COUNT=5000
make generate-dataset
```
