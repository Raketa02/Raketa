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
 * with no rating in any sport has no `skill` and an empty `sports`; one with no counted game has
 * no `variety`; one nobody has rated has no `opinion`. **Each absence asks a different question
 * and they do not move together** — somebody rated in four sports may never have had a game
 * counted, and somebody with a full record of counted games may have been rated by nobody, since
 * rating is a favour and nothing anywhere records that a card was ignored — so each is read where
 * it is drawn and nothing is inferred from another.
 *
 * **`reliability` is not one of them any more** (ADR-0195 §1): everyone starts at 100, so the
 * figure is there for a player nothing has happened to as for anybody, and reads *New*.
 *
 * ## What is deliberately not here
 *
 * **No moment, at any granularity.** Not a timestamp, not *active today*, not a green dot.
 * `lastFive` carries outcomes in order and no dates, and a `lastPlayedAt` beside it would be
 * the same refusal one field further in.
 */

import type { FriendRelation } from '@/features/friends/types';
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

/**
 * **The four bands Player reliability is read in** — the word under the figure
 * ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §1), best first.
 *
 * **Served, and never derived here.** This client holds no 90, 75 or 50: the tone ladder that
 * once drew a bar at 70 nothing applied was a second set of thresholds, and a phone working the
 * band out from the figure disagrees with the server the day the floors move, on exactly the
 * figures a player looks at twice. Written down here rather than read off the contract because a
 * copy table is keyed by it and transport does not reach `components/` — the two are held equal
 * by the compiler in `mappers/wireVocabulary.ts`.
 */
export const RELIABILITY_BANDS = ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW'] as const;

export type ReliabilityBand = (typeof RELIABILITY_BANDS)[number];

/**
 * **The figure and its word** — what the You row's line, the record block, the ring and the
 * Members tag's spoken name are built from. Named apart from the counts because those four read
 * it without them.
 */
export interface ReliabilityFigure {
  /** Points, 0 to 100. Everyone starts at 100. **Served, never derived.** */
  readonly playerScore: number;
  /**
   * The word under the figure, as the server banded it. **Absent only where this build cannot
   * name the served code** — the figure is then drawn alone rather than with a guessed word.
   */
  readonly band?: ReliabilityBand;
  /**
   * Fewer than 3 games played through, ever, across sports: the figure reads *New* in the band's
   * place, because a 100 nobody has tested yet is not a *Very high* one.
   */
  readonly isNew: boolean;
}

/**
 * **The four counts the record shows beside the figure**, over the last 6 months — counts and
 * never ratios, and no ledger (ADR-0195 §1: the product owner chose counts over a list of
 * events).
 */
export interface ReliabilityCounts {
  /** *Shows up*: turned up, late counting as turned up… */
  readonly turnedUp: number;
  /** …of the games that reached their hour with them on the court. May be nought. */
  readonly turnedUpOf: number;
  /** *Being late*: how many times they came late. */
  readonly late: number;
  /** *Keeps plans*: kept… */
  readonly kept: number;
  /** …of the booked games they were in at the hour. May be nought. */
  readonly keptOf: number;
  /** *Results left in dispute*: information only, and it costs no points. */
  readonly leftInDispute: number;
}

/**
 * **The two bands a filter can ask for** — the switch's on positions, *at least Medium* and *at
 * least High* ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §6, [#662](https://github.com/Raketa02/Raketa/issues/662)). Two and not four: the route offers
 * exactly these, and the two are held equal to its request in `mappers/wireVocabulary.ts`.
 */
export const RELIABILITY_MINIMUMS = ['MEDIUM', 'HIGH'] as const;

export type ReliabilityMinimum = (typeof RELIABILITY_MINIMUMS)[number];

/**
 * **Your filter, as it stands in your groups** — on your own record only, and it names nobody.
 *
 * `minimum` is **absent while the filter is off**, which it is until the player switches it on;
 * `hides` is how many of the `of` other players in the player's groups it keeps off their courts,
 * never somebody New, and nought while it is off. Both counts are the server's: the client holds
 * no roster to count against.
 */
export interface ReliabilityFilter {
  readonly minimum?: ReliabilityMinimum;
  readonly hides: number;
  readonly of: number;
}

/**
 * **The figure that deals you with everyone again** — present only while somebody in the player's
 * groups filters them out, and it names nobody: the band in *play only with High reliability or
 * above* and the points that band begins at. The server picks the band (the highest minimum among
 * the filters that hide the player), so reaching its floor passes every one of them at once.
 */
export interface BackWithEveryone {
  readonly band: ReliabilityBand;
  readonly points: number;
}

/**
 * **Player reliability** — the figure in points, its band, *New*, and the counts it is read
 * beside ([#660](https://github.com/Raketa02/Raketa/issues/660)).
 *
 * It replaced the pill and the metered strands it was the weighted mean of: there are no
 * weights, no ratios and no tone here, and nothing on this client blends, bands or thresholds
 * anything.
 */
export interface Reliability extends ReliabilityFigure {
  readonly counts: ReliabilityCounts;
  /**
   * The player's own filter and what it hides — **on your own record only**, and absent where
   * this build cannot name the position it is saved at, so a switch is never drawn standing at
   * Off over a filter that is on.
   */
  readonly filter?: ReliabilityFilter;
  /** Somebody's filter keeps you off a court, and this is the figure back. Own record only. */
  readonly backWithEveryone?: BackWithEveryone;
}

/**
 * **How widely they spread their games — the raw pair, over their whole record.**
 *
 * Two counts and no percentage, deliberately: the card argues three rows above that a perfect
 * record over nine games and one over forty are different claims, so a bare share here would
 * break the rule the card had just made about itself. The share is one division and it is this
 * client's ([`recordCard`](./recordCard.ts)).
 *
 * **It is about every sport**, unlike the skill panel's run of five — a person who plays padel
 * with the same four faces and squash with twenty has one habit — and it is a **career
 * statistic rather than a window**, which is what makes the number mean *how widely do they
 * spread their games* rather than *how widely this season*.
 */
export interface OpponentVariety {
  /**
   * How many **different people** those games were against.
   *
   * A doubles partner is one of them: *a pair is anybody you were on a court with* is the rule
   * this platform already counts familiarity by.
   */
  readonly distinctOpponents: number;
  /**
   * How many **times they were on a court with somebody**, across their counted games.
   *
   * **A count of seats opposite and never of games**, which is the correction rather than a
   * preference: a doubles evening puts three people on the court, so a game-denominated pair
   * published `3 of 1` — a fraction whose numerator exceeds its denominator, drawable only by
   * clamping a share that had gone over a hundred. Counting encounters makes both halves the
   * same kind of thing, and `distinctOpponents` can never exceed it.
   *
   * **Not the skill panel's `countedGames`.** That one is what a Level rests on — confirmed
   * results, in one sport, that the rating folded. This counts people met, across every sport.
   */
  readonly timesOnCourt: number;
}

/**
 * **What other players said** — the average and the number of different people it rests on,
 * to every reader, the subject included.
 *
 * One shape and no arms. It had two: a reader was answered with the figure and the **subject**
 * with a coarse band and no count, folded at the wire boundary from `is_self`, because a
 * published average beside a published count is a **subtraction** — moving from 4,80 over ten
 * to 4,73 over eleven names the new rating as a 4, and the subject knows who they played.
 * [ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §5 weighed that against a player being told *Mixed* about themselves with no number to work
 * on, chose the number, and retired the band from the wire
 * ([#468](https://github.com/Raketa02/Raketa/issues/468)) and from this client
 * ([#473](https://github.com/Raketa02/Raketa/issues/473)). What holds the subtraction in check
 * is the record's own and not this shape's: the collapse to one answer per rater, the
 * fifty-rater window, no zero on the scale, and no individual rating on any route.
 *
 * **It is not in Player reliability.** A star average is not points, nothing acts on it, and it
 * is drawn as the card's last row under a label naming its own author — because every row above
 * it was counted by the system and this is the one thing on the sheet people wrote.
 *
 * Named once because three layers pass it around: the mapper builds it, the row draws it and
 * the spoken reading reads it, and a shape restated at each of those is the shape that
 * eventually differs at one of them.
 */
export interface Opinion {
  /** The mean of what they said, out of five, to one decimal. **Served, never derived.** */
  readonly average: number;
  /**
   * How many **different people** it rests on — always drawn beside the figure.
   *
   * People and not ratings: only somebody's most recent stars count, so a weekly partner is one
   * rater however many evenings they play. At most fifty, which is the window.
   */
  readonly raters: number;
}

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

/**
 * **One of a player's photos on their record** (#799) — its id, which keys it, and a short-lived
 * signed link minted for the response that carried it and recorded nowhere.
 */
export interface RecordPhoto {
  readonly photoId: string;
  readonly photoUrl: string;
}

export interface PlayerRecord {
  /**
   * **The server's answer, never a comparison this client made.** It retitles the sheet and
   * drops the distance, and getting it wrong is most visible on the one screen it matters on.
   */
  readonly isSelf: boolean;
  /**
   * **What this player is called** — their nickname, whole and never with an @, drawn large at the
   * head of the sheet with nothing under it
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). Nothing
   * may derive a familiar form from it.
   */
  readonly nickname: string;
  /**
   * One line they wrote about themselves — their **intro** — verbatim, drawn under the nickname
   * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)).
   *
   * **Omitted where they wrote none**, and never an empty string: the intro is optional and
   * a player who skipped has no line rather than an empty one. Fenced at the write against a
   * phone number, an email, a URL or an `@handle`, so what arrives is a line about a player
   * and never a way to reach one. The same field the deck card carries, read off the profile
   * as it stands rather than off a search record. Present on your own record as on anybody
   * else's — it is what strangers read, shown back to you.
   */
  readonly intro?: string;
  /** Absent where they have no photograph, and on a link that has expired — both draw the poster. */
  readonly photoUrl?: string;
  /**
   * **Every photo, in their own order** — the first is `photoUrl`'s
   * ([ADR-0204](../../../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
   * §2, [#799](https://github.com/Raketa02/Raketa/issues/799)). Whoever the record opens for sees
   * them all, a stranger included. Empty where they have none: the header's poster stands alone.
   */
  readonly photos: readonly RecordPhoto[];
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
   * Player reliability — the figure, its band, *New* and the four counts. **Always there**:
   * everyone starts at 100, so a player nothing has happened to reads *100 · New*.
   */
  readonly reliability: Reliability;
  /**
   * The variety row, which is an **absence** of its own.
   *
   * Omitted where no counted game has ever been recorded for them — a habit nobody has been
   * observed having is not a narrow one.
   */
  readonly variety?: OpponentVariety;
  /**
   * What other players said — the figure and its count, whoever is reading.
   *
   * A **third absence**, asking a third question: omitted where nobody has rated them, which is
   * most people. Rating is a favour, ignoring the card costs nothing, and nothing anywhere
   * records that somebody did not answer — so a game played is not an opinion anybody offered.
   */
  readonly opinion?: Opinion;
  /**
   * **Where the reader stands with them** ([#753](https://github.com/Raketa02/Raketa/issues/753),
   * ADR-0202 §1) — the left button of the record's foot, beside *Block*: *Add friend*, *Request
   * sent ▾*, *Accept* or *Friend ✓ ▾*. `NONE` on your own record, which draws neither.
   *
   * **Nothing here says whether either of them blocked the other** (#773, #779; ADR-0203 §8): a
   * record never opens across a block, either way, so *Block* is always *Block* and Unblock lives in
   * You › Blocked players.
   */
  readonly relation: FriendRelation;
  /**
   * **Whether to offer *Add friend*** ([#779](https://github.com/Raketa02/Raketa/issues/779);
   * ADR-0204 §2, [#799](https://github.com/Raketa02/Raketa/issues/799)) — the server's answer:
   * `relation` is `NONE` and this is not your own record. A request is admitted by the rule the record
   * opened by, so a record that opens is somebody the reader may ask, as many as they like — there is
   * no daily limit. Where it is `false` and nothing stands between them, *Block* stands alone
   * (`friends`' `recordFootOf`).
   */
  readonly canAddFriend: boolean;
}
