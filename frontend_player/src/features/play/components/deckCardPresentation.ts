/**
 * Everything the **deck card** says that the other two cards do not — the meta line's third
 * clause, the quoted intro, the three tiles, and the spoken clauses a listener gets for the
 * tiles.
 *
 * §1's mechanism throughout — code → message, never message → message — and nothing here is a
 * template inlined in a component. The card's *shared* words stay where they were: the level
 * row and the meta line are `playerCardPresentation`'s, and this file composes over them.
 *
 * ## The meta line gains one clause, and it is a liveness code's own words
 *
 * The mocks write *Grzegórzki · 1,9 km · active now*, and two of those three have no producer
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): the area code is never printed, and *active now* is activity recency, which ADR-0107 §3
 * refused on any card. The *1,9 km* is real since
 * [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §2 — one decimal, spot to spot, served — and `metaLine` prints it. What the line draws is
 * `metaLine`'s one licensed clause and the kilometres, plus **`RECENT_ACTIVITY`'s
 * existing words** — *around this week*, deliberately un-datable — drawn when, and only when,
 * the deal's liveness reasons carry the code. It is the same sentence `livenessLine` writes for
 * the reason list, lower-cased because it sits mid-line after a middle dot; the test holds the
 * two equal so a re-wording of one moves the other.
 *
 * ## Three tiles, always three, and a dash where a number is absent
 *
 * *Balance · Reliability · Overlap* — the forecast, the Player Score and the shared slots. A tile
 * whose number is absent — the term stood down, the person unwatched — prints **`—`** and the row
 * stays three (§7): a row of two would move the other two and say nothing about the third. The
 * spoken clauses skip the dash, because *Balance, dash* tells a listener nothing the drawn row
 * does not already decline to.
 *
 * §7 drew a fourth, *Shared tags*, counting the row of tags just above it. It went on
 * 2026-09-15: the tag row already leads with the shared ones in volt and *· you too*, so the count
 * was a number restating what the eye had just read, and a tile of the four that could say
 * nothing the card had not said. The card keeps its three spellings of absence on the row
 * itself (`socialTagOverlap`).
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
 * `In your area · 1,9 km · around this week`, or as much of it as is true — and nothing at all
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

/** The three tiles, in the order they are drawn. */
export type DeckTileKey = 'balance' | 'reliability' | 'overlap';

export const DECK_TILE_LABEL = {
  balance: 'Balance',
  reliability: 'Reliability',
  overlap: 'Overlap',
} as const satisfies Readonly<Record<DeckTileKey, string>>;

/** The three numbers, each **omitted** where the platform has none — never a nought for absent. */
export interface DeckTileFacts {
  /** The forecast, `predicted_balance.pct` — absent where the term stood down. */
  readonly balancePct?: number;
  /** The Player Score — absent where the platform watched nothing. */
  readonly playerScore?: number;
  /** `availability_overlap.shared_count` — absent where the term stood down. */
  readonly sharedSlots?: number;
}

export interface DeckTile {
  readonly key: DeckTileKey;
  readonly label: string;
  /** The figure as printed, or {@link NO_VALUE}. */
  readonly value: string;
  /** Whether `value` is a figure — the spoken clauses skip the dash. */
  readonly present: boolean;
}

/** Always three, in one order. */
export function deckTiles(facts: DeckTileFacts): readonly DeckTile[] {
  return [
    tile('balance', facts.balancePct, formatPercent),
    tile('reliability', facts.playerScore, String),
    tile('overlap', facts.sharedSlots, (slots) => counted(slots, 'slot', 'slots')),
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
