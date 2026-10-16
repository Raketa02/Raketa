/**
 * **Every sentence Raketa settings says** (the screens B5; the settings and their defaults, the
 * mechanics §16.6; leaving, §16.15).
 */

import type { NumberField } from './schemas';

export const SETTINGS_COPY = {
  caption: 'How your club sells its courts through Raketa',
  title: 'Raketa settings',
  numbers: {
    release_lead_days: {
      label: 'Release lead',
      hint: 'Days before a game that an hour still unsold comes back to you. 1 to 13; 3 by default.',
    },
    cut_off_hours: {
      label: 'Free-cancellation cut-off',
      hint:
        'Hours before a game until which players leave for free; a game still short then is ' +
        'called off. 0 to 72; 24 by default.',
    },
    other_clubs_courts: {
      label: 'Distance',
      hint: 'Kilometres from your club. 1 to 50; 10 by default.',
    },
  } satisfies Record<NumberField, { label: string; hint: string }>,
  otherClubs: {
    label: "Offer our groups other clubs' courts when ours are full",
    hint:
      "Only when your courts have no hour your groups' players share in the next 14 days. Your " +
      'own courts always come first.',
  },
  paused: {
    label: 'Pause Raketa bookings',
    hint:
      'No new games are built on your courts. Games already booked are played as booked, and ' +
      'games still filling can book until their book-by.',
  },
  confirm: 'Confirm settings',
  confirming: 'Confirming…',
  save: 'Save settings',
  saving: 'Saving…',
  confirmed: 'Settings confirmed.',
  saved: 'Settings saved.',
  leave: {
    open: 'Leave Raketa',
    title: 'Leave Raketa?',
    lead:
      'Leaving starts with a pause: no new games are built on your courts, and every game ' +
      'already booked is played as booked. Once every booked game has been played and paid ' +
      'out, your payments can be disconnected.',
    paused:
      'Raketa bookings are paused. Once every booked game has been played and paid out, your ' +
      'payments can be disconnected.',
    notSelling:
      "Your settings aren't confirmed yet, so Raketa sells none of your courts: there is " +
      'nothing to leave.',
    cancel: 'Cancel',
    pause: 'Pause Raketa bookings',
    close: 'Close',
  },
} as const;

/** The refusals the settings can meet that are not a number out of its range. */
export const SETTINGS_REFUSALS: Readonly<Record<string, string>> = {
  settings_not_confirmed:
    'Confirm your settings first: until then Raketa sells none of your courts.',
};

/** A number out of its range, or no whole number at all: one sentence per field, with its range. */
export const RANGE_REFUSALS: Readonly<Record<NumberField, string>> = {
  release_lead_days: 'A release lead is 1 to 13 days.',
  cut_off_hours: 'A cut-off is 0 to 72 hours.',
  other_clubs_courts: 'A distance is 1 to 50 km.',
};
