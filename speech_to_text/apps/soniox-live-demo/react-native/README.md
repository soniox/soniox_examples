# Soniox Speech-to-Text React Native (Expo) Example

A minimal React Native (Expo) example demonstrating real-time speech-to-text using the Soniox WebSocket API.

## Features

- Real-time speech transcription
- Visual distinction between final and non-final tokens
- Translation mode (one-way and two-way)
- TypeScript support
- Secure API key handling via temporary key server

## Prerequisites

- Node.js + npm
- Android device
- This example uses the Soniox Temporary API Key Server. See the [server README](../server/README.md) for setup instructions.
- Installed ADB for port forwarding

## Getting Started

### Option 1: Secure Setup (Recommended)

1. Start the temporary API key server:

   ```bash
   cd ../server
   ./start.sh
   ```

   Make sure to set your `SONIOX_API_KEY` environment variable as described in the server README.

2. Install dependencies (Expo React Native: use npm):

   ```bash
   cd ../react-native
   npm install
   ```

3. Start the Expo dev server:

   ```bash
   npm run android
   ```

4. Allow the Android device to reach the server

   ```bash
   adb reverse tcp:8000 tcp:8000
   ```

- Android emulator automatically reaches your host at `10.0.2.2` -> no need to
  use the above command, just ovveride `EXPO_PUBLIC_TEMP_API_BASE_URL`.
- If your temp API server runs on a different host/port, set an environment variable before starting Expo:

  ```bash
  EXPO_PUBLIC_TEMP_API_BASE_URL=http://YOUR_HOST:8000 npm start
  ```

5. Open on your Android device/emulator and grant microphone permissions when prompted. Tap "Start" to begin transcription.

### Option 2: Quick Testing (Less Secure)

If you want to test quickly without setting up the server, you can use your API key directly. Two simple options:

- Hardcode the key in `utils/get-api-key.ts`:

  ```ts
  // speech_to_text/apps/react-native/utils/get-api-key.ts
  export default async function getAPIKey() {
    return "YOUR_SONIOX_API_KEY_HERE";
  }
  ```

Then run the app:

```bash
npm install
npm run android
```

⚠️ Warning: This exposes your API key in the client and should only be used for testing.

## How it Works

- Final tokens: confirmed transcription results that won’t change
- Non-final tokens: tentative results that may update as more audio is processed
- `useSonioxClient` hook connects `useRealTimeAPI` and `useMicrophone`
- Tokens are efficiently rendered using component `Renderer`
- Security: Instead of exposing your main API key, the app fetches temporary API keys from a secure server in `apps/server`

## Code Structure

- `screens/transcribe.tsx` – Live transcription
- `screens/translate-between.tsx` – Two-way translation view
- `screens/translate-from-to.tsx` – One-way translation view
- `hooks/` – Transcription/translation core
- `components/` – UI components and token renderer
- `utils/get-api-key.ts` – Fetches temporary API key

## Documentation

For more details about Soniox, see:

- Soniox Documentation: https://soniox.com/docs

## Notes

- Android emulator uses `10.0.2.2` to reach services running on your development machine’s `localhost`.
- You can override the key server URL with `EXPO_PUBLIC_TEMP_API_BASE_URL`.

## Next Steps

Extend this demo into your app by reusing the `hooks/` and `components/` — they’re designed to be modular.
