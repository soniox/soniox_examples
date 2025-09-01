import { AudioDataEvent, EncodingType, SampleRate, useAudioRecorder } from "@siteed/expo-audio-studio";

// Use native microphone with 'expo-audio-studio' library.
// onAudio: callback function with microphone audio data (chunk of streamed data)
// audioConfig: microphone audio config options
export function useMicrophone(
  onAudio: (data: AudioDataEvent) => Promise<void>,
  audioConfig?: { sampleRate?: SampleRate; channelCount?: 1 | 2; encoding?: EncodingType },
) {
  const { startRecording, stopRecording, isRecording } = useAudioRecorder();

  const start = async () => {
    await startRecording({
      output: { primary: { enabled: false } },
      sampleRate: audioConfig?.sampleRate ?? 16000,
      channels: audioConfig?.channelCount ?? 1,
      encoding: audioConfig?.encoding ?? "pcm_16bit",
      onAudioStream: onAudio,
    });
  };

  return { startRecording: start, stopRecording, isRecording };
}
