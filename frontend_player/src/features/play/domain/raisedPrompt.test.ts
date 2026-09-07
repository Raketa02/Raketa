/**
 * The two rules a surface reads off a prompt before it draws one, both of which are invisible
 * from a screen: **whether it may be asked here at all**, and **whether it has been asked
 * already** ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * The three tables above them are exhaustive over `Prompt` and a fifth prompt fails to
 * compile, so what is asserted here is the reading rather than the coverage.
 */

import {
  NOTHING_ASKED,
  alsoAsked,
  answerableWithoutAWeekGrid,
  firstUnasked,
  type RaisedPrompt,
} from './raisedPrompt';

const KEEP_THIS_RADIUS: RaisedPrompt = { prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 };
const REFRESH_YOUR_TIMES: RaisedPrompt = { prompt: 'REFRESH_YOUR_TIMES' };
const UPDATE_PLAY_INTENT: RaisedPrompt = {
  prompt: 'UPDATE_PLAY_INTENT',
  sportName: 'Padel',
  mode: 'FOR_FUN',
};

describe('what a surface with no week grid may ask', () => {
  /**
   * The one prompt whose *yes* is a request for the grid, on the two surfaces that have none.
   * Dropped rather than drawn: its answer would promise a control that is not on the screen,
   * and dismissal is *not now*, which suppresses it for thirty days everywhere.
   */
  it('drops the one whose yes is the grid, and keeps the rest', () => {
    expect(
      answerableWithoutAWeekGrid([REFRESH_YOUR_TIMES, KEEP_THIS_RADIUS, UPDATE_PLAY_INTENT]),
    ).toEqual([KEEP_THIS_RADIUS, UPDATE_PLAY_INTENT]);
  });

  // A drop is a drop and never a truncation: the question behind it is still asked.
  it('leaves the order of what survives alone', () => {
    expect(answerableWithoutAWeekGrid([KEEP_THIS_RADIUS, REFRESH_YOUR_TIMES])).toEqual([
      KEEP_THIS_RADIUS,
    ]);
    expect(answerableWithoutAWeekGrid([REFRESH_YOUR_TIMES])).toEqual([]);
  });
});

describe('a question already put to this player', () => {
  it('is skipped, and the one behind it is what gets asked', () => {
    const asked = alsoAsked(NOTHING_ASKED, 'padel', 'KEEP_THIS_RADIUS');

    // The half a `prompts[0]`-then-check would lose: every later list starts with the same
    // leading code, so the question behind it would never be reached again this visit.
    expect(firstUnasked([KEEP_THIS_RADIUS, UPDATE_PLAY_INTENT], 'padel', asked)).toEqual(
      UPDATE_PLAY_INTENT,
    );
  });

  it('is nothing left to ask once every question has been', () => {
    const asked = alsoAsked(
      alsoAsked(NOTHING_ASKED, 'padel', 'KEEP_THIS_RADIUS'),
      'padel',
      'UPDATE_PLAY_INTENT',
    );

    expect(firstUnasked([KEEP_THIS_RADIUS, UPDATE_PLAY_INTENT], 'padel', asked)).toBeUndefined();
  });

  /**
   * The declaration is the one prompt held per sport, so a drift answered on padel is not the
   * same question on tennis — and a key that was the code alone would swallow the second one
   * for the rest of the visit.
   */
  it('is that question on that sport, and not the same question on another', () => {
    const asked = alsoAsked(NOTHING_ASKED, 'padel', 'UPDATE_PLAY_INTENT');

    expect(firstUnasked([UPDATE_PLAY_INTENT], 'padel', asked)).toBeUndefined();
    expect(firstUnasked([UPDATE_PLAY_INTENT], 'tennis', asked)).toEqual(UPDATE_PLAY_INTENT);
  });

  it('is recorded once however often it is answered', () => {
    const once = alsoAsked(NOTHING_ASKED, 'padel', 'KEEP_THIS_RADIUS');

    expect(alsoAsked(once, 'padel', 'KEEP_THIS_RADIUS')).toEqual(once);
  });
});
