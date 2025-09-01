import { ExpoAudioStreamModule } from "@siteed/expo-audio-studio";
import { isActiveState, RecorderState } from "@soniox/speech-to-text-web";
import React from "react";
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { moderateScale, scale, verticalScale } from "react-native-size-matters";
import { colors } from "../../global/colors";

interface RecordButtonProps {
  state: RecorderState;
  stopTranscription: () => void;
  startTranscription: () => void;
}

// Simple permission handling
const requestMicrophonePermission = async () => {
  try {
    const { status } = await ExpoAudioStreamModule.requestPermissionsAsync();
    if (status !== "granted") {
      throw new Error("Microphone permission denied");
    }
    return true;
  } catch (error) {
    console.error("Permission error:", error);
    Alert.alert("Permission Required", "Microphone permission is required to record audio.", [{ text: "OK" }]);
    return false;
  }
};

export default function RecordButton({ state, stopTranscription, startTranscription }: RecordButtonProps) {
  const isActive = isActiveState(state);
  const isFinishing = state === "FinishingProcessing";
  const isStarting = state === "OpeningWebSocket";

  const handleStartRecording = async () => {
    try {
      // Request permission first
      const hasPermission = await requestMicrophonePermission();
      if (!hasPermission) {
        return;
      }

      // Start transcription
      startTranscription();
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  };

  return (
    <View style={styles.container}>
      {!isStarting && isActive ? (
        <TouchableOpacity
          style={[styles.button, styles.stopButton, isFinishing && styles.disabledButton]}
          onPress={stopTranscription}
          disabled={isFinishing}
        >
          <Text style={styles.buttonText}>{isFinishing ? "Stopping..." : "Stop"}</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={[styles.button, styles.startButton]}
          onPress={handleStartRecording}
          disabled={isStarting}
        >
          {isStarting ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={colors.white} />
              <Text style={styles.buttonText}>Starting...</Text>
            </View>
          ) : (
            <Text style={styles.buttonText}>Start talking</Text>
          )}
        </TouchableOpacity>
      )}
    </View>
  );
}

export const styles = StyleSheet.create({
  container: {
    alignItems: "center",
  },
  button: {
    paddingHorizontal: scale(12),
    paddingVertical: verticalScale(8),
    borderRadius: moderateScale(8),
    alignItems: "center",
    marginBottom: verticalScale(4),
    minWidth: scale(120),
  },
  startButton: {
    backgroundColor: colors.soniox,
  },
  stopButton: {
    backgroundColor: colors.error,
  },
  disabledButton: {
    opacity: 0.5,
  },
  buttonText: {
    color: colors.white,
    fontSize: moderateScale(14),
    fontWeight: "600",
  },
  loadingContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: moderateScale(8),
  },
});
