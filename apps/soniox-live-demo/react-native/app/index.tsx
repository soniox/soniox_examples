import TabView, { Tab } from "@/components/common/tab-view";
import TranscribeScreen from "@/screens/transcribe";
import TestBetween from "@/screens/translate-between";
import TranslateFromToScreen from "@/screens/translate-from-to";
import { useState } from "react";
import { SafeAreaView } from "react-native-safe-area-context";

export default function App() {
  const [activeTab, setActiveTab] = useState("transcribe");

  const tabs: Tab[] = [
    {
      id: "transcribe",
      label: "Transcribe",
      content: <TranscribeScreen />,
    },
    {
      id: "translate-from-to",
      label: "From-To",
      content: <TranslateFromToScreen />,
    },
    {
      id: "translate-between",
      label: "Between",
      content: <TestBetween />,
    },
  ];

  return (
    <SafeAreaView style={{ flex: 1 }}>
      <TabView tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
    </SafeAreaView>
  );
}
