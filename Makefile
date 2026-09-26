.PHONY: help build test run clean

help:
	@echo "Available targets:"
	@echo "  build    - Build the application"
	@echo "  test     - Run tests"
	@echo "  run      - Run the application"
	@echo "  clean    - Remove build artifacts"
	@echo "  fmt      - Format code"
	@echo "  lint     - Run linter"

build:
	go build -o bin/openrouter-client .

test:
	go test -v ./...

run:
	go run main.go

clean:
	rm -rf bin/
	go clean

fmt:
	go fmt ./...

lint:
	golangci-lint run ./...
