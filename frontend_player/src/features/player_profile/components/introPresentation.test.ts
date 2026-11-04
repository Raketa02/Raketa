/**
 * The words the intro step says, and the three sentences a refused line is answered with.
 *
 * The table is keyed by the wire's reason so a reason with no words fails to compile; what
 * is driven here is that every sentence says what to change and never what was matched, that
 * the counter quotes the one cap the rule holds, and that a reason this build cannot read
 * gets the gap's sentence rather than a blank note.
 */

import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import { INTRO_CAP, INTRO_REFUSAL_REASONS } from '../domain/intro';

import {
  INTRO_REFUSAL_SENTENCE,
  introCounter,
  introRefusalSentence,
  spokenIntroCounter,
} from './introPresentation';

describe('the counter', () => {
  it('counts up to the cap, in the house figure', () => {
    expect(introCounter(0)).toBe('0 / 250');
    expect(introCounter(42)).toBe('42 / 250');
    expect(introCounter(INTRO_CAP)).toBe('250 / 250');
  });

  it('keeps counting past the cap rather than clamping, so the overrun is visible', () => {
    // The box takes everything and the sentence under it says what is wrong; a counter that
    // stopped at the cap would hide how far over a paste went.
    expect(introCounter(267)).toBe('267 / 250');
  });

  it('is spoken as a count of characters, with the cap', () => {
    expect(spokenIntroCounter(42)).toBe('42 of 250 characters');
  });
});

describe('the three refusals', () => {
  it('says what to change for each reason, and never what was matched', () => {
    expect(INTRO_REFUSAL_SENTENCE.too_long).toBe('Keep it under 250 characters.');
    expect(INTRO_REFUSAL_SENTENCE.multiline).toBe('One line, no line breaks.');
    expect(INTRO_REFUSAL_SENTENCE.contains_contact).toBe(
      'Leave out phone numbers, emails, links and handles — people reach you in the chat.',
    );
  });

  it('has a sentence for every reason the wire can send', () => {
    // The exhaustiveness the table is typed for, driven: a fourth reason arrives here as a
    // missing entry before it arrives on a phone as a blank note.
    for (const reason of INTRO_REFUSAL_REASONS) {
      expect(introRefusalSentence(reason)).toBe(INTRO_REFUSAL_SENTENCE[reason]);
      expect(introRefusalSentence(reason).length).toBeGreaterThan(0);
    }
  });

  it('says the gap for a reason this build has no words for', () => {
    // The refusal is still the intro's — the way back is still offered — and the sentence is
    // the one every surface says about a code it is too old to read, rather than a blank.
    expect(introRefusalSentence(undefined)).toBe(OUT_OF_DATE_GAP);
  });
});
