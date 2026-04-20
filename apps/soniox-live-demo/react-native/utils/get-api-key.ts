import { Platform } from "react-native";

// Fetch temporary API key from the local auth server.
// For Android emulator, localhost is accessible via 10.0.2.2
const defaultBaseUrl = Platform.select({
  android: "http://localhost:8000",
  ios: "http://localhost:8000",
  default: "http://localhost:8000",
});

export default async function getAPIKey(): Promise<string> {
  const baseUrl = process.env.EXPO_PUBLIC_TEMP_API_BASE_URL ?? defaultBaseUrl!;
  const response = await fetch(`${baseUrl}/v1/auth/temporary-api-key`, {
    method: "POST",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Failed to fetch temporary API key (${response.status}): ${text}`);
  }

  const data = (await response.json()) as { apiKey: string };
  return data.apiKey;
}
