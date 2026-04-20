import z from "zod";

const transcriptionMessageSchema = z.object({
  type: z.literal("transcription"),
  final_text: z.string(),
  non_final_text: z.string(),
});

const llmResponseMessageSchema = z.object({
  type: z.literal("llm_response"),
  text: z.string(),
});

const sessionStartMessageSchema = z.object({
  type: z.literal("session_start"),
});

const userSpeechStartMessageSchema = z.object({
  type: z.literal("user_speech_start"),
});

const userSpeechEndMessageSchema = z.object({
  type: z.literal("user_speech_end"),
});

export const messageSchema = z.union([
  transcriptionMessageSchema,
  llmResponseMessageSchema,
  sessionStartMessageSchema,
  userSpeechStartMessageSchema,
  userSpeechEndMessageSchema,
]);

export type Message = z.infer<typeof messageSchema>;

/**
 * Add new message from backend to the list of messages.
 * If the last message is of the same type, extend it (LLM response streaming or new transcription tokens).
 * Otherwise, create a new message.
 */
export function updateMessages(
  messages: Message[],
  message: Message
): Message[] {
  const previousMessages = messages.slice(0, -1);
  const lastMessage = messages.at(-1);

  if (!lastMessage) {
    // First message
    return [message];
  }

  if (lastMessage.type !== message.type) {
    // New message type, reset
    return [...previousMessages, lastMessage, message];
  }

  if (
    lastMessage.type === "transcription" &&
    message.type === "transcription"
  ) {
    // Extend the final and update non final tokens
    return [
      ...previousMessages,
      {
        type: "transcription",
        final_text: lastMessage.final_text + message.final_text,
        non_final_text: message.non_final_text,
      },
    ];
  } else if (
    lastMessage.type === "llm_response" &&
    message.type === "llm_response"
  ) {
    // Extend the text
    return [
      ...previousMessages,
      {
        type: "llm_response",
        text: lastMessage.text + message.text,
      },
    ];
  }

  console.error("Unexpected message type");
  return messages;
}
