import { useEffect, useRef, useState } from "react";
import useAutoScroll from "../hooks/useAutoScroll";
import { messageSchema, updateMessages, type Message } from "../utils/messages";
import { Renderer } from "./renderer";
import { useAudioChunkPlayer } from "../hooks/useAudioChunkPlayer";
import { useMicrophone } from "../hooks/useMicrophone";
import { LANGUAGES } from "../languages";

const backendWebsocketUrl = import.meta.env.VITE_SONIOX_VOICE_BOT_WS_URL;

export function Conversation() {
  const websocket = useRef<WebSocket | null>(null);

  const [language, setLanguage] = useState("en");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const autoScrollRef = useAutoScroll(messages);

  const { startMicrophoneStream, cleanupMicrophoneStream } = useMicrophone({
    onData: (data) => websocket.current?.send(data),
    onError: (error) => {
      console.error("Error recording audio:", error);
      setError("Error recording audio.");
      cleanup();
    },
  });

  const {
    cleanupAudioPlayer,
    prepareAudioPlayer,
    addAudioChunk,
    interruptAudio,
  } = useAudioChunkPlayer({});

  const cleanup = () => {
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
    }

    cleanupMicrophoneStream();
    cleanupAudioPlayer();
    setIsRecording(false);
  };

  const startRecording = () => {
    if (websocket.current) {
      return;
    }

    setIsRecording(true);
    setMessages([]);
    setError(null);
    prepareAudioPlayer();

    const url = new URL(backendWebsocketUrl);
    url.searchParams.append("language", language);
    url.searchParams.append("voice", "Alina");

    const ws = new WebSocket(url.toString());
    websocket.current = ws;

    ws.onopen = () => startMicrophoneStream();

    ws.onerror = (e) => {
      console.error("Error connecting to backend:", e);
      setError("Error connecting to backend.");
      cleanup();
    };

    ws.onclose = () => cleanup();

    ws.onmessage = async (e) => {
      try {
        if (typeof e.data === "string") {
          // 1. JSON message from backend
          const data = JSON.parse(e.data);

          // Handle VAD messages - interrupt audio immediately
          if (data.type === "user_speech_start") {
            interruptAudio();
            // Don't add VAD messages to the UI message list
            return;
          }

          if (data.type === "user_speech_end") {
            // Don't add VAD messages to the UI message list
            return;
          }

          // Skip session_start and metric messages - don't add to UI
          if (data.type === "session_start" || data.type === "metric") {
            return;
          }

          // 2. Parse and handle transcription/LLM messages
          const message = messageSchema.parse(data);
          setMessages((messages) => updateMessages(messages, message));

          // If a new transcription message arrives, the user is speaking.
          // We should stop the bot's audio playback immediately.
          if (message.type === "transcription") {
            interruptAudio();
          }
        } else if (e.data instanceof Blob) {
          // 3. Received audio blob chunk (TTS played)
          addAudioChunk(await e.data.arrayBuffer());
        } else {
          console.error("Unexpected message type");
        }
      } catch (e) {
        console.error(e);
      }
    };
  };

  const stopRecording = () => cleanup();

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="bg-[#f2f2f2] rounded-lg shadow p-6 flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-gray-900">Soniox Voice Bot</h2>

      <div
        ref={autoScrollRef}
        className="h-125 overflow-y-auto p-4 border border-gray-300 rounded-lg bg-white"
      >
        <Renderer messages={messages} />
      </div>

      {error && <div className="text-red-600">{error}</div>}

      <div className="flex flex-row gap-2 justify-center items-center">
        <label htmlFor="language" className="mr-2 font-medium text-gray-700">
          Language:
        </label>
        <select
          id="language"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-4 max-w-xs"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          {LANGUAGES.map(({ code, name }) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>

        <div className="flex-1" />

        {isRecording ? (
          <button
            className="px-6 text-md font-bold cursor-pointer py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={stopRecording}
          >
            Listening
          </button>
        ) : (
          <button
            className="px-6 text-md font-bold cursor-pointer py-2 bg-soniox text-white rounded-lg hover:bg-soniox/80"
            onClick={startRecording}
          >
            Start talking
          </button>
        )}
      </div>
    </div>
  );
}
