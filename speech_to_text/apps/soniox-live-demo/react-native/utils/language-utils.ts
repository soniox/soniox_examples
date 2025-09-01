import { getLanguage, languages } from "../global/languages";

// Helper function to safely get the language name.
// Returns the original code if the name can't be found.
export const getLanguageName = (code: string): string => {
  if (!code) return "";
  const found = getLanguage(code);
  return found?.name ?? code;
};

// Expose the languages list for UI usage where needed
export { languages };
