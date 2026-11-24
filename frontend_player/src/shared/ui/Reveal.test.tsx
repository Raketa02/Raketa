/**
 * **The reveal at its own seam** (design system 5.6; PRD #867,
 * [#870](https://github.com/Raketa02/Raketa/issues/870)) — how a screen with one read goes from its
 * skeleton to its content: the content laid out underneath and hidden, then one cross-fade on
 * `motion.fade`, opacity only, and a cut under reduced motion. Whether a skeleton is drawn at all is
 * decided at the first draw, and a revealed screen never goes back to it.
 *
 * Reanimated is real, on the fake clock; the fades are read with `getAnimatedStyle`.
 */

import { act, render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { ReducedMotionProvider } from './overlay';
import { Reveal } from './Reveal';
import { SkeletonBlock, SkeletonGround } from './Skeleton';
import { theme } from './theme';

const HIDDEN = { includeHiddenElements: true } as const;
const FRAME = 16;
const FADE = theme.motion.fade;

/** Where the read stands: on its way, landed with the content, or refused. */
type Read = 'out' | 'landed' | 'refused';

function page(read: Read, reduced = false) {
  return (
    <ReducedMotionProvider value={reduced}>
      <SkeletonGround>
        <Reveal
          finished={read !== 'out'}
          landed={read === 'landed'}
          skeleton={<SkeletonBlock testID="the-skeleton" style={{ height: theme.size.btn }} />}
        >
          <Text>{read === 'refused' ? 'Try again' : 'Inés'}</Text>
        </Reveal>
      </SkeletonGround>
    </ReducedMotionProvider>
  );
}

const skeleton = () => screen.queryByTestId('the-skeleton', HIDDEN);
const opacityOf = (testID: string) =>
  (getAnimatedStyle(screen.getByTestId(testID, HIDDEN)) as { readonly opacity?: number }).opacity;
const contentOpacity = () => opacityOf('reveal-content');
const skeletonOpacity = () => opacityOf('reveal-skeleton');

function frames(count: number) {
  act(() => jest.advanceTimersByTime(count * FRAME));
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('while the read is out', () => {
  it('draws the skeleton from the first frame — no delay before it', () => {
    render(page('out'));

    expect(skeleton()).not.toBeNull();
  });

  it('lays the content out underneath, hidden from sight and from a listener', () => {
    render(page('out'));

    expect(screen.queryByText('Inés')).toBeNull();
    expect(screen.getByText('Inés', HIDDEN)).toBeTruthy();
    expect(contentOpacity()).toBe(0);
  });
});

describe('once the read has finished', () => {
  it('cross-fades from the skeleton to the content over the fade, by opacity alone', () => {
    const { rerender } = render(page('out'));
    frames(3);

    rerender(page('landed'));

    // Named at once: the content is a listener's from the reveal's first frame.
    expect(screen.getByText('Inés')).toBeTruthy();

    const moved = new Set<string>();
    const before = {
      content: { ...(getAnimatedStyle(screen.getByTestId('reveal-content', HIDDEN)) as object) },
      skeleton: { ...(getAnimatedStyle(screen.getByTestId('reveal-skeleton', HIDDEN)) as object) },
    };
    frames(FADE / FRAME / 2);
    // Halfway: both stand part-way, the content coming in as the skeleton goes.
    expect(contentOpacity()).toBeGreaterThan(0);
    expect(contentOpacity()).toBeLessThan(1);
    expect(skeletonOpacity()).toBeGreaterThan(0);
    expect(skeletonOpacity()).toBeLessThan(1);
    for (const [view, was] of Object.entries(before)) {
      const now = getAnimatedStyle(
        screen.getByTestId(view === 'content' ? 'reveal-content' : 'reveal-skeleton', HIDDEN),
      ) as Record<string, unknown>;
      for (const [prop, value] of Object.entries(now)) {
        if (JSON.stringify(value) !== JSON.stringify((was as Record<string, unknown>)[prop])) {
          moved.add(prop);
        }
      }
    }
    expect([...moved]).toEqual(['opacity']);

    frames(FADE / FRAME);

    // Done: the content whole, the skeleton gone — and its clock with it.
    expect(contentOpacity()).toBe(1);
    expect(skeleton()).toBeNull();
    expect(screen.queryByTestId('reveal-skeleton', HIDDEN)).toBeNull();
  });

  it('keeps no skeleton on screen for a minimum: a read that lands at once fades at once', () => {
    const { rerender } = render(page('out'));
    rerender(page('landed'));

    frames(FADE / FRAME + 1);

    expect(skeleton()).toBeNull();
  });

  it('is a cut under reduced motion: the content whole, the skeleton gone, on the next frame', () => {
    const { rerender } = render(page('out', true));
    frames(3);

    rerender(page('landed', true));
    frames(1);

    expect(screen.getByText('Inés')).toBeTruthy();
    expect(contentOpacity()).toBe(1);
    expect(skeleton()).toBeNull();
  });

  it('never goes back to the skeleton during the mount, whatever the read does next', () => {
    const { rerender } = render(page('out'));
    rerender(page('landed'));
    frames(FADE / FRAME + 1);

    rerender(page('out'));
    frames(3);

    // (Its opacity is not read here: under jest a drawing from above resets an animated style's
    // reading to its first value — a phone's commit keeps the one Reanimated set.)
    expect(skeleton()).toBeNull();
    expect(screen.queryByTestId('reveal-skeleton', HIDDEN)).toBeNull();
    expect(screen.getByText('Inés')).toBeTruthy();
  });
});

describe('a read that ends refused, or held for a connection', () => {
  it('reveals what it says in the content’s place, as the content would be', () => {
    const { rerender } = render(page('out'));
    rerender(page('refused'));

    expect(screen.getByText('Try again')).toBeTruthy();
    frames(FADE / FRAME + 1);
    expect(skeleton()).toBeNull();
  });

  it('stands the skeleton again when the read sets out once more with nothing drawn — never a blank page', () => {
    const { rerender } = render(page('out'));
    rerender(page('refused'));
    frames(FADE / FRAME + 1);

    // Try again, or the connection back: the read is out again, and there is still nothing to draw.
    rerender(page('out'));

    expect(skeleton()).not.toBeNull();
    expect(screen.queryByText('Inés')).toBeNull();
    expect(screen.getByText('Inés', HIDDEN)).toBeTruthy();

    // It lands: in it comes, for good.
    rerender(page('landed'));
    frames(FADE / FRAME + 1);
    expect(skeleton()).toBeNull();
    rerender(page('out'));
    frames(3);
    expect(skeleton()).toBeNull();
    expect(screen.getByText('Inés')).toBeTruthy();
  });

  it('draws no skeleton when the read has already ended at the first draw, and one once it sets out', () => {
    const { rerender } = render(page('refused'));

    expect(skeleton()).toBeNull();
    expect(screen.getByText('Try again')).toBeTruthy();

    rerender(page('out'));

    expect(skeleton()).not.toBeNull();
  });
});

describe('a read that already has its answer at the first draw', () => {
  it('draws the content at once: no skeleton, and no fade', () => {
    render(page('landed'));

    expect(skeleton()).toBeNull();
    expect(screen.queryByTestId('reveal-skeleton', HIDDEN)).toBeNull();
    expect(screen.getByText('Inés')).toBeTruthy();
    expect(contentOpacity()).toBe(1);
  });
});
