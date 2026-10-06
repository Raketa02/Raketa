/**
 * The Games deck's three buttons under the stage — ✕, **i** and the ball — named by the game's
 * own words (#553), drawn as the mock's three circles, and locked while a card is leaving. They
 * came here from Players' deck with the stage (#574), whose suite held them to a person's name.
 */

import { render, screen } from '@testing-library/react-native';
import { type ViewStyle } from 'react-native';
import { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

import { DeckAnswers } from './DeckAnswers';
import { BALL_PATHS, BALL_STROKE } from './DeckBall';
import { ANSWER_LABELS } from './deckPresentation';

const noop = () => undefined;

function drawAnswers(answering = false) {
  render(
    <DeckAnswers
      labels={ANSWER_LABELS}
      onPass={noop}
      onAccept={noop}
      onRecord={noop}
      answering={answering}
    />,
  );
}

const button = (name: string) => screen.getByRole('button', { name });

describe("the Games deck's three buttons", () => {
  it('are named by the game’s words, and the ball stays out of the spoken name', () => {
    drawAnswers();

    expect(button(ANSWER_LABELS.pass)).toBeTruthy();
    expect(button(ANSWER_LABELS.accept)).toBeTruthy();
    expect(button(ANSWER_LABELS.record)).toBeTruthy();
    expect(ANSWER_LABELS.accept).not.toMatch(/🎾|ball/);
    expect(screen.queryByText('🎾', { includeHiddenElements: true })).toBeNull();
  });

  it('draw the yes’s ball as a white outline with its two seams, in one stroke weight', () => {
    drawAnswers();

    const drawn = screen.UNSAFE_getAllByType(Path).map((path) => path.props);
    const ball = Object.values(BALL_PATHS).map((d) => drawn.find((path) => path.d === d));

    expect(ball.every((path) => path !== undefined)).toBe(true);
    expect(new Set(ball.map((path) => path?.stroke))).toEqual(new Set([BALL_STROKE]));
    expect(new Set(ball.map((path) => path?.strokeWidth)).size).toBe(1);
    expect(BALL_STROKE).toBe(theme.color.surface);
  });

  it('are circles at the mock’s three sizes, the yes the largest', () => {
    drawAnswers();

    const size = (name: string) =>
      Object.assign({}, ...([button(name).props.style].flat(3) as ViewStyle[]));

    expect(size(ANSWER_LABELS.accept).width).toBe(theme.size.deckAnswer.accept);
    expect(size(ANSWER_LABELS.pass).width).toBe(theme.size.deckAnswer.pass);
    expect(size(ANSWER_LABELS.record).width).toBe(theme.size.deckAnswer.record);
    expect(size(ANSWER_LABELS.accept).borderRadius).toBe(theme.radius.pill);
  });

  it('lock the two answers while a card is leaving, and never the details', () => {
    drawAnswers(true);

    expect(button(ANSWER_LABELS.pass).props.accessibilityState.disabled).toBe(true);
    expect(button(ANSWER_LABELS.accept).props.accessibilityState.disabled).toBe(true);
    expect(button(ANSWER_LABELS.record).props.accessibilityState?.disabled).toBeFalsy();
  });
});
