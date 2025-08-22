import React from "react";

export interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
}

interface TabViewProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export default function TabView({
  tabs,
  activeTab,
  onTabChange,
}: TabViewProps) {
  return (
    <div>
      {/* Tab Navigation */}
      <div className="flex justify-center border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-soniox text-soniox"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>{tabs.find((tab) => tab.id === activeTab)?.content}</div>
    </div>
  );
}
