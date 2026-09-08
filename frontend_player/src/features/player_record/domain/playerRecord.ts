/**
 * **Everything the platform will say about one person, to this reader** — the record sheet's
 * own shape, mapped once at the wire boundary and read by nothing else
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)).
 *
 * ## A record is live, and a card is recorded
 *
 * A player card is a *recorded* answer frozen into an immutable search record, bounded to
 * twenty rows and closed by decision to facts about the searched sport. This is the other
 * thing: current at the moment of opening, every sport, and able to answer about **you** —
 * which no card route can, because no search ever returned the searcher. That is why the
 * shapes are separate types over separate routes rather than one widened card.
 *
 * ## Absence has one spelling, and it is the field's own
 *
 * Every optional here is *the platform has nothing to say*, and **never a nought**. A player
 * with no rating in any sport has no `skill` and an empty `sports`; one nothing has ever
 * fallen due for has no `playerScore`. The four absences on this response ask four different
 * questions and do not move together — somebody rated in four sports may never have had a
 * game counted — so each is read where it is drawn and nothing is inferred from another.
 *
 * ## What is deliberately not here
 *
 * **No moment, at any granularity.** Not a timestamp, not *active today*, not a green dot.
 * `lastFive` carries outcomes in order and no dates, and a `lastPlayedAt` beside it would be
 * the same refusal one field further in.
 */

import type { GameResult } from '@/shared/vocabulary/gameResult';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { Sport } from '@/shared/vocabulary/sport';

/**
 * **Whose record is being opened, and through which door.**
 *
 * Two routes and not one comparison: your own face reads `GET /players/me/record`, which is
 * ungated deliberately — *this is the one screen a held player has for finding out how they
 * appear* — and every other face reads the parameterised route, where admission is decided
 * against a prior disclosure the client cannot see.
 *
 * **The `kind` is the caller's own knowledge and never a derived one.** The court already
 * knows which seat is the searcher's; what it must not do is compare identifiers to find out.
 * Whether the sheet retitles is `PlayerRecord.isSelf` — **the server's answer** — and the two
 * are separate on purpose: this one picks a route, that one picks the words.
 *
 * `playerId` is carried on both arms because the header draws a **generated poster** for a
 * player with no photograph, and a poster is a fact about an id. The `/me` route never sends
 * one back.
 */
export type RecordSubject =
  | { readonly kind: 'me'; readonly playerId: string }
  | { readonly kind: 'player'; readonly playerId: string };

/** One sport somebody holds a rating in, as the header's pill draws it. */
export interface RatedSport {
  readonly sport: Sport;
  readonly level: number;
}

/**
 * The skill card, **for the one sport the sheet is about** — which the server resolved and
 * states back.
 *
 * The sport asked for wins where they are rated in it; otherwise it is the one they have
 * played most. So `sport` is read here rather than assumed to be what was sent, and the panel
 * prints it.
 */
export interface SkillPanel {
  readonly sport: Sport;
  readonly level: number;
  /**
   * The band's published **name**, exactly as the wire spelled it.
   *
   * A key and never derived from the Level: a client mapping a number to a band would be a
   * second set of drawing constants, and the day the boundaries move the two disagree. It is
   * resolved to the bar's own `BandKey` where the bar is drawn, and a band this build cannot
   * name draws no highlighted segment rather than a guessed one.
   */
  readonly band: string;
  /** How sure the platform is, as a whole percentage. Meaningless without `countedGames`. */
  readonly confidence: number;
  /** What that certainty rests on. **`0` is a real answer** — a rating no game has tested. */
  readonly countedGames: number;
  readonly likelyRange: { readonly low: number; readonly high: number };
  /**
   * Their last counted results **in this sport**, oldest to newest.
   *
   * Fewer than five is a real answer and is never padded; an empty list is none. Absent
   * entirely where an outcome this build cannot read was in the run — its length is a claim,
   * so a run half read is a run that cannot be drawn.
   */
  readonly lastFive?: readonly GameResult[];
}

export interface PlayerRecord {
  /**
   * **The server's answer, never a comparison this client made.** It retitles the sheet and
   * drops the distance, and getting it wrong is most visible on the one screen it matters on.
   */
  readonly isSelf: boolean;
  /** The whole handle. Nothing may derive a familiar form from it. */
  readonly nickname: string;
  /** Absent where they have no photograph, and on a link that has expired — both draw the poster. */
  readonly photoUrl?: string;
  /**
   * Whether the photograph wears the **ON COURT** mark — folded here and nowhere else.
   *
   * A boolean rather than the verdict, because *checked and flagged* and *nobody looked* draw
   * **identically** (ADR-0138): a sheet holding the code could branch on it a second way, and
   * the second way is the one that tells a reader a stranger's photograph was doubted. Folding
   * it at the wire boundary makes that unrepresentable rather than merely undone.
   */
  readonly onCourt: boolean;
  /** Their coarse area, as a machine code. **An identifier and never a name.** */
  readonly areaCode: string;
  /** The tags they publish, in the vocabulary's own order. The overlap is not here. */
  readonly socialTags: readonly SocialTagId[];
  /** One per rated sport, **in the registry's own order** — never re-sorted. */
  readonly sports: readonly RatedSport[];
  /** Omitted where they hold no rating at all; the pills then speak alone. */
  readonly skill?: SkillPanel;
  /**
   * Their **Player Score** out of a hundred — the figure the matcher acts on.
   *
   * Omitted where nothing has ever fallen due for them, which is most people today, and is
   * never a nought: nobody has failed to turn up who was never due to.
   */
  readonly playerScore?: number;
}
