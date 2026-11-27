/**
 * **What a link does, by who is on the phone** ([#520](https://github.com/Raketa02/Raketa/issues/520),
 * PRD #500 stories 46–48 and 111–119; [#756](https://github.com/Raketa02/Raketa/issues/756)).
 *
 * The rules the links feature decides by, over plain data: **where a link lands as it arrives** — its
 * own screen, or held for the place that can answer it; **what a group link or a friend link does
 * where the account is**; **what an invitation's link means to the account signed in**; **where a
 * friend link lands once opened**; and **when an answered link is let go of**. The server answers
 * every question they are asked from; these only decide what the app does with the answers.
 */

import type { InvitationLink, InvitationLinkState } from '@/features/auth/types';
import type { FriendRelation } from '@/features/friends/types';

import type { CredentialLink, IncomingLink } from './incomingLink';

/**
 * **Who is on the phone as a link arrives.** `unknown` is a cold start: the operating system hands
 * the app its link before the keychain has been read.
 */
export type LinkSession = 'signed-in' | 'signed-out' | 'unknown';

/** Where a link lands as it arrives: nowhere yet, or the screen of its own it opens. */
export type Landing =
  { readonly kind: 'held' } | { readonly kind: 'its-screen'; readonly link: CredentialLink };

/**
 * **Where a link lands as it arrives** — the screen its page names, or nowhere yet: **held**, and
 * answered by the place that can.
 *
 * - **A group link is always held.** Join a group is a screen inside the player's app, and a person
 *   signed out, not yet onboarded or wearing their administrator profile is not there yet: the link
 *   waits through all of it and opens once they are (story 48). **A friend link is held the same
 *   way** (#756): it is answered by opening it as the account, whose Home the request lands on.
 *   **The app's bare address** is held too: what it asks for is the invitation sheet, which is in the
 *   app.
 * - **An invitation or a reset, with nobody signed in, opens its own screen** — *Set your password*,
 *   *Set a new password* — and so does one at a cold start, which does not know yet: the screen sits
 *   under the `(auth)` guard, which hands a phone that turns out to be signed in to the gate, where
 *   the held link is answered.
 * - **With somebody signed in, it is held**, and a sheet answers it over wherever they are — nobody
 *   is taken off the screen they were on for a link that may not be theirs.
 */
export function landingOf(link: IncomingLink, session: LinkSession): Landing {
  if (link.kind === 'join' || link.kind === 'friend' || link.kind === 'open') {
    return { kind: 'held' };
  }
  return session === 'signed-in' ? { kind: 'held' } : { kind: 'its-screen', link };
}

/** The home a held link is answered over — the player's app, or an administrator area. */
export type LinkHome = 'player' | 'administrator';

/**
 * **What a group link or a friend link does where the account is** (story 46; #756). Both are the
 * player's — Join a group is a player's screen, and a friend's request lands on the player's Home —
 * so each is **answered in the player's app**; in an administrator area it **switches an account
 * that plays to Player** — the switcher's own move, kept as one — and **waits for one that does
 * not**: a link is no reason to take somebody into the player's setup, and *Start playing*'s steps
 * end in the player's app, where it is answered.
 */
export function playersLinkMove(
  home: LinkHome,
  playsToo: boolean,
): 'answer' | 'switch-to-player' | 'wait' {
  if (home === 'player') return 'answer';
  return playsToo ? 'switch-to-player' : 'wait';
}

/**
 * **Where a friend link lands once it is opened** (#756, the friends mechanics §4.2) — on **Home**,
 * with Needs your answer up and the request in it since #817, when the owner's request is there
 * (`ASKED_YOU`: asked by the opening, already open, or a set-aside one brought back — and a request
 * the owner's block swallowed answers the same, landing on Home with no sheet, the cost ADR-0202
 * names). **Nowhere** for the opener's own link (`NONE`) or a
 * friend's (`FRIEND`, which is also the opener's own request crossing the owner's): nothing waits
 * for an answer.
 */
export function friendLinkLanding(relation: FriendRelation): 'home' | 'stay' {
  return relation === 'ASKED_YOU' ? 'home' : 'stay';
}

/** **What an invitation's link means to the account signed in** when it is opened. */
export type InvitationLinkOutcome =
  /** Theirs, and open: the invitation sheet offers that club's invitation — even if set aside. */
  | { readonly kind: 'offer'; readonly clubName: string }
  /** Theirs, and used: they set their password through it — nothing is left to answer. */
  | { readonly kind: 'settled' }
  /** Open, and somebody else's: a sheet names the address it is for, and offers Sign out. */
  | { readonly kind: 'someone-else'; readonly invited: string }
  /** It no longer works: its own sentence, whoever opened it. */
  | { readonly kind: 'spent'; readonly state: Exclude<InvitationLinkState, 'valid'> };

/**
 * **The account's own invitation is offered; anybody else's names its address; a spent one says
 * so** (stories 113, 117; #520's *a phone signed in as someone else gets a sheet naming the invited
 * email*).
 *
 * **Nobody is asked to sign out for a link that no longer works**: signing out would only lead to a
 * screen saying it has expired, so the sentence is said at once. The one exception is a **used** link
 * opened by the account it was sent to — that is how every new person's walk ends, with the password
 * set and the account in, and there is nothing to say.
 *
 * The address is compared the way the server compares one, trimmed and case-folded; the server
 * stays the judge of the invitation itself, and Accept is refused if the two disagree.
 */
export function invitationLinkOutcome(
  link: InvitationLink,
  accountEmail: string,
): InvitationLinkOutcome {
  const theirs = sameAddress(link.email, accountEmail);

  switch (link.state) {
    case 'valid':
      return theirs
        ? { kind: 'offer', clubName: link.clubName }
        : { kind: 'someone-else', invited: link.email };
    case 'used':
      return theirs ? { kind: 'settled' } : { kind: 'spent', state: 'used' };
    case 'expired':
    case 'locked':
      return { kind: 'spent', state: link.state };
  }
}

/**
 * **Whether an invitation's link has been answered once it is weighed** — offered, settled, or said
 * to be spent. Somebody else's is held while its sheet asks: *Sign out* or *Stay signed in* answers
 * it.
 */
export function letsTheLinkGo(outcome: InvitationLinkOutcome): boolean {
  return outcome.kind !== 'someone-else';
}

function sameAddress(a: string, b: string): boolean {
  return a.trim().toLowerCase() === b.trim().toLowerCase();
}
