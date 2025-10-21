import { ErrorStatus, RecorderState, SpeechToTextAPIResponse, TranslationConfig } from "@soniox/speech-to-text-web";
import { useCallback, useEffect, useRef } from "react";

type TranscriptionError = {
  status: ErrorStatus;
  message: string;
  errorCode: number | undefined;
};

const DEFAULT_WS_URI = "wss://stt-rt.soniox.com/transcribe-websocket";
const FINALIZE_MESSAGE = '{ "type": "finalize" }';

// You can provide callbacks on specific websocket moment.
// Code inspired by: https://github.com/soniox/speech-to-text-web.
// onStateChange: when state changes
// onPartialResult: we get tokens (STT data) back from the API
// onError: we got error message, check status, msg, and code for more info
// onStarted: websocket started succesfully
// onFinished: websocket finished succesfully
type Callbacks = {
  onStateChange?: (update: { oldState: RecorderState; newState: RecorderState }) => void;
  onPartialResult?: (res: SpeechToTextAPIResponse) => void;
  onError?: (status: ErrorStatus, msg: string, code?: number) => void;
  onStarted?: () => void;
  onFinished?: () => void;
};

type UseRealTimeAPIOptions = {
  apiKey: string | (() => Promise<string>);
  config?: {
    translation?: TranslationConfig;
    audio?: { sampleRate?: number; channelCount?: number; encoding?: string };
    languageHints?: string[];
  };
  callbacks?: Callbacks;
};

// Manages websocket connection with Soniox real-time (ws) API.
// You have to provide an apiKey (or function to get the key), other
// parameters are optional.
// When real-time API returns tokens, hook calls onPartialResult callback function.
// Config and callbacks are setup when hook is called and can't be changed
// dynamically.
export function useRealTimeAPI({ apiKey, config, callbacks }: UseRealTimeAPIOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const stateRef = useRef<RecorderState>("Init");
  const errorRef = useRef<TranscriptionError | null>(null);

  // Buffer for audio chunks before socket is ready
  const audioBufferRef = useRef<(ArrayBuffer | Uint8Array)[]>([]);

  // Snapshot of config and callbacks (one-time per hook lifecycle)
  const configRef = useRef<Readonly<typeof config>>(config);
  const callbacksRef = useRef<Readonly<typeof callbacks>>(callbacks ?? {});

  // When state changes, call the user-defined callback (onStateChange).
  const updateState = useCallback((newState: RecorderState) => {
    const oldState = stateRef.current;
    stateRef.current = newState;
    callbacksRef.current?.onStateChange?.({ oldState, newState });
  }, []);

  // When error changes, call the user-defined callback (onError).
  const updateError = useCallback((newError: TranscriptionError) => {
    errorRef.current = newError;
    callbacksRef.current?.onError?.(newError.status, newError.message, newError.errorCode);
  }, []);

  // Helper function that get API key from getter function or string.
  const getApiKey = useCallback(async (): Promise<string | null> => {
    try {
      return typeof apiKey === "function" ? await apiKey() : apiKey;
    } catch (err) {
      updateError({
        status: "api_key_fetch_failed",
        message: err?.toString() || "Unknown error",
        errorCode: undefined,
      });
      return null;
    }
  }, [apiKey, updateError]);

  // Closes WebSocket connection
  const cleanup = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) wsRef.current.close();
    wsRef.current = null;
    audioBufferRef.current = [];
  }, []);

  // Sends all buffered data
  const flushAudioBuffer = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      while (audioBufferRef.current.length > 0) {
        const chunk = audioBufferRef.current.shift()!;
        wsRef.current.send(chunk);
      }
    }
  }, []);

  // Starts WebSocket connection. Initially sends config to the Soniox to
  // start real-time STT.
  const connect = useCallback(async () => {
    if (!["Init", "Finished", "Canceled"].includes(stateRef.current)) return;

    updateState("OpeningWebSocket");

    const key = await getApiKey();
    if (!key) return;

    const ws = new WebSocket(DEFAULT_WS_URI);
    wsRef.current = ws;

    // Sends STT config to the Soniox, calls user-defined callback (onStarted)
    // if provided.
    ws.onopen = () => {
      const { audio, translation, languageHints } = configRef.current ?? {};
      // Initial config that is first send to the Soniox
      const config = {
        api_key: key,
        model: "stt-rt-v3",
        audio_format: audio?.encoding ?? "pcm_s16le",
        sample_rate: audio?.sampleRate ?? 16000,
        num_channels: audio?.channelCount ?? 1,
        enable_speaker_diarization: true,
        enable_language_identification: true,
        enable_endpoint_detection: true,
        translation: translation,
        languageHints,
      };
      ws.send(JSON.stringify(config));
      updateState("Running");
      callbacksRef.current?.onStarted?.();

      // Send all stored audio to the soniox
      flushAudioBuffer();
    };

    // If we receive WebSocket error
    ws.onerror = () => {
      updateError({ status: "websocket_error", message: "WebSocket error", errorCode: undefined });
      updateState("Error");
      cleanup();
    };

    // When we receive response from Soniox real-time API.
    ws.onmessage = (event) => {
      try {
        // Try to parse given message int SpeechToTextAPIResponse
        const response: SpeechToTextAPIResponse = JSON.parse(event.data);
        if (response.error_message) {
          updateError({
            status: "api_error",
            message: response.error_message,
            errorCode: response.error_code,
          });
          updateState("Error");
          cleanup();
          return;
        }
        callbacksRef.current?.onPartialResult?.(response);
        if (response.finished) {
          updateState("Finished");
          cleanup();
          callbacksRef.current?.onFinished?.();
        }
      } catch (err) {
        updateError({
          status: "api_error",
          message: err?.toString() ?? "Failed to parse WebSocket message",
          errorCode: undefined,
        });
      }
    };

    ws.onclose = () => {
      if (stateRef.current !== "Finished" && stateRef.current !== "Canceled") updateState("Finished");
    };
  }, [getApiKey, updateState, updateError, cleanup, flushAudioBuffer]);

  // Function that user calls to send audio data to the Soniox real-time API.
  const sendAudio = useCallback((data: ArrayBuffer | Uint8Array) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data);
    } else {
      // store audio until WebSocket is ready
      audioBufferRef.current.push(data);
    }
  }, []);

  const stop = useCallback(() => {
    if (stateRef.current === "Running") {
      wsRef.current?.send("");
      updateState("FinishingProcessing");
    }
  }, [updateState]);

  const finalize = useCallback(() => {
    if (stateRef.current === "Running" || stateRef.current === "FinishingProcessing") {
      wsRef.current?.send(FINALIZE_MESSAGE);
    }
  }, []);

  const cancel = useCallback(() => {
    cleanup();
    updateState("Canceled");
  }, [cleanup, updateState]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return { connect, sendAudio, stop, finalize, cancel };
}
