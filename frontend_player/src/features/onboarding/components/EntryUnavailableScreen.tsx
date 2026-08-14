/**
 * The gate could not be read.
 *
 * There is no safe default to fall through to: sending an unrated player into the app
 * skips onboarding entirely, and sending a rated one into onboarding re-rates a sport
 * they have already proved. Both are worse than saying so and offering the retry.
 *
 * This is the launch screen a player on a dead connection sees, so it says what happened
 * and nothing else.
 */

import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import type { AppError } from "@/shared/errors";
import { Button, Note, theme } from "@/shared/ui";

import { onboardingErrorMessage } from "./onboardingErrorMessage";

export interface EntryUnavailableScreenProps {
  readonly error: AppError;
  readonly onRetry: () => void;
}

export function EntryUnavailableScreen({ error, onRetry }: EntryUnavailableScreenProps) {
  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <View style={s.content}>
        <Text style={s.title} accessibilityRole="header">
          We couldn&apos;t pick up where you left off
        </Text>
        <Note variant="coral" accessibilityRole="alert">
          {onboardingErrorMessage(error)}
        </Note>
        <Button label="Try again" size="lg" onPress={onRetry} />
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.md,
  },
  title: { ...theme.type.h1, color: theme.color.ink },
});
