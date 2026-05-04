.PHONY: generate-profiles generate-dataset run-model kill-llama run-api

COUNT ?=

generate-profiles:
	python -m src.data_generation.generate_profiles $(if $(COUNT),--count $(COUNT),)

generate-dataset:
	python -m src.data_generation.generate_dataset $(if $(COUNT),--count $(COUNT),)

run-model:
	~/llama.cpp/build/bin/llama-server -m ~/Downloads/Qwen2.5-7B-Instruct.Q4_K_M.gguf -c 4096 --temp 0.3 --port 8080

kill-llama:
	killall -9 llama-server

run-api:
	uvicorn src.api.main:app --reload --port 8000