/**
 * The tab tree. A `Stack` for now because there is one screen — the tab bar is a design
 * system primitive the onboarding slice has not reached, and an empty tab bar over a
 * single route would be chrome pretending to be navigation.
 */

import { Stack } from "expo-router";

export default function TabsLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
