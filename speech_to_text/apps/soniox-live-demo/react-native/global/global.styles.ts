import { StyleSheet } from "react-native";
import { moderateScale, scale, verticalScale } from "react-native-size-matters";
import { colors } from "./colors";

export const globalStyles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "flex-start",
  },
  container: {
    flex: 1,
    marginTop: 0,
    marginBottom: 0,
    alignSelf: "center",
    width: "100%",
    maxWidth: scale(900),

    // show a few pixels of gradient on left/right
    marginHorizontal: moderateScale(8),

    // squared look
    backgroundColor: colors.white,
    borderRadius: moderateScale(6),
    paddingTop: verticalScale(12),
    paddingHorizontal: moderateScale(12),
    paddingBottom: 0,

    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
  },

  // Pickers
  pickerHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    marginBottom: verticalScale(12),
    gap: moderateScale(8),
  },
  pickerLabel: {
    fontSize: moderateScale(16),
    fontWeight: "600",
    color: colors.gray[800],
  },
  pickerBold: {
    fontWeight: "900",
    color: colors.gray[800],
  },

  // Cards
  card: {
    flex: 1,
    backgroundColor: "transparent",
    borderRadius: 0,
    marginBottom: 4,
    padding: 0,
  },
  cardTitle: {
    fontSize: moderateScale(14),
    color: colors.gray[700],
    marginBottom: verticalScale(8),
    fontWeight: "600",
  },
  cardInner: {
    flex: 1,
    width: "100%",
    paddingBottom: 0,
  },
});
