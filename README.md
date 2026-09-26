# OpenRouter API Integration

A Go client for interacting with OpenRouter API using the Anthropic SDK.

## Overview

This project provides a simple, reusable Go client for sending messages to models available through OpenRouter's API endpoint. It wraps the Anthropic SDK to work seamlessly with OpenRouter's infrastructure.

## Features

- Clean client wrapper around Anthropic SDK
- Easy configuration with environment variables
- Type-safe API
- Comprehensive test coverage
- Example implementations

## Prerequisites

- Go 1.19 or higher
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

## Installation

```bash
go get github.com/zr70v/test
```

## Setup

### 1. Set Environment Variable

Export your OpenRouter API key:

```bash
export OPENROUTER_API_KEY=your_api_key_here
```

### 2. Basic Usage

```go
package main

import (
	"context"
	"fmt"
	"log"

	"github.com/zr70v/test/client"
)

func main() {
	ctx := context.Background()
	
	// Create a new client (reads OPENROUTER_API_KEY from environment)
	c := client.New("")
	
	// Send a message
	response, err := c.SendMessage(ctx, "typesafe/jev-router", "What is the meaning of life?")
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
	
	fmt.Println("Response:", response)
}
```

### 3. With Explicit API Key

```go
c := client.New("your-api-key-here")
```

## API Documentation

### Client.New(apiKey string) *Client

Creates a new OpenRouter client. If `apiKey` is empty, it reads from the `OPENROUTER_API_KEY` environment variable.

### Client.SendMessage(ctx context.Context, model, message string) (string, error)

Sends a message to the specified model and returns the response.

**Parameters:**
- `ctx`: Context for request cancellation and timeouts
- `model`: Model identifier (e.g., "typesafe/jev-router")
- `message`: The message to send

**Returns:**
- `string`: The model's response
- `error`: Error if the request fails

## Running Examples

```bash
# Basic example
export OPENROUTER_API_KEY=your_api_key
go run examples/basic.go
```

## Running Tests

```bash
go test ./...
```

## Project Structure

```
.
├── main.go              # Entry point
├── go.mod              # Module definition
├── go.sum              # Dependency checksums
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── client/
│   ├── openrouter.go   # Client implementation
│   └── openrouter_test.go  # Client tests
└── examples/
    └── basic.go        # Basic usage example
```

## Environment Variables

- `OPENROUTER_API_KEY` - Your OpenRouter API key (required if not passed to client.New())

## Error Handling

The client will panic if no API key is provided (either via parameter or environment variable). In production, you may want to modify this behavior.

## License

MIT
