/**
 * **A row's on-screen ledger** (#804; the Home rows mechanics §9.2) — once per card and Warsaw day, at
 * most fifty to a report, a failed report's cards owed again ahead of the rest.
 */

import {
  REPORT_AT_MOST,
  cameOnScreen,
  freshLedger,
  nextReport,
  onDay,
  reportAnswered,
} from './onScreen';

const SUNDAY = '2026-11-15';
const MONDAY = '2026-11-16';

describe('a card coming on screen', () => {
  it('is owed, and a report is due', () => {
    const { ledger, due } = cameOnScreen(freshLedger(SUNDAY), ['kuba', 'zofia']);

    expect(due).toBe(true);
    expect(ledger.owed).toEqual(['kuba', 'zofia']);
  });

  it('is owed once, however often it is seen before it is told', () => {
    const once = cameOnScreen(freshLedger(SUNDAY), ['kuba']).ledger;
    const twice = cameOnScreen(once, ['zofia', 'kuba']).ledger;

    expect(twice.owed).toEqual(['kuba', 'zofia']);
  });

  it('owes nothing, and asks no report, once it is told today', () => {
    const told = reportAnswered(
      nextReport(cameOnScreen(freshLedger(SUNDAY), ['kuba']).ledger).ledger,
      ['kuba'],
      true,
    );

    const again = cameOnScreen(told, ['kuba']);
    expect(again.due).toBe(false);
    expect(again.ledger.owed).toEqual([]);
  });

  it('owes nothing while its report is on its way', () => {
    const telling = nextReport(cameOnScreen(freshLedger(SUNDAY), ['kuba']).ledger).ledger;

    expect(cameOnScreen(telling, ['kuba'])).toEqual({ ledger: telling, due: false });
  });
});

describe('the next report', () => {
  it('tells what is owed, in the order seen, and leaves nothing owed', () => {
    const owed = cameOnScreen(freshLedger(SUNDAY), ['kuba', 'zofia', 'marek']).ledger;

    const { ledger, playerIds } = nextReport(owed);
    expect(playerIds).toEqual(['kuba', 'zofia', 'marek']);
    expect(ledger.owed).toEqual([]);
    expect([...ledger.telling]).toEqual(['kuba', 'zofia', 'marek']);
  });

  it('names fifty at most — the route’s cap — and leaves the rest for the one after', () => {
    const ids = Array.from({ length: 52 }, (_, at) => `p${at}`);
    const owed = cameOnScreen(freshLedger(SUNDAY), ids).ledger;

    const first = nextReport(owed);
    expect(REPORT_AT_MOST).toBe(50);
    expect(first.playerIds).toEqual(ids.slice(0, 50));
    expect(first.ledger.owed).toEqual(['p50', 'p51']);
  });

  it('is nothing when nothing is owed', () => {
    const empty = freshLedger(SUNDAY);
    expect(nextReport(empty)).toEqual({ ledger: empty, playerIds: [] });
  });
});

describe('a report answered', () => {
  const sent = () => nextReport(cameOnScreen(freshLedger(SUNDAY), ['kuba', 'zofia']).ledger).ledger;

  it('taken: its cards are told today', () => {
    const ledger = reportAnswered(sent(), ['kuba', 'zofia'], true);

    expect([...ledger.told]).toEqual(['kuba', 'zofia']);
    expect([...ledger.telling]).toEqual([]);
    expect(ledger.owed).toEqual([]);
  });

  it('refused: its cards are owed again, ahead of anything seen since', () => {
    const since = cameOnScreen(sent(), ['marek']).ledger;

    const ledger = reportAnswered(since, ['kuba', 'zofia'], false);
    expect(ledger.owed).toEqual(['kuba', 'zofia', 'marek']);
    expect([...ledger.telling]).toEqual([]);
    expect([...ledger.told]).toEqual([]);
  });
});

describe('a day', () => {
  it('starts empty: a card told yesterday is owed again, and yesterday’s owed are dropped', () => {
    const sunday = cameOnScreen(
      reportAnswered(
        nextReport(cameOnScreen(freshLedger(SUNDAY), ['kuba']).ledger).ledger,
        ['kuba'],
        true,
      ),
      ['zofia'],
    ).ledger;

    const monday = onDay(sunday, MONDAY);
    expect(monday).toEqual(freshLedger(MONDAY));
    expect(cameOnScreen(monday, ['kuba']).due).toBe(true);
  });

  it('is the same ledger the same day', () => {
    const sunday = cameOnScreen(freshLedger(SUNDAY), ['kuba']).ledger;
    expect(onDay(sunday, SUNDAY)).toBe(sunday);
  });
});
