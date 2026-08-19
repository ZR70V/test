# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A minimal Node.js/TypeScript project integrated with [Supermemory](https://supermemory.ai), a memory layer API for AI applications. It provides a configured Supermemory client and an example script showing how to add and search memories.

## Setup

```sh
npm install
cp .env.example .env   # then set SUPERMEMORY_API_KEY (get one at https://console.supermemory.ai)
```

## Commands

- `npm run example` — run `src/examples/add-and-search.ts`, which adds a memory and searches for it
- `npx tsc --noEmit` — typecheck

## Architecture

- `src/lib/supermemory.ts` — exports a configured `Supermemory` client (`supermemory`), reading `SUPERMEMORY_API_KEY` from the environment
- `src/examples/add-and-search.ts` — example usage of `client.add()` and `client.search()`

## Conventions

- Memories are scoped per user/tenant with `containerTag` (e.g. `user_${userId}`) so each user gets an isolated memory space — see [container tags & filtering](https://supermemory.ai/docs/concepts/filtering)
- ES modules throughout (`"type": "module"` in package.json); local imports use explicit `.js` extensions per NodeNext module resolution
