/**
 * The card's words — the two the ticket names, the control that has to name the act it is
 * about to make final, and the refusals.
 */

import { AppError, offlineMessage } from '@/shared/errors';

import type { StarSubject } from '../domain/card';

import {
  CLEAR_HINT,
  LEAVE_ANYBODY_BLANK,
  SENDING_LABEL,
  matchingLine,
  starName,
  starsErrorMessage,
  submitLabel,
  submitName,
} from './starsPresentation';

const KASIA: StarSubject = {
  playerId: 'aaaaaaaa-0000-4000-8000-000000000001',
  name: { kind: 'player', nickname: 'kasia_w' },
};
const TOMEK: StarSubject = {
  playerId: 'bbbbbbbb-0000-4000-8000-000000000002',
  name: { kind: 'player', nickname: 'tomek.p' },
};
const MAREK: StarSubject = {
  playerId: 'cccccccc-0000-4000-8000-000000000003',
  name: { kind: 'player', nickname: 'marekb' },
};
const NOBODY: StarSubject = {
  playerId: 'dddddddd-0000-4000-8000-000000000004',
  name: { kind: 'unknown' },
};

describe('the one line the card has to carry', () => {
  it('says a low answer will not stop you being matched, and names the one opponent', () => {
    expect(matchingLine([TOMEK])).toBe(
      "This helps other players. It won't stop you being matched with tomek.p.",
    );
  });

  it('says it about all of them in doubles, where naming one would be naming the wrong one', () => {
    expect(matchingLine([KASIA, TOMEK, MAREK])).toBe(
      "This helps other players. It won't stop you being matched with any of them.",
    );
  });

  it('does not name a person it cannot name', () => {
    // `?` is what this app draws for a seat `users` can no longer answer for, and a sentence
    // reading *matched with ?* is the one place that mark would be read as a word.
    expect(matchingLine([NOBODY])).toBe(
      "This helps other players. It won't stop you being matched with any of them.",
    );
  });
});

describe('the control', () => {
  it('offers to send the stars when there are stars to send', () => {
    expect(submitLabel(2)).toBe('Send stars');
  });

  /**
   * Submitting with everybody blank closes the card too — *an explicit "I am not rating
   * anyone" is an answer*. So the control names that act rather than saying *Send* over a
   * body with nothing in it.
   */
  it('names the answer for what it is when nobody was given any', () => {
    expect(submitLabel(0)).toBe('Send no stars');
  });

  it('says the two things a player cannot take back after the press, before it', () => {
    expect(LEAVE_ANYBODY_BLANK).toBe(
      'Leave anybody blank. Once you send, this card closes for good.',
    );
  });

  /**
   * Several cards can stand in the list at once, and *Send stars* three times over is three
   * identical buttons to a listener. The visible label is the act; the spoken one is the act
   * **and the evening**, which is `gameRowLabel`'s own answer to the same problem one section
   * further down the tab.
   */
  it('names the evening as well as the act, because a list can hold several cards', () => {
    expect(submitName('Send stars', 'Padel', [KASIA, TOMEK, MAREK])).toBe(
      'Send stars — Padel with kasia_w, tomek.p and marekb',
    );
  });

  it('names a singles evening without a list', () => {
    expect(submitName('Send no stars', 'Squash', [TOMEK])).toBe(
      'Send no stars — Squash with tomek.p',
    );
  });

  it('swaps the label while it is going, and never announces one thing and draws another', () => {
    expect(SENDING_LABEL).toBe('Sending…');
  });
});

describe('what each star announces', () => {
  it('names the person, because a listener has no row to count along', () => {
    expect(starName(1, KASIA)).toBe('1 star for kasia_w');
    expect(starName(4, KASIA)).toBe('4 stars for kasia_w');
  });

  it('says what pressing the star that already stands does', () => {
    expect(CLEAR_HINT).toBe('Clears these stars and leaves them blank.');
  });
});

describe('a refused card', () => {
  const refusal = (code: string) =>
    new AppError('conflict', 'business-conflict', 'test failure', { code });

  it('says the card is closed, because it closed when it was answered', () => {
    expect(starsErrorMessage(refusal('you_have_already_rated_this_game'))).toBe(
      'This card is already answered. It closed when you answered it, and there is no way to reopen it.',
    );
  });

  it('keeps the one code the server refuses to split into three', () => {
    expect(starsErrorMessage(refusal('this_game_is_not_yours_to_rate'))).toBe(
      'No settled game of yours has this address.',
    );
  });

  /**
   * Three refusals a current build cannot earn — the scale is a type, the court is what the
   * answer is read against, and a `Record` cannot hold two answers about one person. They keep
   * their sentences for the adult attestation's reason: an older build or a replayed request
   * can carry a body this card would not have sent, and *try again* would then be the one
   * thing that is not true.
   */
  it('still has a sentence for the three the domain makes unrepresentable', () => {
    expect(starsErrorMessage(refusal('stars_are_one_to_five'))).toBe(
      'Stars are one to five, whole — there is no zero and there are no halves.',
    );
    expect(starsErrorMessage(refusal('they_were_not_on_this_court'))).toBe(
      'One of those players was not on that court, so nothing was sent.',
    );
    expect(starsErrorMessage(refusal('you_rated_the_same_person_twice'))).toBe(
      'That card said two things about one player, and it carries one.',
    );
  });

  it('promises the send resumes when the connection does, because it pauses rather than fails', () => {
    // Nothing about a card carries a deadline the player chose: the seven days are the game's
    // and started without them. So this write pauses like everything else in the app, and the
    // sentence at the control is the one that says so.
    const offline = new AppError('network-unavailable', 'retryable-automatically', 'no socket');

    expect(starsErrorMessage(offline)).toBe(offlineMessage('resumes'));
  });

  it('falls back by recovery category for a code this build has never seen', () => {
    expect(starsErrorMessage(refusal('a_code_from_a_later_build'))).toBe(
      "That can't be done right now.",
    );
  });
});
