import type { Message } from "../utils/messages";

function RenderMessage({ message }: { message: Message }) {
  if (message.type === "transcription") {
    return (
      <div className="flex flex-row justify-end">
        <div className="border bg-soniox text-white rounded-lg p-2 flex-1 max-w-lg">
          <span>{message.final_text}</span>
          <span className="text-white/60">{message.non_final_text}</span>
        </div>
      </div>
    );
  } else if (message.type === "llm_response") {
    return (
      <div className="flex flex-row justify-start">
        <div className="border border-gray-300 bg-gray-200 rounded-lg p-2 flex-1 max-w-lg">
          {message.text}
        </div>
      </div>
    );
  } else {
    console.error("Unexpected message type");
    return (
      <div className="text-gray-400 text-center">Unexpected message type</div>
    );
  }
}

export function Renderer({ messages }: { messages: Message[] }) {
  return (
    <div className="flex flex-col gap-2 pt-4">
      {messages.map((message, index) => (
        <RenderMessage key={index} message={message} />
      ))}
    </div>
  );
}
