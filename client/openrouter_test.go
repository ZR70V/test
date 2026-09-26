package client

import (
	"testing"
)

func TestNewClientWithEmptyAPIKey(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "")
	defer func() {
		if r := recover(); r == nil {
			t.Errorf("expected panic when API key is missing")
		}
	}()
	New("")
}

func TestNewClientWithProvidedAPIKey(t *testing.T) {
	c := New("test-api-key")
	if c == nil {
		t.Errorf("expected client to be created")
	}
	if c.anthropic == nil {
		t.Errorf("expected anthropic client to be initialized")
	}
}

func TestNewClientWithEnvironmentVariable(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "env-api-key")
	c := New("")
	if c == nil {
		t.Errorf("expected client to be created from environment variable")
	}
}
