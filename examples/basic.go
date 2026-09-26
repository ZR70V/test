package main

import (
	"context"
	"fmt"
	"log"

	"github.com/zr70v/test/client"
)

func main() {
	ctx := context.Background()
	c := client.New("")

	response, err := c.SendMessage(ctx, "typesafe/jev-router", "Hello, what's your name?")
	if err != nil {
		log.Fatalf("Error: %v", err)
	}

	fmt.Println("Response:", response)
}
