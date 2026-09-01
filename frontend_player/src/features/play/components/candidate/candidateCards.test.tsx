/**
 * The three cards, and the one contract under them.
 *
 * What is asserted here is what
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3 decided and a build session could quietly undo: that they are **three components over
 * one parts kit** rather than one with a `surface` prop, that each draws its own rows and
 * therefore declares its own set, that the social card does not float, and that the volt tag
 * is a sentence.
 *
 * **Each card's drawn set is asserted against the rows it actually renders**, which is the
 * half `reasonSelection.test.ts` cannot do: the rule there takes a set as an argument, and
 * this is the only place the set and the drawing meet.
 */

import { render, screen } from '@testing-library/react-native';
import { Image, StyleSheet, View, type ViewStyle } from 'react-native';

import { courtPosterFor } from '@/features/player_profile/types';
import { formatLevel, formatRange } from '@/shared/formatting/ratingFormat';
import { theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Evidence, ScoredTerm } from '../../domain/evidence';
import type { Term } from '../../domain/vocabulary';

import { COMPETITIVE_CARD_DRAWS, CandidateCard } from './CandidateCard';
import { CandidateCardSocial, SOCIAL_CARD_DRAWS } from './CandidateCardSocial';
import { CandidatePhoto } from './CandidatePhoto';
import { DECK_CARD_DRAWS, DeckCard } from './DeckCard';

const PLAYER = '9f2a1c44-0000-4000-8000-000000000001';
const PHOTO = 'https://photos.example/9f2a1c44?sig=abc';

/** Their area, and the searcher's — two different codes, so nothing prints *In your area*. */
const THEIR_AREA = 'A+050612+0019938';
const MY_AREA = 'A+050700+0019900';

const ENVELOPE: SearchEnvelope = {
  searchId: '11111111-0000-4000-8000-000000000001',
  mode: 'COMPETITIVE',
  myAreaCode: MY_AREA,
  // The pool and the clamp are the empty state's and the ladder's; no card reads either.
  pool: { radiusKmUsed: 12, playersInRange: 7, window: 'THIS_WEEK' },
  radiusClamp: false,
  // The sort row and the ladder are the pool's, and no card reads either.
  sortsAvailable: [],
  rungOffers: null,
  rulesetVersion: 'ruleset-v1',
  engineVersion: 'matchfit-v1',
  // A shortlist is always the searcher's. The builder is the only surface that reads it.
  optimisedFor: 'SEARCHER',
};

/** One term that fired, with the arithmetic that put it where it is. */
function scored(term: Term, evidence: Evidence): ScoredTerm {
  return { term, weight: 10, value: 0.8, contribution: 8, evidence };
}

/** Every term that fires on the fixture, ranked as the wire delivers them. */
const TERMS: readonly ScoredTerm[] = [
  scored('LEVEL_FIT', {
    kind: 'level_fit',
    myMu: 2.71,
    theirMu: 2.83,
    delta: 0.12,
    direction: 'ABOVE',
  }),
  scored('PREDICTED_BALANCE', {
    kind: 'predicted_balance',
    pct: 74,
    mySigma: 0.16,
    theirSigma: 0.14,
    confidence: 66,
  }),
  scored('AVAILABILITY_OVERLAP', {
    kind: 'availability_overlap',
    sharedCount: 3,
    nextSlot: { day: 2, part: 'evening' },
  }),
  scored('DISTANCE', {
    kind: 'distance',
    km: 4,
    areaCode: THEIR_AREA,
    outsideTheirRadius: false,
  }),
  scored('INTENT_ALIGNMENT', {
    kind: 'intent_alignment',
    myMode: 'COMPETITIVE',
    theirIntent: 'COMPETITIVE',
    aligned: true,
  }),
  scored('PLAYING_STYLE', {
    kind: 'playing_style',
    matched: ['PLAYS_TO_WIN'],
    complementary: [],
    clashing: [],
  }),
  scored('SOCIAL_VIBE', {
    kind: 'social_vibe',
    matched: [],
    complementary: [],
    clashing: [],
  }),
];

function candidate(over: Partial<Candidate> = {}): Candidate {
  return {
    playerId: PLAYER,
    fit: 78,
    distanceKm: 4,
    card: {
      nickname: 'Marek',
      photoUrl: PHOTO,
      areaCode: THEIR_AREA,
      socialTags: ['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK'],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    terms: TERMS,
    concerns: [],
    livenessReasons: [],
    // The sheet's three, which no card draws — stated rather than spread away, so a card
    // that started reading one fails here rather than reading an empty list.
    degradedTerms: [],
    modifiers: [],
    ...over,
  };
}

const noop = () => undefined;

function drawCompetitive(over: Partial<Candidate> = {}) {
  render(
    <CandidateCard
      candidate={candidate(over)}
      envelope={ENVELOPE}
      action="ADD_TO_COURT"
      onAction={noop}
      onWhyFit={noop}
    />,
  );
}

function drawSocial(over: Partial<Candidate> = {}) {
  render(
    <CandidateCardSocial
      candidate={candidate(over)}
      envelope={ENVELOPE}
      action="CHALLENGE"
      onAction={noop}
      onWhyFit={noop}
    />,
  );
}

function drawDeck(over: Partial<Candidate> = {}) {
  render(
    <DeckCard
      candidate={candidate(over)}
      envelope={ENVELOPE}
      onPass={noop}
      onAccept={noop}
      onWhyFit={noop}
    />,
  );
}

/** The outermost drawn box, which is the card's own surface on all three. */
function surface(): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getAllByType(View)[0]?.props.style as ViewStyle);
}

describe('one contract, three shapes', () => {
  it('draws both levels on the competitive card and a level row on the other two', () => {
    // The head-to-head row is what makes `LEVEL_FIT` this card's own, and it is why the
    // three are three components rather than one carrying `surface === …`.
    drawCompetitive();
    expect(screen.getByText(formatLevel(2.71))).toBeTruthy();
    expect(screen.getByText(formatLevel(2.83))).toBeTruthy();
    expect(screen.queryByText(/Established/)).toBeNull();
    screen.unmount();

    for (const draw of [drawSocial, drawDeck]) {
      draw();
      expect(
        screen.getByText(
          `${formatLevel(2.83)} · Established · likely ${formatRange({ low: 2.55, high: 2.87 })}`,
        ),
      ).toBeTruthy();
      screen.unmount();
    }
  });

  it('takes the searcher’s own area off the envelope and never prints either code', () => {
    // The one sentence a client is licensed to compute here is a comparison between two
    // codes (ADR-0021), and `area_code` is a coordinate string no card may print.
    drawSocial();
    expect(screen.getByText('4 km')).toBeTruthy();
    expect(screen.queryByText(new RegExp(THEIR_AREA, 'i'))).toBeNull();
    screen.unmount();

    render(
      <CandidateCardSocial
        candidate={candidate()}
        envelope={{ ...ENVELOPE, myAreaCode: THEIR_AREA }}
        action="CHALLENGE"
        onAction={noop}
        onWhyFit={noop}
      />,
    );
    expect(screen.getByText('In your area · 4 km')).toBeTruthy();
  });

  it('draws the forecast as a bar with its word on the competitive card, and as a row on the deck', () => {
    drawCompetitive();
    // The bar is a tint, so the word beside it is what Part 13's *never colour alone* means
    // — and the bar itself merges into the card body rather than announcing a third time.
    expect(screen.getByText('Fairly even · 74%')).toBeTruthy();
    expect(screen.queryByLabelText('Fairly even, 74%')).toBeNull();
    screen.unmount();

    drawDeck();
    expect(screen.getByText('74% even · 66% sure')).toBeTruthy();
  });

  it('says the measured zero rather than counting to nought', () => {
    // Every card that draws an overlap row filters the term's own sentence off, so the row
    // is the only surface §6.2's zero can reach.
    drawSocial({
      terms: TERMS.map((row) =>
        row.term === 'AVAILABILITY_OVERLAP'
          ? scored('AVAILABILITY_OVERLAP', {
              kind: 'availability_overlap',
              sharedCount: 0,
              nextSlot: null,
            })
          : row,
      ),
    });

    expect(screen.getByText('No shared slots — one of you would have to bend')).toBeTruthy();
  });
});

describe('each card’s drawn set', () => {
  /** The set is what the card renders a value for, and therefore will not restate. */
  const RENDERED: Readonly<Record<Term, RegExp>> = {
    LEVEL_FIT: /above you|Level with you/,
    PREDICTED_BALANCE: /^Forecast /,
    AVAILABILITY_OVERLAP: /you both ticked/,
    DISTANCE: /km away/,
    INTENT_ALIGNMENT: /here to compete too/,
    PLAYING_STYLE: /Both of you/,
    SOCIAL_VIBE: /Different around the game/,
    RELIABILITY: /Player Score/,
  };

  it.each([
    ['competitive', drawCompetitive, COMPETITIVE_CARD_DRAWS],
    ['social', drawSocial, SOCIAL_CARD_DRAWS],
    ['deck', drawDeck, DECK_CARD_DRAWS],
  ])('says nothing on the %s card that the card already draws', (_name, draw, drawn) => {
    draw();

    for (const term of drawn) {
      expect(screen.queryByText(RENDERED[term])).toBeNull();
    }
  });

  it('gives the social and the deck card a reason line, which they would otherwise not have', () => {
    // Without one, `INTENT_ALIGNMENT` — third-largest term in both modes — is invisible on
    // two cards of three.
    for (const draw of [drawSocial, drawDeck]) {
      draw();
      expect(screen.getByText("They're here to compete too")).toBeTruthy();
      screen.unmount();
    }
  });

  it('filters first and takes three after, so a card that promised three draws three', () => {
    drawCompetitive();

    for (const line of [
      '3 slots you both ticked · next Tue evening',
      '4 km away',
      "They're here to compete too",
    ]) {
      expect(screen.getByText(line)).toBeTruthy();
    }
  });
});

describe('the volt tag', () => {
  it('is a sentence on an interest lift, and nothing at all without one', () => {
    drawSocial();
    expect(screen.queryByText('They already said yes to you')).toBeNull();
    screen.unmount();

    drawSocial({ inclusionReason: 'INTEREST_LIFT' });
    expect(screen.getByText('They already said yes to you')).toBeTruthy();
  });
});

describe('the photograph', () => {
  it('is drawn from the minted URL', () => {
    render(<CandidatePhoto playerId={PLAYER} photoUrl={PHOTO} box={{ kind: 'thumb' }} />);

    expect(screen.UNSAFE_getByType(Image).props.source).toEqual({ uri: PHOTO });
  });

  it('falls back to the poster on the omitted id, and to that player’s own poster', () => {
    render(<CandidatePhoto playerId={PLAYER} box={{ kind: 'media' }} />);

    expect(screen.UNSAFE_queryByType(Image)).toBeNull();
    // Found only with the hidden elements included, which is the assertion: 6.9's sentence
    // is carried, and §20.1's merge is what keeps it unspoken inside a card.
    expect(
      screen.getByLabelText('A generated court poster, not a photograph', {
        includeHiddenElements: true,
      }),
    ).toBeTruthy();
    // One player id, one poster — the reason the hash is reached rather than re-implemented.
    expect(courtPosterFor(PLAYER)).toEqual(courtPosterFor(PLAYER));
  });

  it('takes a third of its own box as its corner, at every size', () => {
    render(<CandidatePhoto playerId={PLAYER} box={{ kind: 'face', size: 46 }} />);
    const face = StyleSheet.flatten(screen.UNSAFE_getAllByType(View)[0]?.props.style as ViewStyle);

    expect(face.borderRadius).toBeCloseTo(46 * 0.33);
    expect(face.width).toBe(46);
  });
});

describe('what floats', () => {
  it('is the deck card alone — the pool draws one shape twice', () => {
    drawCompetitive();
    const competitive = surface();
    screen.unmount();

    drawSocial();
    const social = surface();
    screen.unmount();

    drawDeck();
    const deck = surface();

    // #219 B3's argument — *it animates in, and translates and rotates out under the thumb* —
    // reaches the deck alone; a row in a scrolling list is not a transient object.
    expect(competitive.borderRadius).toBe(theme.radius.card);
    expect(social.borderRadius).toBe(theme.radius.card);
    expect(social.shadowOpacity).toBeUndefined();
    expect(social.elevation).toBeUndefined();

    expect(deck.borderRadius).toBe(theme.radius.deckCard);
    expect(deck.shadowOpacity).toBe(theme.shadow.deckCard.shadowOpacity);
  });
});

describe('what each control announces', () => {
  it('speaks the card body in §20.3’s order, which is not the order it is drawn', () => {
    drawSocial();

    expect(
      screen.getByLabelText(
        'Marek. Fit 78 out of 100. 2,83 · Established · likely 2,55 – 2,87. 4 km. ' +
          'Forecast 74% even · 66% sure. ' +
          "They're here to compete too. Both of you: Plays to win.",
      ),
    ).toBeTruthy();
  });

  it('states each fact exactly once, in whichever register that card draws it', () => {
    // The competitive card draws no distance row — which is why `DISTANCE` is not in its set
    // and its reason line survives — so a label that also stated the kilometres would say
    // them twice, in the one register nobody can see. It draws the forecast instead, and
    // that one is a clause because the bar it belongs to announces nothing.
    drawCompetitive();

    expect(
      screen.getByLabelText(
        'Marek. Fit 78 out of 100. 2,83 · Established · likely 2,55 – 2,87. ' +
          'Fairly even · 74%. ' +
          '3 slots you both ticked · next Tue evening. 4 km away. ' +
          "They're here to compete too.",
      ),
    ).toBeTruthy();
  });

  it('names the subject on a primary button whose visible word is one of twenty', () => {
    drawCompetitive();
    expect(screen.getByLabelText('Add Marek to the court')).toBeTruthy();
    screen.unmount();

    drawSocial();
    expect(screen.getByLabelText('Challenge Marek')).toBeTruthy();
  });

  it('keeps the 🎾 out of the deck’s spoken answer and in its visible one', () => {
    drawDeck();

    expect(screen.getByLabelText("Let's play, Marek")).toBeTruthy();
    expect(screen.getByText("🎾 Let's play")).toBeTruthy();
    expect(screen.getByLabelText('Not today, Marek')).toBeTruthy();
  });
});
