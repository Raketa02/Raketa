/**
 * What a live yes says on You › Payments (mock 48): the sport and when on the title line, the club
 * under it, the share on the right — and all of it in one sentence to a listener, with the share's
 * condition the drawing leaves to the grey.
 */

import type { LiveYes } from '../domain/liveYes';

import {
  LIVE_YES_HINT,
  liveYesLabel,
  liveYesTitle,
  liveYesesHeader,
} from './liveYesesPresentation';

const YES: LiveYes = {
  proposalId: 'f0000000-0000-4000-8000-000000000001',
  groupId: 'a0000000-0000-4000-8000-000000000005',
  sport: 'padel',
  kind: 'competitive',
  // Saturday 3 October, 15:00 in Warsaw.
  startsAt: '2026-10-03T13:00:00Z',
  club: { id: 'b0000000-0000-4000-8000-000000000001', name: 'Bonarka Arena' },
  shareGrosze: 2800,
  deadline: '2026-10-02T13:00:00Z',
};

describe('the section’s head', () => {
  it('counts the yeses', () => {
    expect(liveYesesHeader(3)).toBe('Live yeses · 3');
  });
});

describe('a row', () => {
  it('says the sport and when — the weekday within the week, as the court block does', () => {
    expect(liveYesTitle(YES, { kind: 'weekday', weekday: 6 })).toBe('Padel · Saturday 15:00');
    expect(liveYesTitle(YES, { kind: 'today' })).toBe('Padel · Today 15:00');
    expect(liveYesTitle(YES, { kind: 'dated', weekday: 6, day: '2026-10-10' })).toBe(
      'Padel · Saturday 10 Oct 15:00',
    );
  });

  it('says the hour alone when the day cannot be named', () => {
    expect(liveYesTitle(YES, undefined)).toBe('Padel · 15:00');
  });

  it('is one sentence to a listener, the share with its condition', () => {
    expect(liveYesLabel(YES, { kind: 'weekday', weekday: 6 })).toBe(
      'Padel · Saturday 15:00, Bonarka Arena, 28 zł if it fills',
    );
    expect(LIVE_YES_HINT).toBe('Opens the game’s details');
  });

  it('names a club that no longer exists in the card’s words', () => {
    const gone = { ...YES, club: { id: YES.club.id } };
    expect(liveYesLabel(gone, { kind: 'tomorrow' })).toBe(
      'Padel · Tomorrow 15:00, A club, 28 zł if it fills',
    );
  });
});
