/**
 * **The administrator area's fixed sentences** — every word a screen says that quotes no value.
 * The sentences that compose values (*Ogrody 33 · Administrator*, *1 waiting*, *7 Sep*) are
 * functions in `administratorPresentation.ts`, beside this.
 *
 * Taken from the club mocks (club 8–11, 17–20), with *Rakieta* read as **Raketa** (ADR-0187 §8).
 *
 * **This module imports nothing, on purpose** — `groupsCopy.ts`'s reason: the feature barrels form
 * a cycle, and a module with no imports is fully evaluated the moment anything asks for it,
 * whichever way the cycle was entered.
 */

export const ADMINISTRATOR_COPY = {
  /** The area's role, after the club's name in every header's eyebrow (club 17). */
  role: 'Administrator',
  /** An official group's page eyebrow, after the club's name (club 11, 18). */
  official: 'Official',
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
    whatsAppSize: 'WhatsApp group size',
    whatsAppSizePlaceholder: 'How many are in it?',
    sports: 'Sports',
    create: 'Create the group',
    creating: 'Creating the group',
    created: 'Group created',
  },
  group: {
    back: 'Back to Groups',
    /** Club 11's link card, always — no *posted* tag and no *Post again* (PRD #500). */
    linkLine: 'Post this in the WhatsApp group. Everybody who taps it lands here.',
    post: 'Post to WhatsApp',
    copy: 'Copy link',
    /** The players card's policy half (club 11). */
    anyoneJoins: 'anyone with the link joins',
    youApprove: 'you approve joins',
    thisWeek: 'this week',
    /** One code for every group that is not theirs — a colleague's, another club's, none. */
    refused: {
      group_not_found: 'This isn’t a group you run.',
    },
  },
  you: {
    /** The header's title where the account's name has not been read — it always has one here. */
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
