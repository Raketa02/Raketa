/** **Every sentence the Groups page and the Hand over page say** (club mocks 15–16). */

import { sentenceAbout, type RefusalAbout } from '@/ui/forms';

export const GROUPS_COPY = {
  caption: (club: string) => `Official groups at ${club}`,
  madeInTheApp: 'Created by your administrators in the app',
  none: 'No official groups yet. Your administrators create them in the Raketa app.',
  columns: {
    group: 'Group',
    administrator: 'Administrator',
    players: 'Players',
    fromWhatsApp: 'From WhatsApp',
    games: 'Games',
  },
  needsAdministrator: 'needs an administrator',
  waiting: (count: number) => `${count} waiting`,
  fromWhatsApp: (players: number, size: number, percent: number) =>
    `${players} of ${size} · ${percent}%`,
  handOver: {
    title: 'Hand over',
    caption: 'Hand over',
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
      'Its link, who can join and its WhatsApp size stay as they are.',
    confirm: {
      title: (group: string, to: string) => `Hand ${group} over to ${to}?`,
      lead: (to: string, from: string | null) =>
        `${to} answers its join requests from now on` +
        (from === null ? '.' : `, and ${from} stops seeing it in the app.`) +
        ' Its players, its link and who can join stay as they are.',
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
