/**
 * **What a link does, by who is on the phone** — the two rules the links feature decides by
 * ([#520](https://github.com/Raketa02/Raketa/issues/520)): where a link first lands as it arrives,
 * and what an invitation's link means to the account signed in when it is opened.
 */

import type { InvitationLink, InvitationLinkState } from '@/features/auth/types';

import {
  friendLinkLanding,
  invitationLinkOutcome,
  landingOf,
  letsTheLinkGo,
  playersLinkMove,
} from './linkRules';

const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

describe('where a link lands as it arrives', () => {
  /**
   * A group link is opened where the account is in the app — after sign-in, the naming, the
   * questionnaire and the social steps if they are owed — so it never takes anybody anywhere as it
   * arrives: it is held, and the place that can open it does.
   */
  it.each(['signed-in', 'signed-out', 'unknown'] as const)('holds a group link, %s', (session) => {
    expect(landingOf({ kind: 'join', code: 'k7pq2mxa' }, session)).toEqual({ kind: 'held' });
  });

  /**
   * A friend link is held like a group link (#756): it is answered by opening it as the account,
   * so it waits through sign-in, sign-up and onboarding for the player's app.
   */
  it.each(['signed-in', 'signed-out', 'unknown'] as const)('holds a friend link, %s', (session) => {
    expect(landingOf({ kind: 'friend', code: 'tk4m9q2z' }, session)).toEqual({ kind: 'held' });
  });

  /** The app's bare address opens nothing of its own: the invitation sheet answers it. */
  it.each(['signed-in', 'signed-out', 'unknown'] as const)(
    'holds the app’s bare address, %s',
    (session) => {
      expect(landingOf({ kind: 'open' }, session)).toEqual({ kind: 'held' });
    },
  );

  /**
   * Nobody signed in: the page the link names is the screen that answers it — *Set your password*,
   * *Set a new password*. A cold start does not know yet, and the screen's own guard does.
   */
  it.each(['signed-out', 'unknown'] as const)(
    'opens an invitation or a reset on its own screen, %s',
    (session) => {
      expect(landingOf({ kind: 'invite', token: TOKEN }, session)).toEqual({
        kind: 'its-screen',
        link: { kind: 'invite', token: TOKEN },
      });
      expect(landingOf({ kind: 'reset', token: TOKEN }, session)).toEqual({
        kind: 'its-screen',
        link: { kind: 'reset', token: TOKEN },
      });
    },
  );

  /** Somebody is signed in: a sheet answers it over wherever they are, and nobody is moved. */
  it('holds an invitation or a reset for a phone that is signed in', () => {
    expect(landingOf({ kind: 'invite', token: TOKEN }, 'signed-in')).toEqual({ kind: 'held' });
    expect(landingOf({ kind: 'reset', token: TOKEN }, 'signed-in')).toEqual({ kind: 'held' });
  });
});

describe('an invitation’s link, opened by a signed-in account', () => {
  const TOMEK = 'tomek.k@example.com';
  /** What `by-token` says about Tomek's link — the address, the club, and whether it works. */
  const link = (state: InvitationLinkState): InvitationLink => ({
    email: TOMEK,
    clubName: 'Ogrody 33',
    state,
  });

  it('offers the invitation to the account it was sent to', () => {
    expect(invitationLinkOutcome(link('valid'), TOMEK)).toEqual({
      kind: 'offer',
      clubName: 'Ogrody 33',
    });
  });

  it('matches an address however it is cased or spaced', () => {
    expect(invitationLinkOutcome(link('valid'), ' Tomek.K@Example.com ')).toEqual({
      kind: 'offer',
      clubName: 'Ogrody 33',
    });
  });

  it('names the address it is for, to an account that is somebody else', () => {
    expect(invitationLinkOutcome(link('valid'), 'kuba@example.com')).toEqual({
      kind: 'someone-else',
      invited: TOMEK,
    });
  });

  /** A used link is how every new person's walk ends: they set the password, and are in. */
  it('asks nothing of the account that used it', () => {
    expect(invitationLinkOutcome(link('used'), TOMEK)).toEqual({
      kind: 'settled',
    });
  });

  /**
   * A link that no longer works says why, to whoever opened it — nobody is asked to sign out for a
   * link that would open nothing once they had.
   */
  it.each(['expired', 'locked'] as const)(
    'says a link that is %s no longer works, whoever is signed in',
    (state) => {
      expect(invitationLinkOutcome(link(state), TOMEK)).toEqual({
        kind: 'spent',
        state,
      });
      expect(invitationLinkOutcome(link(state), 'kuba@example.com')).toEqual({
        kind: 'spent',
        state,
      });
    },
  );

  it('says a used link is used, to an account it was not sent to', () => {
    expect(invitationLinkOutcome(link('used'), 'kuba@example.com')).toEqual({
      kind: 'spent',
      state: 'used',
    });
  });
});

/**
 * **A group link and a friend link, where the account is** — both are answered in the player's app:
 * Join a group is a player's screen, and a friend's request lands on the player's Home (#756).
 */
describe('a group link or a friend link, where the account is', () => {
  it('is answered in the player’s app', () => {
    expect(playersLinkMove('player', true)).toBe('answer');
    expect(playersLinkMove('player', false)).toBe('answer');
  });

  /** An administrator who plays is switched to Player for it — the switcher's own move. */
  it('switches an administrator who plays to Player', () => {
    expect(playersLinkMove('administrator', true)).toBe('switch-to-player');
  });

  /** One who does not play is not taken into the player's setup by a link: it waits. */
  it('waits for an administrator who does not play', () => {
    expect(playersLinkMove('administrator', false)).toBe('wait');
  });
});

/**
 * **Where a friend link lands once it is opened** (#756, the friends mechanics §4.2) — on Home when
 * the owner's request is there, and nowhere for the opener's own link or a friend's.
 */
describe('a friend link, once opened', () => {
  it('lands on Home when the owner’s request is waiting there', () => {
    expect(friendLinkLanding('ASKED_YOU')).toBe('home');
  });

  /** Your own link, a friend's, or your own request crossing theirs: nothing to answer. */
  it.each(['NONE', 'FRIEND'] as const)('moves nobody when it answers %s', (relation) => {
    expect(friendLinkLanding(relation)).toBe('stay');
  });
});

describe('an invitation’s link, once weighed', () => {
  it('is let go of once offered, settled or said to be spent', () => {
    expect(letsTheLinkGo({ kind: 'offer', clubName: 'Ogrody 33' })).toBe(true);
    expect(letsTheLinkGo({ kind: 'settled' })).toBe(true);
    expect(letsTheLinkGo({ kind: 'spent', state: 'expired' })).toBe(true);
  });

  /** Somebody else's stays held while its sheet asks — Sign out, or Stay signed in, lets it go. */
  it('is held while a sheet asks about somebody else’s', () => {
    expect(letsTheLinkGo({ kind: 'someone-else', invited: 'tomek.k@example.com' })).toBe(false);
  });
});
