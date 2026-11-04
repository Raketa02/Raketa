/**
 * The question and result routes' params are untrusted input — both are reachable from a
 * deep link, and the assessment id becomes a request path.
 */

import { offerParam, parseAssessmentRouteParams, parsePickerOffer } from './routeParams';

const ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';

describe('assessment route params', () => {
  it('accepts a well-formed link', () => {
    expect(parseAssessmentRouteParams({ assessmentId: ID, sport: 'padel' })).toEqual({
      assessmentId: ID,
      sport: 'padel',
    });
  });

  it('rejects an assessment id that is not one', () => {
    expect(
      parseAssessmentRouteParams({ assessmentId: '../../users/me', sport: 'padel' }),
    ).toBeUndefined();
  });

  it('rejects a sport outside the closed set', () => {
    expect(parseAssessmentRouteParams({ assessmentId: ID, sport: 'pickleball' })).toBeUndefined();
  });

  it('takes the question to open on, which arrives as a string like every param', () => {
    // What a review entry links to. Coerced because a route param is text on the wire,
    // however it was written.
    expect(parseAssessmentRouteParams({ assessmentId: ID, sport: 'padel', at: '3' })).toEqual({
      assessmentId: ID,
      sport: 'padel',
      at: 3,
    });
  });

  it('is happy without one, which is the ordinary way into the questionnaire', () => {
    // Absent means *wherever the run stands*, so it is optional rather than defaulted:
    // there is no position that means "follow the end of the run".
    expect(parseAssessmentRouteParams({ assessmentId: ID, sport: 'padel' })?.at).toBeUndefined();
  });

  it('rejects a position that is not one, rather than opening the run somewhere arbitrary', () => {
    // Positions are 1-based, so 0 is not one. A number past the end of the run *is* well
    // formed and is clamped by the screen — the run is served fresh and may be shorter
    // than the one the link was made against.
    for (const at of ['nowhere', '0', '-2', '1.5']) {
      expect(parseAssessmentRouteParams({ assessmentId: ID, sport: 'padel', at })).toBeUndefined();
    }
  });

  it('rejects a missing param, and the array form expo-router can hand over', () => {
    expect(parseAssessmentRouteParams({ assessmentId: ID })).toBeUndefined();
    expect(
      parseAssessmentRouteParams({ assessmentId: ID, sport: ['padel', 'tennis'] }),
    ).toBeUndefined();
  });
});

/**
 * **The sports the picker offers, when a door narrows them** (#731, ADR-0200 §4): *+ Another sport*
 * opens it over the sports the player is unrated in — an official group's own, or any — and the
 * route carries them, so they are untrusted input like every param.
 */
describe('the picker’s offer', () => {
  it('is carried as one param and read back, in the order it was written', () => {
    const params = { offer: offerParam(['tennis', 'badminton']) };

    expect(parsePickerOffer(params)).toEqual(['tennis', 'badminton']);
  });

  it('is no narrowing at all when the route carries none — every sport the server serves', () => {
    expect(parsePickerOffer({})).toBeUndefined();
    expect(parsePickerOffer({ groupId: ID, tab: 'games' })).toBeUndefined();
  });

  it('is no narrowing for an offer that is not one — a sport outside the set, or nothing', () => {
    expect(parsePickerOffer({ offer: 'tennis,pickleball' })).toBeUndefined();
    expect(parsePickerOffer({ offer: '' })).toBeUndefined();
    expect(parsePickerOffer({ offer: ['tennis', 'squash'] })).toBeUndefined();
  });
});
