import {
  DECLARATION_BODY,
  NOBODY_IS_CONTACTED_BY_SEARCHING,
  WEEK_ADDED_FOR_THIS_SEARCH,
  WEEK_CHANGED_AND_ADDED,
  WEEK_CHANGED_FROM_PROFILE,
  courtEntryBody,
  courtEntrySeatLine,
  courtEntryTag,
  courtEntryTitle,
  declarationOptionLabel,
  declarationTitle,
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
});

describe('the closed control', () => {
  // The control is the card, so the name it carries is the court it opens rather than the
  // verb for the machinery underneath it — and the seat count is what decides which court.
  it('names the court it opens when there is one', () => {
    expect(searchControlLabel({ kind: 'searchable', sport: 'padel' }, { seats: 4 })).toBe(
      'Build the four. Four seats, two a side. Nobody is contacted until you send it.',
    );
    expect(searchControlLabel({ kind: 'searchable', sport: 'tennis' }, { seats: 2 })).toBe(
      'Set up the match. Two seats, one a side. Nobody is contacted until you send it.',
    );
  });

  // The availability step's settled shape: a dead control carries the sentence that explains it.
  it('says what is missing rather than going merely grey', () => {
    expect(searchControlLabel({ kind: 'undeclared', sport: 'padel' }, { seats: 4 })).toBe(
      'Say what kind of game first',
    );
  });

  // 6.1: this app never draws a pressable-looking control that refuses.
  it('is not drawn at all where there is nothing to search for', () => {
    expect(searchControlLabel({ kind: 'no-rated-sport' }, { seats: 4 })).toBeUndefined();
  });
});

describe('the way onto the court', () => {
  /**
   * *The four* is a word about a Sport. Every sentence on the card branches on the seat
   * count, so a squash court is never told to build one — the same rule `builderTitle` is
   * written against, read here off the same helper rather than off a second `seats > 2`.
   */
  it('says four things about a doubles court and two about a singles one', () => {
    expect(courtEntryTitle(4)).toBe('Build the four');
    expect(courtEntryTitle(2)).toBe('Set up the match');

    expect(courtEntryBody(4)).toContain('the evenest four');
    expect(courtEntryBody(2)).toContain('the evenest opponent');

    expect(courtEntrySeatLine(4)).toContain('Four seats · two a side');
    expect(courtEntrySeatLine(2)).toContain('Two seats · one a side');
  });

  /**
   * The pill does two different jobs. On four seats it explains a fact the player did not
   * choose; on two there is nothing to explain, so it says what is being handed over.
   */
  it('explains the seat count only where the count is a surprise', () => {
    expect(courtEntryTag({ seats: 4, sportName: 'Padel' })).toBe('padel is doubles');
    expect(courtEntryTag({ seats: 2, sportName: 'Tennis' })).toBe('you pick the sides');
  });

  /** The half a picture of four seats cannot say for itself, on the card and under it. */
  it('says nobody is contacted, beside the court and beneath it', () => {
    expect(courtEntrySeatLine(4)).toContain('nobody is contacted until you send it');
    expect(NOBODY_IS_CONTACTED_BY_SEARCHING).toContain('You choose whom to challenge');
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

  it('names the sport in the question and keeps the switch out of the answer', () => {
    expect(declarationTitle('Padel')).toBe('What kind of game at Padel?');
    expect(DECLARATION_BODY).toContain('single search');
  });
});
