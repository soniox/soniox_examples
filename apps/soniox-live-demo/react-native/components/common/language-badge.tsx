import React from "react";
import { Text, View } from "react-native";
import { moderateScale, scale, verticalScale } from "react-native-size-matters";
import { TextStyle } from "react-native/Libraries/StyleSheet/StyleSheetTypes";
import { colors } from "../../global/colors";
import { getLanguageName } from "../../utils/language-utils";

interface LanguageBadgeProps {
  language: string;
}

export default function LanguageBadge({ language }: LanguageBadgeProps) {
  return (
    <View style={styles.wrapper}>
      <View style={styles.container}>
        <Text style={styles.text}>{getLanguageName(language)}</Text>
      </View>
      <View style={styles.space} />
    </View>
  );
}

const styles = {
  wrapper: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: scale(4),
  },
  container: {
    backgroundColor: colors.gray[200],
    paddingHorizontal: scale(8),
    paddingTop: verticalScale(2),
    paddingBottom: verticalScale(3),
    borderRadius: moderateScale(12),
    transform: [{ translateY: verticalScale(3) }],
  },
  text: {
    fontSize: moderateScale(10),
    lineHeight: verticalScale(12),
    color: colors.gray[600],
    fontWeight: "500" as TextStyle["fontWeight"],
  },
  space: {
    width: scale(4),
  },
};
