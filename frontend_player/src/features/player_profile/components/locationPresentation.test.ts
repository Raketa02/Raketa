/**
 * The words on the location step, without a renderer.
 *
 * **Nothing here writes a coordinate, and that is the assertion worth having.** The step
 * used to print the area back as a degree pair and no longer does — a player cannot check
 * their own latitude, and the fact they wanted was *did that work*. So what is pinned below is
 * the labels that carry the state instead, the sentence about what the area is for, and the
 * club every refusal names (ADR-0200 §10).
 */

import {
  ACCESS_HOW_TO,
  AREA_UPDATES_LINE,
  LOCATION_SAVED,
  NO_FIX_BODY,
  PICK_A_CLUB,
  USE_MY_LOCATION,
  WHY_BODY,
  captureLabel,
  pickClubLabel,
  pickedClubLabel,
} from './locationPresentation';

const A_READING = { kind: 'reading', area: { latitude: 41.39, longitude: 2.17 } } as const;
const A_CLUB = {
  kind: 'club',
  club: { id: 'club-1', name: 'Bonarka Arena', district: 'Podgórze' },
} as const;

describe('the control that reads the device', () => {
  /**
   * The green fill is never the whole fact (Part 13, *never colour alone*): the words on the
   * control change with it, so a player who cannot see the fill is told the same thing.
   */
  it('says which act it is offering, and changes once the phone’s reading is the area', () => {
    expect(captureLabel(undefined)).toBe(USE_MY_LOCATION);
    expect(captureLabel(A_READING)).toBe(LOCATION_SAVED);
  });

  it('still offers the phone while a picked club is the area — it did not produce that one', () => {
    expect(captureLabel(A_CLUB)).toBe(USE_MY_LOCATION);
  });
});

describe('what the step says the area is for', () => {
  it('is ADR-0200 §10’s sentence: club distances, the rounding, and nobody else sees it', () => {
    expect(WHY_BODY).toBe(
      'Raketa shows how far each club is and lists the nearest first. Your area is rounded to about a kilometre and never shown to other players.',
    );
  });

  it('promises nothing about players near you, and nothing about matching', () => {
    // There is no players search any more (ADR-0200 §10, PRD #722 story 73).
    for (const sentence of [WHY_BODY, ACCESS_HOW_TO.refused, ACCESS_HOW_TO.blocked, NO_FIX_BODY]) {
      expect(sentence).not.toMatch(/players near|nearby|match/i);
    }
  });
});

describe('a refusal', () => {
  it('names the other way — a club — in every sentence that follows one', () => {
    // Denied, blocked or no fix: the step and the tab both offer the club, so each says so,
    // and none says the setup can be finished without an area — it never could.
    for (const sentence of [ACCESS_HOW_TO.refused, ACCESS_HOW_TO.blocked, NO_FIX_BODY]) {
      expect(sentence).toContain('pick a club near where you play');
      expect(sentence).not.toMatch(/without an area|later from your profile/);
    }
    expect(PICK_A_CLUB).toBe('Pick a club near where you play');
  });
});

describe('a club, spoken', () => {
  it('names the act and the club on the card, and the area on the chosen one', () => {
    expect(pickClubLabel('Bonarka Arena', 'Podgórze · Padel')).toBe(
      'Pick Bonarka Arena, Podgórze · Padel',
    );
    expect(pickedClubLabel(A_CLUB.club)).toBe('Your area: Bonarka Arena, Podgórze');
  });
});

describe('the one written trace of the cold-start refresh', () => {
  /**
   * `the-words.md` §26's sentence for You, verbatim: silent motion with no written trace is
   * the one thing that would surprise a careful player, so the tab says it once, statically
   * (ADR-0174 §6). Both halves are properties of the code — the refresh on launch, and the
   * coarsening `locationArea` applies — and the sentence may be re-worded only while it keeps
   * saying both.
   */
  it('says when the area moves and how coarse it is, as the words have it', () => {
    expect(AREA_UPDATES_LINE).toBe(
      'Your area updates each time you open Raketa; it is never finer than about a kilometre.',
    );
  });
});
