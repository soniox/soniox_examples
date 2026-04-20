import LanguagePicker from "@/components/common/language-picker";
import { Renderer } from "@/components/renderers/renderer";
import { globalStyles } from "@/global/global.styles";
import { getLanguage, type Language } from "@/global/languages";
import { useSonioxClient } from "@/hooks/use-soniox-client";
import getAPIKey from "@/utils/get-api-key";
import { isActiveState } from "@soniox/speech-to-text-web";
import React, { useMemo, useState } from "react";
import { Text, View } from "react-native";
import RecordButton from "../components/common/record-button";

export default function TranslateFromToScreen() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(() => getLanguage("es"));

  const { finalTokens, nonFinalTokens, state, startTranscription, stopTranscription } = useSonioxClient({
    apiKey: getAPIKey,
    translation: {
      type: "one_way",
      target_language: selectedLanguage.code,
    },
  });

  // TODO: auto scroll refs

  const sourceFinalTokens = useMemo(
    () => finalTokens.filter((t) => t.translation_status !== "translation"),
    [finalTokens],
  );
  const sourceNonFinalTokens = useMemo(
    () => nonFinalTokens.filter((t) => t.translation_status !== "translation"),
    [nonFinalTokens],
  );
  const targetFinalTokens = useMemo(
    () => finalTokens.filter((t) => t.translation_status === "translation"),
    [finalTokens],
  );
  const targetNonFinalTokens = useMemo(
    () => nonFinalTokens.filter((t) => t.translation_status === "translation"),
    [nonFinalTokens],
  );

  return (
    <View style={globalStyles.screen}>
      <View style={globalStyles.container}>
        {/* Top language picker row */}
        <View style={globalStyles.pickerHeader}>
          <Text style={globalStyles.pickerLabel}>
            From <Text style={globalStyles.pickerBold}>ANY</Text> to
          </Text>
          <LanguagePicker
            selectedLanguage={selectedLanguage}
            onChange={setSelectedLanguage}
            disabled={isActiveState(state)}
          />
        </View>

        {/* Source transcription */}
        <View style={globalStyles.card}>
          <Text style={globalStyles.cardTitle}>Transcript</Text>
          <View style={globalStyles.cardInner}>
            <Renderer finalTokens={sourceFinalTokens} nonFinalTokens={sourceNonFinalTokens} />
          </View>
        </View>

        {/* Target translation */}
        <View style={globalStyles.card}>
          <Text style={globalStyles.cardTitle}>{selectedLanguage.name}</Text>
          <View style={globalStyles.cardInner}>
            <Renderer finalTokens={targetFinalTokens} nonFinalTokens={targetNonFinalTokens} />
          </View>
        </View>

        <RecordButton state={state} startTranscription={startTranscription} stopTranscription={stopTranscription} />
      </View>
    </View>
  );
}
