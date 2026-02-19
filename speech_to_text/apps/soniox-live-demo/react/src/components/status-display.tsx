interface StatusDisplayProps {
  state: string;
}

export default function StatusDisplay({ state }: StatusDisplayProps) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${
          state === "recording"
            ? "bg-green-500"
            : state === "stopping"
              ? "bg-yellow-500"
              : state === "error"
                ? "bg-red-500"
                : "bg-gray-400"
        }`}
      ></div>
      <span className="text-sm text-gray-600">{state}</span>
    </div>
  );
}
