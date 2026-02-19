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
            if (token.text === "<end>") {
              return (
                <span
                  key={`end-token-${idx}`}
                  className="text-gray-400 italic text-xs"
                >{` <end>`}</span>
              );
            }
            const isNewSpeaker = token.speaker && token.speaker !== lastSpeaker;
            const isNewLanguage =
              token.language && token.language !== lastLanguage;

            lastSpeaker = token.speaker;
            lastLanguage = token.language;

            return (
              <React.Fragment key={`rendered-token-${idx}`}>
                {isNewSpeaker && token.speaker && (
                  <SpeakerLabel speakerNumber={token.speaker} />
                )}
                {isNewLanguage && !isNewSpeaker && <br />}
                {isNewLanguage && (
                  <span className="text-gray-500 text-xs bg-gray-200 px-2 py-0.5 rounded-full mr-1">
                    {`${getLanguage(token.language!).name}`}
                  </span>
                )}
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
