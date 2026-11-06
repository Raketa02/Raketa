/**
 * **Every sentence this feature says** — Members' pills and tags, the record's two buttons and their
 * sheets, and Home's FRIEND REQUESTS ([#753](https://github.com/Raketa02/Raketa/issues/753); the
 * words [§29.1–§29.2](../../../../../docs/specs/matchmaking/the-words.md#29-friends)).
 *
 * ## Calls, for the product owner to overrule
 *
 * §29 gives every drawn word here but these, written in by #753 and marked where they stand:
 *
 * - **Cancelling a request asks first**, as #753 asks and §29 has no words for: *Cancel your request
 *   to kuba.w?* over *Nobody is told.*, removing's shape.
 * - **The busy words** (*Asking…*, *Accepting…*, *Cancelling…*, *Removing…*), `blocks`' *Blocking…*.
 * - **The refusals that are not the state moving** (`useFriendWrites`): asking somebody you blocked,
 *   and somebody you no longer share a group with.
 * - **The spoken names of a pill and a card's buttons**: a column of *+ Add* or two cards' *Accept*
 *   name nobody, so each says whom — *Add kuba.w*, `blocks`' *Unblock kuba.w*.
 *
 * ## The whole nickname, and no pronoun
 *
 * ADR-0199 §1: every sentence naming somebody uses the whole nickname, never with an @. And no
 * sentence says *her*, *his*, *she* or *he* about another player (ADR-0096; the words §29's note).
 */

import { formatLevel } from '@/shared/formatting/ratingFormat';

export const FRIENDS_COPY = {
  members: {
    /** The black pill on somebody nothing stands between you and — the + drawn in the words. */
    add: '+ Add',
    asking: 'Asking…',
    /** The black pill on somebody who asked you. */
    accept: 'Accept',
    accepting: 'Accepting…',
    /** Amber: your request is open — set aside or not, which is never said. */
    sent: 'request sent',
    /** Green: your friend. */
    friend: 'friend',
  },
  record: {
    add: 'Add friend',
    sent: 'Request sent',
    accept: 'Accept',
    friend: 'Friend',
    asking: 'Asking…',
    accepting: 'Accepting…',
    cancel: {
      /** The act, once, on the button that does it. */
      act: 'Cancel request',
      busy: 'Cancelling…',
      body: 'Nobody is told.',
    },
    remove: {
      act: 'Remove friend',
      busy: 'Removing…',
      body: 'Nobody is told, and your games together stay as they are.',
    },
    /** The button under either act — nothing changes. */
    keep: 'Keep',
    /** Either sheet's close does the same, under its own name: two controls never share one. */
    close: 'Not now',
  },
  home: {
    notNow: 'Not now',
    accept: 'Accept',
    accepting: 'Accepting…',
    /** A link's request, in place of the group line. */
    byLink: 'Invited you to Raketa',
  },
  /** Said where a write was pressed, when the server refused it for a reason that is not the state moving. */
  refused: {
    unblock_them_first: 'You blocked this player. Unblock them on their record first.',
    player_not_in_your_groups: 'You can only ask people from your groups.',
  } as Readonly<Record<string, string>>,
} as const;

/** The spoken name of a Members row's **+ Add** — the person it asks, since a column names nobody. */
export function addLabel(nickname: string): string {
  return `Add ${nickname}`;
}

/** The spoken name of an **Accept** among others — Members' pill, or a card on Home. */
export function acceptLabel(nickname: string): string {
  return `Accept ${nickname}`;
}

/** The spoken name of a card's **Not now**. */
export function notNowLabel(nickname: string): string {
  return `Not now, ${nickname}`;
}

/** The cancel sheet's title: the question its act answers. */
export function cancelTitle(nickname: string): string {
  return `Cancel your request to ${nickname}?`;
}

/** The remove sheet's title (the words §29.1). */
export function removeTitle(nickname: string): string {
  return `Remove ${nickname} as a friend?`;
}

/** *FRIEND REQUESTS · 1* — the row's title, uppercased by its style; never drawn at nought. */
export function requestsHeading(count: number): string {
  return `Friend requests · ${count}`;
}

/** *Inés D. wants to be your friend* — the card's first line, and a request notice's title. */
export function wantsToBeYourFriend(nickname: string): string {
  return `${nickname} wants to be your friend`;
}

/**
 * **The card's where-line, before the reliability chip** (the words §29.2) — *With you in Kazimierz
 * crew · Padel 3,40 ·*, or *Invited you to Raketa* for a link's request. Each part only where the
 * wire named it: the group while both are still in it, the sport and the Level where the screen
 * showed one. The trailing ` ·` stands before the chip the card draws after it; with nothing to say
 * the line is empty and the chip stands alone. The sport arrives named (`sportLabel`'s *Padel*), so
 * this module imports no feature: it is read at module load by every component here, and a feature's
 * barrel would close a loop back into them.
 */
export function whereLine(request: {
  readonly byLink: boolean;
  readonly group?: { readonly name: string };
  readonly sportName?: string;
  readonly level?: number;
}): string {
  if (request.byLink) return FRIENDS_COPY.home.byLink;
  const sport =
    request.sportName === undefined
      ? []
      : [
          [
            request.sportName,
            ...(request.level === undefined ? [] : [formatLevel(request.level)]),
          ].join(' '),
        ];
  const parts = [
    ...(request.group === undefined ? [] : [`With you in ${request.group.name}`]),
    ...sport,
  ];
  return parts.length === 0 ? '' : `${parts.join(' · ')} ·`;
}
