/**
 * What the explainer says, once, for both surfaces that show it.
 *
 * `ADR-0061` requires the permission to be **explained** rather than merely
 * asked, and it names the two controls: *Turn on* and *Not now*. Everything
 * below is this app's own copy — nothing here is keyed on a wire code, so
 * `ADR-0075`'s completeness typecheck has nothing to hold and none is faked.
 *
 * **Four claims, and each one is true of the build that ships them.** That is
 * the constraint this copy was written under rather than a description of it:
 *
 * - The travel figure is **not** mentioned, although `ADR-0062` fixes the line
 *   as *sport, time and travel time*. Nothing can supply a travel time in v1 —
 *   no player has an anchor to measure one from
 *   ([#129](https://github.com/Raketa02/Raketa/issues/129)) — so a screen
 *   promising *how far away it is* would be promising a clause the sentence
 *   cannot print.
 * - **Standby is not mentioned either**, although the loudness rule is entirely
 *   about it: only a seat she asked for buzzes (`ADR-0065`). Nothing in this
 *   build joins a queue, so *queue for a match and we will buzz you* describes
 *   an act she cannot take.
 * - What replaces both is the rule that **is** true of every message this build
 *   can send: one line at a time, which is `ADR-0062`'s collapse rule and the
 *   whole of the frequency control in v1.
 * - The last card is the one the whole screen exists to make believable, and it
 *   is a **behaviour** rather than a reassurance: refusing costs her the message
 *   and never the card, and nothing on Now reads permission to make it so.
 */

/** The heading, on the onboarding screen and on the sheet alike. */
export const EXPLAINER_TITLE = 'When a seat opens up';

export const EXPLAINER_EYEBROW = 'Raketa';

export interface ExplainerPoint {
  readonly title: string;
  readonly body: string;
}

export const EXPLAINER_POINTS: readonly ExplainerPoint[] = [
  {
    title: 'Matches lose players at short notice',
    body: 'When somebody drops out of a match at your level, the seat goes to whoever takes it first. That is usually decided in minutes, and usually while you are doing something else.',
  },
  {
    title: 'One line, and never the venue',
    body: 'The sport and when it starts. Never the club — a lock screen gets read over shoulders, and where you are going to be is the part of it that is nobody else’s business.',
  },
  {
    title: 'One at a time, not a pile',
    body: 'A new seat replaces the last message rather than stacking beside it. However many seats open this week, there is one line from us on your phone.',
  },
  {
    title: 'Saying no costs you nothing here',
    body: 'Every seat you could take is on your Now screen either way. This only decides whether your phone tells you before you look.',
  },
] as const;

/** The control that spends the OS prompt. **The only one that does.** */
export const TURN_ON_LABEL = 'Turn on';

export const TURN_ON_HINT = 'Asks your phone for permission to send notifications';

/** The control that spends nothing. */
export const NOT_NOW_LABEL = 'Not now';

export const NOT_NOW_HINT = 'Continues without notifications. Your phone is not asked anything.';

/** Named for what it dismisses, never bare "Close" — see `CloseControl`. */
export const SHEET_CLOSE_LABEL = 'Close, and continue without notifications';
