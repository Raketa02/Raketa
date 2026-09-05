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
import { Image, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { courtPosterFor } from '@/features/player_profile/types';
import { formatLevel, formatRange, formatSignedLevel } from '@/shared/formatting/ratingFormat';
import { balanceShare, courtSeatCount, theme } from '@/shared/ui';

import type { Candidate, SearchEnvelope } from '../../domain/candidate';
import type { Evidence, ScoredTerm } from '../../domain/evidence';
import type { Term } from '../../domain/vocabulary';
import { toCandidate } from '../../mappers/candidateMappers';
import type { Wire } from '@/test-support/transport';

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
  // Last, so it is the lowest-ranked survivor everywhere: what it is here for is the drop on
  // the competitive card, and a term that displaced somebody's third reason line would be
  // testing the cap instead (#312).
  scored('RELIABILITY', { kind: 'reliability', score: 74, floorBreached: false }),
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

/**
 * A **wire** candidate, for the one assertion that has to cross the mapper.
 *
 * Everything else here builds a `Candidate` directly, because a card takes one — but §3's drop
 * happens at the mapper and an unknown tag id is unrepresentable on the domain side, so the only
 * honest way to assert it is to send one in.
 */
function wireRow(over: Partial<Wire['CandidateSchema']> = {}): Wire['CandidateSchema'] {
  return {
    player_id: PLAYER,
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname: 'Marek',
      area_code: THEIR_AREA,
      social_tags: ['PLAYS_TO_WIN'],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
    ...over,
  } as Wire['CandidateSchema'];
}

/** The Sport is the screen's, so the card is handed one — it is never on `player_card`. */
const SPORT_NAME = 'Tennis';

/**
 * The same Sport counted, and one that is not.
 *
 * Read off `Court`'s own coordinates rather than written as 2 and 4, because that is what the
 * card is handed: a fixture that hardcoded the numbers would keep passing on the day a sport
 * changed how many people stand on it.
 */
const SINGLES = courtSeatCount('tennis');
const DOUBLES = courtSeatCount('padel');

function drawCompetitive(over: Partial<Candidate> = {}, bestMatch = false, seats = SINGLES) {
  render(
    <CandidateCard
      candidate={candidate(over)}
      envelope={ENVELOPE}
      sportName={SPORT_NAME}
      seats={seats}
      action="ADD_TO_COURT"
      onAction={noop}
      onWhyFit={noop}
      bestMatch={bestMatch}
    />,
  );
}

/** A candidate the platform has actually watched — the card #312 drew for the first time. */
function withRecord(over: Partial<Candidate['card']> = {}): Partial<Candidate> {
  return {
    card: {
      ...candidate().card,
      playerScore: 74,
      countedGames: 29,
      lastFive: ['WIN', 'LOSS', 'WIN', 'WIN', 'LOSS'],
      ...over,
    },
  };
}

/** What a counted game would move, as the server sends it: `winDelta > 0 > lossDelta`. */
const AT_STAKE = { winDelta: 0.08, lossDelta: -0.05 } as const;

/** Every term except the one named — the shape a stood-down term arrives in (§8). */
function without(term: Term): readonly ScoredTerm[] {
  return TERMS.filter((row) => row.term !== term);
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

/**
 * The card body's own spoken name — the label §20.3 fixes the order of.
 *
 * Read off the outermost element rather than matched whole, so an assertion about one clause
 * says only that: the full-string assertions live in *what each control announces*, and a test
 * about the tag row should not need editing when a reason line is re-worded.
 */
function spokenBody(): string {
  return screen.UNSAFE_getAllByType(View)[0]?.props.accessibilityLabel as string;
}

/** The outermost drawn box, which is the card's own surface on all three. */
function surface(): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getAllByType(View)[0]?.props.style as ViewStyle);
}

/** Every drawn box on screen, flattened — the two helpers below both read the band off it. */
function boxes(): readonly ViewStyle[] {
  return screen
    .UNSAFE_getAllByType(View)
    .map((box) => StyleSheet.flatten(box.props.style as ViewStyle))
    .filter((style): style is ViewStyle => style !== undefined);
}

/** The bar's track if it is drawn at all, found by the one radius only it draws. */
function drawnTrack(): ViewStyle | undefined {
  return boxes().find((style) => style.borderRadius === theme.radius.balanceBar);
}

function track(): ViewStyle {
  const found = drawnTrack();
  if (found === undefined) throw new Error('no balance bar on screen');
  return found;
}

/**
 * The fold, as the drawn width of your own segment.
 *
 * Read from **inside** the track rather than from anywhere on screen: a percentage width is
 * not unique to the bar, and a helper that found the first one anywhere would keep passing
 * while measuring something else entirely.
 */
function yoursWidth(): string {
  const all = boxes();
  const at = all.findIndex((style) => style.borderRadius === theme.radius.balanceBar);
  if (at < 0) throw new Error('no balance bar on screen');

  const found = all.slice(at + 1).find((style) => typeof style.width === 'string');
  if (found === undefined) throw new Error('no balance segment inside the bar');
  return String(found.width);
}

describe('one contract, three shapes', () => {
  it('draws both levels on the competitive card and a level row on the other two', () => {
    // The head-to-head row is what makes `LEVEL_FIT` this card's own, and it is why the
    // three are three components rather than one carrying `surface === …`.
    drawCompetitive();
    expect(screen.getByText(formatLevel(2.71))).toBeTruthy();
    // Twice: hugely on the photo panel, and again on the right of the band. The panel states
    // what they published and the band states one side of a comparison — one fact drawn twice
    // and said once, which is what §10 is about.
    expect(screen.getAllByText(formatLevel(2.83))).toHaveLength(2);
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

  it('draws the forecast as a band with its word on the competitive card, and as a row on the deck', () => {
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
    // The reason line and never the block, which is the same two words with nothing after
    // them: the card draws *Player Score* over a figure now, and what §5 drops is the
    // sentence `Player Score {score}`.
    RELIABILITY: /^Player Score \d/,
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

  /**
   * §5 booked this the day the block was specified — *"`RELIABILITY` joins them the day the
   * Player Score block prints and not before"* — and #312 is that day.
   */
  it('stops saying Player Score as a sentence now the competitive card prints it', () => {
    expect(COMPETITIVE_CARD_DRAWS).toContain('RELIABILITY');

    drawCompetitive(withRecord());
    expect(screen.queryByText(/^Player Score \d/)).toBeNull();
    screen.unmount();

    // And leaves it on the cards that draw no block, which is what keeps it a per-card rule.
    // It is the lowest-ranked term on the fixture, so it is asserted where the cap cannot
    // reach it: a card whose only firing term is this one.
    drawSocial({
      terms: [scored('RELIABILITY', { kind: 'reliability', score: 74, floorBreached: false })],
    });
    expect(screen.getByText('Player Score 74')).toBeTruthy();
  });

  /**
   * §5's *When nothing survives* claim, **re-checked rather than re-read**.
   *
   * The surviving set is one term smaller than it was, so the claim is worth confirming rather
   * than inheriting. It rests on two things and #312 touched neither: `DISTANCE` never stands
   * down, and this card draws no distance row — so the sentence for it is never filtered and a
   * survivor always exists, even on a candidate with nothing else firing and no liveness
   * reason to fall back to.
   */
  it('cannot run out of reasons, with the surviving set one term smaller', () => {
    expect(COMPETITIVE_CARD_DRAWS).not.toContain('DISTANCE');

    drawCompetitive({
      terms: TERMS.filter((row) => COMPETITIVE_CARD_DRAWS.includes(row.term as Term)).concat(
        TERMS.filter((row) => row.term === 'DISTANCE'),
      ),
      livenessReasons: [],
    });

    expect(screen.getByText('4 km away')).toBeTruthy();
  });
});

describe('the volt tag', () => {
  it('is a sentence on the social card, which #309 did not touch', () => {
    drawSocial();
    expect(screen.queryByText('They already said yes to you')).toBeNull();
    screen.unmount();

    drawSocial({ inclusionReason: 'INTEREST_LIFT' });
    expect(screen.getByText('They already said yes to you')).toBeTruthy();
  });

  it('is two words beside the handle on the competitive card, which #309 reversed', () => {
    // #231's open decision #14 turned it into a sentence because *"a full sentence does not go
    // where a two-word tag went"*. The two-word form was never gone — it is the liveness
    // twin's, and §10 says the two codes are two facts with ONE tag.
    drawCompetitive({ inclusionReason: 'INTEREST_LIFT' });

    expect(screen.getByText('Wants to play you')).toBeTruthy();
    expect(screen.queryByText('They already said yes to you')).toBeNull();
  });

  it('replaces the coral tag where both would fall on the same card', () => {
    drawCompetitive({ inclusionReason: 'INTEREST_LIFT' }, true);

    expect(screen.getByText('Wants to play you')).toBeTruthy();
    expect(screen.queryByText('Best match')).toBeNull();
  });

  it('leaves the handle bare where neither fact is true', () => {
    drawCompetitive();

    expect(screen.queryByText('Wants to play you')).toBeNull();
    expect(screen.queryByText('Best match')).toBeNull();
  });

  it('draws the coral tag only where the ordering rule says so', () => {
    drawCompetitive({}, true);

    expect(screen.getByText('Best match')).toBeTruthy();
  });
});

/**
 * The green border, which is the tag's second copy and never its replacement.
 *
 * It is bound to **the tag that is drawn** rather than to `inclusionReason` beneath it, so the
 * one card whose handle says *Wants to play you* is the one card outlined — the two cannot come
 * apart on a card wearing the coral tag, and Part 13's *never colour alone* is discharged by the
 * word rather than by the outline ([#310](https://github.com/Raketa02/Raketa/issues/310)).
 */
describe('the border on a lifted card', () => {
  it('is voltStroke where the volt tag is, and volt is nowhere near it', () => {
    drawCompetitive({ inclusionReason: 'INTEREST_LIFT' });

    expect(surface().borderColor).toBe(theme.color.voltStroke);
    // The refusal that survived #309: volt itself is 1,25 on surface and would be no border.
    expect(surface().borderColor).not.toBe(theme.color.volt);
  });

  it('is the ordinary card border where nobody said yes, coral tag or not', () => {
    drawCompetitive({}, true);

    expect(surface().borderColor).toBe(theme.color.line);
  });

  it('is not drawn on the social card, which #309 left alone and says it in a sentence', () => {
    drawSocial({ inclusionReason: 'INTEREST_LIFT' });

    expect(surface().borderColor).toBe(theme.color.line);
    expect(screen.getByText('They already said yes to you')).toBeTruthy();
  });
});

/**
 * **The Social tag row** — the four answers, and the three spellings of absence between them.
 *
 * The rule is `domain/socialTagOverlap`'s and is unit-tested there; what these assert is the half
 * that only a rendered card can show — that what is drawn is what is spoken, and that the one
 * sentence which is a **claim** is drawn in the one state that earned it.
 */
describe('the social tag row', () => {
  const tagTerm = (kind: 'playing_style' | 'social_vibe', over: object = {}) =>
    scored(kind === 'playing_style' ? 'PLAYING_STYLE' : 'SOCIAL_VIBE', {
      kind,
      matched: [],
      matchedInFull: true,
      complementary: [],
      clashing: [],
      ...over,
    } as Evidence);

  it('draws every tag they published and marks the shared ones in words', () => {
    drawCompetitive({ terms: [tagTerm('playing_style', { matched: ['PLAYS_TO_WIN'] })] });

    // The tint is the second cue. The marker is the first, and it is on the chip itself.
    expect(screen.getByText('🏆 Plays to win · you too')).toBeTruthy();
    expect(screen.getByText('🍻 Stays for a drink')).toBeTruthy();
  });

  /**
   * §10 — *the fact is said once*, across the two registers. `tagTermReason`'s precedence is
   * matched first, so a term with anything matched writes `Both of you: …` — the same ids the
   * row has just drawn as chips. The chips are the richer form and the sentence goes.
   */
  it('takes the Both of you sentence off the card the chips are on', () => {
    drawCompetitive({ terms: [tagTerm('playing_style', { matched: ['PLAYS_TO_WIN'] })] });
    expect(screen.queryByText(/Both of you/)).toBeNull();
    screen.unmount();

    // And leaves it on the card that draws no row, which is what keeps it a per-card rule.
    drawSocial({ terms: [tagTerm('playing_style', { matched: ['PLAYS_TO_WIN'] })] });
    expect(screen.getByText('Both of you: Plays to win')).toBeTruthy();
  });

  /** Complementary and clashing are a different relationship and stay prose — the ticket's own. */
  it('keeps a complementary pair as a sentence and tints nothing off it', () => {
    drawCompetitive({
      terms: [
        tagTerm('playing_style', {
          complementary: [{ a: 'PLAYS_TO_WIN', b: 'QUIET_AND_FOCUSED' }],
        }),
      ],
    });

    expect(screen.getByText('Plays to win meets Quiet and focused')).toBeTruthy();
    expect(screen.queryByText(/· you too/)).toBeNull();
  });

  it('stands the amber line in the row’s place when they fired and shared nothing', () => {
    // Both columns, because the claim needs both — one alone is a half-comparison and draws
    // the tags untinted instead.
    drawCompetitive({ terms: [tagTerm('playing_style'), tagTerm('social_vibe')] });

    expect(screen.getByText('No tags in common')).toBeTruthy();
    // In its place: the tags themselves are not drawn under a line saying none of them matched.
    expect(screen.queryByText('🏆 Plays to win')).toBeNull();
  });

  it('draws untinted tags and no amber line when the terms stood down', () => {
    // Nothing compared them, so *No tags in common* would be a claim rather than an answer.
    drawCompetitive({ terms: [] });

    expect(screen.getByText('🏆 Plays to win')).toBeTruthy();
    expect(screen.getByText('🍻 Stays for a drink')).toBeTruthy();
    expect(screen.queryByText('No tags in common')).toBeNull();
    expect(screen.queryByText(/· you too/)).toBeNull();
  });

  /**
   * The third spelling. `matched` is narrowed at the mapper against the same nineteen the
   * labels come from, so an old build sees an empty list where the platform found an overlap —
   * and `matchedInFull` is what stops that becoming the amber claim.
   */
  it('says nothing about the overlap when the match is a tag it cannot name', () => {
    drawCompetitive({
      terms: [tagTerm('playing_style', { matchedInFull: false }), tagTerm('social_vibe')],
    });

    expect(screen.queryByText('No tags in common')).toBeNull();
    expect(screen.getByText('🏆 Plays to win')).toBeTruthy();
  });

  /**
   * The same claim, one register over. `tagTermReason` falls through to the term's **measured
   * zero** when nothing matched — *"Different on court, not incompatible"* — which is *No tags
   * in common* in prose, on every card rather than one. A term that matched something did not
   * score zero, so the bit closes that branch too.
   */
  it('withholds the measured zero as well, which is the same claim as a sentence', () => {
    drawCompetitive({ terms: [tagTerm('playing_style', { matchedInFull: false })] });
    expect(screen.queryByText(/Different on court/)).toBeNull();
    screen.unmount();

    // And says it where nothing was narrowed away, which is what makes it a real zero.
    drawSocial({ terms: [tagTerm('playing_style')] });
    expect(screen.getByText(/Different on court/)).toBeTruthy();
  });

  /**
   * §3, end to end — and it is walked through the **mapper** on purpose.
   *
   * `Candidate.card.socialTags` is `SocialTagId[]`, so an unknown id cannot be handed to a card
   * at all: the type is the guarantee and the narrowing is the mapper's. A card-level fixture
   * that simply left a known tag out would assert nothing about an unknown one, so the wire row
   * goes through `toCandidate` and the card draws what comes back.
   */
  it('drops an id this build has no words for rather than drawing it blank', () => {
    const drawn = toCandidate(
      wireRow({
        player_card: {
          ...wireRow().player_card,
          social_tags: ['PLAYS_TO_WIN', 'DOES_A_CROSSWORD'],
        },
      }),
    );

    render(
      <CandidateCard
        candidate={drawn}
        envelope={ENVELOPE}
        sportName={SPORT_NAME}
        seats={SINGLES}
        action="ADD_TO_COURT"
        onAction={noop}
        onWhyFit={noop}
      />,
    );

    expect(screen.getByText('🏆 Plays to win')).toBeTruthy();
    // No blank chip, no placeholder, and no `undefined undefined` where the glyph would go.
    expect(screen.queryByText(/undefined/)).toBeNull();
    expect(screen.UNSAFE_getAllByType(Text).filter((t) => t.props.children === '')).toEqual([]);
  });

  it('is drawn on the competitive card alone, which is where the label can carry it', () => {
    for (const draw of [drawSocial, drawDeck]) {
      draw({ terms: [tagTerm('playing_style', { matched: ['PLAYS_TO_WIN'] })] });
      expect(screen.queryByText(/· you too/)).toBeNull();
      expect(screen.queryByText('No tags in common')).toBeNull();
      screen.unmount();
    }
  });

  it('speaks what it draws, in each of the three states that draw anything', () => {
    drawCompetitive({ terms: [tagTerm('playing_style', { matched: ['PLAYS_TO_WIN'] })] });
    expect(spokenBody()).toContain('Tags you share: Plays to win');
    expect(spokenBody()).toContain('Their other tags: Stays for a drink');
    screen.unmount();

    drawCompetitive({ terms: [] });
    expect(spokenBody()).toContain('Their tags: Plays to win, Stays for a drink');
    screen.unmount();

    drawCompetitive({ terms: [tagTerm('playing_style'), tagTerm('social_vibe')] });
    expect(spokenBody()).toContain('No tags in common');
  });
});

/**
 * **The three record blocks** — what the platform watched, and the one spelling absence has.
 *
 * The fields are omitted rather than sent as `0`, and the whole of what these assert is that
 * the drawing keeps that distinction: a block whose fact is absent is **hidden**, a run of
 * three is drawn as three, and a card for somebody nothing has ever been arranged for draws
 * none of the three and is a correct card ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 */
describe('the record block', () => {
  /** Every square drawn on screen, found by the one size only the run of form draws. */
  function squares(): readonly ViewStyle[] {
    return boxes().filter((style) => style.width === theme.size.recordSquare);
  }

  it('draws the three facts the platform watched, each under its own name', () => {
    drawCompetitive(withRecord());

    expect(screen.getByText('Player Score')).toBeTruthy();
    expect(screen.getByText('74')).toBeTruthy();
    expect(screen.getByText('Counted')).toBeTruthy();
    expect(screen.getByText('29')).toBeTruthy();
    expect(screen.getByText('Last 5')).toBeTruthy();
    expect(squares()).toHaveLength(5);
  });

  it('draws none of the three for a brand-new player, and that is a correct card', () => {
    // Never zeroed: somebody nothing was ever arranged for has not failed to turn up, and
    // *Player Score 0 · Counted 0* would be two invented numbers.
    drawCompetitive();

    expect(screen.queryByText('Player Score')).toBeNull();
    expect(screen.queryByText('Last 5')).toBeNull();
    expect(screen.queryByText('Counted')).toBeNull();
    expect(squares()).toHaveLength(0);
  });

  it('hides one block without hiding the two beside it', () => {
    // Three independent absences, not one. A player whose games were all unscored has a count
    // and no run, and the contract calls that pair consistent rather than broken.
    drawCompetitive(withRecord({ lastFive: undefined }));

    expect(screen.getByText('Player Score')).toBeTruthy();
    expect(screen.getByText('Counted')).toBeTruthy();
    expect(screen.queryByText('Last 5')).toBeNull();
  });

  it('draws the gap rather than padding the run to five', () => {
    // The gap IS the statement: three squares means three counted results, and a fourth drawn
    // in some neutral fill would claim a game nobody played.
    drawCompetitive(withRecord({ lastFive: ['WIN', 'WIN', 'LOSS'] }));

    expect(squares()).toHaveLength(3);
  });

  it('tells a win from a loss by fill, in two neutrals rather than two hues', () => {
    // The ratios are `recordSquares.test.ts`'s; what is asserted here is that the drawing uses
    // the pair that file derives, so a repaint cannot happen in one place only.
    drawCompetitive(withRecord({ lastFive: ['WIN', 'LOSS'] }));

    expect(squares().map((style) => style.backgroundColor)).toEqual([
      theme.color.ink,
      theme.color.muted,
    ]);
  });

  it('speaks the run as a count against its own length, never as five elements', () => {
    // Colour is never the only signal, and a listener handed five squares has nothing at all.
    // Five clauses would read the row as a table, so the row is one clause and it counts.
    drawCompetitive(withRecord());
    expect(spokenBody()).toContain('3 of the last 5 won');
    screen.unmount();

    // And the denominator is the real one — a run of three says *of the last 3*, because
    // padding in words is the same lie as padding in squares.
    drawCompetitive(withRecord({ lastFive: ['WIN', 'WIN', 'LOSS'] }));
    expect(spokenBody()).toContain('2 of the last 3 won');
  });

  it('speaks the other two blocks with the scale and the noun the drawing leaves off', () => {
    drawCompetitive(withRecord());

    // Two out-of-a-hundred figures on one card, so this one says what it is out of — and the
    // count says what it is a count of, which the box's own name does for a reader.
    expect(spokenBody()).toContain('Player Score 74 out of 100');
    expect(spokenBody()).toContain('29 counted games');
  });

  it('says nothing about a record on the two cards that draw none', () => {
    for (const draw of [drawSocial, drawDeck]) {
      draw(withRecord());
      expect(screen.queryByText('Player Score')).toBeNull();
      // Nor in the register nobody can see: `candidateFacts` is not asked for a record, so
      // there are no clauses to compose rather than clauses that were left out.
      expect(screen.queryByLabelText(/counted games/)).toBeNull();
      screen.unmount();
    }
  });
});

/**
 * **What's at stake** — two figures, and the three reasons a card may not print them.
 *
 * The absence in for fun and the absence for an unrated pair are the contract's and arrive as
 * no field. The doubles one is the client's, and it is the interesting one: the figures are
 * real, the server sent them, and the card still must not draw them.
 */
describe('what is at stake', () => {
  it('draws both figures as served on a singles court, signed', () => {
    drawCompetitive({ ...withRecord(), atStake: AT_STAKE });

    expect(screen.getByText('Win, counted')).toBeTruthy();
    expect(screen.getByText(formatSignedLevel(0.08))).toBeTruthy();
    expect(screen.getByText('Lose, counted')).toBeTruthy();
    expect(screen.getByText(formatSignedLevel(-0.05))).toBeTruthy();
  });

  it('signs the gain and never invents the loss’s minus', () => {
    drawCompetitive({ atStake: AT_STAKE });

    expect(screen.getByText('+0,08')).toBeTruthy();
    // U+2212, and the server's own sign — nothing here negates a figure to draw it.
    expect(screen.getByText('\u22120,05')).toBeTruthy();
  });

  it('hides them on a doubles seat, where the other three seats are unknown', () => {
    // A win against one named person isn't a thing that exists until the four are known. The
    // server prices the pairing anyway, so this is a refusal to draw rather than an absence.
    drawCompetitive({ atStake: AT_STAKE }, false, DOUBLES);

    expect(screen.queryByText('Win, counted')).toBeNull();
    expect(screen.queryByText('Lose, counted')).toBeNull();
    expect(spokenBody()).not.toContain('Win, counted');
  });

  it('draws nothing where the field never crossed, which is an unrated pair', () => {
    // `at_stake` is omitted in competitive too, where either of them holds no rating in this
    // sport — the card has nothing to hide rather than something to refuse.
    drawCompetitive();

    expect(screen.queryByText('Win, counted')).toBeNull();
    expect(screen.queryByText('Lose, counted')).toBeNull();
  });

  it('is absent in for fun, where the card that draws it is not the card on screen', () => {
    // *A counted result is meaningless rather than unavailable.* The field never crosses, and
    // the surface a for-fun pool draws has no box for it — asserted on the card rather than
    // taken on trust, and with the figures present so the absence is the surface's own.
    for (const draw of [drawSocial, drawDeck]) {
      draw({ atStake: AT_STAKE });
      expect(screen.queryByText('Win, counted')).toBeNull();
      expect(screen.queryByText('Lose, counted')).toBeNull();
      expect(screen.queryByLabelText(/counted \+0,08/)).toBeNull();
      screen.unmount();
    }
  });

  it('speaks both or neither, because one of them is half a symmetrical fact', () => {
    drawCompetitive({ atStake: AT_STAKE });

    expect(spokenBody()).toContain('Win, counted +0,08');
    expect(spokenBody()).toContain('Lose, counted \u22120,05');
  });
});

describe('the photo panel', () => {
  it('prints the level they published, over a pinned scrim', () => {
    // The panel is the card's identity: what this person published, drawn whatever fired. The
    // scrim is what makes a white label over an unknowable ground computable at all — the
    // ratio itself is `textOnMedia.test.ts`'s.
    drawCompetitive();

    const scrims = screen
      .UNSAFE_getAllByType(View)
      .map((box) => StyleSheet.flatten(box.props.style as ViewStyle))
      .filter((style) => style?.backgroundColor === theme.color.photoScrim);

    expect(scrims).toHaveLength(1);
  });

  it('keeps the level when the term behind the band stands down', () => {
    // `player_card.level` and `level_fit.theirMu` are two fields, and the panel takes the
    // published one precisely so a stood-down term cannot blank the card's identity.
    drawCompetitive({ terms: without('LEVEL_FIT') });

    expect(screen.getByText(formatLevel(2.83))).toBeTruthy();
  });

  it('draws the search’s sport, capitalised, and never one off the candidate', () => {
    drawCompetitive();

    expect(screen.getByText(SPORT_NAME)).toBeTruthy();
  });

  it('draws the same panel over the generated poster', () => {
    // Nothing about the panel branches on whether there is a photograph: the scrim clears AA
    // over every poster stop by construction, so the level and the sport are drawn identically.
    drawCompetitive({ card: { ...candidate().card, photoUrl: undefined } });

    expect(screen.UNSAFE_queryByType(Image)).toBeNull();
    // Both of them still: the panel's and the band's, exactly as over a photograph.
    expect(screen.getAllByText(formatLevel(2.83))).toHaveLength(2);
    expect(screen.getByText(SPORT_NAME)).toBeTruthy();
  });
});

describe('the head-to-head band', () => {
  it('draws one bar with its segment labels, at the size that carries them', () => {
    drawCompetitive();

    // `sm` drops labels because there is no room beside the fold for a 9,5pt line, and it is
    // 16 tall. The band is taller, so the caller picks the size that carries them rather than
    // changing the floor — read off the drawn track, which is where the choice shows.
    expect(track().height).toBe(theme.size.balanceBar.md);
    // Drawn and hidden with the bar they sit inside: the bar's whole spoken name is
    // `balanceLabel`, and two segment captions announced beside it would be it said twice.
    expect(screen.getByText('you', { includeHiddenElements: true })).toBeTruthy();
    expect(screen.getByText('them', { includeHiddenElements: true })).toBeTruthy();
  });

  it('folds at the level advantage and never at the forecast', () => {
    // The bar says WHICH side and the figure says HOW even. They are two facts, and a bar fed
    // the forecast would be the client deriving one from the other. Asserted on the drawn
    // fold, so it is the picture that is checked rather than the argument passed.
    drawCompetitive();

    expect(yoursWidth()).toBe(`${balanceShare(2.71 - 2.83)}%`);
    expect(yoursWidth()).not.toBe(`${balanceShare(74)}%`);
  });

  it('collapses to the row the card drew before it, when only the forecast fired', () => {
    // `PREDICTED_BALANCE` is in the drawn set whether or not the band can draw it, so its
    // reason line is filtered off either way — a band that simply vanished would take the fact
    // off the card in both registers at once.
    drawCompetitive({ terms: without('LEVEL_FIT') });

    expect(drawnTrack()).toBeUndefined();
    expect(screen.getByText('Predicted balance')).toBeTruthy();
    expect(screen.getByText('Fairly even · 74%')).toBeTruthy();
  });

  it('draws neither the bar nor a tint when the forecast stood down', () => {
    drawCompetitive({ terms: without('PREDICTED_BALANCE') });

    expect(drawnTrack()).toBeUndefined();
    expect(screen.getByText(formatLevel(2.71))).toBeTruthy();
  });
});

describe('the card’s border', () => {
  it('is never coral, which stays 5.1’s pressed state and not a permanent one', () => {
    // The designs draw coral on every competitive card. That refusal is untouched by #310: a
    // permanent coral outline is every row under an imaginary finger, and 1.2 is *when
    // everything is accented, nothing is*. The green one is a different colour and a different
    // claim — it marks one row, and only where somebody has actually said yes.
    for (const lifted of [{}, { inclusionReason: 'INTEREST_LIFT' as const }]) {
      drawCompetitive(lifted);
      expect(surface().borderColor).not.toBe(theme.color.coral);
      screen.unmount();
    }
  });

  it('is the workhorse line on an ordinary row', () => {
    drawCompetitive();

    expect(surface().borderColor).toBe(theme.color.line);
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
          // The tag row's clauses, between the identifying facts and the argument — and
          // grouped, because a listener hearing *you too* once per tag is being read a table.
          'Tags you share: Plays to win. Their other tags: Stays for a drink. ' +
          '3 slots you both ticked · next Tue evening. 4 km away. ' +
          "They're here to compete too.",
      ),
    ).toBeTruthy();
  });

  it('carries the record and the stake in §20.3’s order, between the band and the tags', () => {
    // Five more clauses, all of them identifying facts: what the platform watched, then what
    // this pairing would move, then what the candidate published, then the argument. §20.3's
    // one divergence from visual order is about the reasons and does not reach any of them.
    drawCompetitive({ ...withRecord(), atStake: AT_STAKE });

    expect(
      screen.getByLabelText(
        'Marek. Fit 78 out of 100. 2,83 · Established · likely 2,55 – 2,87. ' +
          'Fairly even · 74%. ' +
          'Player Score 74 out of 100. 3 of the last 5 won. 29 counted games. ' +
          'Win, counted +0,08. Lose, counted \u22120,05. ' +
          'Tags you share: Plays to win. Their other tags: Stays for a drink. ' +
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
