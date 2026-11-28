/**
 * **The reveal at its own seam** (design system 5.6; PRD #867,
 * [#870](https://github.com/Rakieta02/Rakieta/issues/870)) — how a screen with one read goes from its
 * skeleton to its content: the content laid out underneath and hidden, then one cross-fade on
 * `motion.fade`, opacity only, and a cut under reduced motion. Whether a skeleton is drawn at all is
 * decided at the first draw, and a revealed screen never goes back to it.
 *
 * Reanimated is real, on the fake clock; the fades are read with `getAnimatedStyle`.
 *
 * **A screen with several parts** (#871): the rule's table — together before the ceiling, top-down
 * from it, never a lower part before an upper one, never a part taken back — and the ceiling's one
 * timer per mount; and a part of a scrolling column, whose skeleton holds its place while it waits.
 */

import { act, fireEvent, render, renderHook, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { useTopOnPage, type Followed } from './onScreen';
import { ReducedMotionProvider } from './overlay';
import { Reveal, useRevealParts } from './Reveal';
import { REVEAL_CEILING, partsToShow } from './revealParts';
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

describe('the rule for a screen with several parts', () => {
  const T = true;
  const F = false;

  it.each<[string, readonly boolean[], boolean, number, number]>([
    ['nothing finished yet: nothing shown', [F, F], F, 0, 0],
    ['the top part finished before the ceiling: it waits for the rest', [T, F], F, 0, 0],
    ['a lower part finished before the ceiling: it waits too', [F, T], F, 0, 0],
    ['every part finished before the ceiling: all of them, together', [T, T], F, 0, 2],
    ['at the ceiling: the finished parts from the top', [T, F], T, 0, 1],
    ['at the ceiling: never a lower part before an upper one', [F, T], T, 0, 0],
    ['at the ceiling: stopping at the first part not finished', [T, F, T], T, 0, 1],
    ['at the ceiling with every part finished: all of them', [T, T, T], T, 0, 3],
    ['after the ceiling: the next part in order, as it finishes', [T, T, F], T, 1, 2],
    ['a part shown stays shown, though its read sets out again', [F, F], F, 2, 2],
    ['a part shown stays shown after the ceiling too', [F, T], T, 1, 1],
  ])('%s', (_case, finished, pastCeiling, shown, toShow) => {
    expect(partsToShow({ finished, pastCeiling, shown })).toBe(toShow);
  });
});

describe('useRevealParts', () => {
  it('shows every part at once when every read has finished at the first draw — and sets no clock', () => {
    const { result } = renderHook(() => useRevealParts([true, true]));

    expect(result.current.shown).toBe(2);
    expect(jest.getTimerCount()).toBe(0);
  });

  it('shows nothing before the ceiling while a part is out, then the finished ones from the top at it', () => {
    const { result } = renderHook(() => useRevealParts([true, false]));
    expect(result.current).toEqual({ shown: 0, pastCeiling: false });

    act(() => jest.advanceTimersByTime(REVEAL_CEILING - 1));
    expect(result.current.shown).toBe(0);

    act(() => jest.advanceTimersByTime(1));
    expect(result.current).toEqual({ shown: 1, pastCeiling: true });
  });

  it('shows everything together the moment the last part finishes, before the ceiling', () => {
    const { result, rerender } = renderHook(({ finished }) => useRevealParts(finished), {
      initialProps: { finished: [false, false] as readonly boolean[] },
    });
    act(() => jest.advanceTimersByTime(REVEAL_CEILING / 2));

    rerender({ finished: [true, true] });

    expect(result.current.shown).toBe(2);
  });

  it('measures the ceiling from the mount, once — another draw does not move it', () => {
    const { result, rerender } = renderHook(({ finished }) => useRevealParts(finished), {
      initialProps: { finished: [false, false] as readonly boolean[] },
    });
    act(() => jest.advanceTimersByTime(REVEAL_CEILING - 100));
    rerender({ finished: [true, false] });

    act(() => jest.advanceTimersByTime(100));

    expect(result.current.shown).toBe(1);
  });

  it('then shows each part in order as it finishes', () => {
    const { result, rerender } = renderHook(({ finished }) => useRevealParts(finished), {
      initialProps: { finished: [false, true, false] as readonly boolean[] },
    });
    act(() => jest.advanceTimersByTime(REVEAL_CEILING));
    expect(result.current.shown).toBe(0);

    rerender({ finished: [true, true, false] });
    expect(result.current.shown).toBe(2);

    rerender({ finished: [true, true, true] });
    expect(result.current.shown).toBe(3);
  });

  it('never takes a part back, whatever its reads do next', () => {
    const { result, rerender } = renderHook(({ finished }) => useRevealParts(finished), {
      initialProps: { finished: [true, true] as readonly boolean[] },
    });

    rerender({ finished: [false, false] });

    expect(result.current.shown).toBe(2);
  });

  it('stops its clock once everything is shown, and when the screen goes', () => {
    const { rerender, unmount } = renderHook(({ finished }) => useRevealParts(finished), {
      initialProps: { finished: [false] as readonly boolean[] },
    });
    expect(jest.getTimerCount()).toBe(1);

    rerender({ finished: [true] });
    expect(jest.getTimerCount()).toBe(0);

    unmount();
    const again = renderHook(() => useRevealParts([false]));
    expect(jest.getTimerCount()).toBe(1);
    again.unmount();
    expect(jest.getTimerCount()).toBe(0);
  });
});

/**
 * **A row standing in a wrapper on a watched page** — where it reads its own top on the page, as
 * `HomeRow` does: its `y` in its parent, added to where the section around it stands.
 */
let probed: Followed<number> | undefined;
function Row() {
  const { top, laidOut } = useTopOnPage();
  probed = top;
  return <View testID="row" onLayout={(event) => laidOut(event.nativeEvent.layout.y)} />;
}
const at = (y: number) => ({ nativeEvent: { layout: { x: 0, y, width: 360, height: 100 } } });

describe('a part of a scrolling column', () => {
  /** A part whose content draws nothing until its read lands — Home's FOR YOU, say. */
  function part(read: Read) {
    return (
      <SkeletonGround>
        <Reveal
          sizedBy="skeleton"
          finished={read !== 'out'}
          landed={read === 'landed'}
          skeleton={<SkeletonBlock testID="the-skeleton" style={{ height: theme.size.btn }} />}
        >
          {read === 'out' ? null : <Text>Inés</Text>}
        </Reveal>
      </SkeletonGround>
    );
  }
  const positionOf = (testID: string) =>
    StyleSheet.flatten(screen.getByTestId(testID, HIDDEN).props.style).position;

  it('stands its skeleton in the column while it waits, the content laid out over it unseen', () => {
    render(part('out'));

    expect(positionOf('reveal-skeleton')).not.toBe('absolute');
    expect(positionOf('reveal-content')).toBe('absolute');
  });

  it('gives the column back to the content at the reveal, the skeleton fading over it', () => {
    const { rerender } = render(part('out'));

    rerender(part('landed'));

    expect(positionOf('reveal-content')).not.toBe('absolute');
    expect(positionOf('reveal-skeleton')).toBe('absolute');
    expect(screen.getByText('Inés')).toBeTruthy();
    frames(FADE / FRAME + 1);
    expect(skeleton()).toBeNull();
  });

  it('is drawn as its content at once when its read has finished at the first draw', () => {
    render(part('landed'));

    expect(skeleton()).toBeNull();
    expect(positionOf('reveal-content')).not.toBe('absolute');
  });
});

describe('on a page that watches what is on screen', () => {
  it('passes on where it stands, so a row inside it is measured on the page through it', () => {
    render(
      <Reveal testID="area" sizedBy="skeleton" finished landed skeleton={null}>
        <Row />
      </Reveal>,
    );

    act(() => {
      fireEvent(screen.getByTestId('area'), 'layout', at(480));
      fireEvent(screen.getByTestId('row'), 'layout', at(30));
    });

    expect(probed?.get()).toBe(510);
  });
});
