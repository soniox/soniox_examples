import { useRecording } from "@soniox/react";
import StatusDisplay from "../components/status-display";
import RecordButton from "../components/record-button";
import Renderer from "./renderer";
import useAutoScroll from "@/hooks/useAutoScroll";

export default function Transcribe() {
  const recording = useRecording({
    model: "stt-rt-v4",
    enable_language_identification: true,
    enable_speaker_diarization: true,
    enable_endpoint_detection: true,
  });

  const allTokens = [...recording.finalTokens, ...recording.partialTokens];
  const autoScrollRef = useAutoScroll(allTokens);

  return (
    <div className="bg-[#f2f2f2] rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Live Transcribe
        </h2>
        <StatusDisplay state={recording.state} />
      </div>

      <div
        ref={autoScrollRef}
        className="h-[500px] overflow-y-auto p-4 border rounded-lg bg-white mb-4"
      >
        <Renderer
          tokens={allTokens}
          placeholder="Click start to begin transcribing"
        />
      </div>

      {recording.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <div className="text-red-700 text-sm">
            Error: {recording.error.message}
          </div>
        </div>
      )}

      <RecordButton
        isActive={recording.isActive}
        isStopping={recording.state === "stopping"}
        stop={recording.stop}
        start={recording.start}
      />
    </div>
  );
}
