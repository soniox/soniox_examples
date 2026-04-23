import LanguagePicker from "@/components/common/language-picker";
import { Renderer } from "@/components/renderers/renderer";
import { useSonioxClient } from "@/hooks/use-soniox-client";
import getAPIKey from "@/utils/get-api-key";
import { isActiveState } from "@soniox/speech-to-text-web";
import React, { useMemo, useState } from "react";
import { Text, View } from "react-native";
import RecordButton from "../components/common/record-button";
import { globalStyles } from "../global/global.styles";
import { getLanguage, type Language } from "../global/languages";

export default function TranslateBetweenScreen() {
  const [languageA, setLanguageA] = useState<Language>(() => getLanguage("en"));
  const [languageB, setLanguageB] = useState<Language>(() => getLanguage("es"));

  const { finalTokens, nonFinalTokens, state, startTranscription, stopTranscription } = useSonioxClient({
    apiKey: getAPIKey,
    translation: {
      type: "two_way",
      language_a: languageA.code,
      language_b: languageB.code,
    },
  });

  const languageAFinalTokens = useMemo(
    () => finalTokens.filter((t) => t.language === languageA.code),
    [finalTokens, languageA.code],
  );
  const languageANonFinalTokens = useMemo(
    () => nonFinalTokens.filter((t) => t.language === languageA.code),
    [nonFinalTokens, languageA.code],
  );
  const languageBFinalTokens = useMemo(
    () => finalTokens.filter((t) => t.language === languageB.code),
    [finalTokens, languageB.code],
  );
  const languageBNonFinalTokens = useMemo(
    () => nonFinalTokens.filter((t) => t.language === languageB.code),
    [nonFinalTokens, languageB.code],
  );

  const pickersDisabled = isActiveState(state);

  return (
    <View style={globalStyles.screen}>
      <View style={globalStyles.container}>
        {/* Top language picker row */}
        <View style={globalStyles.pickerHeader}>
          <Text style={globalStyles.pickerLabel}>From</Text>
          <LanguagePicker selectedLanguage={languageA} onChange={setLanguageA} disabled={pickersDisabled} />
          <Text style={globalStyles.pickerLabel}>to</Text>
          <LanguagePicker selectedLanguage={languageB} onChange={setLanguageB} disabled={pickersDisabled} />
        </View>

        {/* Source transcription (language A) */}
        <View style={globalStyles.card}>
          <Text style={globalStyles.cardTitle}>{languageA.name}</Text>
          <View style={globalStyles.cardInner}>
            <Renderer finalTokens={languageAFinalTokens} nonFinalTokens={languageANonFinalTokens} />
          </View>
        </View>

        {/* Target transcription (language B) */}
        <View style={globalStyles.card}>
          <Text style={globalStyles.cardTitle}>{languageB.name}</Text>
          <View style={globalStyles.cardInner}>
            <Renderer finalTokens={languageBFinalTokens} nonFinalTokens={languageBNonFinalTokens} />
          </View>
        </View>

        <RecordButton state={state} startTranscription={startTranscription} stopTranscription={stopTranscription} />
      </View>
    </View>
  );
}
