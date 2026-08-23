/**
 * Every query key this feature uses, in one factory.
 *
 * Keyed on the match, because the answer is about one match and one viewer. There
 * is no list key and no `all` beneath it that anything invalidates: a departure
 * corrects **Now** through `ADR-0074`'s update, and correcting this screen is what
 * the write's own response does — it hands back its own answer and the screen
 * writes it, rather than marking itself stale and asking again.
 */

export const departureKeys = {
  all: ['departure'] as const,
  screen: (matchId: string) => [...departureKeys.all, 'screen', matchId] as const,
};
