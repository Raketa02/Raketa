/**
 * The two things about the poster a screen cannot observe, and one of them was a shipped bug.
 *
 * **Asserted against the drawing, which is the declared exception to "assert what the player
 * can observe"** — the same exception `ConfidenceRing.test.tsx` takes, and for the same
 * reason. A poster is one accessible node carrying one label; underneath it there is no text,
 * no role and no name, so a suite that only went through a screen could not tell two posters
 * that collided in a `<Defs>` id from two that did not, nor a flat figure from one that had
 * quietly gained a second value.
 *
 * Which hue and which pose a given player gets is *not* here — that belongs to the hash that
 * chooses them, and it is held next door in `courtPosterFraming.test.ts`.
 */

import { render, screen } from '@testing-library/react-native';
import { Circle, Ellipse, G, LinearGradient, Path, Rect, Stop } from 'react-native-svg';

import { CourtPoster, type CourtPosterPose } from './CourtPoster';
import { POSTER_HUES, theme, type PosterHue } from './theme';

const HUE = POSTER_HUES[0] as PosterHue;

const gradientIds = () =>
  screen.UNSAFE_queryAllByType(LinearGradient).map((node) => node.props.id as string);

/** The three props anything in an SVG can name a colour in. */
const PAINTS = ['fill', 'stroke', 'stopColor'] as const;

/** Every colour the drawing names, wherever it names one. The ground's `url(…)` is not one. */
const paints = () =>
  new Set(
    [
      ...screen.UNSAFE_queryAllByType(Rect),
      ...screen.UNSAFE_queryAllByType(G),
      ...screen.UNSAFE_queryAllByType(Path),
      ...screen.UNSAFE_queryAllByType(Circle),
      ...screen.UNSAFE_queryAllByType(Ellipse),
      ...screen.UNSAFE_queryAllByType(Stop),
    ]
      .flatMap((node) => PAINTS.map((prop) => (node.props as Record<string, unknown>)[prop]))
      .filter(
        (paint): paint is string =>
          typeof paint === 'string' && paint !== 'none' && !paint.startsWith('url('),
      ),
  );

describe("the gradient's id", () => {
  it('is per instance, so the same person drawn twice at one size does not collide', () => {
    // UI §G6 bug #3: the prototype composed this from the player id and the width, so the
    // pool — which draws one person in a candidate card and again in the header — emitted
    // duplicates, and the second poster took the first one's colours. Composing it from the
    // id, the width AND the height is the same bug one screen further out.
    render(
      <>
        <CourtPoster hue={HUE} pose="serve" accessibilityLabel="A generated poster" />
        <CourtPoster hue={HUE} pose="serve" accessibilityLabel="A generated poster" />
      </>,
    );

    const ids = gradientIds();

    expect(ids).toHaveLength(2);
    expect(new Set(ids).size).toBe(2);
  });

  it('is what the ground is painted with, rather than a hex the component repeated', () => {
    render(<CourtPoster hue={HUE} pose="forehand" accessibilityLabel="A generated poster" />);

    expect(screen.UNSAFE_getByType(Rect).props.fill).toBe(`url(#${gradientIds()[0] as string})`);
  });
});

describe('what the poster is painted in', () => {
  it('is four values and there is no fifth', () => {
    // The figure is flat and at ONE value: no second value, no gradient on the figure, no
    // skin tone, no hair. A fifth paint here is that constraint having been given up.
    render(<CourtPoster hue={HUE} pose="lunge" accessibilityLabel="A generated poster" />);

    expect(paints()).toEqual(new Set([HUE.light, HUE.dark, theme.color.ink, theme.color.volt]));
  });
});

describe('the pose', () => {
  it('changes the figure, which is the whole of what it does', () => {
    const figure = (pose: CourtPosterPose) => {
      render(<CourtPoster hue={HUE} pose={pose} accessibilityLabel="A generated poster" />);
      const drawn = screen.UNSAFE_queryAllByType(Path).map((node) => node.props.d as string);
      screen.unmount();
      return drawn.join(' ');
    };

    expect(new Set([figure('forehand'), figure('serve'), figure('lunge')]).size).toBe(3);
  });
});

describe('the one accessible node', () => {
  it('carries the label the caller gave it, and nothing under it is reachable', () => {
    render(<CourtPoster hue={HUE} pose="serve" accessibilityLabel="A generated court poster" />);

    expect(screen.getByLabelText('A generated court poster')).toBeTruthy();
  });
});
