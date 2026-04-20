import { useMicrophone } from "@/hooks/use-microphone";
import { useRealTimeAPI } from "@/hooks/use-real-time-api";
import { AudioDataEvent } from "@siteed/expo-audio-studio";
import {
  ErrorStatus,
  isActiveState,
  RecorderState,
  SpeechToTextAPIResponse,
  Token,
  TranslationConfig,
} from "@soniox/speech-to-text-web";
import { Buffer } from "buffer";
import { useCallback, useEffect, useRef, useState } from "react";

interface UseSonioxClientOptions {
  apiKey: string | (() => Promise<string>);
  languageHints?: string[];
  translation?: TranslationConfig;
  audio?: { sampleRate?: number; channelCount?: number; encoding?: string };
}

type TranscriptionError = {
  status: ErrorStatus;
  message: string;
  errorCode: number | undefined;
};

export function useSonioxClient(options: UseSonioxClientOptions) {
  const [finalTokens, setFinalTokens] = useState<Token[]>([]);
  const [nonFinalTokens, setNonFinalTokens] = useState<Token[]>([]);
  const [state, setState] = useState<RecorderState>("Init");
  const [error, setError] = useState<TranscriptionError | null>(null);
  const isActiveRef = useRef(true);

  const processTokens = (res: SpeechToTextAPIResponse) => {
    const newFinal: Token[] = [];
    const newNonFinal: Token[] = [];

    for (const token of res.tokens) {
      if (token.is_final) newFinal.push(token);
      else newNonFinal.push(token);
    }

    if (newFinal.length > 0) setFinalTokens((prev) => [...prev, ...newFinal]);
    setNonFinalTokens(newNonFinal);
  };

  const { connect, sendAudio, stop, cancel } = useRealTimeAPI({
    apiKey: options.apiKey,
    config: {
      languageHints: options.languageHints,
      translation: options.translation,
      audio: options.audio,
    },
    callbacks: {
      onPartialResult: processTokens,
      onStateChange: (update) => setState(update.newState),
      onError: (status, message, errorCode) => setError({ status, message, errorCode }),
      onStarted: () => console.log("transcription started"),
      onFinished: () => console.log("transcription finished"),
    },
  });

  const handleOnAudio = async (data: AudioDataEvent) => {
    if (typeof data.data === "string") {
      const buf = Buffer.from(data.data, "base64");
      const MAX_CHUNK_SIZE = 60000;
      let offset = 0;

      while (offset < buf.length) {
        const end = Math.min(offset + MAX_CHUNK_SIZE, buf.length);
        const chunk = buf.subarray(offset, end);
        sendAudio(chunk);
        offset = end;
      }
    }
  };

  const { startRecording, stopRecording } = useMicrophone(handleOnAudio);

  const startTranscription = async () => {
    if (isActiveState(state)) return;
    isActiveRef.current = true;

    setFinalTokens([]);
    setNonFinalTokens([]);
    setError(null);
    stopRecording();
    await startRecording();
    await connect();
  };

  const stopTranscription = useCallback(() => {
    isActiveRef.current = false;
    stopRecording();
    stop();
  }, [stop, stopRecording]);

  // Ensure that we stop recording audio and stop websocket connection on
  // component unmount.
  useEffect(() => {
    return () => stopTranscription();
  }, [stopTranscription]);

  return {
    finalTokens,
    nonFinalTokens,
    state,
    error,
    startTranscription,
    stopTranscription,
  };
}
