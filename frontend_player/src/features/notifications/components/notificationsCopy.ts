/**
 * **Every sentence the notifications feature says** — the row on the You tab, the screen behind it,
 * the bell on Home, the list behind the bell and the banner ([#559](https://github.com/Raketa02/Raketa/issues/559);
 * the screens A7, A7.2, A9; mocks 50, 52, 53).
 *
 * **Import-light** — shared formatting and vocabulary only — because the shell composes the row
 * into the You tab and the bell into Home at module load.
 *
 * **What a notice says is not here.** A notice's title and body are the backend's
 * (`notifications/application/words.py`), the words the push was drawn in: the phone's system draws a
 * push before the app runs, so the list draws the same words rather than a second set.
 */

import { dayDate } from '@/shared/date/calendarDay';
import { dayLabel } from '@/shared/vocabulary/availabilityPresentation';

import type { ChoiceKey } from '../domain/choices';
import type { GivenWhen } from '../domain/notice';

/** The screen's and the row's title. */
export const NOTIFICATIONS_TITLE = 'Notifications';

const DOT = ' · ';

interface ChoiceWords {
  /** The row's title on the screen. */
  readonly title: string;
  /** What it is, and its cap (mock 53). */
  readonly line: string;
  /** Its name on the You tab's row (mock 50). */
  readonly short: string;
}

export const NOTIFICATIONS_COPY = {
  loading: 'Reading your notifications…',
  readAgain: 'Try again',
  /** Seven always on (A7.2; mock 52) — *the club confirmed / couldn't take it* is two notices. */
  alwaysOn: {
    title: 'Always on',
    tag: 'on',
    rows: [
      'It’s a game! · you paid',
      'Confirm your payment to keep your seat',
      'Game called off · with the refund',
      'Someone left your game',
      'You’ve been refunded',
      'The club confirmed / couldn’t take it',
      'Your post didn’t fill',
    ],
  },
  yourChoice: {
    title: 'Your choice',
    on: 'On',
    off: 'Off',
    rows: {
      youCompleteIt: {
        title: 'You complete it',
        line: 'A card needs only you · at most 1 a day, bundled',
        short: 'You complete it',
      },
      challengesForYou: {
        title: 'Challenges for you',
        line: 'A member’s post names you · at most 3 a day, bundled',
        short: 'Challenges',
      },
      fillInAlerts: {
        title: 'Fill in alerts',
        line: 'A booked game you fit needs one more · at most 3 a day',
        short: 'Fill in alerts',
      },
    } satisfies Readonly<Record<ChoiceKey, ChoiceWords>>,
  },
  /**
   * The line at the top while the phone may not show a notice (A7.2): asked once it may be, and
   * sent to the phone's settings once only they can change it.
   */
  permission: {
    ask: {
      line: 'Your phone doesn’t show Raketa’s notifications yet — a game filling, a seat to rescue, a refund.',
      button: 'Allow notifications',
      busy: 'Asking…',
    },
    blocked: {
      line: 'Notifications for Raketa are switched off in your phone’s settings.',
      button: 'Open settings',
    },
  },
  /** The row's line when only the seven always on are left. */
  noneChosen: 'Only the ones always on',
  /** The bell on Home, and the list behind it. */
  bell: 'Recent notifications',
  list: {
    loading: 'Reading what you were told…',
    empty:
      'Nothing yet — when a game fills, a seat opens or money moves, it’s told here and on your phone.',
  },
  banner: {
    close: 'Close this notification',
    opens: 'Opens the game',
  },
} as const;

/** *You complete it · Challenges · Fill in alerts* — the choices that are on, as the row says them. */
export function notificationsRowLine(on: readonly ChoiceKey[]): string {
  if (on.length === 0) return NOTIFICATIONS_COPY.noneChosen;
  return on.map((key) => NOTIFICATIONS_COPY.yourChoice.rows[key].short).join(DOT);
}

/** The middle dot is a mark to the eye; a listener hears a pause. */
const spoken = (line: string) => line.split(DOT).join(', ');

/** A choice's switch, spoken: *You complete it. A card needs only you, at most 1 a day, bundled* */
export function choiceSpoken(key: ChoiceKey): string {
  const words = NOTIFICATIONS_COPY.yourChoice.rows[key];
  return `${words.title}. ${spoken(words.line)}`;
}

/** A notice, spoken — the banner's name and announcement: *It's a game! · you paid. Padel · …* */
export function noticeSpoken(title: string, body: string): string {
  return body === '' ? title : `${title}. ${body}`;
}

/** A row of the list, spoken: the notice, and when it was given. */
export function noticeRowSpoken(title: string, body: string, when: string | undefined): string {
  const notice = noticeSpoken(title, body);
  return when === undefined ? notice : `${notice}. ${when}`;
}

/** An always-on row, spoken with its tag: *Someone left your game, always on*. */
export function alwaysOnSpoken(row: string): string {
  return `${spoken(row)}, always on`;
}

/** *14:05* · *Yesterday 14:05* · *Mon 14:05* · *20 Sep* — when a notice was given, on its row. */
export function givenLine(when: GivenWhen): string {
  switch (when.day) {
    case 'today':
      return when.clock;
    case 'yesterday':
      return `Yesterday ${when.clock}`;
    case 'weekday':
      return `${dayLabel(when.weekday)} ${when.clock}`;
    case 'date':
      return dayDate(when.date);
  }
}
