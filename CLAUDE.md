# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A minimal Node/TypeScript project integrating [Supermemory](https://docs.supermemory.ai/) for persistent, long-term memory.

- `src/memory.ts` — Supermemory client setup plus `remember()` (persist) and `recall()` (search) helpers, scoped by `containerTag`.
- `src/index.ts` — example usage: recall relevant memories for a message, then persist that message.

## Setup

```bash
npm install
cp .env.example .env   # then fill in SUPERMEMORY_API_KEY
npm start -- "some message"
```

## Conventions

- Never hardcode the Supermemory API key — it's read from `SUPERMEMORY_API_KEY` in the environment (`.env`, gitignored).
- Use a consistent `containerTag` per user/project to keep memory scoped and isolated (see `SUPERMEMORY_CONTAINER_TAG` in `.env`).
- Recall relevant memory before generating a response, and persist anything worth remembering afterward.
