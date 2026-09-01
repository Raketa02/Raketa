import {
  DECLARATION_BODY,
  WEEK_ADDED_FOR_THIS_SEARCH,
  WEEK_CHANGED_AND_ADDED,
  WEEK_CHANGED_FROM_PROFILE,
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
  it('says the act when there is one', () => {
    expect(searchControlLabel({ kind: 'searchable', sport: 'padel' })).toBe('Search');
  });

  // The availability step's settled shape: a dead control carries the sentence that explains it.
  it('says what is missing rather than going merely grey', () => {
    expect(searchControlLabel({ kind: 'undeclared', sport: 'padel' })).toBe(
      'Say what kind of game first',
    );
  });

  // 6.1: this app never draws a pressable-looking control that refuses.
  it('is not drawn at all where there is nothing to search for', () => {
    expect(searchControlLabel({ kind: 'no-rated-sport' })).toBeUndefined();
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
