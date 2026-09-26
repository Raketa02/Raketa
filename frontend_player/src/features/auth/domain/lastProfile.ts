/**
 * **Which profile the account wears** — Player, or the Administrator of one club — and how the
 * phone keeps the last one ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, [ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §3, [#518](https://github.com/Raketa02/Raketa/issues/518)).
 *
 * *Profile* is the switcher's word and UI vocabulary, not a domain term (ADR-0185 §1): a **Player
 * profile** is an aggregate, and this is not it. Switching is client state, never a new token — the
 * administrator's authority is re-read by the server on every request — so what the phone keeps is
 * only *which hat the app had on*, and **Player is the default** for an account that has chosen
 * nothing.
 */

export type ProfileChoice =
  { readonly kind: 'player' } | { readonly kind: 'administrator'; readonly clubId: string };

export const PLAYER_PROFILE: ProfileChoice = { kind: 'player' };

const PLAYER = 'player';
const ADMINISTRATOR = 'administrator:';

/** How a choice is written on the phone — one short string, whose club part is an id. */
export function savedProfile(choice: ProfileChoice): string {
  return choice.kind === 'player' ? PLAYER : `${ADMINISTRATOR}${choice.clubId}`;
}

/**
 * **What was saved, read back** — or nothing, for a value this build does not recognise, which is
 * the default (ADR-0188 §4). Whether an administrator profile read back is still *held* is the
 * gate's question, against what the account holds now; this only reads the phone's string.
 */
export function profileChoiceFrom(saved: string | undefined): ProfileChoice | undefined {
  if (saved === PLAYER) return PLAYER_PROFILE;
  if (saved?.startsWith(ADMINISTRATOR) === true) {
    const clubId = saved.slice(ADMINISTRATOR.length);
    return clubId === '' ? undefined : { kind: 'administrator', clubId };
  }
  return undefined;
}
