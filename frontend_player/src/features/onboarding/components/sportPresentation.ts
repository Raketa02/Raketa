/**
 * A sport's name and its identity colour — the two things the wire does not carry.
 *
 * `SportResource` describes how a sport is *played and sold* (player count, bookable
 * durations); what it is called in this locale and what colour it wears are presentation,
 * and presentation is the client's.
 *
 * Sport identity deliberately reuses the semantic palette rather than extending it: four
 * more hues would make every screen with a sport dot noisier, and the dot always sits
 * beside the sport's name in text. **A fifth sport forces a real decision** — and until
 * that decision is made, the domain's closed set and the theme's keys are the same four,
 * so a sport that reached one without the other fails `pnpm typecheck`.
 */

import { theme } from "@/shared/ui";

import type { Sport } from "../domain/Sport";

const LABELS: Readonly<Record<Sport, string>> = {
  padel: "Padel",
  tennis: "Tennis",
  squash: "Squash",
  badminton: "Badminton",
};

export function sportLabel(sport: Sport): string {
  return LABELS[sport];
}

export function sportColour(sport: Sport): string {
  return theme.sport[sport];
}
