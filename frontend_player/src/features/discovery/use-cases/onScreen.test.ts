/**
 * **A row's reporter** (#804) — batched, once per card and Warsaw day, a failure carried into the next
 * batch, the midnight window still told, a late answer kept off the new day, and nothing after the
 * row goes. Driven through the real HTTP layer with only the socket faked, on a hand-turned clock: the
 * day is whatever the suite says, and a batch window closes when the suite closes it.
 */

import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { REPORT_BATCH_MS } from '../domain/onScreen';

import { onScreenReporter, type ReporterClock } from './onScreen';

const ON_SCREEN_PATH = '/api/v1/on-screen';
const SUNDAY = '2026-11-15';
const MONDAY = '2026-11-16';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  transport.on('POST', ON_SCREEN_PATH, () => noContent());
});

afterEach(() => transport.restore());

/** A clock the suite turns: the day it says, and windows that close when it closes them. */
function handClock() {
  let today = SUNDAY;
  const windows: { readonly ms: number; readonly run: () => void; off: boolean }[] = [];
  const clock: ReporterClock = {
    today: () => today,
    after: (ms, run) => {
      const one = { ms, run, off: false };
      windows.push(one);
      return () => {
        one.off = true;
      };
    },
  };
  return {
    clock,
    turnTo: (day: string) => {
      today = day;
    },
    /** The windows still open, by how long each was to wait. */
    open: () => windows.filter((one) => !one.off).map((one) => one.ms),
    /** Every open window closes, and what each sent reaches the socket and is answered. */
    close: async () => {
      for (const one of windows.splice(0)) if (!one.off) one.run();
      await settle();
    },
  };
}

async function settle() {
  for (let turn = 0; turn < 10; turn += 1) await new Promise((done) => setTimeout(done, 0));
}

const reports = () =>
  transport
    .requestsTo('POST', ON_SCREEN_PATH)
    .map((request) => request.body as Wire['OnScreenRequest']);

describe('a row’s reporter', () => {
  it('tells nothing until the window closes, then every card seen in it, in one report', async () => {
    const { clock, open, close } = handClock();
    const reporter = onScreenReporter('SAME_LEVEL', clock);

    reporter.seen(['kuba']);
    reporter.seen(['kuba', 'zofia']);
    expect(open()).toEqual([REPORT_BATCH_MS]);
    await settle();
    expect(reports()).toEqual([]);

    await close();
    expect(reports()).toEqual([{ row: 'SAME_LEVEL', player_ids: ['kuba', 'zofia'] }]);
  });

  it('opens no window for a card already told today, and tells it again the next day', async () => {
    const { clock, turnTo, open, close } = handClock();
    const reporter = onScreenReporter('SAME_VIBE', clock);
    reporter.seen(['karol']);
    await close();

    reporter.seen(['karol']);
    expect(open()).toEqual([]);

    turnTo(MONDAY);
    reporter.seen(['karol']);
    await close();
    expect(reports()).toEqual([
      { row: 'SAME_VIBE', player_ids: ['karol'] },
      { row: 'SAME_VIBE', player_ids: ['karol'] },
    ]);
  });

  it('keeps a failed report’s cards owed, and tells them first in the window the next card opens', async () => {
    const { clock, open, close } = handClock();
    const reporter = onScreenReporter('SAME_LEVEL', clock);
    transport.on('POST', ON_SCREEN_PATH, () => errorResponse(503, 'block_state_unavailable'));
    reporter.seen(['kuba']);
    await close();
    expect(open()).toEqual([]);

    transport.on('POST', ON_SCREEN_PATH, () => noContent());
    reporter.seen(['zofia']);
    await close();

    expect(reports()).toEqual([
      { row: 'SAME_LEVEL', player_ids: ['kuba'] },
      { row: 'SAME_LEVEL', player_ids: ['kuba', 'zofia'] },
    ]);
  });

  it('still tells the window open at midnight as it closes', async () => {
    const { clock, turnTo, close } = handClock();
    const reporter = onScreenReporter('SAME_LEVEL', clock);
    reporter.seen(['kuba']);

    turnTo(MONDAY);
    await close();

    expect(reports()).toEqual([{ row: 'SAME_LEVEL', player_ids: ['kuba'] }]);
  });

  it('keeps an answer that lands after the day turned off the new day', async () => {
    const { clock, turnTo, close } = handClock();
    const reporter = onScreenReporter('SAME_LEVEL', clock);
    let answer: (response: Response) => void = () => undefined;
    transport.on('POST', ON_SCREEN_PATH, () => new Promise<Response>((done) => (answer = done)));
    reporter.seen(['kuba']);
    await close();

    // Monday begins with Zofia, and Sunday's report about Kuba is answered after it.
    turnTo(MONDAY);
    transport.on('POST', ON_SCREEN_PATH, () => noContent());
    reporter.seen(['zofia']);
    answer(noContent());
    await settle();

    reporter.seen(['kuba']);
    await close();
    expect(reports().map((report) => report.player_ids)).toEqual([['kuba'], ['zofia', 'kuba']]);
  });

  it('stops with the row: an open window tells nothing, and nothing seen after opens one', async () => {
    const { clock, open, close } = handClock();
    const reporter = onScreenReporter('SAME_LEVEL', clock);
    reporter.seen(['kuba']);

    reporter.stop();
    expect(open()).toEqual([]);
    reporter.seen(['zofia']);
    expect(open()).toEqual([]);
    await close();

    expect(reports()).toEqual([]);
  });
});
