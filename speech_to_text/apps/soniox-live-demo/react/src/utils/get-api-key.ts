// Fetch temporary API key from the server, so we can establish websocket connection.
// Read more on: https://soniox.com/docs/speech-to-text/guides/direct-stream#temporary-api-keys
export default async function getAPIKey() {
  const response = await fetch(
    "http://localhost:8000/v1/auth/temporary-api-key",
    {
      method: "POST",
    },
  );
  const { apiKey } = await response.json();
  return apiKey;
}
