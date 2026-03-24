.PHONY: generate-profiles generate-dataset

COUNT ?=

generate-profiles:
	python -m src.data_generation.generate_profiles $(if $(COUNT),--count $(COUNT),)

generate-dataset:
	python -m src.data_generation.generate_dataset $(if $(COUNT),--count $(COUNT),)
