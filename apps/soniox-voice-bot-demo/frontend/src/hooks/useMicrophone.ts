import { useCallback, useRef } from "react";

const TARGET_SAMPLE_RATE = 16000;
const CHUNK_SIZE = 512; // 32ms at 16kHz

export const useMicrophone = ({
  onData,
  onError,
}: {
  onData: (data: ArrayBuffer) => void;
  onError: (error: Error) => void;
}) => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startMicrophoneStream = useCallback(() => {
    const start = async () => {
      const isFirefox = navigator.userAgent.includes("Firefox");

      try {
        // Get microphone with constraints for better quality
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: TARGET_SAMPLE_RATE,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: isFirefox,
            autoGainControl: isFirefox,
          },
        });
        streamRef.current = stream;

        // Create AudioContext at 16kHz
        const audioContext = new AudioContext({
          sampleRate: TARGET_SAMPLE_RATE,
        });
        audioContextRef.current = audioContext;

        // Create audio source from stream
        const source = audioContext.createMediaStreamSource(stream);

        // Create script processor for capturing audio chunks
        const processor = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
        processorRef.current = processor;

        processor.onaudioprocess = (event) => {
          const inputBuffer = event.inputBuffer;
          const channelData = inputBuffer.getChannelData(0);

          // Convert Float32 to Int16 PCM
          const int16Data = new Int16Array(channelData.length);
          for (let i = 0; i < channelData.length; i++) {
            const sample = Math.max(-1, Math.min(1, channelData[i]));
            int16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
          }

          // Send raw PCM data
          onData(int16Data.buffer);
        };

        // Connect: source -> processor -> destination (silent)
        source.connect(processor);
        processor.connect(audioContext.destination);
      } catch (err) {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    };

    start();
  }, [onData, onError]);

  const cleanupMicrophoneStream = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  return {
    startMicrophoneStream,
    cleanupMicrophoneStream,
  };
};
