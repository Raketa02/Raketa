import {
  DECLARATION_BODY,
  WEEK_CHANGED_FROM_PROFILE,
  declarationOptionLabel,
  declarationTitle,
  intentLabel,
  modeControlLabel,
  modeLabel,
  searchControlLabel,
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

  it('names the sport in the question and keeps the switch out of the answer', () => {
    expect(declarationTitle('Padel')).toBe('What kind of game at Padel?');
    expect(DECLARATION_BODY).toContain('single search');
  });
});
