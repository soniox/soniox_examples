import { Renderer } from "@/components/renderers/renderer";
import { globalStyles } from "@/global/global.styles";
import { useSonioxClient } from "@/hooks/use-soniox-client";
import getAPIKey from "@/utils/get-api-key";
import { Text, View } from "react-native";
import RecordButton from "../components/common/record-button";

export default function TranscribeScreen() {
  const { finalTokens, nonFinalTokens, state, startTranscription, stopTranscription } = useSonioxClient({
    apiKey: getAPIKey,
  });

  return (
    <View style={globalStyles.screen}>
      <View style={globalStyles.container}>
        <View style={globalStyles.card}>
          <Text style={globalStyles.cardTitle}>Transcript</Text>
          <View style={globalStyles.cardInner}>
            <Renderer finalTokens={finalTokens} nonFinalTokens={nonFinalTokens} />
          </View>
        </View>

        <RecordButton state={state} startTranscription={startTranscription} stopTranscription={stopTranscription} />
      </View>
    </View>
  );
}
