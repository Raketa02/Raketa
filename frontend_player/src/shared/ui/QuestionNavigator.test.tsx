/**
 * The navigator, asserted against the drawing.
 *
 * **This is the declared exception to "assert what the player can observe", and the ring's
 * suite made the same argument.** A segment is a rectangle: no text, no role, no accessible
 * name — one label covers the whole row, and it is the caller's copy. So a screen-level
 * suite cannot tell a row that grew by one from a row that redrew every segment as
 * answered, and *both* of this component's states would slip through it. Reaching for the
 * drawn Views is what makes them observable at all.
 *
 * What the label says, and that moving changes it, is asserted where a player meets it —
 * `features/onboarding/components/questionLoop.test.tsx`.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View } from 'react-native';

import { QuestionNavigator } from './QuestionNavigator';
import { theme } from './theme';

const LABEL = 'the run so far';

interface DrawnSegment {
  readonly filled: boolean;
  readonly tall: boolean;
}

/** Every drawn segment, in order. The row itself has no width; a segment is what does. */
function segments(): DrawnSegment[] {
  return screen
    .UNSAFE_queryAllByType(View)
    .map((node) => StyleSheet.flatten(node.props.style))
    .filter((style) => style.width === theme.size.navigator.segmentWidth)
    .map((style) => ({
      filled: style.backgroundColor === theme.color.coral,
      tall: style.height === theme.size.navigator.currentHeight,
    }));
}

describe('what the navigator draws', () => {
  it('draws one segment per question that exists — the answers, and the one being asked', () => {
    render(<QuestionNavigator answered={3} outstanding at={4} accessibilityLabel={LABEL} />);

    // Never a segment for a question the engine has not decided to ask: that segment is
    // the denominator this whole component exists to not claim.
    expect(segments()).toHaveLength(4);
  });

  it('fills what has been answered, and leaves the question being asked empty', () => {
    render(<QuestionNavigator answered={2} outstanding at={3} accessibilityLabel={LABEL} />);

    expect(segments().map((segment) => segment.filled)).toEqual([true, true, false]);
  });

  it('grows by one with each answer', () => {
    const { rerender } = render(
      <QuestionNavigator answered={1} outstanding at={2} accessibilityLabel={LABEL} />,
    );
    expect(segments()).toHaveLength(2);

    rerender(<QuestionNavigator answered={2} outstanding at={3} accessibilityLabel={LABEL} />);
    expect(segments()).toHaveLength(3);
  });

  it('shrinks when the run does', () => {
    // A revision truncates the transcript, so a step can describe less progress than the
    // one before it. The navigator is drawn from what the run holds now, never from what
    // it last drew — a component counting up would be wrong in the one direction it could
    // not detect.
    const { rerender } = render(
      <QuestionNavigator answered={5} outstanding at={6} accessibilityLabel={LABEL} />,
    );
    expect(segments()).toHaveLength(6);

    rerender(<QuestionNavigator answered={2} outstanding at={3} accessibilityLabel={LABEL} />);
    expect(segments()).toHaveLength(3);
  });

  it('makes the segment the player is standing on the tall one', () => {
    render(<QuestionNavigator answered={3} outstanding at={4} accessibilityLabel={LABEL} />);

    expect(segments().map((segment) => segment.tall)).toEqual([false, false, false, true]);
  });

  it('draws where the player is standing and what is answered as two separate facts', () => {
    // Walked back to the second of three answers. Fill says it is answered; height says
    // they are there. Collapsing the two would mean walking back moved nothing on screen,
    // in the one component whose job is to say where you are.
    render(<QuestionNavigator answered={3} outstanding at={2} accessibilityLabel={LABEL} />);

    expect(segments()).toEqual([
      { filled: true, tall: false },
      { filled: true, tall: true },
      { filled: true, tall: false },
      { filled: false, tall: false },
    ]);
  });

  it('draws no tall segment when the questionnaire has stopped', () => {
    // Every question drawn has been answered and none is outstanding, so the player is
    // standing one past the end — at a position with no segment. Nothing is being asked,
    // and nothing pretends to be.
    render(
      <QuestionNavigator answered={3} outstanding={false} at={4} accessibilityLabel={LABEL} />,
    );

    expect(segments()).toHaveLength(3);
    expect(segments().every((segment) => segment.filled)).toBe(true);
    expect(segments().some((segment) => segment.tall)).toBe(false);
  });
});
