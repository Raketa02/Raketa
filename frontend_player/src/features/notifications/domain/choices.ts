/**
 * **The three notices a player chooses** (#559; the screens A7.2; the mechanics §17.2) — *You
 * complete it* and *Challenges for you* on, *Fill in alerts* off, until changed. The seven always
 * on are no choice, and are not here: they are words on the screen and nothing else.
 *
 * Every tap saves all three (`PUT /players/me/notifications` replaces them), so what a tap leaves
 * is computed whole here, from the three as the last tap left them.
 */

export type ChoiceKey = 'youCompleteIt' | 'challengesForYou' | 'fillInAlerts';

/** The three, in the screen's order (mock 53). */
export const CHOICES = [
  'youCompleteIt',
  'challengesForYou',
  'fillInAlerts',
] as const satisfies readonly ChoiceKey[];

export type NotificationChoices = Readonly<Record<ChoiceKey, boolean>>;

/** The choices that are on, in the screen's order — the row's line (mock 50). */
export function choicesOn(choices: NotificationChoices): readonly ChoiceKey[] {
  return CHOICES.filter((key) => choices[key]);
}

/** One tap: this choice the other way, the rest as they were. */
export function switched(choices: NotificationChoices, key: ChoiceKey): NotificationChoices {
  return { ...choices, [key]: !choices[key] };
}
