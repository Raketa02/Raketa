/**
 * What the end of the part says when it cannot finish.
 *
 * The area is held at the step — *Continue* waits for one (ADR-0200 §10) — and once more here,
 * for a draft that arrives without one and for a picked club the server no longer knows.
 *
 * The week arrives from **both** directions since ADR-0102 gave it a floor: a draft that
 * holds no ticked cell, and a commit the server refused with `weekly_hours_empty`.
 * They are asked for in the same words on purpose — which side noticed is not something a
 * player has any use for — and that is asserted rather than left to two tables that could
 * drift into two sentences.
 *
 * The intro is the other refusal that names a step, and it is a different kind: nothing is
 * *missing* — the line is there and the server will not admit it — so it is drawn in its own
 * sentence, keyed by the reason, with the way back to the step that takes the line.
 */

import { AppError, networkUnavailable } from '@/shared/errors';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { MissingAnswer } from '../domain/profileCommit';

import { answerStillWanted, stepTheCommitRefused } from './commitPresentation';

/** A refusal off the wire, as `mapErrorResponse` would have built it. */
const refusal = (code: string, details?: Record<string, unknown>) =>
  new AppError('validation', 'requires-user-correction', 'diagnostic', {
    code,
    status: 400,
    ...(details === undefined ? {} : { details }),
  });

describe('the answer the last step asks for', () => {
  it('is the week, when nothing was ticked on it', () => {
    // ADR-0102 gave the grid a floor of one, so a blank week is an answer still wanted
    // rather than an answer of *no preference*.
    const wanted = answerStillWanted(['availability', 'gender']);

    expect(wanted?.answer).toBe('availability');
    expect(wanted?.copy.label).toBe('Set when you usually play');
  });

  it('is the area, when that is what the player continued past', () => {
    const wanted = answerStillWanted(['location', 'gender']);

    expect(wanted?.answer).toBe('location');
    expect(wanted?.copy.label).toBe('Set the area you play in');
  });

  it('is the earliest one, so two outstanding answers are not two round trips', () => {
    // `missing` is in step order. Sending the player to the later one would bounce them back
    // here only to be sent to the earlier one next.
    const wanted = answerStillWanted(['availability', 'location']);

    expect(wanted?.answer).toBe('availability');
  });

  it('is nothing when the only question left is the one this step asks', () => {
    // There is no step to go back to: the three answers about the player are immediately
    // above the finish, and what says so is the step's own hint.
    expect(answerStillWanted(['gender'])).toBeUndefined();
  });

  it('is nothing when nothing is outstanding', () => {
    expect(answerStillWanted([])).toBeUndefined();
  });

  it('names a step to go back to for every answer that has one', () => {
    // The exhaustiveness the table is typed for, driven rather than asserted by the compiler
    // alone: a further answer added to `MissingAnswer` arrives here as a missing entry.
    const goesBack: readonly MissingAnswer[] = ['availability', 'location'];

    for (const answer of goesBack) {
      const wanted = answerStillWanted([answer]);
      expect(wanted?.answer).toBe(answer);
      expect(wanted?.copy.title.length).toBeGreaterThan(0);
      expect(wanted?.copy.finishHint.length).toBeGreaterThan(0);
    }
  });
});

describe('a commit the server refused', () => {
  it('reads the week off `weekly_hours_empty`, and offers the step that asks it', () => {
    // **The commit re-validates what the picker already enforced.** A disabled control is
    // absent from a replayed request and from a build that predates the floor, so this
    // refusal is a real thing to render rather than an impossible one.
    const refused = stepTheCommitRefused(refusal('weekly_hours_empty'));

    expect(refused?.step).toBe('availability');
    expect(refused?.label).toBe('Set when you usually play');
  });

  it('reads a picked club the server does not know as the area still wanted, never try again', () => {
    // Sending the same `club_id` again would be refused the same way, so the way back is the
    // location step, in the words the draft would have used for an area it never held.
    const wanted = answerStillWanted(['location']);

    expect(stepTheCommitRefused(refusal('location_club_unknown', { field: 'club_id' }))).toEqual({
      step: 'location',
      body: wanted?.copy.body,
      label: wanted?.copy.label,
    });
    expect(wanted?.copy.body).not.toMatch(/players|match/i);
  });

  it('says the same words the draft would have said about the same answer', () => {
    // Which side noticed is not the player's to care about: they are being asked for the
    // same thing either way, so they are asked for it in the same sentence.
    const wanted = answerStillWanted(['availability']);

    expect(stepTheCommitRefused(refusal('weekly_hours_empty'))).toEqual({
      step: 'availability',
      body: wanted?.copy.body,
      label: wanted?.copy.label,
    });
  });

  it('is the intro, in the sentence its reason names', () => {
    // The refusal's reason and never its pattern: the server says `contains_contact`, and
    // what the player reads is what to leave out — not what was found.
    expect(stepTheCommitRefused(refusal('intro_not_admitted', { reason: 'too_long' }))).toEqual({
      step: 'intro',
      body: 'Keep it under 250 characters.',
      label: 'Change your intro',
    });
    expect(stepTheCommitRefused(refusal('intro_not_admitted', { reason: 'multiline' }))).toEqual({
      step: 'intro',
      body: 'One line, no line breaks.',
      label: 'Change your intro',
    });
    expect(
      stepTheCommitRefused(refusal('intro_not_admitted', { reason: 'contains_contact' })),
    ).toEqual({
      step: 'intro',
      body: 'Leave out phone numbers, emails, links and handles — people reach you in the chat.',
      label: 'Change your intro',
    });
  });

  it('still sends the player back to the intro for a reason this build cannot read', () => {
    // The code is known and the detail is not. The way back is still the intro's; the
    // sentence is the gap's.
    expect(stepTheCommitRefused(refusal('intro_not_admitted', { reason: 'profanity' }))).toEqual({
      step: 'intro',
      body: OUT_OF_DATE_GAP,
      label: 'Change your intro',
    });
  });

  it('names nothing for a refusal about something no step can fix', () => {
    // The generic failure still has the recovery sentence and the promise that nothing was
    // lost. What this table adds is only ever a step to go back to.
    expect(stepTheCommitRefused(refusal('player_profile_already_exists'))).toBeUndefined();
  });

  it('names nothing for a failure that carries no code at all', () => {
    // A transport failure never reached the backend, so there is no code to branch on —
    // and branching on the message instead is what this table exists not to do.
    expect(stepTheCommitRefused(networkUnavailable())).toBeUndefined();
  });
});
