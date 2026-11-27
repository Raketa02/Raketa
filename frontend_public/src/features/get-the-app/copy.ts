/**
 * **The way in's words.** *Open in Rakieta* is the ADR's own name for the button (ADR-0187 §4),
 * and names the app as a mock sentence would (§8, which ADR-0211 respells *Rakieta*).
 */
export const GET_THE_APP_COPY = {
  /** What a screen reader calls the two store buttons. */
  stores: 'Get the app',
  appStore: 'App Store',
  googlePlay: 'Google Play',
  openInRakieta: 'Open in Rakieta',
} as const;
