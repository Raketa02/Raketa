/**
 * The three notices a player chooses (#559; the screens A7.2; the mechanics §17.2): which are on,
 * in the screen's order, and what one tap leaves.
 */

import { CHOICES, choicesOn, switched, type NotificationChoices } from './choices';

const DEFAULTS: NotificationChoices = {
  youCompleteIt: true,
  challengesForYou: true,
  fillInAlerts: false,
};

describe('the three choices', () => {
  it('are drawn in the screen’s order — You complete it, Challenges for you, Fill in alerts', () => {
    expect(CHOICES).toEqual(['youCompleteIt', 'challengesForYou', 'fillInAlerts']);
  });

  it('name the ones that are on, in that order', () => {
    expect(choicesOn(DEFAULTS)).toEqual(['youCompleteIt', 'challengesForYou']);
    expect(
      choicesOn({ youCompleteIt: false, challengesForYou: false, fillInAlerts: true }),
    ).toEqual(['fillInAlerts']);
  });

  it('name none when every one is off', () => {
    expect(
      choicesOn({ youCompleteIt: false, challengesForYou: false, fillInAlerts: false }),
    ).toEqual([]);
  });
});

describe('a tap', () => {
  it('turns one choice the other way and leaves the rest', () => {
    expect(switched(DEFAULTS, 'fillInAlerts')).toEqual({ ...DEFAULTS, fillInAlerts: true });
    expect(switched(DEFAULTS, 'youCompleteIt')).toEqual({ ...DEFAULTS, youCompleteIt: false });
  });

  it('tapped twice is where it started', () => {
    expect(switched(switched(DEFAULTS, 'challengesForYou'), 'challengesForYou')).toEqual(DEFAULTS);
  });
});
