import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { moderateScale, verticalScale } from "react-native-size-matters";
import { getSpeakerColor } from "../../utils/speaker-colors";

interface SpeakerLabelProps {
  speakerNumber: string;
  style?: any;
}

export default function SpeakerLabel({ speakerNumber, style }: SpeakerLabelProps) {
  const color = getSpeakerColor(speakerNumber);
  return (
    <View style={[styles.container, style]}>
      <Text style={[styles.label, { color }]}>Speaker {speakerNumber}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: verticalScale(8),
    width: "100%",
  },
  label: {
    fontSize: moderateScale(12),
    fontWeight: "600",
    textTransform: "uppercase",
  },
});
