/**
 * A Band's identity and meaning, and a Rating status in words.
 *
 * The thing to notice about this file is what it does *not* assert: no band edge appears
 * anywhere in it, because none appears in the module. The edges are deliberately uneven,
 * they were wrong once already, and they travel on the response.
 */

import { BAND_NAMES, bandPresentation, ratingStatusLabel } from './bandPresentation';

describe('bands', () => {
  it('recognises the four the engine names, whatever the casing', () => {
    expect(bandPresentation('Established')?.key).toBe('established');
    expect(bandPresentation('developing')?.key).toBe('developing');
    expect(bandPresentation(' Advanced ')?.key).toBe('advanced');
  });

  it('gives each one the plain-language meaning the glossary says it has', () => {
    // "Developing" on its own tells a player nothing, which is the whole reason a band
    // has a meaning as well as a name.
    expect(bandPresentation('New')?.meaning).toContain('starting out');
    expect(bandPresentation('Advanced')?.meaning.length).toBeGreaterThan(0);
  });

  it('has no identity for a band this build has never heard of', () => {
    // The screen still shows the name, the numbers and the trail — a band added after
    // this build shipped must not be able to blank the result screen. What it loses is
    // the colour and the sentence, neither of which can be guessed.
    expect(bandPresentation('Elite')).toBeUndefined();
  });

  it('names all four for the level bar, which draws every band and not just yours', () => {
    expect(BAND_NAMES).toEqual({
      new: 'New',
      developing: 'Developing',
      established: 'Established',
      advanced: 'Advanced',
    });
  });
});

describe('rating status', () => {
  it('says what onboarding produces in words', () => {
    expect(ratingStatusLabel('initial_estimate')).toBe('Initial estimate');
  });

  it('shows a status it does not recognise rather than dropping it', () => {
    // The same rule the difficulty tag follows: the server's own word beats a blank.
    expect(ratingStatusLabel('provisional')).toBe('provisional');
  });
});
