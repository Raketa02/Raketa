/**
 * **Every sentence this feature says** — Members' pills and tags, the record's two buttons and their
 * sheets, and FRIEND REQUESTS, in Needs your answer since #816 ([#753](https://github.com/Raketa02/Raketa/issues/753); the
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
 * - **The refusals that are not the state moving** (`useFriendWrites`): asking somebody you blocked.
 *   Asking somebody who can no longer be asked was one, and is the state moving since #799.
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
 * And these, written in by #757:
 *
 * - **The picker's reading line**, *Reading your friends…*, the register above.
 * - **A greyed row's spoken reason**: *the court is full* after a row the full court greys.
 *
 * And these, written in by #758:
 *
 * - **The ask's busy word**, *Asking…* — Members' own, read from `members`.
 * - ***Asked*, spoken whole**: *Asked zofia.b to get a padel level* — a column of *Asked* names
 *   nobody.
 * - **Asking from a group you have since left** (`not_one_of_your_groups`): *You're not in this
 *   group any more.* §29 gives no refusal; the others an ask can meet are the state moving, and say
 *   nothing.
 *
 * And these, written in by #765 (Home's ASKED FOR A LEVEL; the words §29.5 gives every drawn word):
 *
 * - **The spoken name of a card's Not now**, *Not now, your padel level* — two cards' *Not now*,
 *   and a friend request's beside them, would otherwise name nothing.
 * - **The busy words** are onboarding's *Starting…* for the coral button, the start's own, and none
 *   for Not now, which the friend request card's Not now has none of either.
 *
 * And this, written in by #779 (strangers from the ranking; the words §30.8):
 *
 * - **Asking somebody you blocked** names You › Blocked players, since the record's Unblock it named
 *   is gone (ADR-0203 §8).
 *
 * #779's two other calls went with #799 (ADR-0204 §2; the words §31.13): **there is no daily limit**,
 * so no sentence for one, and **asking somebody no longer askable says nothing** — the server's
 * unnamed `player_unavailable` is the state moving, the record is read again, and it reads _This
 * record isn't available_.
 *
 * And these, written in by #801 (the round friend button; the words §31.9–§31.10):

- **The round button's spoken names** are §31.9's own calls; **its busy words** are none — it draws
  the next mark at once instead.
- **The *Request sent* sheet's busy word** is the record's *Cancelling…*.
- **A refusal on the round button is a toast**: there is no room under a 24pt mark for a note.

 * **#816 took the where-line away** (ADR-0205 §1): a friend request in Needs your answer says who
 * and their chip, and an ask for a level its title alone. _With you in Kazimierz crew_, _Invited you
 * to Raketa_, _Found you in the padel ranking_, Home rows' three found-by lines, _A few questions,
 * and they can add you to a game._ and _You're on question 5._ are no longer drawn, so no longer
 * spelled here.
 *
 * And these, written in by #818 (the sport-levels line; the words §29.2):
 *
 * - **The `·` between two sports goes with the one before it** (`sportLevelEntries`), so a line that
 *   wraps ends in one rather than starting with one.
 * - **The tile's spoken name** (`requestTileLabel`): who asks, then every sport and its Level — the
 *   dots are colour, and say nothing.
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
import { askersFormOf, type AskersForm } from '../domain/levelAsk';
import type { FriendRelation } from '../domain/vocabulary';

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
  /** **ASKED FOR A LEVEL** (the screens §6.4; the words §29.5). */
  levelAsks: {
    notNow: 'Not now',
    /** The coral button with a questionnaire in the sport left halfway; the title doesn't change. */
    carryOn: 'Carry on',
  },
  /**
   * **FRIEND REQUESTS** in Needs your answer (#816). The where-line and its found-by sentences went
   * with Home's row (ADR-0205 §1).
   */
  home: {
    notNow: 'Not now',
    accept: 'Accept',
    accepting: 'Accepting…',
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
  /**
   * **The picker** (#757; the screens §4.2; friends 3, 6) — the page from a group's Friends tab, with
   * no tabs and **Done** at its foot. A row's line is `pickerLine` or `noLevelLine`.
   */
  picker: {
    done: 'Done',
    reading: 'Reading your friends…',
    /** Spoken after a row a full court greys: why it cannot be picked now. */
    full: 'the court is full',
    /** A greyed no-Level row, once you asked (§29.3) — you ask once per sport, ever. */
    asked: 'Asked',
  },
  /**
   * **The round friend button** (#801; the Home rows screens §8; the words §31.9) — no words of its
   * own, a drawn mark per relation; its spoken names are `roundLabel`. **Its worded twin** on a
   * sheet says these, the + and the ✓ drawn before them.
   */
  round: {
    worded: {
      NONE: 'Add friend',
      SENT: 'Request sent',
      FRIEND: 'Friends',
      ASKED_YOU: 'Accept',
    } satisfies Readonly<Record<FriendRelation, string>>,
    /** From **…**: what stands, and the one act under it — no question, so no *Keep* (§31.9). */
    requestSent: { title: 'Request sent', act: 'Cancel request', busy: 'Cancelling…' },
  },
  /** Said where a write was pressed, when the server refused it for a reason that is not the state moving. */
  refused: {
    /**
     * Members still offers **+ Add** on somebody you blocked (no block shows there, #745's call), and
     * the record's own Unblock is gone (#779, ADR-0203 §8): the way back is You › Blocked players.
     */
    unblock_them_first: 'You blocked this player. Unblock them in You › Blocked players first.',
    /** An ask for a Level (#758) from a group you have since left. */
    not_one_of_your_groups: 'You’re not in this group any more.',
  } as Readonly<Record<string, string>>,
} as const;

/**
 * **The round friend button's spoken name** (the words §31.9, each a call) — the button's whole name,
 * kept for tests (ADR-0198): a row of marks names nobody, so each says whom and where the reader
 * stands. Keyed by the relation, so one with no name fails to compile.
 */
const ROUND_LABEL: Readonly<Record<FriendRelation, (nickname: string) => string>> = {
  NONE: (nickname) => `Add ${nickname} as a friend`,
  SENT: (nickname) => `Request sent to ${nickname}`,
  FRIEND: (nickname) => `Friends with ${nickname}`,
  ASKED_YOU: (nickname) => `Accept ${nickname}'s request`,
};

export function roundLabel(relation: FriendRelation, nickname: string): string {
  return ROUND_LABEL[relation](nickname);
}

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

/** A sport on a request's sport-levels line, named — `sportLabel`'s *Padel* — with its Level. */
export interface NamedLevel {
  readonly name: string;
  readonly level: number;
}

/**
 * *Padel 3,40 ·* · *Tennis 2,90* — **a friend request's sport-levels line** (#818; the words §29.2),
 * one entry per sport, its dot drawn before it. Every entry but the last carries the `·` before the
 * next, so a line that wraps ends in one rather than starting with one.
 */
export function sportLevelEntries(levels: readonly NamedLevel[]): readonly string[] {
  return levels.map((one, at) => {
    const entry = sportLevel(one.name, one.level);
    return at < levels.length - 1 ? `${entry} ·` : entry;
  });
}

/**
 * *ines.d wants to be your friend, Padel 3,40, Tennis 2,90* — **a request tile, spoken** (#818): who
 * asks, then every sport they play with its Level, as drawn. The dots are colour, and say nothing.
 */
export function requestTileLabel(nickname: string, levels: readonly NamedLevel[]): string {
  return [
    wantsToBeYourFriend(nickname),
    ...levels.map((one) => sportLevel(one.name, one.level)),
  ].join(', ');
}

/** *Asked you · 2* — the one tab that counts, while requests wait; *Asked you* alone at nought. */
export function askedYouTab(count: number): string {
  const name = FRIENDS_COPY.page.tabs.ASKED_YOU;
  return count > 0 ? `${name} · ${count}` : name;
}

/**
 * *Padel 2,75 · Tennis 3,10* — a friend's line on *Friends*: every sport they play with its Level
 * (call 11). The sport arrives named, so this module imports no feature: it is read at module load
 * by every component here, and a feature's barrel would close a loop back into them.
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

/** *2,75 · established* — a picker row's line: the Level in the sport and its band, lower case. */
export function pickerLine(level: number, band: string): string {
  return `${formatLevel(level)} · ${band.toLowerCase()}`;
}

/** *No padel level yet* — a picker row for a friend unrated in the sport, greyed (§29.3). */
export function noLevelLine(sportInLine: string): string {
  return `No ${sportInLine} level yet`;
}

/** *Ask zofia.b to get a padel level* — under a greyed no-Level row (§29.3). No pronoun (ADR-0096). */
export function askForALevelLabel(nickname: string, sportInLine: string): string {
  return `Ask ${nickname} to get a ${sportInLine} level`;
}

/** *Asked*, spoken whole: whom, and for which Level — a column of *Asked* names nobody. */
export function askedForALevelLabel(nickname: string, sportInLine: string): string {
  return `Asked ${nickname} to get a ${sportInLine} level`;
}

/** A picker row, spoken: who, their line, and why it cannot be picked while the court is full. */
export function pickerRowLabel(nickname: string, line: string, full: boolean): string {
  return [nickname, line, ...(full ? [FRIENDS_COPY.picker.full] : [])].join(', ');
}

/** *ASKED FOR A LEVEL · 2* — the row's title, uppercased by its style; `count` is sports, never 0. */
export function levelAsksHeading(count: number): string {
  return `Asked for a level · ${count}`;
}

/**
 * **Who wants to play** — the card's title, by how many asked (§29.5): one named, two named
 * together, three or more the two newest and the rest counted. Keyed by the form, so a count with no
 * sentence fails to compile.
 */
const WANT_TO_PLAY: Readonly<
  Record<AskersForm, (nicknames: readonly string[], sportInLine: string) => string>
> = {
  one: ([first], sport) => `${first} wants to play ${sport} with you`,
  two: ([first, second], sport) => `${first} and ${second} want to play ${sport} with you`,
  more: ([first, second, ...rest], sport) =>
    `${first}, ${second} and ${rest.length} more want to play ${sport} with you`,
};

/** *tomek.k and kuba.w want to play padel with you* — `nicknames` newest first, never empty. */
export function wantToPlay(nicknames: readonly string[], sportInLine: string): string {
  return WANT_TO_PLAY[askersFormOf(nicknames.length)](nicknames, sportInLine);
}

/** *Get your padel level* — the tile's coral button, which starts the sport's questionnaire. */
export function getYourLevelLabel(sportInLine: string): string {
  return `Get your ${sportInLine} level`;
}

/** The spoken name of a card's **Not now**: which ask it puts away. */
export function notNowLevelAskLabel(sportInLine: string): string {
  return `Not now, your ${sportInLine} level`;
}

/** **Not now's toast** — neutral, held to be read: where the level can still be got (§29.5). */
export function setAsideToast(sportInLine: string): string {
  return `You can get your ${sportInLine} level any time, from You › Skill passport.`;
}
