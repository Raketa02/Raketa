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
    title: 'You',
  },
} as const;
