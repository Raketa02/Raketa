/**
 * **The administrator area's fixed sentences** — every word a screen says that quotes no value.
 * The sentences that compose values (*1 waiting*, *3 members*) are
 * functions in `administratorPresentation.ts`, beside this.
 *
 * Taken from the club mocks (club 8–11, 17–20), their *Rakieta* read as written (ADR-0211).
 *
 * **This module imports nothing, on purpose** — `groupsCopy.ts`'s reason: the feature barrels form
 * a cycle, and a module with no imports is fully evaluated the moment anything asks for it,
 * whichever way the cycle was entered.
 */

export const ADMINISTRATOR_COPY = {
  groups: {
    title: 'Groups',
    newGroup: '+ New official group',
    newGroupLabel: 'New official group',
    emptyTitle: 'No official groups yet',
    emptyLine: 'Make one for each WhatsApp group you run, then post its link there.',
    groupHint: 'Opens the group',
  },
  newGroup: {
    title: 'New official group',
    back: 'Back to Groups',
    namePlaceholder: 'Same name as the WhatsApp group',
    homeClub: 'Home club',
    /** The group's size, not its WhatsApp group's: the crowd gathers anywhere (#529). */
    size: 'Group size',
    sizePlaceholder: 'How many are in it?',
    sports: 'Sports',
    create: 'Create the group',
    creating: 'Creating the group',
    created: 'Group created',
  },
  group: {
    back: 'Back to Groups',
    /** The link card's two doors — no *posted* tag and no *Post again* (PRD #500). */
    share: 'Share link',
    copy: 'Copy link',
    /** The members card's hint: the card is the door to Members. */
    membersHint: 'Opens Members',
    /** One code for every group that is not theirs — a colleague's, another club's, none. */
    refused: {
      group_not_found: 'This isn’t a group you run.',
    },
    /** Members, opened from the page — so a refusal means the group was handed on since. */
    membersRefused: {
      group_not_found: 'This isn’t a group you run any more.',
    },
  },
  you: {
    /** The header's title where the account has no nickname — one that has not started playing. */
    title: 'You',
    /** The group of one row per official group, each opening its settings. */
    groups: 'Group settings',
    /** The group holding *Start playing*, for an account that does not play yet. */
    playing: 'Playing',
    startPlaying: 'Start playing',
    startPlayingLine: 'Get a Skill rating, then find people to play with',
  },
  /**
   * **The profile switcher** (club 6–7, #518) — the chip in each profile's You header, and the sheet
   * it opens: one row per profile the account holds, the one worn ticked.
   */
  switcher: {
    /** The chip's name, ahead of the profile it shows now. */
    chip: 'Switch profile',
    /** No mock titles the sheet; a sheet is a real modal, and its heading is where focus lands. */
    title: 'Your profiles',
    /** The sheet's close keeps the profile worn — named by what it keeps, never just *Close*. */
    close: 'Keep this profile',
    player: 'Player',
    administrator: 'Administrator',
  },
  /**
   * **The invitation sheet** (club 5, #518) — a club offering an account that already exists the
   * administrator profile, on launch. The title and the body are functions of the club and of what
   * the account holds, in `administratorPresentation`.
   */
  invitation: {
    accept: 'Accept',
    accepting: 'Accepting the invitation',
    notNow: 'Not now',
    /** The sheet's close sets it aside too — named by what it does, never just *Close*. */
    close: 'Decide later',
    /** The one button left once the invitation has gone — nothing to decide later. */
    done: 'OK',
  },
  /**
   * **The handover sheet** (ADR-0192 §2) — a club telling this account it handed it a group. Nothing
   * is asked of the person, so the sheet's one choice is where to go: the group, or nowhere. The
   * title and the body are functions of the club and the groups, in `administratorPresentation`.
   */
  handover: {
    /** One group handed: straight to its page, where its requests wait. */
    openGroup: 'Open the group',
    /** Several handed at once: the Groups tab, where each now has a card. */
    openGroups: 'See your groups',
    gotIt: 'Got it',
    /** The close does what *Got it* does, under its own name — two controls, two names. */
    close: 'Dismiss',
  },
  /** An official group's settings, opened from its row on the You tab (#517). */
  settings: {
    title: 'Group settings',
    back: 'Back to You',
    save: 'Save',
    saved: 'Saved',
    saving: 'Saving the settings',
    /** One code for every group that is not theirs — a colleague's, another club's, none. */
    refused: {
      group_not_found: 'This isn’t a group you run any more.',
    },
  },
} as const;
