import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { moderateScale, verticalScale } from "react-native-size-matters";
import { colors } from "../../global/colors";

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

export default function TabView({ tabs, activeTab, onTabChange }: TabViewProps) {
  const activeTabData = tabs.find((tab) => tab.id === activeTab);
  return (
    <LinearGradient
      colors={["#001227", "#0a59bb", "#ffffff"]}
      start={{ x: 0.5, y: 0 }}
      end={{ x: 0.5, y: 1 }}
      style={styles.gradientBackground}
    >
      <View style={styles.container}>
        <View style={styles.tabHeaders}>
          {tabs.map((tab) => (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tabHeader, activeTab === tab.id && styles.activeTabHeader]}
              onPress={() => onTabChange(tab.id)}
            >
              <Text style={[styles.tabHeaderText, activeTab === tab.id && styles.activeTabHeaderText]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.tabContent}>{activeTabData?.content}</View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientBackground: {
    flex: 1,
  },
  container: {
    flex: 1,
    padding: moderateScale(4),
  },
  tabHeaderText: {
    fontSize: moderateScale(16),
    fontWeight: "500",
    color: colors.white,
  },
  activeTabHeaderText: {
    fontWeight: "600",
  },
  tabContent: {
    flex: 1,
    borderRadius: moderateScale(12),
    padding: moderateScale(4),
  },
  tabHeaders: {
    flexDirection: "row",
    borderRadius: moderateScale(12),
    marginBottom: verticalScale(4),
    overflow: "hidden",
  },
  tabHeader: {
    flex: 1,
    paddingVertical: verticalScale(8),
    alignItems: "center",
    justifyContent: "center",
    borderBottomWidth: verticalScale(2),
    borderBottomColor: "transparent",
  },
  activeTabHeader: {
    borderBottomWidth: verticalScale(2),
    borderBottomColor: "#00ff85",
  },
});
