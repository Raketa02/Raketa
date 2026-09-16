/**
 * Every sentence the Radar pane says, held to `the-words.md` §26 — so a build session that
 * reworded one fails here rather than on somebody's phone.
 */

import { WIDEN_IN_YOU } from './deckPresentation';
import {
  BACK_TO_YOU_LABEL,
  LOOKING_AROUND,
  PRIVACY_LINE,
  RADAR_FAILED,
  TAP_FOR_THE_FULL_CARD,
  TRY_AGAIN,
  YOU_LABEL,
  ZOOM_IN_LABEL,
  ZOOM_OUT_LABEL,
  cardDistance,
  emptyHint,
  nobodyInReach,
  offScreen,
  playersInView,
  radarHint,
  reliabilityChip,
  ringLabel,
  tagsInCommon,
  widthAcross,
} from './radarPresentation';

describe('the field', () => {
  it('labels the viewer, a ring and the counter', () => {
    expect(YOU_LABEL).toBe('you');
    expect(ringLabel(5)).toBe('5 km');
    expect(widthAcross(18)).toBe('18 km across');
    expect(widthAcross(5.4)).toBe('5,4 km across');
  });

  it('prints the counter to one decimal below 10 and whole above, wherever a pinch rests', () => {
    expect(widthAcross(1.5)).toBe('1,5 km across');
    expect(widthAcross(7.83)).toBe('7,8 km across');
    expect(widthAcross(10)).toBe('10 km across');
    expect(widthAcross(23.4)).toBe('23 km across');
    expect(widthAcross(110)).toBe('110 km across');
  });
});

describe('the card', () => {
  it('prints the distance to one decimal', () => {
    expect(cardDistance(1.9)).toBe('1,9 km');
    expect(cardDistance(0.1)).toBe('0,1 km');
  });

  it('labels the reliability chip, and draws a dash where nobody was watched', () => {
    expect(reliabilityChip(88)).toBe('88 reliability');
    expect(reliabilityChip(undefined)).toBe('— reliability');
  });

  it('counts the tags in common and never lists them', () => {
    expect(tagsInCommon(2)).toBe('2 tags in common');
    expect(tagsInCommon(1)).toBe('1 tag in common');
    expect(tagsInCommon(0)).toBe('no tags in common');
  });

  it('ends with the door to the full card', () => {
    expect(TAP_FOR_THE_FULL_CARD).toBe('Tap for the full card ›');
  });
});

describe('the footer', () => {
  it('counts the players in view and says how many are off screen, or that this is all of them', () => {
    expect(playersInView(14)).toBe('14 players in view');
    expect(playersInView(1)).toBe('1 player in view');
    expect(offScreen(0)).toBe('all of them');
    expect(offScreen(8)).toBe('+8 off screen');
  });

  it('always opens the hint with the privacy line, and switches the rest on the zoom state', () => {
    expect(PRIVACY_LINE).toBe('Distance and bearing only — never an address, never a street.');
    expect(radarHint('wide')).toBe(
      'Distance and bearing only — never an address, never a street. Drag to move, pinch or use ± to zoom, tap anybody to fly to them.',
    );
    expect(radarHint('closer')).toBe(radarHint('wide'));
    expect(radarHint('closest')).toBe(
      'Distance and bearing only — never an address, never a street. Tap a card for the full profile and the two answers.',
    );
  });

  it('says the empty reading with the reach and the sport, and the deck’s own widen sentence', () => {
    expect(nobodyInReach({ reachKm: 10, sportName: 'Padel' })).toBe(
      'Nobody within 10 km plays padel yet',
    );
    expect(emptyHint()).toBe(`${PRIVACY_LINE} ${WIDEN_IN_YOU}`);
  });

  it('says the loading and the failure', () => {
    expect(LOOKING_AROUND).toBe('Looking around…');
    expect(RADAR_FAILED).toBe('The radar couldn’t load');
    expect(TRY_AGAIN).toBe('Try again');
  });
});

describe('the cluster, spoken', () => {
  it('names the three controls', () => {
    expect(ZOOM_IN_LABEL).toBe('Zoom in');
    expect(ZOOM_OUT_LABEL).toBe('Zoom out');
    expect(BACK_TO_YOU_LABEL).toBe('Back to you');
  });
});
