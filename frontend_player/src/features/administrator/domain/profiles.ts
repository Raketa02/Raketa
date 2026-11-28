/**
 * **The profiles one account can switch between** — what the switcher lists, and which of them is
 * worn ([#518](https://github.com/Rakieta02/Rakieta/issues/518), PRD #500 stories 134–135; ADR-0185
 * §1, §3).
 *
 * **Player first, then one administrator profile per club**, in the server's order — Player only
 * for an account that acts as a player, since an account an Invitation opened has not asked to
 * play. *Profile* is the switcher's word, not a domain term (ADR-0185 §1).
 *
 * **The switcher is drawn only for an account with two or more**: a single profile has nothing to
 * switch to, and a chip that opens a list of one is a control that does nothing.
 */

import type { HeldProfiles, ProfileChoice } from '@/features/auth/types';

export type ProfileOption =
  /** The player profile, by the player's nickname — absent before the naming (ADR-0199 §1). */
  | { readonly kind: 'player'; readonly name: string | undefined }
  | { readonly kind: 'administrator'; readonly clubId: string; readonly clubName: string };

export function profileOptions(user: {
  readonly nickname?: string | undefined;
  readonly profiles: HeldProfiles;
}): readonly ProfileOption[] {
  const clubs = user.profiles.administers.map((club): ProfileOption => ({
    kind: 'administrator',
    ...club,
  }));
  return user.profiles.actsAsPlayer ? [{ kind: 'player', name: user.nickname }, ...clubs] : clubs;
}

/** Whether there is anything to switch to. */
export function switcherShown(options: readonly ProfileOption[]): boolean {
  return options.length > 1;
}

/** The profile an option is, as the phone keeps it. */
export function choiceOf(option: ProfileOption): ProfileChoice {
  return option.kind === 'player'
    ? { kind: 'player' }
    : { kind: 'administrator', clubId: option.clubId };
}

/** Whether this option is the profile the app wears now. */
export function isWorn(option: ProfileOption, worn: ProfileChoice): boolean {
  if (option.kind === 'player') return worn.kind === 'player';
  return worn.kind === 'administrator' && worn.clubId === option.clubId;
}
