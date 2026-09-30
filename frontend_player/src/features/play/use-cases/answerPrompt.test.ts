/**
 * Answering a prompt — **and which module each answer lands in.**
 *
 * The split is the thing under test rather than the requests: a *yes* is a write through the
 * route that owns the value and a *not now* is a row about the question, so the assertions
 * below are mostly about what a given answer **did not** touch.
 */

import { installTransport, noContent, type Transport } from '@/test-support/transport';

import { acceptPrompt, declinePrompt, type PromptWrites } from './answerPrompt';

const DECLINES = '/api/v1/prompt-declines';

const TUESDAY_EVENING = { day: 2, hour: 19 } as const;
const SATURDAY_MORNING = { day: 6, hour: 9 } as const;

let transport: Transport;
let written: unknown[];

/** The three routes that own the values, as the ports the hook supplies for real. */
function ports(): PromptWrites {
  return {
    saveWeek: (week) => {
      written.push({ week });
      return Promise.resolve();
    },
    saveRadius: (radiusKm) => {
      written.push({ radiusKm });
      return Promise.resolve();
    },
    declareIntent: (declaration) => {
      written.push(declaration);
      return Promise.resolve();
    },
  };
}

beforeEach(() => {
  transport = installTransport();
  written = [];
  transport.on('POST', DECLINES, () => noContent());
});

afterEach(() => transport.restore());

describe('yes — a write through the route that owns the value', () => {
  it('saves the week the search ran on, and never the one on screen', async () => {
    // The engine compares the **post-rung** grid, so the working copy behind the sheet is
    // not always the week that was asked about. The payload is.
    await acceptPrompt(
      {
        raised: {
          prompt: 'KEEP_THESE_TIMES',
          week: [TUESDAY_EVENING, SATURDAY_MORNING],
          profileWeek: [TUESDAY_EVENING],
        },
        sport: 'padel',
      },
      ports(),
    );

    expect(written).toEqual([{ week: [TUESDAY_EVENING, SATURDAY_MORNING] }]);
  });

  it('saves a cleared week as the answer it is', async () => {
    await acceptPrompt(
      {
        raised: { prompt: 'KEEP_THESE_TIMES', week: [], profileWeek: [TUESDAY_EVENING] },
        sport: 'padel',
      },
      ports(),
    );

    expect(written).toEqual([{ week: [] }]);
  });

  it('makes the widening the profile’s own radius', async () => {
    await acceptPrompt(
      { raised: { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }, sport: 'padel' },
      ports(),
    );

    expect(written).toEqual([{ radiusKm: 22 }]);
  });

  it('declares the mode the searches kept choosing, for the sport that raised it', async () => {
    await acceptPrompt(
      {
        raised: { prompt: 'UPDATE_PLAY_INTENT', sportName: 'Padel', mode: 'COMPETITIVE' },
        sport: 'padel',
      },
      ports(),
    );

    // `DRIFT_PROMPT` is the one of the closed five that names this exact act, and the sheet is
    // the only place it can be reported from — the interstitial's prop accepts the two Play
    // screens and not this.
    expect(written).toEqual([{ sport: 'padel', intent: 'COMPETITIVE', surface: 'DRIFT_PROMPT' }]);
  });

  /**
   * The one *yes* that writes nothing, and it is not an oversight.
   *
   * `REFRESH_YOUR_TIMES` carries no value, and it is only ever drawn on a week the profile
   * already holds — so a write here would land the same state, record nothing, and leave the
   * grid as stale as it was while the button claimed otherwise.
   */
  it('writes nothing for the prompt that carries nothing to write', async () => {
    await acceptPrompt({ raised: { prompt: 'REFRESH_YOUR_TIMES' }, sport: 'padel' }, ports());

    expect(written).toEqual([]);
  });

  it('never writes a decline, whichever prompt was accepted', async () => {
    await acceptPrompt(
      { raised: { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }, sport: 'padel' },
      ports(),
    );

    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });
});

describe('not now — a row about the question, and never a value', () => {
  it('records the prompt and the sport whose screen raised it', async () => {
    await declinePrompt({ raised: { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }, sport: 'padel' });

    expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1);
    expect(transport.requestsTo('POST', DECLINES)[0]?.body).toEqual({
      prompt: 'KEEP_THIS_RADIUS',
      sport: 'PADEL',
    });
  });

  /**
   * Keyed by the question and **never by the value quoted** — declining *keep 22 km?* also
   * answers *keep 32 km?*, because the player answered about a habit rather than a number.
   */
  it('sends no radius, no week and no search to key a suppression by', async () => {
    await declinePrompt({ raised: { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }, sport: 'padel' });

    expect(transport.requestsTo('POST', DECLINES)[0]?.body).not.toMatchObject({ radius_km: 22 });
    expect(Object.keys(transport.requestsTo('POST', DECLINES)[0]?.body as object)).toEqual([
      'prompt',
      'sport',
    ]);
  });

  it('records the two loop prompts the same way', async () => {
    await declinePrompt({ raised: { prompt: 'REFRESH_YOUR_TIMES' }, sport: 'tennis' });
    await declinePrompt({
      raised: { prompt: 'UPDATE_PLAY_INTENT', sportName: 'Tennis', mode: 'FOR_FUN' },
      sport: 'tennis',
    });

    expect(transport.requestsTo('POST', DECLINES).map((sent) => sent.body)).toEqual([
      { prompt: 'REFRESH_YOUR_TIMES', sport: 'TENNIS' },
      { prompt: 'UPDATE_PLAY_INTENT', sport: 'TENNIS' },
    ]);
  });

  /**
   * The one prompt with no *not now* to record. The route refuses it with
   * `prompt_does_not_suppress`, and a request sent to be told that is a round trip spent
   * learning what the app already knows.
   */
  it('sends nothing for the prompt a decline buys nothing on', async () => {
    await declinePrompt({
      raised: { prompt: 'KEEP_THESE_TIMES', week: [], profileWeek: [TUESDAY_EVENING] },
      sport: 'padel',
    });

    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });
});
