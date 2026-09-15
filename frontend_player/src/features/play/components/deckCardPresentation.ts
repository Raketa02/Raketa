/**
 * Everything the **deck card** says that the other two cards do not — the meta line's third
 * clause, the quoted intro, the four tiles, the hint line, the three buttons' visible marks,
 * and the spoken clauses a listener gets for the tiles.
 *
 * §1's mechanism throughout — code → message, never message → message — and nothing here is a
 * template inlined in a component. The card's *shared* words stay where they were: the level
 * row and the meta line are `playerCardPresentation`'s, and this file composes over them.
 *
 * ## The meta line gains one clause, and it is a liveness code's own words
 *
 * The mocks write *Grzegórzki · 1,9 km · active now*, and none of those three has a producer
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): the area code is never printed, the distance is whole kilometres between coarse areas,
 * and *active now* is activity recency, which ADR-0107 §3 refused on any card. What the line
 * draws instead is `metaLine`'s one licensed clause and the kilometres, plus **`RECENT_ACTIVITY`'s
 * existing words** — *around this week*, deliberately un-datable — drawn when, and only when,
 * the deal's liveness reasons carry the code. It is the same sentence `livenessLine` writes for
 * the reason list, lower-cased because it sits mid-line after a middle dot; the test holds the
 * two equal so a re-wording of one moves the other.
 *
 * ## Four tiles, always four, and a dash where a number is absent
 *
 * *Balance · Reliability · Overlap · Shared tags* — the forecast, the Player Score, the shared
 * slots and the shared-tag count. A tile whose number is absent — the term stood down, the person
 * unwatched, the tags uncompared — prints **`—`** and the row stays four (§7): a row of three
 * would move the other three and say nothing about the fourth. The spoken clauses skip the dash,
 * because *Balance, dash* tells a listener nothing the drawn row does not already decline to.
 *
 * *Reliability* and not *Player Score*, on the record sheet's own argument: beside a Level and a
 * Fit, *Score* is a fourth number a reader can take for a rating, and *reliability* is the one
 * word that says what it is not.
 *
 * ## The intro is quoted, and the quotes are the drawing's
 *
 * The line crosses verbatim and is printed inside typographic quotation marks, so a reader sees
 * it as the person's own words rather than as the card's. The marks are added here, once, rather
 * than at the wire — a quoted string on the wire would be a style decision spelled into a field
 * somebody else reads back.
 */

import { counted } from '@/shared/formatting/counted';
import { formatPercent } from '@/shared/formatting/ratingFormat';

import { livenessLine } from './livenessPresentation';
import { metaLine, type MetaLineFacts } from './playerCardPresentation';

/**
 * The meta line's third clause — `RECENT_ACTIVITY`'s own words, **derived** and lower-cased
 * because it sits after a middle dot. One string in the app for the code, whichever register
 * it is drawn in.
 */
export const AROUND_THIS_WEEK_CLAUSE = livenessLine('RECENT_ACTIVITY').toLowerCase();

/**
 * The meta line's facts, plus whether the deal said this person is around this week.
 *
 * The kilometres are optional here where `MetaLineFacts` requires them: the distance term can
 * stand down, and the week clause is the liveness code's own and does not stand down with it.
 */
export interface DeckMetaLineFacts extends Omit<MetaLineFacts, 'km'> {
  readonly km?: number;
  readonly aroundThisWeek: boolean;
}

/**
 * `In your area · 2 km · around this week`, or as much of it as is true — and nothing at all
 * where neither the distance nor the week is known.
 *
 * With no distance the clause stands alone in the code's own sentence case, because it starts
 * the line: the area comparison is a clause *on* the kilometres and is not drawn without them.
 */
export function deckMetaLine(facts: DeckMetaLineFacts): string | undefined {
  if (facts.km === undefined) {
    return facts.aroundThisWeek ? livenessLine('RECENT_ACTIVITY') : undefined;
  }
  const line = metaLine({ ...facts, km: facts.km });
  return facts.aroundThisWeek ? `${line} · ${AROUND_THIS_WEEK_CLAUSE}` : line;
}

/** The person's own line, inside the card's quotation marks. */
export function quotedIntro(intro: string): string {
  return `“${intro}”`;
}

/** What a tile prints where its number is absent. */
export const NO_VALUE = '—';

/** The four tiles, in the order they are drawn. */
export type DeckTileKey = 'balance' | 'reliability' | 'overlap' | 'sharedTags';

export const DECK_TILE_LABEL = {
  balance: 'Balance',
  reliability: 'Reliability',
  overlap: 'Overlap',
  sharedTags: 'Shared tags',
} as const satisfies Readonly<Record<DeckTileKey, string>>;

/** The four numbers, each **omitted** where the platform has none — never a nought for absent. */
export interface DeckTileFacts {
  /** The forecast, `predicted_balance.pct` — absent where the term stood down. */
  readonly balancePct?: number;
  /** The Player Score — absent where the platform watched nothing. */
  readonly playerScore?: number;
  /** `availability_overlap.shared_count` — absent where the term stood down. */
  readonly sharedSlots?: number;
  /** How many tags the two share — absent where the comparison was not made. */
  readonly sharedTags?: number;
}

export interface DeckTile {
  readonly key: DeckTileKey;
  readonly label: string;
  /** The figure as printed, or {@link NO_VALUE}. */
  readonly value: string;
  /** Whether `value` is a figure — the spoken clauses skip the dash. */
  readonly present: boolean;
}

/** Always four, in one order. */
export function deckTiles(facts: DeckTileFacts): readonly DeckTile[] {
  return [
    tile('balance', facts.balancePct, formatPercent),
    tile('reliability', facts.playerScore, String),
    tile('overlap', facts.sharedSlots, (slots) => counted(slots, 'slot', 'slots')),
    tile('sharedTags', facts.sharedTags, String),
  ];
}

function tile(
  key: DeckTileKey,
  figure: number | undefined,
  print: (n: number) => string,
): DeckTile {
  return {
    key,
    label: DECK_TILE_LABEL[key],
    value: figure === undefined ? NO_VALUE : print(figure),
    present: figure !== undefined,
  };
}

/** `Balance 72%` · `Reliability 88` · … — one clause per tile that has a figure. */
export function deckTileClauses(tiles: readonly DeckTile[]): readonly string[] {
  return tiles.filter((t) => t.present).map((t) => `${t.label} ${t.value}`);
}

/**
 * The hint under the tiles — the mock's, and it names the two paths and the long press.
 *
 * Both halves are load-bearing: the drag is never the only path (§20.5's rule kept in its other
 * half), and the long press is what opens the record — the reading a card cannot fit.
 */
export const DECK_HINT_LINE = 'Drag the card, or use the buttons · long-press for the full record';

/**
 * The 🎾 — the yes button's visible mark, drawn and never spoken.
 *
 * The glyph is in the visible mark alone — `deckAnswerLabels` composes the spoken name without
 * it, per §E6: *"otherwise it announces as 'tennis ball let's play'"*. It is the same split the
 * fit pill's ✦ takes. The ✕ is Feather's and the *i* is a letter, so neither has a word here.
 */
export const ACCEPT_GLYPH = '🎾';
