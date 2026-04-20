import { colors } from "@/global/colors";
import { Language, languages } from "@/global/languages";
import { useState } from "react";
import { FlatList, Modal, Pressable, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { moderateScale, scale, verticalScale } from "react-native-size-matters";

interface Props {
  selectedLanguage: Language;
  onChange: (lang: Language) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function LanguagePicker({
  selectedLanguage,
  onChange,
  disabled,
  placeholder = "Select language",
}: Props) {
  const [modalVisible, setModalVisible] = useState(false);

  return (
    <View style={styles.container}>
      <Pressable
        style={[styles.dropdown, disabled && styles.dropdownDisabled]}
        onPress={() => !disabled && setModalVisible(true)}
      >
        <Text style={styles.dropdownText}>{selectedLanguage?.name ?? placeholder}</Text>
      </Pressable>

      <Modal visible={modalVisible} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Select Language</Text>
            <FlatList
              data={languages}
              keyExtractor={(item) => item.code}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.option}
                  onPress={() => {
                    onChange(item);
                    setModalVisible(false);
                  }}
                >
                  <Text style={[styles.optionText, item.code === selectedLanguage?.code && styles.optionSelected]}>
                    {item.name}
                  </Text>
                </TouchableOpacity>
              )}
            />
            <Pressable style={styles.closeBtn} onPress={() => setModalVisible(false)}>
              <Text style={styles.closeBtnText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

export const styles = StyleSheet.create({
  container: {
    marginBottom: 0,
  },
  dropdown: {
    paddingVertical: verticalScale(4),
    paddingHorizontal: scale(14),
    borderWidth: 1,
    borderColor: colors.gray[300],
    borderRadius: moderateScale(8),
    backgroundColor: colors.white,
  },
  dropdownDisabled: {
    backgroundColor: colors.gray[100],
  },
  dropdownText: {
    fontSize: moderateScale(16),
    color: colors.gray[800],
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContainer: {
    width: "85%",
    maxHeight: "70%",
    backgroundColor: colors.white,
    borderRadius: moderateScale(12),
    padding: moderateScale(16),
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: moderateScale(6),
    elevation: 6,
  },
  modalTitle: {
    fontSize: moderateScale(18),
    fontWeight: "600",
    marginBottom: verticalScale(12),
    color: colors.gray[800],
  },
  option: {
    paddingVertical: verticalScale(12),
    borderBottomWidth: 1,
    borderColor: colors.gray[200],
  },
  optionText: {
    fontSize: moderateScale(16),
    color: colors.gray[700],
  },
  optionSelected: {
    fontWeight: "bold",
    color: colors.gray[600],
  },
  closeBtn: {
    marginTop: verticalScale(12),
    alignSelf: "flex-end",
    paddingVertical: verticalScale(8),
    paddingHorizontal: scale(16),
  },
  closeBtnText: {
    fontSize: moderateScale(16),
    color: colors.gray[600],
  },
});
