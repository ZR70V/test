package client

import (
	"context"
	"fmt"
	"os"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

const OpenRouterBaseURL = "https://openrouter.ai/api"

type Client struct {
	anthropic *anthropic.Client
}

func New(apiKey string) *Client {
	if apiKey == "" {
		apiKey = os.Getenv("OPENROUTER_API_KEY")
	}
	if apiKey == "" {
		panic("OPENROUTER_API_KEY environment variable or apiKey parameter is required")
	}

	c := anthropic.NewClient(
		option.WithBaseURL(OpenRouterBaseURL),
		option.WithAPIKey(apiKey),
	)

	return &Client{
		anthropic: &c,
	}
}

func (c *Client) SendMessage(ctx context.Context, model, message string) (string, error) {
	resp, err := c.anthropic.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     model,
		MaxTokens: 1024,
		Messages: []anthropic.MessageParam{
			anthropic.NewUserMessage(
				anthropic.NewTextBlock(message),
			),
		},
	})
	if err != nil {
		return "", fmt.Errorf("failed to send message: %w", err)
	}

	if len(resp.Content) == 0 {
		return "", fmt.Errorf("empty response from model")
	}

	if resp.Content[0].Type == "text" {
		return resp.Content[0].Text, nil
	}

	return "", fmt.Errorf("unexpected response type: %s", resp.Content[0].Type)
}
