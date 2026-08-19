// Command managed-agent-app is a minimal client for the Anthropic Managed
// Agents API: it starts a session against a pre-created agent, sends a
// single user message, and prints the agent's reply as it streams in.
package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/anthropics/anthropic-sdk-go"
)

const (
	agentID       = "agent_01AGF8Kj64MeNfCm5C2bbxZH"
	environmentID = "env_01BWX8ih681ehFvza8W1BJVG"
)

func main() {
	if os.Getenv("ANTHROPIC_API_KEY") == "" && os.Getenv("ANTHROPIC_AUTH_TOKEN") == "" {
		fmt.Fprintln(os.Stderr, "error: set ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN) before running")
		os.Exit(1)
	}

	message := "Hello! What can you help me with?"
	if len(os.Args) > 1 {
		message = strings.Join(os.Args[1:], " ")
	}

	client := anthropic.NewClient()
	ctx := context.Background()

	session, err := client.Beta.Sessions.New(ctx, anthropic.BetaSessionNewParams{
		Agent: anthropic.BetaSessionNewParamsAgentUnion{
			OfString: anthropic.String(agentID),
		},
		EnvironmentID: environmentID,
		Title:         anthropic.String("Quickstart session"),
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: creating session: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Session: %s (status: %s)\n\n", session.ID, session.Status)

	// Open the stream before sending the message so no early events are missed.
	stream := client.Beta.Sessions.Events.StreamEvents(ctx, session.ID, anthropic.BetaSessionEventStreamParams{})
	defer stream.Close()

	if _, err := client.Beta.Sessions.Events.Send(ctx, session.ID, anthropic.BetaSessionEventSendParams{
		Events: []anthropic.BetaManagedAgentsEventParamsUnion{{
			OfUserMessage: &anthropic.BetaManagedAgentsUserMessageEventParams{
				Type: anthropic.BetaManagedAgentsUserMessageEventParamsTypeUserMessage,
				Content: []anthropic.BetaManagedAgentsUserMessageEventParamsContentUnion{{
					OfText: &anthropic.BetaManagedAgentsTextBlockParam{
						Type: anthropic.BetaManagedAgentsTextBlockTypeText,
						Text: message,
					},
				}},
			},
		}},
	}); err != nil {
		fmt.Fprintf(os.Stderr, "error: sending message: %v\n", err)
		os.Exit(1)
	}

	exitCode := 0

events:
	for stream.Next() {
		switch event := stream.Current().AsAny().(type) {
		case anthropic.BetaManagedAgentsAgentMessageEvent:
			for _, block := range event.Content {
				fmt.Print(block.Text)
			}
		case anthropic.BetaManagedAgentsSessionErrorEvent:
			fmt.Fprintf(os.Stderr, "\n[session error: %s]\n", event.Error.Message)
			exitCode = 1
		case anthropic.BetaManagedAgentsSessionStatusTerminatedEvent:
			break events
		case anthropic.BetaManagedAgentsSessionStatusIdleEvent:
			// Idle is transient (e.g. between tool calls); only stop once the
			// stop reason isn't asking us to keep going.
			if event.StopReason.Type == "requires_action" {
				continue
			}
			if event.StopReason.Type == "retries_exhausted" {
				exitCode = 1
			}
			break events
		}
	}

	fmt.Println()

	if err := stream.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "error: stream: %v\n", err)
		os.Exit(1)
	}

	os.Exit(exitCode)
}
