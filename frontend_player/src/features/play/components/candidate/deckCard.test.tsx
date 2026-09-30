/**
 * The deck card, held to what the mock draws and the fields it draws from
 * ([ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): every element in the mock's order, each off the field named for it, a dash for an absent
 * tile, the shared tags first, the mark with its tick over an un-washed top — and **no liker
 * marking**, no reason line, and one element whose action is the long press.
 */

import { render, screen } from '@testing-library/react-native';
import { Text, View, type TextStyle, type ViewStyle } from 'react-native';
import { Path } from 'react-native-svg';

import { formatLevel, formatRange } from '@/shared/formatting/ratingFormat';
import { ON_COURT_CLAUSE, ON_COURT_MARK, theme } from '@/shared/ui';
import { TICK_PATH } from '@/shared/ui/Tick';
import { socialTagChip } from '@/shared/vocabulary/socialTagPresentation';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Evidence, ScoredTerm } from '../../domain/evidence';
import type { Term } from '../../domain/vocabulary';
import { deckAnswerLabels } from '../accessibilityPresentation';
import { BALL_PATHS, BALL_STROKE } from '../DeckBall';
import { NO_VALUE } from '../deckCardPresentation';
import { DeckAnswers } from '../DeckAnswers';
import { livenessLine, inclusionLine } from '../livenessPresentation';

import { DeckCard } from './DeckCard';

const PLAYER = '9f2a1c44-0000-4000-8000-000000000001';
const PHOTO = 'https://photos.example/9f2a1c44?sig=abc';
const HERE = 'A+050612+0019938';

const ENVELOPE: SearchEnvelope = {
  searchId: '11111111-0000-4000-8000-000000000001',
  mode: null,
  myAreaCode: HERE,
  pool: { radiusKmUsed: 8, playersInRange: 7, window: 'THIS_WEEK', remaining: 5, wantToPlayYou: 2 },
  radiusClamp: false,
  sortsAvailable: [],
  rungOffers: null,
  rulesetVersion: 'ruleset-v1',
  engineVersion: 'matchfit-v1',
  optimisedFor: 'SEARCHER',
};

function scored(term: Term, evidence: Evidence): ScoredTerm {
  return { term, weight: 10, value: 0.8, contribution: 8, evidence };
}

const TERMS: readonly ScoredTerm[] = [
  scored('LEVEL_FIT', {
    kind: 'level_fit',
    myMu: 2.71,
    theirMu: 2.6,
    delta: -0.11,
    direction: 'BELOW',
  }),
  scored('PREDICTED_BALANCE', {
    kind: 'predicted_balance',
    pct: 72,
    mySigma: 0.16,
    theirSigma: 0.14,
    confidence: 66,
  }),
  scored('AVAILABILITY_OVERLAP', {
    kind: 'availability_overlap',
    sharedCount: 9,
    nextSlot: { day: 2, hour: 19 },
  }),
  scored('DISTANCE', { kind: 'distance', km: 2, areaCode: HERE, outsideTheirRadius: false }),
  scored('INTENT_ALIGNMENT', {
    kind: 'intent_alignment',
    myMode: 'FOR_FUN',
    theirIntent: 'FOR_FUN',
    aligned: true,
  }),
  scored('PLAYING_STYLE', {
    kind: 'playing_style',
    matched: ['HERE_TO_IMPROVE'],
    matchedInFull: true,
    complementary: [],
    clashing: [],
  }),
  scored('SOCIAL_VIBE', {
    kind: 'social_vibe',
    matched: [],
    matchedInFull: true,
    complementary: [],
    clashing: [],
  }),
];

function candidate(
  over: Partial<Candidate> = {},
  card: Partial<Candidate['card']> = {},
): Candidate {
  return {
    playerId: PLAYER,
    fit: 76,
    // The mock's own *1,9 km* — one decimal, spot to spot (ADR-0174 §2) — and not the
    // evidence's whole `2`, which is the engine's input and is never printed.
    distanceKm: 1.9,
    card: {
      name: 'Filip N.',
      photoUrl: PHOTO,
      photoReview: 'allowed',
      areaCode: HERE,
      socialTags: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE', 'TALKS_THROUGH_THE_MATCH'],
      level: 2.6,
      band: 'Developing',
      range: { low: 2.3, high: 2.9 },
      playerScore: 88,
      intro: 'Two games in. Moved here in September, still learning the city.',
      ...card,
    },
    terms: TERMS,
    concerns: [],
    livenessReasons: ['RECENT_ACTIVITY'],
    degradedTerms: [],
    modifiers: [],
    ...over,
  };
}

const noop = () => undefined;

/** The chips as drawn — the vocabulary's glyph, the words, and *· you too* on the shared one. */
const SHARED_CHIP = socialTagChip({ id: 'HERE_TO_IMPROVE', shared: true });
const PLAYS_TO_WIN_CHIP = socialTagChip({ id: 'PLAYS_TO_WIN', shared: false });

function draw(over: Partial<Candidate> = {}, card: Partial<Candidate['card']> = {}) {
  render(
    <DeckCard
      candidate={candidate(over, card)}
      envelope={ENVELOPE}
      sportName="Padel"
      onLongPress={noop}
    />,
  );
}

/** The body is the one element, and the outermost `View` holding a name is it. */
function spokenBody(): string {
  const body = screen
    .UNSAFE_getAllByType(View)
    .find((view) => typeof view.props.accessibilityLabel === 'string');
  return body?.props.accessibilityLabel as string;
}

/** Every rendered text, in tree order — the mock's order is what the card is held to. */
function textsInOrder(): readonly string[] {
  return screen
    .UNSAFE_getAllByType(Text)
    .map((text) => text.props.children)
    .filter((children): children is string => typeof children === 'string');
}

const styleOf = (text: ReturnType<typeof screen.getByText>): TextStyle =>
  Object.assign({}, ...([text.props.style].flat(3) as TextStyle[]));

describe('what the deck card draws, in the mock’s order', () => {
  it('draws the level, the sport, the mark, the name, the meta line, the intro, the tags and three tiles', () => {
    draw();

    const texts = textsInOrder();
    const order = [
      formatLevel(2.6),
      'Padel',
      ON_COURT_MARK,
      'Filip N.',
      'In your area · 1,9 km · around this week',
      '“Two games in. Moved here in September, still learning the city.”',
      SHARED_CHIP,
      PLAYS_TO_WIN_CHIP,
      'Balance',
      '72%',
      'Reliability',
      '88',
      'Overlap',
      '9 hours',
    ];
    const seen = order.map((line) => texts.indexOf(line));

    expect(seen.every((at) => at >= 0)).toBe(true);
    expect([...seen].sort((a, b) => a - b)).toEqual(seen);
  });

  /** The tag row above the tiles already leads with the shared ones, and the hint was instructions. */
  it('draws no Shared tags tile and no hint line under the tiles', () => {
    draw();

    expect(screen.queryByText('Shared tags')).toBeNull();
    expect(screen.queryByText(/Drag the card|long-press/)).toBeNull();
    expect(textsInOrder().at(-1)).toBe('9 hours');
  });

  it('prints the level in the existing 40pt figure and the name in the card’s own role', () => {
    draw();

    expect(styleOf(screen.getByText(formatLevel(2.6))).fontSize).toBe(theme.num.levelHero.fontSize);
    expect(styleOf(screen.getByText('Filip N.')).fontSize).toBe(theme.type.deckName.fontSize);
    expect(styleOf(screen.getByText('Filip N.')).fontFamily).toBe(theme.type.deckName.fontFamily);
  });

  it('draws the mark with its tick, on a photograph the check passed, and not otherwise', () => {
    draw();
    expect(screen.getByText(ON_COURT_MARK)).toBeTruthy();
    expect(screen.UNSAFE_getAllByType(Path).some((path) => path.props.d === TICK_PATH)).toBe(true);
    expect(spokenBody()).toContain(ON_COURT_CLAUSE);
    screen.unmount();

    draw({}, { photoReview: 'flagged' });
    expect(screen.queryByText(ON_COURT_MARK)).toBeNull();
    expect(spokenBody()).not.toContain(ON_COURT_CLAUSE);
  });

  it('draws the wash as a gradient, and never a scrim over the top', () => {
    draw();

    // One gradient, in the card's own box; the photograph's top is left clear for the Level
    // and the mark, which take the text shadow instead.
    expect(screen.UNSAFE_getAllByType(Path).length).toBeGreaterThanOrEqual(1);
    const level = styleOf(screen.getByText(formatLevel(2.6)));
    expect(level.textShadowRadius).toBe(theme.shadow.textOnMedia.textShadowRadius);
  });
});

describe('the meta line', () => {
  it('says *around this week* on the liveness code alone', () => {
    draw({ livenessReasons: [] });

    expect(screen.getByText('In your area · 1,9 km')).toBeTruthy();
    expect(screen.queryByText(/around this week/)).toBeNull();
  });

  it('keeps the week and drops the kilometres where the distance term stood down', () => {
    draw({ distanceKm: undefined });

    expect(screen.queryByText(/km/)).toBeNull();
    expect(screen.getByText(livenessLine('RECENT_ACTIVITY'))).toBeTruthy();
  });

  it('is absent where neither the distance nor the week is known', () => {
    draw({ distanceKm: undefined, livenessReasons: [] });

    expect(screen.queryByText(/km/)).toBeNull();
    expect(screen.queryByText(/this week/i)).toBeNull();
  });
});

describe('the intro', () => {
  it('closes the gap where they wrote none', () => {
    draw({}, { intro: undefined });

    expect(screen.queryByText(/“/)).toBeNull();
    expect(spokenBody()).not.toContain('“');
  });

  it('is spoken as their own words, inside the marks', () => {
    draw();

    expect(spokenBody()).toContain(
      '“Two games in. Moved here in September, still learning the city.”',
    );
  });
});

describe('the tags', () => {
  it('draws the shared ones first, volt, with *· you too*, and the rest on dark', () => {
    draw();

    const shared = screen.getByText(SHARED_CHIP);
    const rest = screen.getByText(PLAYS_TO_WIN_CHIP);
    const texts = textsInOrder();

    // Served *after* Plays to win, drawn before it.
    expect(SHARED_CHIP).toMatch(/· you too$/);
    expect(texts.indexOf(SHARED_CHIP)).toBeLessThan(texts.indexOf(PLAYS_TO_WIN_CHIP));
    expect(styleOf(shared).color).toBe(theme.color.ink);
    expect(styleOf(rest).color).toBe(theme.color.surface);
  });

  it('speaks what it draws', () => {
    draw();

    expect(spokenBody()).toContain('Tags you share: Here to improve');
    expect(spokenBody()).toContain('Their other tags: Plays to win, Talks through the match');
  });
});

describe('the three tiles', () => {
  it('prints a dash for an absent number and keeps the row at three', () => {
    draw(
      { terms: TERMS.filter((row) => row.term !== 'PREDICTED_BALANCE') },
      { playerScore: undefined },
    );

    expect(screen.getAllByText(NO_VALUE)).toHaveLength(2);
    expect(screen.getByText('Balance')).toBeTruthy();
    expect(screen.getByText('Reliability')).toBeTruthy();
    expect(screen.getByText('9 hours')).toBeTruthy();
    // The dashes say nothing to a listener; the one figure does.
    expect(spokenBody()).not.toContain('Balance');
    expect(spokenBody()).toContain('Overlap 9 hours');
  });

  it('speaks the tiles that have a figure', () => {
    draw();

    expect(spokenBody()).toContain('Balance 72%');
    expect(spokenBody()).toContain('Reliability 88');
    expect(spokenBody()).toContain('Overlap 9 hours');
    expect(spokenBody()).not.toContain('Shared tags');
  });
});

describe('what the deck card never draws', () => {
  /** The liker is unmarked and placed by the nudge (ADR-0169 §4); the count of them is the chip's. */
  it('marks a liker in no way — no sentence, no tag', () => {
    draw({ inclusionReason: 'INTEREST_LIFT' });

    expect(screen.queryByText(inclusionLine('INTEREST_LIFT'))).toBeNull();
    expect(screen.queryByText(livenessLine('INTEREST_RECEIVED'))).toBeNull();
    expect(spokenBody()).not.toMatch(/said yes|Wants to play you/);
  });

  it('makes no case — no reason line and no concern', () => {
    draw({ concerns: ['SOCIAL_VIBE'] });

    expect(screen.queryByText("They're here for fun too")).toBeNull();
    expect(screen.queryByText(/here to compete/)).toBeNull();
    expect(spokenBody()).not.toMatch(/here for fun|here to compete/);
  });

  it('draws no buttons of its own — the three are the stage’s, below it', () => {
    draw();

    expect(screen.queryByLabelText(/^Not today/)).toBeNull();
    expect(screen.queryByLabelText(/^Let's play/)).toBeNull();
  });
});

describe('the one element', () => {
  it('speaks the card in the drawn order, and its action is the long press', () => {
    draw();

    const body = spokenBody();
    expect(body.startsWith('Filip N.. Fit 76 out of 100. ')).toBe(true);
    expect(body).toContain(
      `${formatLevel(2.6)} · Developing · likely ${formatRange({ low: 2.3, high: 2.9 })}`,
    );
    expect(body.indexOf(ON_COURT_CLAUSE)).toBeLessThan(body.indexOf('In your area'));
    expect(body.indexOf('Here to improve')).toBeLessThan(body.indexOf('Balance 72%'));
    expect(screen.getByRole('button', { name: body })).toBeTruthy();
  });

  /** A card behind the top one is the same drawing with no element in it. */
  it('is no element at all without a long press to carry', () => {
    render(<DeckCard candidate={candidate()} envelope={ENVELOPE} sportName="Padel" />);

    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.getByText('Filip N.')).toBeTruthy();
  });

  /**
   * The stage promotes the card behind in place when the top one has gone, and the card has to
   * hold its side of that: the same tree with and without the long press, so that taking on the
   * action does not throw the drawing away — a photograph decoded again over the person who was
   * plainly there is the blink the release is meant not to have.
   */
  it('takes on the long press as the same element, and nothing in it is drawn again', () => {
    const behind = <DeckCard candidate={candidate()} envelope={ENVELOPE} sportName="Padel" />;
    const view = render(behind);
    const drawn = screen.getByText('Filip N.');

    view.rerender(
      <DeckCard candidate={candidate()} envelope={ENVELOPE} sportName="Padel" onLongPress={noop} />,
    );

    // Identity, not equality: the question is whether it is the same node, and a node that
    // was thrown away cannot be printed by the matcher either.
    expect(Object.is(screen.getByText('Filip N.'), drawn)).toBe(true);
    expect(screen.getByRole('button')).toBeTruthy();
  });
});

describe('the three buttons under the stage', () => {
  it('are named for the person, and the ball stays out of the spoken name', () => {
    render(
      <DeckAnswers
        labels={deckAnswerLabels('Filip N.')}
        onPass={noop}
        onAccept={noop}
        onRecord={noop}
      />,
    );

    const labels = deckAnswerLabels('Filip N.');
    expect(screen.getByRole('button', { name: labels.pass })).toBeTruthy();
    expect(screen.getByRole('button', { name: labels.accept })).toBeTruthy();
    expect(screen.getByRole('button', { name: labels.record })).toBeTruthy();
    expect(labels.record).toBe('Filip N.’s record');
    expect(labels.accept).not.toMatch(/🎾|ball/);
    expect(screen.queryByText('🎾', { includeHiddenElements: true })).toBeNull();
  });

  /** A drawing and not an emoji: the platform's ball was its own colours, and clipped above. */
  it('draw the yes’s ball as a white outline with its two seams, in one stroke weight', () => {
    render(
      <DeckAnswers
        labels={deckAnswerLabels('Filip N.')}
        onPass={noop}
        onAccept={noop}
        onRecord={noop}
      />,
    );

    const drawn = screen.UNSAFE_getAllByType(Path).map((path) => path.props);
    const ball = Object.values(BALL_PATHS).map((d) => drawn.find((path) => path.d === d));

    expect(ball).toHaveLength(3);
    expect(ball.every((path) => path !== undefined)).toBe(true);
    expect(new Set(ball.map((path) => path?.stroke))).toEqual(new Set([BALL_STROKE]));
    expect(new Set(ball.map((path) => path?.strokeWidth)).size).toBe(1);
    expect(ball.every((path) => path?.fill === 'none')).toBe(true);
    expect(BALL_STROKE).toBe(theme.color.surface);
  });

  /** The seams are arcs of the ball's own circle, and each begins and ends on it. */
  it('draw seams that meet the ball’s outline', () => {
    const numbers = (d: string) => d.match(/-?\d+(?:\.\d+)?/g)?.map(Number) ?? [];
    const [x0, y0, r] = numbers(BALL_PATHS.ball);
    const centre = { x: (x0 ?? 0) + (r ?? 0), y: y0 ?? 0 };
    const onTheBall = (x: number, y: number) =>
      Math.abs(Math.hypot(x - centre.x, y - centre.y) - (r ?? 0)) < 0.02;

    for (const seam of [BALL_PATHS.leftSeam, BALL_PATHS.rightSeam]) {
      const [sx, sy, sr, , , , , ex, ey] = numbers(seam);
      expect(sr).toBe(r);
      expect(onTheBall(sx ?? 0, sy ?? 0)).toBe(true);
      expect(onTheBall(ex ?? 0, ey ?? 0)).toBe(true);
    }
  });

  it('are circles at the mock’s three sizes, the yes the largest', () => {
    render(
      <DeckAnswers
        labels={deckAnswerLabels('Filip N.')}
        onPass={noop}
        onAccept={noop}
        onRecord={noop}
      />,
    );

    const labels = deckAnswerLabels('Filip N.');
    const size = (name: string) =>
      Object.assign(
        {},
        ...([screen.getByRole('button', { name }).props.style].flat(3) as ViewStyle[]),
      );

    expect(size(labels.accept).width).toBe(theme.size.deckAnswer.accept);
    expect(size(labels.pass).width).toBe(theme.size.deckAnswer.pass);
    expect(size(labels.record).width).toBe(theme.size.deckAnswer.record);
    expect(size(labels.accept).borderRadius).toBe(theme.radius.pill);
    expect(theme.size.deckAnswer.accept).toBeGreaterThan(theme.size.deckAnswer.pass);
    expect(theme.size.deckAnswer.pass).toBeGreaterThan(theme.size.deckAnswer.record);
  });

  it('lock the two answers while a card is leaving, and never the record', () => {
    render(
      <DeckAnswers
        labels={deckAnswerLabels('Filip N.')}
        onPass={noop}
        onAccept={noop}
        onRecord={noop}
        answering
      />,
    );

    const labels = deckAnswerLabels('Filip N.');
    expect(
      screen.getByRole('button', { name: labels.pass }).props.accessibilityState.disabled,
    ).toBe(true);
    expect(
      screen.getByRole('button', { name: labels.accept }).props.accessibilityState.disabled,
    ).toBe(true);
    expect(
      screen.getByRole('button', { name: labels.record }).props.accessibilityState?.disabled,
    ).toBeFalsy();
  });
});
