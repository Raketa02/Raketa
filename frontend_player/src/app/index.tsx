/**
 * A placeholder, and deliberately so — routing, sessions and the onboarding flow arrive
 * in later slices. It exists to prove the launch path end to end: config validated,
 * both font families loaded, the splash gone, a themed screen on top.
 *
 * It shows the resolved config because a wrong `EXPO_PUBLIC_API_URL` is the single most
 * common reason a device build talks to nothing — and on a phone, `localhost` is the
 * phone. These are public config values, never secrets.
 */

import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { getEnv } from "@/shared/config/env";
import { theme } from "@/shared/ui/theme";

export default function PlaceholderRoute() {
  const env = getEnv();

  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <View style={s.content}>
        <Text style={s.eyebrow}>Player app</Text>
        <Text style={s.title}>Rakieta</Text>
        <Text style={s.body}>
          The app boots. Routing, sessions and onboarding arrive in later slices.
        </Text>

        <View style={s.rows}>
          <Row label="Environment" value={env.environment} />
          <Row label="API" value={env.apiUrl} />
        </View>
      </View>
    </SafeAreaView>
  );
}

function Row({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <Text style={s.rowValue} numberOfLines={1}>
        {value}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.color.paper,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.xs,
  },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: "uppercase",
  },
  title: {
    ...theme.type.h1,
    color: theme.color.ink,
  },
  body: {
    ...theme.type.tiny,
    color: theme.color.muted,
  },
  rows: {
    marginTop: theme.space.md,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.sm,
    gap: theme.space.xxs,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: theme.space.md,
  },
  rowLabel: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
  },
  rowValue: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.ink,
    flexShrink: 1,
  },
});
