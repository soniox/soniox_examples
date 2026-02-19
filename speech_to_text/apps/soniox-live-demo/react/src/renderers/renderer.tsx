import { getLanguage } from "@/config/languages";
import SpeakerLabel from "../components/speaker-label";
import React from "react";

interface Token {
  text: string;
  is_final: boolean;
  speaker?: string;
  language?: string;
  translation_status?: "none" | "original" | "translation";
}

interface RendererProps {
  tokens: readonly Token[];
  placeholder: string;
}

// Component for pretty displaying tokens. It adds label for different speakers
// and label for different languages. It also visually displays difference
// between final and non-final tokens.
export default function Renderer({ tokens, placeholder }: RendererProps) {
  let lastSpeaker: string | undefined;
  let lastLanguage: string | undefined;
  return (
    <>
      {tokens.length === 0 ? (
        <div className="text-gray-500 text-center flex items-center justify-center h-full">
          {placeholder}
        </div>
      ) : (
        <div>
          {tokens.map((token, idx) => {
            // Track speaker changes to show speaker labels only when speaker changes
            const isNewSpeaker = token.speaker && token.speaker !== lastSpeaker;
            const isNewLanguage =
              token.language && token.language !== lastLanguage;

            lastSpeaker = token.speaker;
            lastLanguage = token.language;

            return (
              <React.Fragment key={`rendered-token-${idx}`}>
                {/* Show speaker label if speaker changed or new speaker joined */}
                {isNewSpeaker && token.speaker && (
                  <SpeakerLabel speakerNumber={token.speaker} />
                )}
                {/* Show new language on a new line */}
                {isNewLanguage && !isNewSpeaker && <br />}
                {/* Show language label if language changed or new language is detected */}
                {isNewLanguage && (
                  <span className="text-gray-500 text-xs bg-gray-200 px-2 py-0.5 rounded-full mr-1">
                    {`${getLanguage(token.language!).name}`}
                  </span>
                )}
                {/* Display final and non-final tokens with different colors */}
                <span
                  className={token.is_final ? "text-gray-900" : "text-gray-500"}
                >
                  {token.text}
                </span>
              </React.Fragment>
            );
          })}
        </div>
      )}
    </>
  );
}
