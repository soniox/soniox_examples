import LanguageBadge from "@/components/common/language-badge";
import { Token } from "@soniox/speech-to-text-web";
import React, { useCallback, useMemo, useRef, useState } from "react";
import { FlatList, NativeScrollEvent, NativeSyntheticEvent, StyleSheet, Text, View } from "react-native";
import { moderateScale, verticalScale } from "react-native-size-matters";
import { colors } from "../../global/colors";
import SpeakerLabel from "../common/speaker-label";

export interface TokenBlock {
  speaker: string;
  language?: string;
  tokens: Token[];
  id: string;
}

// We group tokens together based on their speaker and language. This is done
// for performance benefits.
export function groupTokensIntoBlocks(tokens: Token[], idPrefix = "final", idOffset = 0): TokenBlock[] {
  if (!tokens.length) return [];

  const blocks: TokenBlock[] = [];
  let current: TokenBlock | null = null;

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    const speaker = token.speaker || "UNKNOWN";

    if (!current || current.speaker !== speaker || current.language !== token.language) {
      // Create new TokenBlock if speaker or language changes

      if (current) blocks.push(current);
      const id: string = `${idPrefix}-${i + idOffset}-${speaker}-${token.language ?? ""}`;
      current = { speaker, language: token.language, tokens: [token], id };
    } else {
      // If no new speaker or language append tokens to last block

      current.tokens.push(token);
    }
  }

  if (current) blocks.push(current);
  return blocks;
}

// Merge finalTokens and nonFinalTokens into renderable objects. We need to
// generate keys/ids smartly so react-native won't rerender tokens that didn't
// and won't change -- they are final.
export function mergeTokensIntoDisplayBlocks(finalTokens: Token[], nonFinalTokens: Token[]): TokenBlock[] {
  const finalBlocks = groupTokensIntoBlocks(finalTokens);
  if (!nonFinalTokens.length) return finalBlocks;

  const lastFinal = finalBlocks[finalBlocks.length - 1];
  const nonFinalSpeaker = nonFinalTokens[0].speaker || "UNKNOWN";
  const nonFinalLanguage = nonFinalTokens[0].language || "UNKNOWN";

  // If non-final continues the last final block (same speaker and same language),
  // reuse that block's id (no remount)
  if (lastFinal && lastFinal.speaker === nonFinalSpeaker && lastFinal.language === nonFinalLanguage) {
    return [
      ...finalBlocks.slice(0, -1),
      { ...lastFinal, tokens: [...lastFinal.tokens, ...nonFinalTokens], id: lastFinal.id },
    ];
  }

  // Otherwise create one or more non-final blocks. Use offset so their ids
  // don't collide with final block ids (offset by finalTokens.length).
  const nonfinalBlocks = groupTokensIntoBlocks(nonFinalTokens, "nonfinal", finalTokens.length);
  return [...finalBlocks, ...nonfinalBlocks];
}

type TokenRendererProps = {
  tokens: Token[];
};

export const TokenRenderer = React.memo(function TokenRenderer({ tokens }: TokenRendererProps) {
  // Memoize rendered tokens for performance; only re-render if tokens array changes
  const rendered = useMemo(() => {
    let lastLanguage: string | null = null;

    return tokens.map((token, idx) => {
      const isFinal = token.is_final ?? true;

      const showLanguageBadge = token.language && token.language !== lastLanguage;
      if (showLanguageBadge) lastLanguage = token.language!;

      const textStyle =
        token.text === "<end>" ? styles.endToken : isFinal ? styles.finalTokenText : styles.nonFinalTokenText;

      return (
        <Text key={idx} style={textStyle}>
          {showLanguageBadge && <LanguageBadge language={token.language!} />}
          {token.text}
        </Text>
      );
    });
  }, [tokens]);

  return <Text>{rendered}</Text>;
});

type RendererProps = {
  finalTokens: Token[];
  nonFinalTokens: Token[];
};

export function Renderer({ finalTokens, nonFinalTokens }: RendererProps) {
  const flatListRef = useRef<FlatList<TokenBlock>>(null);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  const blocks = useMemo(
    () => mergeTokensIntoDisplayBlocks(finalTokens, nonFinalTokens),
    [finalTokens, nonFinalTokens],
  );

  const scrollToBottom = useCallback(() => {
    if (!autoScrollEnabled || !blocks.length) return;
    try {
      flatListRef.current?.scrollToIndex({ index: blocks.length - 1, animated: true });
    } catch {
      flatListRef.current?.scrollToEnd({ animated: true });
    }
  }, [autoScrollEnabled, blocks.length]);

  const handleScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, layoutMeasurement, contentSize } = e.nativeEvent;
    const distanceFromBottom = contentSize.height - (contentOffset.y + layoutMeasurement.height);
    setAutoScrollEnabled(distanceFromBottom < 50);
  };

  const renderBlock = useCallback(({ item }: { item: TokenBlock }) => {
    const isEndOnlyBlock = item.tokens.every((t) => t.text === "<end>");
    return (
      <View>
        {!isEndOnlyBlock && <SpeakerLabel speakerNumber={item.speaker} />}
        <TokenRenderer tokens={item.tokens} />
      </View>
    );
  }, []);

  return (
    <FlatList
      ref={flatListRef}
      data={blocks}
      keyExtractor={(item) => item.id}
      renderItem={renderBlock}
      onContentSizeChange={scrollToBottom}
      onLayout={scrollToBottom}
      onScroll={handleScroll}
      scrollEventThrottle={16}
      windowSize={21}
      initialNumToRender={10}
      removeClippedSubviews
      maxToRenderPerBatch={10}
      updateCellsBatchingPeriod={50}
    />
  );
}

export const styles = StyleSheet.create({
  blockContent: {
    textAlign: "left",
    marginTop: verticalScale(4),
    fontSize: moderateScale(16),
    lineHeight: verticalScale(24),
    color: colors.gray[800],
  },
  finalTokenText: {
    color: colors.gray[800],
  },
  nonFinalTokenText: {
    color: colors.gray[500],
    fontStyle: "italic",
  },
  endToken: {
    fontSize: moderateScale(12),
    color: colors.gray[400],
    fontStyle: "italic",
  },
});
