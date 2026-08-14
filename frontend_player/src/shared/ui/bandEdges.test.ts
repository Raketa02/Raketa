/**
 * The level bar's drawing boundaries, pinned because the engine derives the same three
 * numbers on the other side of the HTTP contract.
 *
 * The bar cuts the 1,00–5,00 scale into four contiguous segments so it has no gaps —
 * contiguity is a **rendering** requirement with no meaning in the model, which is why
 * `theme.band`'s `lo`/`hi` stay client-owned and the response carries no drawing geometry.
 * But the engine bands a Level from halfway across the gap between printed bands, so *its*
 * effective edges are the printed lower bounds less `BAND_EDGE_TOLERANCE` — and those come
 * out at the same 1,55 · 2,65 · 3,85. Neither side copied the other; both arrived here.
 *
 * That agreement is the whole risk. Retune the tolerance and the engine names a different
 * Band without moving the segment the coral mark is drawn in, so for Levels inside a gap the
 * picture and the word disagree — quietly, and only for the players who land there. The two
 * apps cannot import each other, so a pair of mirrored assertions is the only mechanism
 * available: this file is the half that fires here, and
 * `backend/tests/unit/test_band_edges_mirrored.py` is the half that fires there, where the
 * numbers are derived from the `Band` definition rather than typed in.
 *
 * A test and not a runtime check, on purpose. A `theme.ts` that asserted its own values
 * would be the app refusing to launch over a drawing detail; a red build is the right place
 * for a disagreement only a human can reconcile.
 */

import { theme, type BandKey } from './theme';

/** The scale the bar draws, and the scale the engine rates on. */
const SCALE_LOW = 1;
const SCALE_HIGH = 5;

/** Low to high, which is also the order `LevelBar` lays them out in. */
const BANDS = [
  'new',
  'developing',
  'established',
  'advanced',
] as const satisfies readonly BandKey[];

/**
 * Where the failure has to be repaired, attached to every failure below.
 *
 * A pin whose message does not say what else moves is a pin the next person re-baselines in
 * isolation — which is exactly the drift it exists to prevent.
 */
const MIRRORED_IN_THE_ENGINE =
  "These are the engine's effective band edges — each printed band's lower bound less " +
  'BAND_EDGE_TOLERANCE, in backend/app/engines/racketskill/core.py — reached independently ' +
  "here as the level bar's contiguous drawing boundaries. " +
  'backend/tests/unit/test_band_edges_mirrored.py derives them there and fails for the same ' +
  'retune. A change to BAND_EDGE_TOLERANCE has to move both sides in the same change, or ' +
  'the coral mark starts landing in a segment the response does not name.';

/**
 * Run assertions with the note appended to whatever they fail with.
 *
 * Jest has no message argument on `expect`, so this is the equivalent of the `assert x, msg`
 * the backend half uses. The last test in this file drives it deliberately red, which is
 * what proves the note reaches a failure rather than merely existing in this file.
 */
function mirrored(body: () => void): void {
  try {
    body();
  } catch (failure) {
    if (failure instanceof Error) {
      failure.message = `${failure.message}\n\n${MIRRORED_IN_THE_ENGINE}`;
    }
    throw failure;
  }
}

/** The three interior boundaries, read off the theme in the order the bar draws them. */
const drawnEdges = BANDS.slice(1).map((key) => theme.band[key].lo);

describe('the level bar and the engine agree about where a band ends', () => {
  it('cuts the scale where the engine bands it', () => {
    mirrored(() => {
      expect(drawnEdges).toEqual([1.55, 2.65, 3.85]);
    });
  });

  it('leaves no gap and no overlap between segments', () => {
    // A bar drawn from the *printed* band edges (1,0–1,5 · 1,6–2,6 · 2,7–3,8 · 3,9–5,0)
    // would have three gaps in it, and a Level inside one would have nowhere to be drawn.
    // Closing them is what produces the effective edges above — the same three numbers,
    // arrived at for an entirely different reason.
    mirrored(() => {
      BANDS.forEach((key, index) => {
        const next = BANDS[index + 1];
        if (next === undefined) return;
        expect(theme.band[key].hi).toBe(theme.band[next].lo);
      });
    });
  });

  it('covers the whole drawn scale exactly once, from 1,00 to 5,00', () => {
    mirrored(() => {
      expect(theme.band.new.lo).toBe(SCALE_LOW);
      expect(theme.band.advanced.hi).toBe(SCALE_HIGH);

      // Ascending and non-empty, so every Level on the scale falls in exactly one segment.
      BANDS.forEach((key) => {
        expect(theme.band[key].hi).toBeGreaterThan(theme.band[key].lo);
      });
    });
  });

  it('fails with the engine constant named, which is the mechanism', () => {
    // Without this the note is a string nobody reads: the three tests above would fail with
    // a bare numeric diff, and a bare numeric diff is what gets re-baselined.
    expect(() =>
      mirrored(() => {
        expect(theme.band.developing.lo).toBe(-1);
      }),
    ).toThrow(/BAND_EDGE_TOLERANCE/);
  });
});
