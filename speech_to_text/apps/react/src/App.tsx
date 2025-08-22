import { useState } from "react";
import TabView, { type Tab } from "./components/tab-view";
import Transcribe from "./renderers/transcribe";
import TranslateTo from "./renderers/translate-to";
import TranslateBetween from "./renderers/translate-between";

function App() {
  const [activeTab, setActiveTab] = useState("transcribe");

  const tabs: Tab[] = [
    {
      id: "transcribe",
      label: "Transcribe",
      content: <Transcribe />,
    },
    {
      id: "translate-to",
      label: "Translate To",
      content: <TranslateTo />,
    },
    {
      id: "translate-between",
      label: "Translate Between",
      content: <TranslateBetween />,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <TabView tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
  );
}

export default App;
