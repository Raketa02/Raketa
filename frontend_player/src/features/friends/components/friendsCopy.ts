/**
 * **Every sentence this feature says** — Members' pills and tags, the record's two buttons and their
 * sheets, and Home's FRIEND REQUESTS ([#753](https://github.com/Raketa02/Raketa/issues/753); the
 * words [§29.1–§29.2](../../../../../docs/specs/matchmaking/the-words.md#29-friends)); You ›
 * Friends, the Add friends sheet and the result screen's PLAYED WITH
 * ([#754](https://github.com/Raketa02/Raketa/issues/754); the words §29.1, §29.3); and the friend
 * link — the sheet's card, and what opening somebody's says when it cannot
 * ([#756](https://github.com/Raketa02/Raketa/issues/756); the words §29.3–§29.4).
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
 * And these, written in by #754:
 *
 * - **The You tab's row line**: *3 friends · 1 asked you*, *1 friend*, *No friends yet* — §29 gives
 *   the row no line, and every row on the tab has one.
 * - **The sheet with no group to list**: *You're in no group yet. Join one to add the people in
 *   it.* §29 gives none; a player in no group still opens the sheet.
 * - **The busy and reading words**, and *Try again*, the register `blocks` uses.
 * - **The spoken names**: *Cancel your request to michal.r* for a row's **Cancel**, and *Add
 *   friends* for the header's pill, whose + is a mark.
 * - **The + of *+ Add friends* is typed**, as #753 typed *+ Add*'s — §29 says drawn, and both turn
 *   at once if the product owner rules so.
 *
 * And these, written in by #756:
 *
 * - **New link asks first**, as #756 asks and §29 has no words for: *Make a new link?* over *The
 *   link you have now stops working, and anyone who opens it finds nothing there.*, **New link** and
 *   **Keep this link**.
 * - **Copy's two answers**, the group page's *Link copied* and *Couldn't copy the link*, spelled
 *   again here because `groups` draws this feature's pills and cannot be read back.
 * - **Opening a link of somebody you blocked** (`unblock_them_first`, #748's call): *This link is
 *   from somebody you blocked. Unblock them in Blocked players to see their request.* A dead link
 *   says the public page's *Nothing at that link* (§29.4).
 * - **The spoken names**: *Your friend link, raketa.app/f/tk4m9q2z* for the field, *Copy your
 *   friend link* and *Make a new link* for its two buttons.
 *
 * ## The whole nickname, and no pronoun
 *
 * ADR-0199 §1: every sentence naming somebody uses the whole nickname, never with an @. And no
 * sentence says *her*, *his*, *she* or *he* about another player (ADR-0096; the words §29's note).
 */

import { codeMessage, type AppError } from '@/shared/errors';
import { linkWithoutScheme } from '@/shared/formatting/linkFormat';
import { formatLevel } from '@/shared/formatting/ratingFormat';

import type { FriendsTab } from '../domain/friendList';

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
  /** **You › Friends** (the screens §4.1): the header, the three tabs, their rows and empty lines. */
  page: {
    title: 'Friends',
    /** The header's black pill, top right (friends 3) — the + typed, as Members' *+ Add*. */
    add: '+ Add friends',
    /** Its spoken name: the + is a mark, never read out. */
    addLabel: 'Add friends',
    tabs: {
      friends: 'Friends',
      ASKED_YOU: 'Asked you',
      YOU_ASKED: 'You asked',
    } satisfies Readonly<Record<FriendsTab, string>>,
    /** One line per tab (§29.3, each a call). */
    empty: {
      friends: 'No friends yet. Add them from your groups, or send your link.',
      ASKED_YOU: 'Nobody has asked you yet.',
      YOU_ASKED: "You haven't asked anyone.",
    } satisfies Readonly<Record<FriendsTab, string>>,
    accept: 'Accept',
    accepting: 'Accepting…',
    cancel: 'Cancel',
    cancelling: 'Cancelling…',
    reading: 'Reading…',
    readAgain: 'Try again',
    /** What a tap on a row does; the row's label already says whose. */
    openRecord: 'Opens their record',
  },
  /** **The Add friends sheet** (the screens §5; friends 4). */
  sheet: {
    title: 'Add friends',
    close: 'Close',
    /** The section's eyebrow over the groups card. */
    fromYourGroups: 'From your groups',
    none: "You're in no group yet. Join one to add the people in it.",
    reading: 'Reading your groups…',
    /** What a tap on a group does. */
    openMembers: 'Opens its Members',
  },
  /**
   * **The sheet's link card** (the screens §5; friends 4; the words §29.3): the link, **Copy**, and a
   * small **New link** under it, which asks first.
   */
  link: {
    title: 'Not on Raketa yet?',
    copy: 'Copy',
    copyLabel: 'Copy your friend link',
    copied: 'Link copied',
    notCopied: 'Couldn’t copy the link',
    newLink: 'New link',
    newLinkLabel: 'Make a new link',
    reading: 'Reading your link…',
    /** Under the field once a New link is made (§29.3, a call). */
    made: 'New link made. The old one no longer works.',
    confirm: {
      title: 'Make a new link?',
      body: 'The link you have now stops working, and anyone who opens it finds nothing there.',
      act: 'New link',
      busy: 'Making a new link…',
      keep: 'Keep this link',
      /** The sheet's close does what *Keep* does, under its own name. */
      close: 'Not now',
    },
  },
  /**
   * **Opening somebody's link, refused** — said as a toast wherever the link landed (#756). Any
   * other failure says its recovery sentence (`codeMessage`).
   */
  linkRefused: {
    friend_link_not_found: 'Nothing at that link',
    unblock_them_first:
      'This link is from somebody you blocked. Unblock them in Blocked players to see their request.',
  } as Readonly<Record<string, string>>,
  /** **The You tab's row** — its title; the line is `friendsRowLine`. */
  row: { title: 'Friends' },
  /** **The result screen's card** (§29.1) — the eyebrow over it, uppercased by its style. */
  playedWith: { heading: 'Played with' },
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

/** *Asked you · 2* — the one tab that counts, while requests wait; *Asked you* alone at nought. */
export function askedYouTab(count: number): string {
  const name = FRIENDS_COPY.page.tabs.ASKED_YOU;
  return count > 0 ? `${name} · ${count}` : name;
}

/**
 * *Padel 2,75 · Tennis 3,10* — a friend's line on *Friends*: every sport they play with its Level
 * (call 11). The sport arrives named, as `whereLine`'s does, so this module imports no feature.
 */
export function sportsLine(
  sports: readonly { readonly name: string; readonly level: number }[],
): string {
  return sports.map((one) => `${one.name} ${formatLevel(one.level)}`).join(' · ');
}

/** *Padel 2,71* — a PLAYED WITH row's line, Members' own; the sport alone where they hold no Level. */
export function sportLevel(name: string, level: number | undefined): string {
  return level === undefined ? name : `${name} ${formatLevel(level)}`;
}

/** *8 members · 2 to add* — a group in the Add friends sheet, its singular and nought forms. */
export function groupCountsLine(members: number, toAdd: number): string {
  const size = members === 1 ? '1 member' : `${members} members`;
  const left = toAdd === 0 ? 'nobody to add' : `${toAdd} to add`;
  return `${size} · ${left}`;
}

/** *3 friends · 1 asked you* — the You tab's row: how many friends, and who waits on an answer. */
export function friendsRowLine(friends: number, askedYou: number): string {
  const count =
    friends === 0 ? 'No friends yet' : friends === 1 ? '1 friend' : `${friends} friends`;
  return askedYou > 0 ? `${count} · ${askedYou} asked you` : count;
}

/** A person's row, spoken in the order it is drawn: the name, then the line where there is one. */
export function personRowLabel(nickname: string, line: string): string {
  return line === '' ? nickname : `${nickname}, ${line}`;
}

/** The spoken name of a *You asked* row's **Cancel** — whose request, since a column names nobody. */
export function cancelRequestLabel(nickname: string): string {
  return `Cancel your request to ${nickname}`;
}

/** A group in the sheet, spoken: its name and its counts. */
export function groupRowLabel(name: string, members: number, toAdd: number): string {
  return `${name}, ${groupCountsLine(members, toAdd)}`;
}

/**
 * **What opening somebody's link says when it cannot** — *Nothing at that link*, the blocked
 * owner's sentence, or the failure's recovery sentence.
 */
export function linkOpeningMessage(error: AppError): string {
  return codeMessage(FRIENDS_COPY.linkRefused, error);
}

/** *Your friend link, raketa.app/f/tk4m9q2z* — the card's field, spoken. */
export function friendLinkLabel(link: string): string {
  return `Your friend link, ${linkWithoutScheme(link)}`;
}
