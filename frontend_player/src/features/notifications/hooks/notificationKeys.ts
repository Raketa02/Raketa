/**
 * **The notifications feature's query keys** — the three choices, which the You tab's row and the
 * screen both read and a tap writes; the recent list behind Home's bell, which a push arriving
 * re-reads; and two answers the phone gives rather than the server — whether it may show a notice,
 * and nothing else (#559).
 *
 * The permission is held here, beside the reads, for the reason the phone's preferences are: the
 * screen's *Allow notifications* and the registration under the tabs read one answer, and the app
 * re-reads it on every return to the foreground — a player who switched it on in Settings meanwhile
 * is pushed from that moment. A sign-out clears it with everything else.
 */

export const notificationKeys = {
  all: ['notifications'] as const,
  /** `GET /players/me/notifications`. */
  choices: () => [...notificationKeys.all, 'choices'] as const,
  /** `GET /players/me/notices` — the list behind the bell. */
  notices: () => [...notificationKeys.all, 'notices'] as const,
  /** The phone's answer: may this app show a notice. */
  permission: () => [...notificationKeys.all, 'permission'] as const,
};
