import type { LinkedGroup, Sport } from './mappers';

/** **The group page's words.** The separator is the mocks' middle dot, as the app's. */

const DOT = ' · ';

export const GROUP_PAGE_COPY = {
  /** What a screen reader calls the list of sports. */
  sports: 'Sports',
  /**
   * Where somebody without the app puts the link once they have it (#500 story 47). *Play › Join*
   * is one place in the app, so it never breaks across lines.
   */
  pasteInstruction: 'After you sign up, paste this link in Play › Join',
} as const;

const SPORT_NAMES: Readonly<Record<Sport, string>> = {
  padel: 'Padel',
  tennis: 'Tennis',
  squash: 'Squash',
  badminton: 'Badminton',
};

/** *Padel*: a sport as a person names it. */
export function sportName(sport: Sport): string {
  return SPORT_NAMES[sport];
}

/** *Ogrody 33 · Grzegórzki*: where the group plays. */
export function whereItPlays(club: LinkedGroup['club']): string {
  return `${club.name}${DOT}${club.district}`;
}

/** *11 members*, and *1 member*. */
export function membersLine(count: number): string {
  return count === 1 ? '1 member' : `${count} members`;
}

/**
 * *Ogrody 33 · Grzegórzki · Padel, Tennis · 11 members*: the line a messenger draws under the
 * group's name. A group nobody is rated in yet has no sports to say.
 */
export function previewLine(group: LinkedGroup): string {
  const sports = group.sports.map(sportName).join(', ');
  return [whereItPlays(group.club), sports, membersLine(group.memberCount)]
    .filter((part) => part !== '')
    .join(DOT);
}
