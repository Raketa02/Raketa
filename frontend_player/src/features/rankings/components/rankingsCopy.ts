/**
 * **Every sentence the Rankings page and Home's trophy say** ([#775](https://github.com/Raketa02/Raketa/issues/775)),
 * as [the words §30](../../../../../docs/specs/matchmaking/the-words.md#30-rankings) write them. Where
 * this file and §30 differ, §30 wins.
 *
 * **No sentence says *her*, *his*, *she* or *he* about another player** (ADR-0096; §30's preamble):
 * a player is named by their nickname, or is *you*. `rankingsCopy.test.ts` holds that over every
 * sentence here.
 *
 * **The marks are drawn, never characters** — ▲, ▼, — and the trophy (§30's preamble; Archivo ships
 * none of them): `chipFace` says which mark a chip draws, and `RankChip` draws it.
 *
 * The spoken names — the trophy's, a row's, the pill's hint — are this ticket's calls: §30 writes only
 * what is drawn, and ADR-0198 asks a screen for its names and nothing more.
 */

import { sportInLine, sportLabel } from '@/features/onboarding/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { SportPillWords } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Chip, GapLine, PlaceCard, PlayerAbove, PlayerBelow } from '../domain/ranking';
import type { TopTenPlayer } from '../domain/topTen';
import type { ChipKind, RankingView } from '../domain/vocabulary';

export const RANKINGS_COPY = {
  /** §30.2 */
  title: 'Rankings',
  subline: 'Competitive games only',
  back: 'Back to Home',
  /** §30.3 */
  eyebrow: 'YOUR PLACE',
  /** §30.4: the whole line, in first place. */
  topOfTheList: 'Top of the list',
  /** §30.6: under *Just you so far* and *None of your friends is ranked…* — opens §29.3's sheet. */
  addFriends: 'Add friends',
  /** §30.7: the reader's own row, and their step on the podium. */
  you: 'You',
  /** The trophy's spoken name with no place, and the start of it with one. */
  trophy: 'Rankings',
  trophyHint: 'Opens the rankings',
  /** The pill's hint, where there is another sport to switch to. */
  pillHint: 'Shows the ranking in another sport',
  openRecord: 'Opens their record',
  openOwnRecord: 'Opens your record',
  /** The jump button's hint (#776) — a call: §30.7 writes only what it reads. */
  jumpHint: 'Shows your row in the list',
} as const;

/** §30.2: the switch under the header, *General* · *Friends* (#777). */
export const VIEW_WORDS: Readonly<Record<RankingView, string>> = {
  GENERAL: 'General',
  FRIENDS: 'Friends',
};

/**
 * **An ordinal** (§30's `{place}`): *1st, 2nd, 3rd, 4th … 11th, 12th, 13th … 21st, 22nd, 23rd …
 * 101st, 111th, 112th* — *-st*, *-nd* and *-rd* follow a last digit of 1, 2 and 3, except after a
 * ten.
 */
export function ordinal(place: number): string {
  const lastTwo = place % 100;
  if (lastTwo >= 11 && lastTwo <= 13) return `${place}th`;
  switch (place % 10) {
    case 1:
      return `${place}st`;
    case 2:
      return `${place}nd`;
    case 3:
      return `${place}rd`;
    default:
      return `${place}th`;
  }
}

/** §30.1: the trophy's place, *#7* — and no words without one. */
export function trophyPlace(place: number | undefined): string | undefined {
  return place === undefined ? undefined : `#${place}`;
}

/** Where the trophy's place stands, spoken — the view it is counted in (#777). */
const TROPHY_AMONG: Readonly<Record<RankingView, string>> = {
  GENERAL: '',
  FRIENDS: ' among your friends',
};

/**
 * The trophy, spoken — *Rankings, 7th in padel*, *Rankings, 4th among your friends in padel*, or
 * *Rankings* with no place.
 */
export function trophyLabel(sport: Sport, place: number | undefined, view: RankingView): string {
  return place === undefined
    ? RANKINGS_COPY.trophy
    : `${RANKINGS_COPY.trophy}, ${ordinal(place)}${TROPHY_AMONG[view]} in ${sportInLine(sport)}`;
}

/** §30.3: *of 13*. */
export function ofListed(listed: number): string {
  return `of ${listed}`;
}

/** **What a chip draws** — a mark and a count, a mark alone, or a word (§30.3, §30.7). */
export type ChipFace =
  | { readonly mark: 'up' | 'down'; readonly count: string }
  | { readonly mark: 'same' }
  | { readonly word: string };

export function chipFace(chip: Chip): ChipFace {
  switch (chip.kind) {
    case 'UP':
      return { mark: 'up', count: String(chip.places) };
    case 'DOWN':
      return { mark: 'down', count: String(chip.places) };
    case 'SAME':
      return { mark: 'same' };
    case 'NEW':
      return { word: 'New' };
  }
}

/** §30.3: beside the card's chip — *▲ 1 up this week*. No *this week* in a row (§30.7). */
const CARD_CHIP_WORDS: Readonly<Record<ChipKind, string>> = {
  UP: 'up this week',
  DOWN: 'down this week',
  SAME: 'no change this week',
  NEW: 'this week',
};

export function cardChipWords(chip: Chip): string {
  return CARD_CHIP_WORDS[chip.kind];
}

/** A chip, spoken — *up 2 this week*: the drawn mark has no reading of its own. */
const CHIP_SPOKEN: Readonly<Record<ChipKind, string>> = {
  UP: 'up',
  DOWN: 'down',
  SAME: 'no change this week',
  NEW: 'new this week',
};

export function chipSpoken(chip: Chip): string {
  return 'places' in chip
    ? `${CHIP_SPOKEN[chip.kind]} ${chip.places} this week`
    : CHIP_SPOKEN[chip.kind];
}

/** The place card, spoken whole — *your place: 7th of 13, 2,71, up 1 this week*. */
export function placeCardSpoken(placed: {
  readonly place: number;
  readonly of: number;
  readonly level: number;
  readonly chip?: Chip;
}): string {
  return [
    `your place: ${ordinal(placed.place)} ${ofListed(placed.of)}`,
    formatLevel(placed.level),
    ...(placed.chip === undefined ? [] : [chipSpoken(placed.chip)]),
  ].join(', ');
}

/** **A piece of the gap line** — the numbers in it are bold, as rankings 3 draws them (§30.4). */
export interface LinePart {
  readonly text: string;
  readonly strong?: true;
}

const DOT: LinePart = { text: ' · ' };

/** A difference of levels: the decimal comma and two decimals — *0,04* (§30's `{gap}`). */
function gapOf(gap: number): LinePart {
  return { text: formatLevel(gap), strong: true };
}

/**
 * The part about the player above. **The count is the server's**: it sends none above five wins
 * (the mechanics §7.1), so a count here is always one to say.
 */
function aboveParts(above: PlayerAbove): readonly LinePart[] {
  if (above.tied) return [{ text: `Level with ${above.nickname} · one win puts you ahead` }];
  const behind = [gapOf(above.gap), { text: ` behind ${above.nickname}` }];
  if (above.wins === undefined) return behind;
  return [
    ...behind,
    { text: above.wins === 1 ? ' · one win closes it' : ` · about ${above.wins} wins close it` },
  ];
}

function belowParts(below: PlayerBelow): readonly LinePart[] {
  if (below.gap === 0) return [{ text: `${below.nickname} is level with you` }];
  return [{ text: `${below.nickname} is ` }, gapOf(below.gap), { text: ' behind you' }];
}

/**
 * **The gap line** (§30.4): *Top of the list* in first place, the whole line; otherwise the part
 * about the player above, then the part about the player below, joined by ` · ` — each left out
 * where there is nobody the reader can see that way.
 */
export function gapLineParts(line: GapLine): readonly LinePart[] {
  if (line.kind === 'top') return [{ text: RANKINGS_COPY.topOfTheList }];
  const parts = [
    ...(line.above === undefined ? [] : [aboveParts(line.above)]),
    ...(line.below === undefined ? [] : [belowParts(line.below)]),
  ];
  return parts.flatMap((part, at) => (at === 0 ? part : [DOT, ...part]));
}

/** The not-listed cards' line (§30.5) — the cards that carry no place. */
export type NotListedCard = Extract<
  PlaceCard,
  { readonly state: 'NEEDS_RESULTS' | 'NO_LEVEL' | 'OFF_THE_LIST' }
>;

/**
 * **A not-listed card's one line** (§30.5), in the view's words — the rows §30.5 keys by view:
 *
 * - **General**: *2 of 5 games — 3 more competitive padel games put you on the list* (the singular
 *   with one to go, the count kept — a call recorded in §30.5); *No squash level yet — get one, then 5
 *   competitive games put you on the list*.
 * - **Friends** (#777), which takes one result: *Not ranked in padel yet — your first confirmed
 *   competitive game puts you on the list*; *No squash level yet — get one, then one competitive game
 *   puts you on the list*.
 * - **Both**: *Off the list — no competitive padel game in 90 days. Your next one puts you back.*
 *
 * Every count is the wire's.
 */
export function notListedLine(card: NotListedCard, sport: Sport, view: RankingView): string {
  const inLine = sportInLine(sport);
  switch (card.state) {
    case 'NEEDS_RESULTS': {
      if (view === 'FRIENDS') {
        return `Not ranked in ${inLine} yet — your first confirmed competitive game puts you on the list`;
      }
      const toGo = Math.max(card.resultsToEnter - card.results, 0);
      const more =
        toGo === 1
          ? `1 more competitive ${inLine} game puts you on the list`
          : `${toGo} more competitive ${inLine} games put you on the list`;
      return `${card.results} of ${card.resultsToEnter} games — ${more}`;
    }
    case 'NO_LEVEL': {
      // Friends' card asks for *one* game (§30.5), General's for the wire's count — 5.
      const then =
        view === 'FRIENDS'
          ? 'one competitive game puts you on the list'
          : `${card.resultsToEnter} competitive games put you on the list`;
      return `No ${inLine} level yet — get one, then ${then}`;
    }
    case 'OFF_THE_LIST':
      return `Off the list — no competitive ${inLine} game in 90 days. Your next one puts you back.`;
  }
}

/** **The Friends cards that are the page** (§30.6) — nobody but the reader is listed, or nobody. */
export type FriendsCard = Extract<PlaceCard, { readonly state: 'JUST_YOU' | 'NO_FRIEND_LISTED' }>;

/** §30.6, keyed by the card's state, so a state with no words fails to compile. */
const FRIENDS_CARD_LINE: Readonly<Record<FriendsCard['state'], (sport: Sport) => string>> = {
  JUST_YOU: () => 'Just you so far',
  NO_FRIEND_LISTED: (sport) => `None of your friends is ranked in ${sportInLine(sport)} yet`,
};

/** §30.6: *Just you so far*, or *None of your friends is ranked in padel yet* — each with Add friends. */
export function friendsCardLine(card: FriendsCard, sport: Sport): string {
  return FRIENDS_CARD_LINE[card.state](sport);
}

/** §30.5: the coral button — *Get your squash level*. */
export function getYourLevelLabel(sport: Sport): string {
  return `Get your ${sportInLine(sport)} level`;
}

/** §30.7: *Nobody ranked in badminton yet*. */
export function nobodyRankedLine(sport: Sport): string {
  return `Nobody ranked in ${sportInLine(sport)} yet`;
}

/** §30.7: a row's name — the reader's own reads *You*. */
export function rowName(row: { readonly nickname: string; readonly isYou: boolean }): string {
  return row.isYou ? RANKINGS_COPY.you : row.nickname;
}

/** A row or a podium step, spoken — *6th, Karol, 2,75*. */
export function rankedRowLabel(row: {
  readonly place: number;
  readonly nickname: string;
  readonly level: number;
  readonly isYou: boolean;
}): string {
  return `${ordinal(row.place)}, ${rowName(row)}, ${formatLevel(row.level)}`;
}

/** §30.7: the floating jump button, *You · 212th* (#776). Spoken as it reads. */
export function jumpButtonLabel(place: number): string {
  return `${RANKINGS_COPY.you} · ${ordinal(place)}`;
}

/**
 * **The sport pill's words** — the deck's own control (#774), in this page's words: a sport's name,
 * the pill's spoken name, and what pressing it does here. Read at the call, never at load, for the
 * barrels' cycle the groups page's words note.
 */
export const RANKINGS_PILL_WORDS: SportPillWords = {
  sportName: (sport) => sportLabel(sport),
  pillLabel: (sport) => `Sport: ${sportLabel(sport)}`,
  pillHint: RANKINGS_COPY.pillHint,
};

/**
 * **Top 10 on Home** ([#805](https://github.com/Raketa02/Raketa/issues/805); §31.1, §31.11): FOR
 * YOU's line, *Top 10*, and its footer's link, ***Open the rankings ›*** since
 * [#821](https://github.com/Raketa02/Raketa/issues/821) (ADR-0205 §5; home refactor 12, 13), where it
 * read *Rankings ›*. The pill's hint and the link's spoken name are calls: §31 writes only what is
 * drawn. The empty line is §30.7's `nobodyRankedLine`, as §31.11 cites it, and a card reads
 * `rowName`'s *You*.
 */
export const TOP_TEN_COPY = {
  /** FOR YOU's line (#820) — its title, and what it is named. */
  line: 'Top 10',
  /** The open line's link, drawn with its ›: *Open the rankings ›* (#821). */
  rankings: 'Open the rankings',
  pillHint: 'Shows Top 10 in another sport',
} as const;

/** *Open the rankings ›*, spoken — what it opens: *Open the rankings in padel*. */
export function topTenRankingsLabel(sport: Sport): string {
  return `${TOP_TEN_COPY.rankings} in ${sportInLine(sport)}`;
}

/**
 * A Top 10 card, spoken — *1st, ines.d, 3,40, down 1 this week*, or *7th, You, 2,71, up 1 this week*:
 * the numeral and the drawn chip have no reading of their own.
 */
export function topTenCardLabel(player: TopTenPlayer): string {
  return [
    rankedRowLabel(player),
    ...(player.chip === undefined ? [] : [chipSpoken(player.chip)]),
  ].join(', ');
}

/** **Top 10's pill** — the Rankings page's words, with this row's hint. */
export const TOP_TEN_PILL_WORDS: SportPillWords = {
  ...RANKINGS_PILL_WORDS,
  pillHint: TOP_TEN_COPY.pillHint,
};
