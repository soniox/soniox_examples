import { useCallback, useRef } from "react";
import { loadAudioConcatProcessor } from "../utils/audioConcatProcessor";

export const useAudioChunkPlayer = ({
  sampleRate = 24000,
  volume = 1,
}: {
  sampleRate?: number;
  volume?: number;
}) => {
  const audioContext = useRef<AudioContext | null>(null);
  const gain = useRef<GainNode | null>(null);
  const audioWorklet = useRef<AudioWorkletNode | null>(null);

  const cleanupAudioPlayer = useCallback(() => {
    audioWorklet.current?.port.postMessage({ type: "interrupt" });
    audioWorklet.current?.disconnect();
    gain.current?.disconnect();
    audioContext.current?.close();

    audioWorklet.current = null;
    gain.current = null;
    audioContext.current = null;
  }, []);

  const prepareAudioPlayer = useCallback(async () => {
    try {
      const context = new AudioContext({ sampleRate });
      audioContext.current = context;

      const analyser = context.createAnalyser();
      gain.current = context.createGain();
      gain.current.connect(analyser);
      analyser.connect(context.destination);

      await loadAudioConcatProcessor(context.audioWorklet);
      audioWorklet.current = new AudioWorkletNode(
        context,
        "audio-concat-processor",
      );
      audioWorklet.current.connect(context.destination);

      await context.resume();
    } catch (error) {
      audioContext.current?.close();
      throw error;
    }
  }, [sampleRate]);

  const addAudioChunk = useCallback(
    async (chunk: ArrayBuffer) => {
      if (!audioWorklet.current) {
        return;
      }
      if (gain.current) {
        gain.current.gain.value = volume;
      }
      audioWorklet.current.port.postMessage({ type: "clearInterrupted" });
      audioWorklet.current.port.postMessage({ type: "buffer", buffer: chunk });
    },
    [volume],
  );

  const interruptAudio = useCallback(() => {
    if (!audioWorklet.current || !gain.current || !audioContext.current) {
      return;
    }
    audioWorklet.current.port.postMessage({ type: "interrupt" });
    gain.current?.gain.exponentialRampToValueAtTime(
      0.0001,
      audioContext.current.currentTime + 0.5,
    );

    // reset volume back
    setTimeout(() => {
      if (gain.current) {
        gain.current.gain.value = volume;
      }
      audioWorklet.current?.port.postMessage({ type: "clearInterrupted" });
    }, 500);
  }, [volume]);

  return {
    prepareAudioPlayer,
    cleanupAudioPlayer,
    addAudioChunk,
    interruptAudio,
  };
};
