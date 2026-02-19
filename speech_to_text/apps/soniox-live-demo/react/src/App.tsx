import { useState } from "react";
import { SonioxProvider } from "@soniox/react";
import TabView, { type Tab } from "./components/tab-view";
import Transcribe from "./renderers/transcribe";
import TranslateFromTo from "./renderers/translate-to";
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
      label: "Translate From-To",
      content: <TranslateFromTo />,
    },
    {
      id: "translate-between",
      label: "Translate Between",
      content: <TranslateBetween />,
    },
  ];

  return (
    <SonioxProvider
      apiKey={async () => {
        const response = await fetch(
          "http://localhost:8000/v1/auth/temporary-api-key",
          { method: "POST" },
        );
        const { apiKey } = await response.json();
        return apiKey;
      }}
    >
      <div className="min-h-screen bg-gradient-to-b from-[#001227cc] via-[#0a59bbcc] to-[#ffffffcc] p-4">
        <div className="max-w-4xl mx-auto">
          <TabView
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </div>
      </div>
    </SonioxProvider>
  );
}

export default App;
