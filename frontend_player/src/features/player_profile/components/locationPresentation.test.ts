/**
 * The words on the location step, without a renderer.
 *
 * **Nothing here writes a coordinate, and that is the assertion worth having.** The step
 * used to print the area back as a degree pair and no longer does — a player cannot check
 * their own latitude, and the fact they wanted was *did that work*. So the two things pinned
 * below are the two labels that carry the state instead, and the promise the copy makes
 * about what is kept.
 */

import {
  LOCATION_SAVED,
  USE_MY_LOCATION,
  WHY_BODY,
  WITHOUT_AN_AREA_LABEL,
  WITH_AN_AREA_LABEL,
  captureLabel,
  continueLabel,
} from './locationPresentation';

const AN_AREA = { latitude: 41.39, longitude: 2.17 };

describe('the control that reads the device', () => {
  /**
   * The green fill is never the whole fact (Part 13, *never colour alone*): the words on the
   * control change with it, so a player who cannot see the fill is told the same thing.
   */
  it('says which act it is offering, and changes once there is an area', () => {
    expect(captureLabel(undefined)).toBe(USE_MY_LOCATION);
    expect(captureLabel(AN_AREA)).toBe(LOCATION_SAVED);
  });
});

describe('what the step promises about the reading', () => {
  it('states the rounding, and that the exact position is not what is kept', () => {
    // The sentence that has to earn the OS prompt. It may be re-worded; it may not stop
    // saying either of these, because both are properties of the code above it — the
    // coarsening `locationArea` applies, and the fact that nothing finer is ever held.
    expect(WHY_BODY).toContain('round it to about 1 km');
    expect(WHY_BODY).toContain('never store your exact location');
    // Foreground only, permanently — the one promise the app config enforces on both
    // platforms, and the one a player is most entitled to hear before a prompt.
    expect(WHY_BODY).toContain('track you in the background');
  });
});

describe('the control that continues', () => {
  /**
   * The label names the consequence rather than hiding it behind a note the player may not
   * read. Location is what discovery is built on: leaving without one is allowed, and it is
   * not the same act as leaving with one.
   */
  it('says what continuing costs when there is no area', () => {
    expect(continueLabel(undefined)).toBe(WITHOUT_AN_AREA_LABEL);
    expect(continueLabel(AN_AREA)).toBe(WITH_AN_AREA_LABEL);
  });
});
