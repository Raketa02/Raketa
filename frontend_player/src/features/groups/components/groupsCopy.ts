/**
 * **The groups feature's fixed sentences** — every word a screen says that quotes no value. The
 * sentences that compose values (*11 members · Coach Andrzej approves joins*) are functions in
 * `groupsPresentation.ts`, beside this.
 *
 * **This module imports nothing, on purpose.** The feature barrels form a cycle — `groups` reads
 * `onboarding`'s sport names, `onboarding` reaches `auth`, `auth` the shell, and the shell draws
 * Groups — and a component that reads its copy at module load inside that cycle would read it
 * before it was defined. A module with no imports is fully evaluated the moment anything asks for
 * it, whichever way the cycle was entered.
 */

export const GROUPS_COPY = {
  list: {
    newGroup: '+ New',
    newGroupLabel: 'New group',
    join: 'Join',
    joinLabel: 'Join a group',
    empty: 'No groups yet — join or create one for the people you already play with',
  },
  newGroup: {
    title: 'New group',
    back: 'Back to Groups',
    name: 'Name',
    namePlaceholder: 'Give it any name…',
    homeClub: 'Home club',
    required: 'required',
    homeClubPlaceholder: 'Search clubs by name…',
    homeClubHint: 'Start typing a club’s name. Every club in Raketa is here.',
    /** Under the field until a club is chosen (play 6–10). */
    homeClubConsequence:
      'Every group lives at a club: its courts are where the app looks first for this group’s games.',
    noClubNote: 'Only clubs in Raketa can be a home club.',
    setAsHome: 'Set as home ›',
    groupAlreadyHere: 'group already here',
    change: 'Change',
    changeLabel: 'Change the home club',
    whoCanJoin: 'Who can join',
    anyone: 'Anyone',
    peopleIApprove: 'People I approve',
    noSportNote:
      'No sport to pick: the group plays whatever its members are rated in. Everybody sees the sports they play.',
    create: 'Create the group',
    creating: 'Creating the group',
    createNote:
      'You get a link to send to the WhatsApp crowd. When they finish getting rated, they land here.',
    created: 'Group created',
  },
  joinGroup: {
    title: 'Join a group',
    back: 'Back to Groups',
    field: 'Group, club or link',
    paste: 'Paste',
    pasteLabel: 'Paste a link',
    clearLabel: 'Clear the search',
    noGroupsHere: 'No groups here yet',
    nothingAtLink: 'Nothing at that link',
  },
  group: {
    back: 'Back to Groups',
    /** One code for *no such group* and *not one of yours* — both have one remedy. */
    refused: {
      group_not_found: 'This group isn’t one of yours.',
    },
  },
  action: {
    join: 'Join',
    ask: 'Ask to join',
    requested: 'requested · waiting',
    in: 'you’re in',
  },
  retry: 'Try again',
} as const;
