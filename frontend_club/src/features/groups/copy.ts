/**
 * **Every sentence the Groups page and a group's page say** (club mocks 15–16, and 20's request
 * card).
 */

import { sportName } from '@/features/club-details/mappers';
import { SETTINGS_COPY } from '@/features/raketa-settings/copy';
import { sentenceAbout, type RefusalAbout } from '@/ui/forms';

import type { SportLevel } from './mappers';

export const GROUPS_COPY = {
  caption: (club: string) => `Official groups at ${club}`,
  madeInTheApp: 'Created by your administrators in the app',
  none: 'No official groups yet. Your administrators create them in the Raketa app.',
  columns: {
    group: 'Group',
    administrator: 'Administrator',
    players: 'Players',
    fromOriginalGroup: 'From original group',
    games: 'Games',
  },
  /**
   * The line over the table: whether the groups are offered other clubs' courts, which they are
   * by default, and then only at an hour the club's own are full (B8, Q128). On, it is the
   * setting's own help line.
   */
  otherClubs: {
    /** The line up to its link: whether they are offered, and the way to change it. */
    lead: (offered: boolean, km: number) =>
      offered
        ? `${SETTINGS_COPY.otherClubs.hint(km)} Change it in`
        : "Your groups are offered only your courts. Offer other clubs' courts in",
    settings: 'Raketa settings',
    end: '.',
  },
  needsAdministrator: 'needs an administrator',
  waiting: (count: number) => `${count} waiting`,
  fromOriginalGroup: (players: number, size: number, percent: number) =>
    `${players} of ${size} · ${percent}%`,
  page: {
    title: 'Official group',
    caption: 'Official group',
  },
  /** Somebody asking to join, whom the club answers whoever runs the group (ADR-0191 §1). */
  requests: {
    title: (count: number) => `Want to join · ${count}`,
    runBy: (name: string) => `${name} answers them in the app, and you can answer them here too.`,
    nobody:
      'Nobody runs this group right now, so they wait for you. Answer them here, or hand the ' +
      'group over below.',
    explain: 'Approve lets them in at once. Decline tells them nothing, and they can ask again.',
    /** Somebody whose account reads as nobody: the club's one fallback (ADR-0199 §5). */
    unnamed: 'A player',
    unrated: 'Not rated in any sport yet',
    approve: 'Approve',
    decline: 'Decline',
    /** Each button, spoken with whom it answers: a list of them all says *Approve*. */
    approveWho: (name: string) => `Approve ${name}`,
    declineWho: (name: string) => `Decline ${name}`,
  },
  handOver: {
    administrator: 'Administrator',
    to: 'Hand it over to',
    /** With nobody to choose: nobody at all, or nobody else when somebody runs it already. */
    nobody: (somebodyRunsIt: boolean) =>
      `There is nobody ${somebodyRunsIt ? 'else ' : ''}to give it to yet. Only an ` +
      'administrator who has accepted their invitation can run a group.',
    inviteFirst: 'Invite an administrator first',
    cancel: 'Cancel',
    submit: 'Hand over',
    submitting: 'Handing over…',
    explain:
      'The new administrator answers its join requests from now on, the waiting ones included. ' +
      'Its link, who can join and its group size stay as they are.',
    confirm: {
      title: (group: string, to: string) => `Hand ${group} over to ${to}?`,
      lead: (to: string, from: string | null) =>
        `${to} answers its join requests from now on` +
        (from === null ? '.' : `, and ${from} stops seeing it in the app.`) +
        ` Raketa tells ${to} in the app. Its players, its link and who can join stay as they are.`,
      cancel: 'Cancel',
      submit: 'Hand over',
    },
  },
} as const;

/** The refusals a handover can meet, said about the person it was for. */
const HAND_OVER_REFUSALS: Readonly<Record<string, (name: string) => string>> = {
  administrator_not_active: (name) =>
    `${name} isn't one of your active administrators any more. Choose someone else.`,
  group_not_found: () => "This group isn't one of your official groups any more.",
};

/** The sentence for a handover's refusal: about the person, or one every form can meet. */
export function handOverRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, HAND_OVER_REFUSALS);
}

/**
 * *Padel 2,44 · Tennis 2,60*: every sport somebody is rated in, with the Level written the way
 * the app writes one, two places after a comma.
 */
export function levelsLine(levels: readonly SportLevel[]): string {
  if (levels.length === 0) return GROUPS_COPY.requests.unrated;
  return levels
    .map(({ sport, level }) => `${sportName(sport)} ${level.toFixed(2).replace('.', ',')}`)
    .join(' · ');
}

/** The refusals an answer can meet, said about the person it was for. */
const ANSWER_REFUSALS: Readonly<Record<string, (name: string) => string>> = {
  join_request_not_found: (name) => `${name} isn't waiting any more: somebody answered first.`,
  group_not_found: () => "This group isn't one of your official groups any more.",
};

/** The sentence for an answer's refusal: about the person, or one every form can meet. */
export function answerRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, ANSWER_REFUSALS);
}
