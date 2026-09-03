# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Project overview

This is a minimal Expo (React Native) app, scaffolded from the `blank` template.

- Entry point: `index.js` registers `App.js` as the root component.
- `app.json` holds the Expo app config (name, icons, platform settings).

## Common commands

```bash
npm install        # install dependencies
npx expo start      # start the Metro dev server (scan the QR code with Expo Go, or press a/i/w)
npm run android      # start and open on Android
npm run ios          # start and open on iOS (macOS only)
npm run web           # start and open in the browser
```

There is no test suite or linter configured yet.
