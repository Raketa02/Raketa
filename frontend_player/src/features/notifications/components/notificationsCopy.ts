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
  /**
   * Seventeen always on (A7.2 as #620 amends it, Q113 adds *Fix your card*, and #663 the five steps
   * at the court; mock 52 drew seven) — the mechanics §17.2's table, a row a line of it: *the club
   * confirmed / said no / didn't answer in time* is one row for three notices, as *A game you left*
   * is for two. The quiet row for the take at the cut-off is never pushed, so it is not listed.
   *
   * The court's five are always on because each decides someone's record or result (ADR-0195
   * §7), and each row is its notice's title with the name and the club left out, as the rows above
   * it are.
   */
  alwaysOn: {
    title: 'Always on',
    tag: 'on',
    rows: [
      'It’s a game! · held',
      'It’s a game! · the club answers by …',
      'Waiting for one payment',
      'Fix your card by … to keep your seat',
      'Confirm your payment by … to keep your seat',
      'Game called off · nothing was taken, or with the refund',
      'Someone left your game · or it’s filling again',
      'You’ve been refunded',
      'The club confirmed / said no / didn’t answer in time',
      'Your new game',
      'A game you left',
      'Your post didn’t fill',
      '… is at the club and you’re not there yet',
      '… is at the club · who you said isn’t here yet',
      'How did it go? · your game’s hour has ended',
      'Is that right? · … put a score up, or changed it',
      'Was … at the club? · they say they were',
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
  /** The row's line when only the ones always on are left. */
  noneChosen: 'Only the ones always on',
  /** The bell on Home, and the list behind it. */
  bell: 'Recent notifications',
  list: {
    /** A row that came since the last visit, said before its words while it stands out. */
    new: 'New',
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

/** A notice, spoken — the banner's name and announcement: *It's a game! · 30 zł held. Padel · …* */
export function noticeSpoken(title: string, body: string): string {
  return body === '' ? title : `${title}. ${body}`;
}

/**
 * A row of the list, spoken: the notice, and when it was given — and first that it is new, on the
 * visit it stands out.
 */
export function noticeRowSpoken(
  title: string,
  body: string,
  when: string | undefined,
  standsOut: boolean,
): string {
  const notice = noticeSpoken(title, body);
  const said = when === undefined ? notice : `${notice}. ${when}`;
  return standsOut ? `${NOTIFICATIONS_COPY.list.new}. ${said}` : said;
}

/** The most the bell writes as figures; above it, *99+* (Q101). The server's count is exact. */
const BELL_CEILING = 99;

/** *3* · *99+* — the bell's number as drawn, and nothing at nought. */
export function bellFigure(count: number): string | undefined {
  if (count <= 0) return undefined;
  return count > BELL_CEILING ? `${BELL_CEILING}+` : String(count);
}

/**
 * The bell's name, with its number: *Recent notifications, 3 new*. Exact above 99 — the cap is the
 * drawing's room, and a listener is not short of it.
 */
export function bellSpoken(count: number): string {
  return count <= 0 ? NOTIFICATIONS_COPY.bell : `${NOTIFICATIONS_COPY.bell}, ${count} new`;
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
