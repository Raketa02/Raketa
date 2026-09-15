import {
  DECLARATION_BODY,
  DECLARATION_EYEBROW,
  MODE_HEADING,
  WEEK_ADDED_FOR_THIS_SEARCH,
  WEEK_CHANGED_AND_ADDED,
  WEEK_CHANGED_FROM_PROFILE,
  courtEntryLabel,
  courtEntryTitle,
  declarationOptionLabel,
  declarationLine,
  declarationTitle,
  intentGloss,
  intentLabel,
  modeControlLabel,
  modeLabel,
  searchControlLabel,
  weekFootnote,
} from './findAGamePresentation';
import { modeWord } from './searchPresentation';

describe('the two vocabularies for one kind of evening', () => {
  it('gives a control Title case and a sentence lower case', () => {
    expect(modeLabel('FOR_FUN')).toBe('For fun');
    expect(modeWord('FOR_FUN')).toBe('for fun');
  });

  // The arity gap is ADR-0094's central move, and it is visible in the copy.
  it('has a third label for the declaration, and it says something', () => {
    expect(intentLabel('NO_PREFERENCE')).toBe('Either suits me');
  });
});

describe('telling the two rows of answers apart', () => {
  it('names each by what it commits to, where the visible words are the same', () => {
    expect(modeControlLabel('COMPETITIVE')).toBe('Competitive, this search');
    expect(declarationOptionLabel('COMPETITIVE', 'Padel')).toBe('Competitive, your usual at Padel');
  });

  /**
   * The two never appear together any more (#293), and the lifetime is said where it can be
   * acted on rather than in a heading over a region: `modeControlLabel` announces it on the
   * control, and the declaration's own eyebrow and title carry *your usual*.
   */
  it('keeps the durable answer named on the surfaces that own it', () => {
    expect(MODE_HEADING).toBe('What kind of game');

    expect(DECLARATION_EYEBROW).toBe('Kept on your profile');
    expect(declarationTitle('Padel')).toContain('usual');

    // And the two headings no longer differ by two words and a question mark.
    expect(declarationTitle('Padel')).not.toContain(MODE_HEADING);
  });

  /**
   * Three near-synonyms in a column need saying what each one means to whoever reads it, and
   * *Either suits me* needs it most: indifference is an answer somebody gave.
   */
  it('glosses every answer, in one line each about the player', () => {
    for (const intent of ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const) {
      expect(intentGloss(intent)).not.toBe('');
      expect(intentGloss(intent)).not.toContain('\n');
      expect(intentGloss(intent)).not.toBe(intentLabel(intent));
    }
  });
});

describe('the closed control', () => {
  // The control is the card, so the name it carries is the court it opens rather than the
  // verb for the machinery underneath it — and the seat count is what decides which court.
  it('names the court it opens when there is one', () => {
    expect(
      searchControlLabel({ kind: 'searchable', sport: 'padel', intent: 'FOR_FUN' }, { seats: 4 }),
    ).toBe('Build a doubles. Four seats, two a side.');
    expect(
      searchControlLabel({ kind: 'searchable', sport: 'tennis', intent: 'FOR_FUN' }, { seats: 2 }),
    ).toBe('Build a singles. Two seats, one a side.');
  });

  /**
   * 6.1: this app never draws a pressable-looking control that refuses — and since #293 an
   * undeclared sport draws no court card at all rather than a greyed one saying *Say what kind
   * of game first*. The declaration is a precondition for the form, not a field on it.
   */
  it('is not drawn at all where there is nothing to search for', () => {
    expect(
      searchControlLabel({ kind: 'undeclared', sport: 'padel' }, { seats: 4 }),
    ).toBeUndefined();
    expect(searchControlLabel({ kind: 'no-rated-sport' }, { seats: 4 })).toBeUndefined();
  });
});

describe('the way onto the court', () => {
  /**
   * Every sentence on the card branches on the seat count, so a squash court is never told to
   * build a four — the same rule `builderTitle` is written against, read off the same helper
   * rather than off a second `seats > 2`. The title names the **game**, which is one word
   * apart across the two shapes where *Build the four* against *Set up the match* was all of
   * them.
   */
  it('names the game the sport plays, and says two different things about the two shapes', () => {
    expect(courtEntryTitle(4)).toBe('Build a doubles');
    expect(courtEntryTitle(2)).toBe('Build a singles');
  });

  /**
   * The picture is hidden from the tree — the card is one button — so the shape it draws is
   * the card's spoken name's to say, and it is said nowhere else.
   */
  it('says the shape to a listener, since the court is drawn only for a reader', () => {
    expect(courtEntryLabel(4)).toContain('Four seats, two a side');
    expect(courtEntryLabel(2)).toContain('Two seats, one a side');
  });
});

describe('what the screen says about a temporary week and a permanent answer', () => {
  it('states what a changed week costs, not only that it changed', () => {
    expect(WEEK_CHANGED_FROM_PROFILE).toContain('this search only');
  });

  /**
   * The slot under the grid holds two lines (6.8), and two facts can be true at once — the
   * player edited their week, and a rung added a cell to the search that ran. So the pair is
   * decided here rather than by a screen stacking whichever hold
   * ([#283](https://github.com/Raketa02/Raketa/issues/283)).
   */
  it('says both facts in one sentence, or one of them, or nothing', () => {
    expect(weekFootnote({ improvised: false, addedForThisSearch: false })).toBeUndefined();
    expect(weekFootnote({ improvised: true, addedForThisSearch: false })).toBe(
      WEEK_CHANGED_FROM_PROFILE,
    );
    expect(weekFootnote({ improvised: false, addedForThisSearch: true })).toBe(
      WEEK_ADDED_FOR_THIS_SEARCH,
    );
    expect(weekFootnote({ improvised: true, addedForThisSearch: true })).toBe(
      WEEK_CHANGED_AND_ADDED,
    );
  });

  /**
   * `takenRungLine`'s rule, read on the other screen: the control that offered the widening
   * says *look outside your week* rather than naming a Saturday morning, and the plus on the
   * grid is what says which square it was. Naming it in prose as well would be the one place
   * the feature prints a slot the player never chose.
   */
  it('explains the mark without naming the cell it is on', () => {
    for (const sentence of [WEEK_ADDED_FOR_THIS_SEARCH, WEEK_CHANGED_AND_ADDED]) {
      expect(sentence).toContain('plus');
      expect(sentence).not.toMatch(/Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday/);
      expect(sentence).not.toMatch(/morning|afternoon|evening/);
    }
  });

  /**
   * *Your usual* is the app's own phrase — `declarationOptionLabel` has been announcing it
   * since the interstitial shipped — and the body says **who reads the answer** rather than
   * disambiguating a control that is no longer above it (#293).
   */
  it('names the sport in the question and says who reads the answer', () => {
    expect(declarationTitle('Padel')).toBe('Your usual game at Padel');
    expect(declarationOptionLabel('COMPETITIVE', 'Padel')).toContain('your usual at Padel');

    expect(DECLARATION_BODY).toContain('somebody else’s search');
    expect(DECLARATION_BODY).toContain('a yes on Players becomes a game');
    // The deck reads no declaration any more (ADR-0169 §2), so it is not named as a reader.
    expect(DECLARATION_BODY).not.toContain('Match me');
    // The sentence it replaced pointed at the segment, which is not drawn beside it any more.
    expect(DECLARATION_BODY).not.toContain('above');
  });
});

describe('the declaration, standing under the segment', () => {
  const at = (
    intent: 'COMPETITIVE' | 'FOR_FUN' | 'NO_PREFERENCE',
    mode: 'COMPETITIVE' | 'FOR_FUN',
  ) => declarationLine({ intent, mode, sportName: 'Padel' });

  /**
   * At rest the line is a **statement**: the durable value, named, on a screen it had no
   * representation on at all before ([#294](https://github.com/Raketa02/Raketa/issues/294)).
   */
  it('says what the profile holds, and offers to change it', () => {
    const standing = at('COMPETITIVE', 'COMPETITIVE');

    expect(standing.kind).toBe('agrees');
    expect(standing.spoken).toBe('Your usual at Padel is Competitive');
    expect(standing.value).toBe('Competitive');
    expect(standing.action).toBe('Change');
  });

  /**
   * Moved off the declaration, the **same slot** says what the disagreement costs — and what it
   * does not: other people still find this player as the profile says.
   */
  it('says the durable fact still holds when the switch has moved off it', () => {
    const standing = at('COMPETITIVE', 'FOR_FUN');

    expect(standing.kind).toBe('differs');
    expect(standing.spoken).toBe(
      'Just this search. Players still find you as Competitive at Padel.',
    );
    // The value that does not move is the declaration, never the mode the segment is on.
    expect(standing.value).toBe('Competitive');
    expect(standing.action).toBe('Update');
  });

  /** `declarationAgreesWithMode`'s rule, read on the copy: indifference is contradicted by neither. */
  it('never offers to narrow an answer that said either would do', () => {
    for (const mode of ['COMPETITIVE', 'FOR_FUN'] as const) {
      expect(at('NO_PREFERENCE', mode).kind).toBe('agrees');
      expect(at('NO_PREFERENCE', mode).value).toBe('Either suits me');
    }
  });

  /**
   * Both names carry the **lifetime**, which is this screen's recurring problem: *Competitive*
   * is on it twice, and only *your usual* against *just this search* tells the two apart. The
   * control's name says what pressing it does rather than repeating the word drawn on it.
   */
  it('names both states and both controls by what they commit to', () => {
    expect(at('COMPETITIVE', 'COMPETITIVE').spoken).toContain('Your usual');
    expect(at('COMPETITIVE', 'FOR_FUN').spoken).toContain('Just this search');

    expect(at('COMPETITIVE', 'COMPETITIVE').actionLabel).toBe('Change your usual at Padel');
    expect(at('COMPETITIVE', 'FOR_FUN').actionLabel).toBe('Make For fun your usual at Padel');
  });

  /** The sentence is drawn in pieces and spoken whole — one element, one name. */
  it('hands the screen the same sentence it hands a listener', () => {
    for (const [intent, mode] of [
      ['COMPETITIVE', 'COMPETITIVE'],
      ['COMPETITIVE', 'FOR_FUN'],
    ] as const) {
      const standing = at(intent, mode);
      expect(`${standing.lead}${standing.value}${standing.tail}`).toBe(standing.spoken);
    }
  });
});

describe('the declaration, standing on a surface with no mode', () => {
  const dealing = (intent: 'COMPETITIVE' | 'FOR_FUN' | 'NO_PREFERENCE') =>
    declarationLine({ intent, mode: undefined, sportName: 'Padel' });

  /**
   * `POST /deck` carries no mode — `SearchEnvelope.mode` is null exactly there — so the deal
   * runs on the declaration itself, and the line states that rather than leaving it to be
   * inferred from a control that is missing
   * ([#295](https://github.com/Raketa02/Raketa/issues/295)).
   */
  it('says the deal is dealt on the declaration, and names the kind it deals in', () => {
    expect(dealing('COMPETITIVE').spoken).toBe('Dealing Competitive games at Padel — your usual');
    expect(dealing('FOR_FUN').spoken).toBe('Dealing For fun games at Padel — your usual');
  });

  /**
   * The deck's whole distinction: there is no switch here, so there is nothing for the
   * declaration to disagree with and no state that offers to reconcile the two.
   */
  it('has no drift variant at all, whatever was declared', () => {
    for (const intent of ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const) {
      expect(dealing(intent).kind).toBe('deals');
      expect(dealing(intent).action).toBe('Change');
      expect(dealing(intent).actionLabel).toBe('Change your usual at Padel');
    }
  });

  /**
   * `declarationNamesAKind`'s rule, read on the copy. A `NO_PREFERENCE` player is dealt on the
   * for-fun vector `modeForIntent` **inherits** for them, and printing *dealing for fun games
   * — your usual* would report that inheritance back as the answer they gave. ADR-0094:
   * *"indifference about the kind of evening is not a third kind of evening."*
   */
  it('claims no kind for an answer that named none', () => {
    expect(dealing('NO_PREFERENCE').spoken).toBe(
      'Dealing on your usual at Padel — Either suits me',
    );
    expect(dealing('NO_PREFERENCE').spoken).not.toContain('For fun');
  });

  /** The same contract the other states keep: drawn in pieces, spoken whole. */
  it('hands the screen the same sentence it hands a listener', () => {
    for (const intent of ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const) {
      const line = dealing(intent);
      expect(`${line.lead}${line.value}${line.tail}`).toBe(line.spoken);
      expect(line.value).toBe(intentLabel(intent));
    }
  });
});
