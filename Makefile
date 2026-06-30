.PHONY: install playground server

install:
	uv sync

playground:
	agents-cli playground

server:
	uv run python server.py

frontend:
	npm run start
