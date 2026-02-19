interface RecordButtonProps {
  isActive: boolean;
  isStopping: boolean;
  stop: () => void;
  start: () => void;
}

export default function RecordButton({
  isActive,
  isStopping,
  stop,
  start,
}: RecordButtonProps) {
  return (
    <div className="text-center">
      {isActive ? (
        <button
          className="px-6 text-md font-bold cursor-pointer py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={stop}
          disabled={isStopping}
        >
          {isStopping ? "Finishing..." : "Stop Recording"}
        </button>
      ) : (
        <button
          className="px-6 text-md font-bold cursor-pointer py-2 bg-soniox text-white rounded-lg hover:bg-soniox/80"
          onClick={start}
        >
          Start Recording
        </button>
      )}
    </div>
  );
}
