/**
 * **The builder** — the court, and the three ways to fill it.
 *
 * Where a finished search goes, and the screen the last three tickets deliberately declined to
 * point at ([#271](https://github.com/Raketa02/Raketa/issues/271)). ⚡ fills every empty seat
 * at once, *Pick players myself* opens the pool, and hand-seating somebody and then pressing ⚡
 * is the third — which is the *same request* as the first, because `locked_seats` is *"a
 * property of what you send rather than of where you send it"*.
 *
 * ## What this screen holds, and what it refuses to
 *
 * The **membership** is `playSession`'s — `{ originSearchId, seats }`, ids and nothing else —
 * and the **facts** about those ids are Query's, read back off the record under
 * `searchKeys.detail(originSearchId)`. Between them sits the one thing that is neither: the
 * **seating**, which is where each of them is standing right now.
 *
 * It is route-local, and it has to be. A seating is meaningless off this court, it is not a
 * fact about the line-up — `ForecastResponse` answers with *every* arrangement whatever order
 * the request was sent in — and the court **pops** back from the pool, so a route-local value
 * survives exactly as long as the court a player is looking at. It is also *derived* rather
 * than initialised: absent means *whatever the current arrangement says*, so an answer landing
 * seats people without this screen writing anything down.
 *
 * **The origin can change under it, and that is ⚡.** `POST /lineups` mints a search of its
 * own, so a fill re-binds the line-up to the record it just wrote: the four it seated came off
 * *that* search's rows, and `POST /forecasts` refuses anybody the cited search never showed.
 * Everything else here reads the origin off the line-up, so nothing else has to know.
 *
 * ## The wait is under the court, and the court fills one seat at a time
 *
 * ⚡'s wait is **not** `SearchingLatch`, and the difference is what the answer is about. A
 * search on *Find a game* has nothing on screen to show, so its wait covers the screen and
 * lifts onto this one; a fill seats people on a court the player is **already looking at**, so
 * a latch takes away the one thing the wait is about and hands it back complete a second and a
 * half later. `SeatingWait` is a block in the page instead, and the seats land behind it in
 * seat order (`seatReveal`).
 *
 * That is what `motion.hold.fill`'s `650 plus 550 a seat` had always been for — the 550 is
 * booked in `theme.ts` to *"the animation it drives"*, and nothing drove it. **The line-up is
 * therefore committed when the last seat lands rather than when the response does**: seating
 * it on the response would put a full court and its forecast card on screen underneath a wait
 * still drawing the seats.
 *
 * Nothing is delayed by any of it. The whole answer is in memory before the first seat
 * appears, which is `the-play-screens.md` §3's *"presentation over a completed answer"*.
 *
 * ## The court is a fixed width, and the width is chosen by the seat
 *
 * `size.court.build` is `46 / seatRatio`, because **46pt is the seat every rule about a seat
 * is written against** — 7.12's handle truncation, the clear badge's 44-inside-46 conflict.
 * Drawn at the content width, as this screen drew it, that seat is 81pt on a large phone and
 * every one of those arguments is about a court nobody draws.
 *
 * ## A swap is a selection, and only membership costs a round trip
 *
 * `ForecastResponse` returns **all three** arrangements, so trading two seats picks a different
 * one out of a response already held: instant, with no request. What is asked for is a
 * *membership* — add, replace, remove — and `searchKeys.forecast` sorts the ids into its key so
 * seat order cannot mint a second entry for one question
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §11).
 *
 * **No forecast arithmetic runs here**, and the check for that is looking for arithmetic. The
 * only numbers this file computes are seat counts. The percentage, its word, its tone, the two
 * side strengths, the gap between them, whether it is provisional and which arrangement is the
 * evenest are all read.
 *
 * ## The court opens on the evenest arrangement, and it opens that way for free
 *
 * `is_current` on a **line-up** is the evenest arrangement, and `lineup.seats` is that
 * arrangement's seating ([#289](https://github.com/Raketa02/Raketa/issues/289)) — so the four
 * a fill lands are already sitting the closest game they can play, *Even it out* is drawn
 * **shut**, and the sentence beside the figure says why. Nothing on this side selects it: the
 * client drew `is_current` before and draws it now, which is the whole of what that ticket cost
 * here. A swap lights the control, moves the figure and turns the sentence into what pressing
 * it would buy; pressing it puts them back.
 *
 * **Trading the two opponents is silently allowed and the figure does not move.** A pairing is
 * who is beside you, so the seats move and it is the same game — nothing is said, and nothing
 * needs to be (`domain/forecast`'s selection rule).
 *
 * ## A swap is no longer a mode, and the toggle it needed is gone
 *
 * It was a `switch` in a card over the court (6.12's first and only consumer), because a tap
 * on an occupied seat meant two things: *replace this player* with it off, *trade these two*
 * with it on. What made the second meaning need a control was that the first one existed.
 *
 * **The forecast card is what removed the first.** Its side rows draw every seated player as
 * their own face and handle — a 44pt control opening that person's record — so the court's
 * seats stopped being the place a player goes to find out about somebody or to act on them.
 * A seat with one meaning needs no mode to disambiguate it, so it trades, always, and what
 * was the switch's description is now a line of copy above the graphic (`SWAP_HINT`).
 *
 * **Replacing somebody is the clear badge and then the hole it leaves** — two taps where there
 * was one, on exactly the seats a replacement was ever allowed against, and *Pick players
 * myself* still opens the pool without touching the court at all. Both refusals went with the
 * mode, because there is no replacement left on a tap to refuse (`domain/lineup`).
 *
 * ## The card no longer says why these four
 *
 * `GroupReason` had a row of its own under the names — *the four of you share the most slots*
 * and two others. It is gone, and the copy went with it rather than staying as a table nothing
 * renders: read under two side strengths, a signed gap, an evenness percentage and four faces,
 * a sentence naming what the engine went looking for is a caption on an answer the reader has
 * already been given four views of. The code is still parsed; only the sentence is gone.
 *
 * ## What the forecast card draws, and the one thing it still refuses
 *
 * **The two side strengths, the gap between them, and a two-segment bar.** Every one of those
 * is a number only the engine has — a side's strength is not the mean of the two people
 * standing on it — and the card went without them for exactly as long as that stayed true:
 * `SidesSchema` carried seats and no strengths, so drawing them meant averaging the seated
 * players' levels, which is the one thing §11.3 says the check is looking for.
 * `ArrangementSchema.split` is what changed it
 * ([#289](https://github.com/Raketa02/Raketa/issues/289), ADR-0136): `your_side`, `their_side`
 * and a **signed** `gap`, three views of the computation `pct` is the fourth view of. The bar
 * takes the gap as its `advantage` and maps it itself
 * ([7.11](../../../../docs/design-system.md#711-the-balance-bar)); this screen does no
 * arithmetic over any of the three.
 *
 * > The note this replaces said *"the builder draws no balance bar, because 7.11 takes an
 * > advantage and nothing on a line-up serves one."* It is rewritten rather than deleted,
 * > because the reason it was true is the reason the bar is honest now: what makes a bar
 * > drawable is a **served** advantage, and there is one.
 *
 * **A confidence tag is still refused.** `sigma_group` crosses, and a *high · medium · low*
 * pill over it is a client thresholding an engine number. `the-words.md` §16 puts `confidence`
 * in exactly one place — the candidate card's `PredictedBalanceEvidence`, where the engine
 * serves the percentage — and *"this is the only place `confidence` is drawn at all"*.
 *
 * What the card says beside the figure is **what the control beside it would buy**: the evenest
 * arrangement's own percentage, read out of a response already held (`arrangedYourWayLine`).
 * That is a selection like *Even it out* itself, not a calculation.
 *
 * **The card names the same four people twice, and the two rows are different things.** The
 * split row labels a **strength** — one box, one number, whose half of the court it belongs to
 * — and the names beneath it are one **control** per person, each opening `SH.whyfit` for the
 * player it names (§20.4.1). To a listener they are one element and four, which is §20.1
 * deciding it: the split row has no action in it and the names each have one.
 *
 * ## ⚡ raises questions, and the sheet has nowhere to stand in front of
 *
 * `POST /lineups` mints a search like `POST /searches` does, and a minted search raises
 * prompts. Find a game asks them between the latch lifting and the court being pushed; here
 * the court **is** what the fill landed on, so the sheet stands in front of an answer already
 * on screen and closing it is the whole of where anybody goes
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * **`REFRESH_YOUR_TIMES` never reaches this screen.** Its *yes* is a request for the week
 * grid, this screen has none, and a sheet drawing it would either promise a control that is
 * not here or — since dismissal is *not now*, and *not now* suppresses for thirty days — spend
 * the offer on the surface that cannot honour it. The use-case drops it.
 *
 * ## The one thing on this screen that reaches another person
 *
 * *"Searching, browsing, seating, swapping and replacing produce nothing outbound"* — and then
 * the court fills, and the pinned slot becomes **the send**. It is drawn here and owned
 * elsewhere: the CTA is *"the screen's own 10.1 slot, **calling** a challenges use-case"*, and
 * `SH.propose`, the send itself and every sentence either says are `features/challenges/`'
 * ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md) §8).
 *
 * **Pending, never optimistic, and the *or* dissolves.** Success replaces the whole stack, so a
 * rolled-back send has nowhere to return *to*; nothing is rolled forward, so nothing needs
 * rolling back. The control is busy, the stack is replaced on success only, and the toast fires
 * after the reply ([#239](https://github.com/Raketa02/Raketa/issues/239) §5).
 *
 * **And a refusal is followed by a re-read, never by a payload.** Both sources are already this
 * screen's: `line_up_no_longer_sendable` re-reads the **origin search**, whose withheld rows the
 * court already turns into marked seats, and the open-challenge refusal re-reads the player's
 * own challenges for a name. **Neither re-runs the search** — that mints an id the whole line-up
 * must adopt and can drop a seat nobody touched, which is H-18's harm arriving through the
 * remedy. When the re-read marks nobody, the court says so **at court level** rather than
 * leaving the player refused in front of four seats that all look fine.
 */

import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import {
  A_PAIR_HERE_IS_ALREADY_PLAYING,
  CHALLENGE_SENT,
  LINE_UP_CHANGED,
  NOTHING_MARKED_AFTER_THE_REFRESH,
  ProposeSheet,
  SENDING_LABEL,
  SEND_CHALLENGE_LABEL,
  challengeErrorMessage,
  openChallengeLine,
  sendRefusal,
  useInviteSeats,
  useOpenPair,
  useSendChallenge,
  type ProposedCourt,
  type SendRefusal,
} from '@/features/challenges/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { ShellScreen, landOnNow } from '@/features/shell/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { handleStem, playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import {
  BALANCE_INK,
  BALANCE_SOFT,
  BalanceBar,
  Button,
  Card,
  Hairline,
  Note,
  PlayerPhoto,
  behindOverlay,
  courtSeatCount,
  theme,
  useCollapsedPresentation,
  useLiveRegion,
  type BalanceBarTone,
} from '@/shared/ui';

import type { Candidate } from '../domain/candidate';
import {
  arrangementFor,
  courtSeating,
  courtWithYou,
  evenestArrangement,
  firstEmptySeat,
  seatedIds,
  seatingOf,
  seatingToDraw,
  seatsFilled,
  shortfallBySeat,
  swapSeats,
  toBuildSeat,
  type SeatOccupancy,
  type Seating,
} from '../domain/forecast';
import { seatPlaces, withheldSeats, type CourtHalf } from '../domain/lineup';
import { socialTagOverlap } from '../domain/socialTagOverlap';
import { alreadyAsked } from '../domain/raisedPrompt';
import type { UnfilledReason } from '../domain/vocabulary';
import { sentWeekForOrigin } from '../domain/workingWeek';
import { useFillSeats, useForecast, useSearchRecord } from '../hooks/useBuilder';
import { useReadSearchBack } from '../hooks/usePool';
import { usePlaySession } from '../store/playSession.store';

import {
  PLAY_LIVE_REGIONS,
  courtSummaryLabel,
  provisionalForecastAnnouncement,
  seatedNameLabel,
  splitRowLabel,
} from './accessibilityPresentation';
import { balanceLabel, balanceTone, balanceWord } from './balancePresentation';
import {
  ALREADY_EVENEST,
  EVEN_IT_OUT_LABEL,
  GAP_WORD,
  arrangedYourWayLine,
  FILLING_LABEL,
  FORECASTING_LABEL,
  NO_RECORD_BODY,
  NO_RECORD_TITLE,
  PICK_PLAYERS_LABEL,
  PROVISIONAL_WORD,
  RETRY_FORECAST_LABEL,
  SIDE_HEADINGS,
  START_OVER_LABEL,
  SWAP_HINT,
  VS_WORD,
  USE_MATCHMAKING_LABEL,
  UNREADABLE_SEARCH_TITLE,
  builderTitle,
  forecastHeading,
  sideName,
} from './builderPresentation';
import { CourtBuild } from './court/CourtBuild';
import { PromptSheet } from './PromptSheet';
import type { CourtSeatOccupant } from './court/CourtSeat';
import { handlesOn, type SeatedHandle } from './court/seatedHandles';
import { WITHHELD_SEAT_LINE, optimisedForLine, unfilledSeatLine } from './courtPresentation';
import { useHeldWait } from './heldWait';
import { playErrorMessage } from './playErrorMessage';
import { SeatingWait } from './SeatingWait';
import { forecastAssumption } from './searchPresentation';
import { engineFillStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';
import { useSeatsRevealed } from './seatReveal';
import { WhyFitSheet } from './whyfit/WhyFitSheet';

/**
 * The pool — the ranked list, and **the one screen the ladder is on**
 * ([#272](https://github.com/Raketa02/Raketa/issues/272)).
 *
 * Every remedy this court states routes here and nowhere else, which is what makes the
 * shortfall statements actionable rather than informative: a seat's own tap and the control
 * beneath the court are the same act against the same seat.
 */
export const POOL_ROUTE = '/play/pool';

/**
 * The builder's own path, named here so the screen that pushes it and the screen that is
 * pushed are one edit apart.
 *
 * Play owns its inner paths — the shell's table holds each tab's **start**, and everything
 * under `/play/…` is this feature's own depth (`PlaySegment`'s `DECK_ROUTE`, same rule).
 */
export const BUILDER_ROUTE = '/play/builder';

export interface BuilderScreenProps {
  /**
   * The search this builder was opened on — validated by the route (`schemas/routeParams.ts`).
   *
   * It is the origin **until a line-up exists**, after which the line-up's own is
   * authoritative: ⚡ mints a search and re-binds to it, and a screen still reading its arrival
   * param would ask for a forecast under a search that never showed the people now seated.
   */
  readonly arrivalSearchId: string;
}

export function BuilderScreen({ arrivalSearchId }: BuilderScreenProps) {
  const lineup = usePlaySession((state) => state.lineup);
  const seatAll = usePlaySession((state) => state.seatAll);
  const unseat = usePlaySession((state) => state.unseat);
  const discardLineup = usePlaySession((state) => state.discardLineup);
  const profileSurface = useProfileSurface();

  /**
   * The search the court's **answer** came off, when there is no line-up to read it from.
   *
   * ⚡ can seat nobody — *three of four is an honest answer, and so is nobody* — and that
   * answer still has a court with a reason on every seat. Without this, a fill that seated no
   * one would leave the screen reading the record it arrived on, and the reasons the engine
   * gave would be dropped on the floor.
   */
  const [answeredSearchId, setAnsweredSearchId] = useState(arrivalSearchId);
  const originSearchId = lineup?.originSearchId ?? answeredSearchId;
  const record = useSearchRecord(originSearchId);

  /**
   * **Who you are, which is the account's fact rather than an answer's**
   * ([#282](https://github.com/Raketa02/Raketa/issues/282)).
   *
   * `Relationship.SELF` names the searcher on every seating the engine returns, and reading
   * the id off one was the whole of what this screen had — but the builder draws a court
   * **before any answer exists**, so your own seat was a ring with no face until a fill came
   * back. The id is served, and has been all along: `GET /users/me` is where an id comes
   * from, and the searcher a route reads off the bearer token is this same player.
   *
   * It is read here, at the screen, and handed down — a seat that fetched its own occupant
   * would be a drawing reaching for global state. `SELF` keeps the job it is actually for:
   * **which seat** is yours, which is a fact about an arrangement and not about an account.
   *
   * `undefined` while the launch read is still in flight, which is the one frame the faceless
   * seat is still honest for.
   */
  const self = useCurrentUser().data?.id;

  const fill = useFillSeats();
  const send = useSendChallenge();
  /**
   * **The same act on a court that already stands** — `POST /challenges/{id}/seats`, the send's
   * shape minus the mint.
   *
   * Both are mounted and exactly one is ever used, decided by whether the origin names a
   * challenge: a hook mounted conditionally is not a hook, and the alternative — a second screen
   * component — is the fork `the-loop-components.md` §4.2 refuses by putting *one screen at two
   * routes*.
   */
  const invite = useInviteSeats();
  /**
   * The remedy for `line_up_no_longer_sendable`, and **the pool's own act borrowed rather than
   * copied**: it writes the whole record back under the key this screen is already subscribed
   * to, so a marked seat appears from one cache write and nothing here holds a second answer.
   */
  const reread = useReadSearchBack();
  /**
   * The send is the one act in the app that **fails** offline rather than pausing, so it is the
   * one control with nothing to read its own paused state off. Part 11: the closed button is
   * the courtesy and `networkMode: 'always'` is the mechanism.
   */
  const online = useIsOnline();
  const collapsed = useCollapsedPresentation();

  /**
   * Where each of them is standing. **Absent is not empty** — it is *whatever the arrangement
   * says*, which is what lets an answer land without this screen writing a seating down.
   */
  const [seating, setSeating] = useState<Seating | undefined>(undefined);

  /**
   * **The court ⚡ answered with, while it is still landing on screen.**
   *
   * The fill's answer is in memory the moment the response arrives, and the line-up is
   * committed to `playSession` only once the last seat has been drawn — which is what lets the
   * court fill **one seat at a time** rather than arriving complete behind a lifted latch
   * (`seatReveal`). Nothing is delayed: the beat is presentation over an answer already held,
   * and `motion.hold.fill`'s 550-a-seat has been booked to it since before it was drawn.
   *
   * Route-local with the seating, and for the same reason: it is meaningless off this court
   * and it dies with the screen. The search id travels with it because it is the id the
   * line-up will be bound to, and reading it back off state that changes in between would be
   * two facts about one answer.
   */
  const [landing, setLanding] = useState<
    { readonly searchId: string; readonly seating: Seating } | undefined
  >(undefined);

  /**
   * Whether `SH.propose` is up, and **what the last send was refused with**.
   *
   * Route-local for the seating's reason: neither is a fact about the line-up, and the court
   * pops, so both are gone the moment the player is anywhere else. The refusal is held rather
   * than read off `send.error` because it is what decides *which source is being re-read* — a
   * screen that re-derived it every render would start the read again on each one.
   */
  const [proposing, setProposing] = useState(false);
  const [refusal, setRefusal] = useState<SendRefusal | undefined>(undefined);

  /**
   * **Whose record is being read** — `SH.player`, over the court rather than over a list.
   *
   * The seat itself and not an id, for the reason the pool and the deck both hold a row: the
   * sheet reads no global state, so a screen holding an id would be looking the same seat up
   * again on every render of a sheet that is already holding it. Route-local with the seating
   * and the refusal, and gone the moment the court pops.
   *
   * **It replaced the Fit sheet's own state rather than joining it** ([#384](https://github.com/Raketa02/Raketa/issues/384)):
   * a face opens the person, and the pairing's arithmetic is a row inside what that opens.
   */
  const [reading, setReading] = useState<ReadRecord | undefined>(undefined);

  /**
   * **Whose Fit is being explained** — `SH.whyfit`, now reached only from the record's own row.
   *
   * The row itself and not an id, for the same reason: the sheet takes `(candidate, envelope)`
   * and reads no global state.
   *
   * **One route reaches it.** The hold on the seat went with #285, and the face went with #384
   * — what is left is a row that names what it opens, which is the only place the arithmetic of
   * a *pairing* has ever belonged.
   */
  const [explaining, setExplaining] = useState<Candidate | undefined>(undefined);

  /**
   * Where accessibility focus goes when `SH.propose` closes — **the control that opened it**.
   *
   * Part 13's rule for every overlay in this app: without it a listener is returned to the top
   * of the screen and has to find their place again, which after the app's one irreversible act
   * is the worst place to lose somebody.
   */
  const sendControl = useRef<View>(null);

  /**
   * Where the prompt sheet hands focus back — **⚡, which is what raised it.**
   *
   * Null exactly when the fill filled the court, because that is when the two ways of filling
   * it are replaced by the send. `moveAccessibilityFocus` is silent on an empty ref, so a full
   * fill returns a listener to the platform's own landing rather than onto the send control,
   * which is the last place a question about a radius should leave anybody.
   */
  const fillControl = useRef<View>(null);

  const origin = record?.origin;
  const sport = origin?.sport;
  const seats = sport === undefined ? 0 : courtSeatCount(sport);
  const members = lineup?.seats ?? [];

  /**
   * **The half-built court this builder is completing**, or nothing on Play's own route.
   *
   * Read off the **record's origin** and not off a route param: the challenge is what the search
   * was run for, so it is already stamped on the answer this screen is drawing, and a second
   * spelling arriving down the route would be one more thing that can disagree with it. That is
   * `the-loop-components.md` §4.2's *no `from` parameter* discharged by the model rather than by
   * a rule — the route under `/chats/…` carries the challenge id because a path has to say what
   * it is looking at, and this screen never reads it.
   */
  const completing = origin?.completing;
  /** Who on this court has already said yes. Their seats are not controls (ADR-0150 §8). */
  const accepted = new Set(completing?.accepted ?? []);

  /**
   * The ask, or the absence of one — **the one place *is there a forecast to fetch* is
   * decided.**
   *
   * `undefined` on an empty court, because `ForecastRequest.players` is *"one, two or three"*
   * and a request with nobody in it is a question about nothing. Built as a value rather than
   * spelled once in a guard and once in an `enabled`, which is the shape both other Play
   * screens' asks already take.
   */
  const forecast = useForecast(
    origin === undefined || members.length === 0
      ? undefined
      : { sport: origin.sport, mode: origin.mode, searchId: originSearchId, players: members },
  );

  const arrangements = forecast.data ?? [];

  /**
   * The seating is reset by a **membership** change and by nothing else.
   *
   * Adjusted during render rather than in an effect, which is `CourtBuild`'s own answer to the
   * same question: an effect would draw one frame of the old seating over the new four. The
   * key is the origin and the *set* of members, for `searchKeys.forecast`'s reason — a
   * re-arrangement is not a change of who is playing, and resetting on one would undo the swap
   * that caused it.
   */
  const membership = `${originSearchId}|${[...members].sort().join(',')}`;
  const [heldMembership, setHeldMembership] = useState(membership);
  if (heldMembership !== membership) {
    setHeldMembership(membership);
    setSeating(undefined);
  }

  const seated = seating ?? seatingToDraw(arrangements, { seats, members });
  const chosen = arrangementFor(arrangements, seated);
  /**
   * The flattest of the three, read **once** and used twice: the sentence beside the figure
   * quotes its percentage, and *Even it out* selects it. Two readings of one response is two
   * chances for the number a player is shown and the arrangement they get to disagree.
   *
   * `undefined` on a court with one arrangement — a singles line-up, and a four that could not
   * be seated — where there is nothing to be evener than.
   */
  const evenest = arrangements.length < 2 ? undefined : evenestArrangement(arrangements);

  const filled = seatsFilled(seated);
  const open = seats - filled;
  const places = seatPlaces(seated.map(toBuildSeat));
  /** See the control's own note: absent on a court somebody has accepted, never disabled. */
  const mayStartOver = lineup !== undefined && completing === undefined;

  /**
   * A seated player the live gates no longer admit — a **set difference**, derived here and
   * stored nowhere. `undefined` rows mark nobody: with no record held, reading *no live rows*
   * as *everybody is gone* would mark a whole court on a cold cache.
   *
   * **The rows are whatever the record's latest answer holds**, which is the mint's today and
   * a read-back's once the pool re-reads one. Today the difference is therefore empty by
   * construction — a line-up is seated out of the rows it is bound to, so nobody in it can be
   * missing from them — and that is the same *marks nobody* the docblock's `undefined` gives.
   * It becomes a real mark at the moment `GET /searches/{id}` replaces the entry and drops the
   * rows the product has since agreed not to show
   * ([#272](https://github.com/Raketa02/Raketa/issues/272)), which is why the derivation reads
   * the entry rather than a read-back it would have to keep separately.
   */
  const withheld = new Set(
    withheldSeats(
      lineup,
      record?.candidates.map((row) => row.playerId),
    ),
  );
  const shortfall = record?.court === undefined ? undefined : shortfallBySeat(record.court);

  const rows = new Map((record?.candidates ?? []).map((row) => [row.playerId, row]));

  /**
   * The handles on each half, **read once and drawn twice** — as the label over a side's
   * strength, and as one control per person underneath it.
   *
   * Two readings of one seating would be two chances for the row saying *You + Marek is worth
   * 2,82* and the row offering *why is Marek here* to disagree about who is standing where.
   */
  const halfOf = (side: CourtHalf) => {
    const handles = handlesOn(side, seated, places, { rows, self });
    return {
      handles,
      /** Whole handles — the register a **sentence** is in, and the split row's spoken name. */
      name: sideName(
        handles.map((one) => one.name),
        SIDE_HEADINGS[side],
      ),
      /**
       * The same half as a **drawing**: each handle cut at its first word break, so two names
       * and a `+` fit on one line of a panel half the card wide.
       *
       * Two strings rather than one, because they are two registers and not two lengths.
       * `handleStem` is a prefix of what somebody typed and a sentence still carries all
       * sixty-four characters of it — which is the whole of why ADR-0107 permits this at all,
       * and it only holds while the two stay apart.
       */
      drawn: sideName(
        handles.map((one) => handleStem(one.name)),
        SIDE_HEADINGS[side],
      ),
    };
  };
  const yours = halfOf('yours');
  const theirs = halfOf('theirs');

  /**
   * `SH.whyfit`'s two inputs, or nothing — **one value, so the sheet and the hide behind it
   * cannot disagree.**
   *
   * The sheet needs a record as well as a row, and the tree behind a modal has to say it is
   * behind one (Part 13). Read as two conditions, an evicted record would hide the whole
   * screen behind an overlay that never rendered, and a listener would be left with nothing at
   * all — so *is there a sheet* is derived once and both sites read it.
   */
  const explained =
    explaining === undefined || record === undefined
      ? undefined
      : { candidate: explaining, envelope: record.envelope };

  /**
   * **The court as it is drawn**, which is the committed seating except while one is landing.
   *
   * A seat holds its answer once it has landed, and is empty until then — so the four arrive
   * one after another rather than all at once. Two seats are exempt and both for the same
   * reason, that they were already on screen: **yours**, and anybody you had seated by hand
   * before pressing ⚡. A player who visibly disappeared and came back would be the fill
   * un-seating somebody it is filling around.
   */
  const drawn: Seating =
    landing === undefined
      ? seated
      : landing.seating.map((seat, at) =>
          seat.kind === 'you' ||
          at < revealed ||
          (seat.kind === 'player' && members.includes(seat.playerId))
            ? seat
            : EMPTY_SEAT,
        );

  const occupants: readonly CourtSeatOccupant[] = drawn.map((seat, at) =>
    toOccupant(seat, { self, rows, accepted, unfilled: shortfall?.get(at) ?? null }),
  );

  /**
   * Everybody about to be asked: the court minus you, in seat order. Nobody invites themselves.
   *
   * **And minus anybody who has already said yes**, on a court that is being completed: they are
   * not being asked, they answered weeks ago, and a pre-send sheet listing them under *Who you're
   * asking* would be naming an act this route refuses to take — an accepted player may not be
   * removed, and they are not being invited either.
   */
  const invitees = seatedIds(seated).filter((playerId) => !accepted.has(playerId));

  /**
   * The second of the two re-reads, asked **only** once the pair rule has fired.
   *
   * A court is built, looked at and sent from without anybody needing to know what else the
   * organiser has open, so this costs nothing until the one press that needs it.
   */
  const pair = useOpenPair(invitees, refusal?.kind === 'READ_YOUR_CHALLENGES');
  // The handle is the **record's**, because that is where a name lives: `challenges` answers a
  // player id and has never seen a nickname.
  const pairName = pair === undefined ? undefined : rows.get(pair)?.card.nickname;

  const sportName = sport === undefined ? undefined : sportLabel(sport);
  const profile = profileSurface.data;
  const optimised = optimisedForLine(record?.envelope.optimisedFor ?? null);

  /**
   * ⚡'s own week. The fill is a **new search for the same origin**, so it runs on the week the
   * origin was asked under — sent unless it can be shown to be the profile's own grid, which is
   * the one case an omitted override already means. Unprovable is *sent*: a fill that quietly
   * ran on a different week from the search above it would be the two disagreeing silently.
   *
   * **An origin with no week of its own sends none**, which is the same sentence read from the
   * other end: a challenge fill composed no week, so the one it ran on *is* the profile's grid
   * and an omitted override is what says so (ADR-0150 §7).
   */
  const sentWeek =
    origin?.week === undefined ? undefined : sentWeekForOrigin(origin.week, profile?.week);

  /**
   * The fill's wait — the second of Play's two, and the one with a **stagger over its floor**.
   *
   * The floor is `650 plus 550 a seat`, and it collapses to the bare floor for a listener or a
   * player who asked for reduced motion: *"a listener gets none of the craft and all of the
   * latency"*, in front of an answer already in memory (§20.11, `searchingWait`). Nothing here
   * delays a request either way.
   *
   * A **paused** write is not in flight at all and a refusal has nothing to hold for, which are
   * the same two subtractions Find a game makes for the same two reasons.
   */
  const held = useHeldWait(
    fill.isPending && !fill.isPaused,
    searchingFloorMs({ kind: 'fill', seats, collapsed }),
  );
  const filling = held && !fill.isPaused && fill.error === null;
  const playersInRange = fill.isSuccess ? fill.data.playersInRange : undefined;

  /**
   * How much of the answer is on screen — the stagger `motion.hold.fill` has always paid for,
   * as a number the court can draw.
   *
   * It runs off `landing` rather than off `filling`, so the seats start arriving when there is
   * something to arrive: for as long as the request is in flight the court is empty and the
   * block underneath says what is being looked for.
   */
  const revealed = useSeatsRevealed(landing !== undefined, seats, collapsed);

  /**
   * **The line-up is committed when the last seat has landed**, and not when the response did.
   *
   * Both halves of one act, exactly as before — the answer's own search becomes the origin and
   * the people it seated become the line-up — moved to the end of the beat that draws them.
   * Committing on the response instead would put a full court and its forecast card on screen
   * underneath a wait that is still drawing the seats, which is the state the reveal exists to
   * replace.
   *
   * The origin id is set on the response and not here: it is what makes the fill's own
   * candidates readable, and the seats being drawn are read out of them.
   */
  useEffect(() => {
    if (landing === undefined || filling) return;
    seatAll(landing.searchId, seatedIds(landing.seating));
    setLanding(undefined);
  }, [landing, filling, seatAll]);

  /**
   * **The question ⚡ raised, and the beat it is asked in.**
   *
   * The **first** prompt and never a stack of them, for Find a game's reason: the response
   * orders them in the vocabulary's own order, so a client drawing the first one it understands
   * draws the same one twice for the same search. What reaches here is already filtered to the
   * ones a screen with no week grid can honour (`use-cases/fillSeats`).
   *
   * It is asked **after the latch lifts**, and there it stops. Find a game puts the sheet
   * between the wait and the push because the court is somewhere else; ⚡ fills the court the
   * player is already looking at, so what the sheet stands in front of is an answer that has
   * already landed and closing it is the whole of where anybody goes
   * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
   *
   * **Remembered for the visit, not for the search ⚡ minted.** It was the minted id, on the
   * argument that ⚡ is a press and a second press is a second question worth asking — true of
   * the press and false of the question. `KEEP_THESE_TIMES` is about the **working week**, and
   * arriving here at all means a search has already run on it and already asked: ⚡ minting a
   * second search over an unchanged week put the identical question up two taps after *not
   * now* ([#287](https://github.com/Raketa02/Raketa/issues/287)). The list is `playSession`'s,
   * because the week it is about is.
   */
  const asked = usePlaySession((state) => state.askedQuestions);
  const recordAsked = usePlaySession((state) => state.recordAsked);
  const filledSearch = fill.isSuccess ? fill.data.record.searchId : undefined;
  const raised = fill.isSuccess ? fill.data.prompts[0] : undefined;
  /**
   * The question and everything needed to draw it, or nothing — **one value, because the
   * overlay behind it and the sheet itself must not be able to disagree.** Two expressions for
   * one sheet is a screen that can hide itself behind a modal it did not mount.
   */
  const question =
    raised === undefined || filledSearch === undefined || sport === undefined
      ? undefined
      : { raised, sport, search: filledSearch };
  const asking =
    question !== undefined &&
    !filling &&
    !alreadyAsked(asked, question.sport, question.raised.prompt);

  /**
   * **The third live region**, and the one nobody else could have claimed (§20.9).
   *
   * Moving a player across the net changes the forecast **while focus stays on the seat that
   * moved**, so the figure is the only one in the tab that changes where the listener is not —
   * and it announces itself. It carries §17's caveat rather than a bare number, which is
   * ADR-0108's rule that the figure and its caveat are one thing, and §B9's word rather than a
   * bare percentage, which is the Part 13 rule the tint is already held to.
   *
   * `null` while there is no forecast: a region with nothing in it is silence rather than an
   * empty sentence.
   */
  useLiveRegion(
    chosen === undefined ? null : provisionalForecastAnnouncement(chosen.forecast),
    PLAY_LIVE_REGIONS.provisionalForecast,
  );

  /** Fill this seat, or replace who is in it — one act, against one seat, on the pool. */
  const openPool = (seat: number) =>
    router.push({ pathname: POOL_ROUTE, params: { search: originSearchId, seat: String(seat) } });

  function fillTheSeats() {
    if (origin === undefined) return;
    fill.mutate(
      // **A fill names the challenge it completes and says nothing else about the court**
      // (ADR-0150 §2): the sport, the kind of evening and the locked seats are all read off it,
      // and the people who accepted are its locked seats. So a second ⚡ on this court re-seats
      // around the same people rather than around whoever the first one found, which is the
      // request's own shape rather than a rule this screen applies.
      completing !== undefined
        ? { kind: 'challenge', completing, sport: origin.sport }
        : {
            kind: 'search',
            origin,
            lockedSeats: members,
            sentWeek,
            // The profile's own week may not have landed, and that is stated rather than
            // replaced with an empty one: the prompt that would have quoted it is dropped
            // instead of drawn against a grid nobody holds (`use-cases/fillSeats`).
            quotes: { sportName: sportLabel(origin.sport), profileWeek: profile?.week },
          },
      {
        onSuccess: ({ record: answer }) => {
          // The origin moves now, because the answer's own candidates are what the seats
          // about to land are drawn from. The **line-up** is committed at the end of the beat
          // that draws them — see `landing` and the effect that commits it.
          setAnsweredSearchId(answer.searchId);
          setSeating(undefined);
          setLanding({ searchId: answer.searchId, seating: courtSeating(answer.court) });
        },
      },
    );
  }

  /**
   * **The send** — and the whole of what a refusal costs, in one place.
   *
   * The court goes out **exactly as it is drawn**: seat order, your own seat in it, holes kept,
   * and the sides derived from position by the mapper. *"The arrangement you built is what is
   * recorded, and it is what they answer — never a better one worked out afterwards."*
   *
   * Nothing is re-checked here. Five facts are re-verified server-side in the send's own
   * transaction, because the line-up may be an hour old and nothing in Play background-refetches
   * — a client-side pre-check would be a fifth reading of the one class of rule that must not be
   * stale, taken from the one source that is.
   *
   * **A duplicate press is explicitly-valid repetition.** No `Idempotency-Key`: one open
   * challenge per pair across sports is a rule that does not expire and a key does, so the
   * second send is made, read and refused by the same check that would refuse a stranger's.
   */
  function sendTheChallenge() {
    if (self === undefined) return;

    // The previous refusal, and the read it started, both belong to the press that caused them.
    setRefusal(undefined);
    reread.reset();

    const court = courtWithYou(seated, self) satisfies ProposedCourt;
    const onError = (error: AppError) => {
      const next = sendRefusal(error);
      setRefusal(next);
      startTheReRead(next);
    };

    // **The court that already stands is grown, and the one that does not is minted.** Two
    // routes, one press, and the branch is the origin's — see `completing`.
    if (completing !== undefined) {
      invite.mutate(
        { challengeId: completing.challengeId, searchId: originSearchId, court },
        {
          // **The send pops back to the challenge screen**, which is the surface that draws the
          // result: the new seats, their fresh deadlines, and a standing that may now be awaiting
          // answers again. Nothing here resets the shell stack — `landOnNow`'s *"there is nothing
          // left to be behind: the court is gone"* is false when the thing behind is the
          // challenge you were completing (ADR-0150 §7). There is no toast for the same reason:
          // the confirmation is a screen that states what happened rather than a sentence
          // standing in for one, which is the whole of why the send's own toast interrupts.
          onSuccess: () => router.back(),
          onError,
        },
      );
      return;
    }

    send.mutate(
      { searchId: originSearchId, court },
      {
        onSuccess: () => {
          // The stack goes first and the sentence second, in that order and not the other:
          // `landOnNow` ends the Play session and mounts the destination, and the toast is
          // spoken from the host's effect on the commit after it — so the platform's own
          // screen-change notification does not clobber the one announcement that interrupts.
          landOnNow();
          showToast({ message: CHALLENGE_SENT, tone: 'ok', politeness: 'interrupting' });
        },
        onError,
      },
    );
  }

  /**
   * The half of a refusal that is a **request**, and the reason it is a `switch`.
   *
   * Every arm is named, so a third source added to `SendRefusal` fails `pnpm typecheck` here
   * rather than quietly starting no read — which is the failure mode an `if` on one code has,
   * and it is invisible: the sentence still renders and the seats simply never get marked.
   *
   * `READ_YOUR_CHALLENGES` starts nothing imperatively because its read is **declarative** —
   * `useOpenPair`'s `enabled` is the held refusal, so setting it is the request.
   */
  function startTheReRead(next: SendRefusal): void {
    switch (next.kind) {
      // The origin search, **never a fresh one**: a re-run mints an id the whole line-up must
      // adopt, and its untouched seats are only *probably* in the new answer.
      case 'READ_THE_ORIGIN_BACK':
        if (record !== undefined) reread.mutate(record);
        return;
      case 'READ_YOUR_CHALLENGES':
      case 'SAY_SO':
        return;
    }
  }

  /**
   * What the court says about a refused send — **at court level**, in the shape the shortfall
   * statements already use on this screen.
   *
   * The gate refusal says one sentence while the re-read is in flight and keeps it once the
   * read-back has marked somebody; when the read-back marks **nobody** it becomes the dead end,
   * which is the case the send and the index genuinely disagree about and the one that would
   * otherwise leave a player refused in front of four seats that all look fine.
   *
   * **A re-read that failed keeps the first sentence rather than reaching the dead end**, and
   * the gate is `isSuccess` for that reason: the dead end says the refusal and the refresh
   * *disagree*, which is a claim only a refresh that happened can make. What the player is left
   * with is still true — the line-up went out of date — and the way on is the control they
   * pressed, which is the tab's rule about where a retry belongs.
   */
  function refusalLine(): string | undefined {
    if (refusal === undefined) return undefined;

    switch (refusal.kind) {
      case 'READ_THE_ORIGIN_BACK':
        return reread.isSuccess && withheld.size === 0
          ? NOTHING_MARKED_AFTER_THE_REFRESH
          : LINE_UP_CHANGED;
      // The name is the **record's**, not the refusal's. A pair between two invitees is on a
      // list this player cannot read, and so is a seated player the read-back has since
      // withheld — both answer with the sentence that names nobody rather than with a `?`.
      case 'READ_YOUR_CHALLENGES':
        return pairName === undefined
          ? A_PAIR_HERE_IS_ALREADY_PLAYING
          : openChallengeLine(playerName(namedPlayer(pairName)));
      case 'SAY_SO':
        return challengeErrorMessage(refusal.error);
    }
  }

  /** Read once per render: the sentence is the same wherever it is drawn, and it is drawn once. */
  const refused = refusalLine();

  return (
    <>
      {/* Both overlays are **siblings** of the screen they cover, never children:
          `behindOverlay` hides everything inside the element carrying it, and an overlay
          rendered in there would hide itself along with the screen. `SH.propose` takes the
          same hide as the latch — a modal sheet's Part 13 obligation is that the tree behind
          it says so, and here that tree holds a second control spelled with the sheet's own
          words. */}
      <View
        style={s.root}
        {...behindOverlay(proposing || explained !== undefined || reading !== undefined || asking)}
      >
        <ShellScreen
          /* **The game this screen is here to build**, in the same two words as the control
             that opened it — the control names the screen it opens (`builderPresentation`).

             **And nothing above it.** `Padel · doubles · for fun` stood there as 10.3's
             eyebrow and read as the title said twice: *doubles* is in both lines, the Sport is
             on the court below in the picture and in its spoken summary, and what was left
             over was one word of mode. Where the record cannot be read there is no shape to
             name, so the fallback is a name rather than a court shape the screen is guessing
             at. */
          title={
            sportName === undefined || origin === undefined
              ? UNREADABLE_SEARCH_TITLE
              : builderTitle(seats)
          }
          // **The gesture, drawn.** This screen is genuinely pushed — Find a game stays
          // underneath it — so the platform's own back already lands here, and 10.3's chevron
          // is opt-in for exactly the screens that can say where it goes. It adds no
          // behaviour: it is the same `back` a swipe performs, on a control a thumb can find
          // without knowing the gesture exists. The session is untouched either way — only
          // `enterPlay` ends one, and going back is not entering.
          onBack={router.back}
          action={
            origin === undefined || filling ? undefined : open === 0 ? (
              /* **The court, once full.** The two ways to fill it are gone, because there is
                 nothing left to fill, and the slot becomes the one act that reaches another
                 person. */
              <View style={s.action}>
                {refused === undefined ? null : (
                  <Note variant="coral" accessibilityRole="alert">
                    {refused}
                  </Note>
                )}
                {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}

                {/* Pending on the pinned CTA, and disabled while the send is in flight or
                    there is no connection to make it over. `self` is the account's own id and
                    is absent only while the launch read is in flight: a court this client
                    cannot name you on is not a court it may send. */}
                {/* A `View` around the button, because focus has to land on a **host element**
                    this component holds a ref to and `Button` is a component. The same shape
                    `BottomSheet` uses for its own heading. */}
                <View ref={sendControl}>
                  <Button
                    label={SEND_CHALLENGE_LABEL}
                    size="lg"
                    busy={send.isPending || invite.isPending}
                    busyLabel={SENDING_LABEL}
                    disabled={!online || self === undefined}
                    onPress={() => setProposing(true)}
                  />
                </View>
              </View>
            ) : (
              <View style={s.action}>
                {fill.error !== null ? (
                  <Note variant="coral" accessibilityRole="alert">
                    {playErrorMessage(fill.error)}
                  </Note>
                ) : null}
                {fill.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

                {/* The failed act's own control is the retry — ⚡ is what failed, and pressing
                    it again is that act rather than the screen it failed on (`retryTarget`).

                    A `View` around it for `sendControl`'s reason: focus has to land on a
                    **host element** this component holds a ref to, and `Button` is a
                    component. It is where the prompt sheet hands focus back. */}
                <View ref={fillControl}>
                  <Button
                    label={USE_MATCHMAKING_LABEL}
                    size="lg"
                    busy={fill.isPending}
                    busyLabel={FILLING_LABEL}
                    onPress={fillTheSeats}
                  />
                </View>
                <Button
                  label={PICK_PLAYERS_LABEL}
                  variant="secondary"
                  onPress={() => openPool(firstEmptySeat(seated))}
                />
              </View>
            )
          }
        >
          {record === undefined || sport === undefined || sportName === undefined ? (
            <Note title={NO_RECORD_TITLE}>
              <Text style={s.body}>{NO_RECORD_BODY}</Text>
            </Note>
          ) : (
            <>
              {/* The engine filled the seats **around** somebody, so it stopped optimising for
                  you — said before it is discovered, and read off the envelope rather than
                  derived from having sent a `locked_seats` list. */}
              {optimised === undefined || filling ? null : (
                <Note variant="info">
                  <Text style={s.body}>{optimised}</Text>
                </Note>
              )}

              {/* **What a seat does, above the seat that does it.** It stood in a card as a
                  `switch`'s description while a swap was a mode; the mode is gone and a tap
                  always trades, so what is left is the capability rather than a control. Drawn
                  on the toggle's own gate — one other person on the court, and not mid-fill —
                  because there is nothing to trade with until there is somebody to trade. */}
              {filled > 1 && !filling ? <Text style={s.swapHint}>{SWAP_HINT}</Text> : null}

              {/* `pointerEvents` and not a prop on the court: while the engine is seating it
                  there is nothing on it to operate, and a seat that opened the pool mid-fill
                  would leave the answer landing on a screen the player is no longer on. It is
                  a fact about this beat rather than a mode the court has. */}
              <View
                style={s.court}
                pointerEvents={filling ? 'none' : 'auto'}
                accessibilityElementsHidden={filling}
                importantForAccessibility={filling ? 'no-hide-descendants' : 'auto'}
              >
                <CourtBuild
                  sport={sport}
                  width={theme.size.court.build}
                  summary={courtSummaryLabel({ sportName, filled: seatsFilled(drawn), seats })}
                  seats={occupants}
                  onOpenPool={openPool}
                  onSwap={(from, to) => setSeating(swapSeats(seated, from, to))}
                  onClear={(at) => {
                    const seat = seated[at];
                    if (seat?.kind === 'player') unseat(seat.playerId);
                  }}
                />
              </View>

              {/* **The wait, under the court it is seating** — never over it. See
                  `SeatingWait`: a fill's answer has its own subject already on screen, and a
                  latch would take away the one thing the wait is about. */}
              {filling ? (
                <SeatingWait status={engineFillStatus({ playersInRange, seats })} />
              ) : null}

              {/* The court's own statement of its shortfall. The remedy is the pool, one tap
                  away on the seat itself and on the control beneath it — and the block is
                  hidden from a listener, because every seat already announces its own (§20.1's
                  merge rule; see `courtStatements`). */}
              {(filling ? [] : courtStatements({ seated, shortfall, withheld })).map((line) => (
                <Text
                  key={line}
                  style={s.body}
                  accessibilityElementsHidden
                  importantForAccessibility="no-hide-descendants"
                >
                  {line}
                </Text>
              ))}

              {/* A dock, never a refusal: the availability term zeroes, nobody is removed from
                  the court for it, and the honest line is that you would all have to bend. */}
              {record.court?.dock == null || filling ? null : (
                <Note variant="amber">
                  <Text style={s.body}>{unfilledSeatLine(record.court.dock)}</Text>
                </Note>
              )}

              {/* Paused, not loading. `networkMode: 'online'` holds the forecast rather than
                  failing it, and `isFetching` is **false** while it waits — so a screen that
                  drew only the spinner would answer a swap made offline with nothing at all:
                  no number, no sentence and no reason why (Part 11's amendment names this
                  request by name). */}
              {forecast.isPaused && !filling ? (
                <Note variant="amber">{offlineMessage('resumes')}</Note>
              ) : null}

              {forecast.isFetching && !filling ? (
                <ActivityIndicator
                  accessibilityLabel={FORECASTING_LABEL}
                  color={theme.color.muted}
                />
              ) : null}

              {forecast.error === null || filling ? null : (
                <View style={s.failure}>
                  <Note variant="coral" accessibilityRole="alert">
                    {playErrorMessage(forecast.error)}
                  </Note>
                  {/* The one wait in this tab that gains a control of its own: a player who has
                      stopped changing seats would otherwise sit with no number and no way to
                      ask again (`domain/retryTarget`). */}
                  <Button
                    label={RETRY_FORECAST_LABEL}
                    variant="secondary"
                    onPress={() => void forecast.refetch()}
                  />
                </View>
              )}

              {chosen === undefined || filling ? null : (
                <Card>
                  <Text style={s.eyebrow}>{forecastHeading(seats)}</Text>

                  {/* **What the percentage is a percentage of** — the two side strengths and
                      the gap between them, each labelled by who is standing on that half.
                      All three are read off `split` and none is computed: a side's strength is
                      not the mean of the two people on it, so the one honest way to draw this
                      row was for the engine to serve it (#289, §11.3).

                      **One accessibility element, not six.** The five things in it are one
                      claim, and a listener navigating a row drawn as a table stops five times
                      to assemble it (§20.1, `splitRowLabel`). */}
                  <View
                    style={s.split}
                    accessible
                    accessibilityLabel={splitRowLabel(
                      { yours: yours.name, theirs: theirs.name },
                      chosen.split,
                    )}
                  >
                    {/* **The three figures and nothing else.** The two panels beneath say who
                        each half is, in the register a panel can hold, and the row that used
                        to print the same two joined phrases under its own numbers was the
                        card naming these four people three times over. The spoken name is
                        unchanged and still carries both halves whole — it is one element, and
                        a strength with nobody attached to it is not a claim. */}
                    <View style={s.splitSide}>
                      <Text style={s.sideLevel}>{formatLevel(chosen.split.yourSide)}</Text>
                    </View>

                    {/* **Signed, as it was served.** The sign is which way the game leans,
                        and taking it off would be this screen doing arithmetic over a number
                        it was handed — the same rule that stopped it deriving the two
                        strengths either side of it. */}
                    <View>
                      <Text style={s.gapWord}>{GAP_WORD}</Text>
                      <Text style={s.gapLevel}>{formatLevel(chosen.split.gap)}</Text>
                    </View>

                    <View style={[s.splitSide, s.splitTheirs]}>
                      <Text style={s.sideLevel}>{formatLevel(chosen.split.theirSide)}</Text>
                    </View>
                  </View>

                  {/* 7.11's two-segment form, which has always drawn exactly this and was
                      unused here only because nothing served an advantage. The **signed** gap
                      is that advantage; the bar maps it to a fold and this screen does no
                      arithmetic over it, and the tone is the served figure's.

                      **Hidden**, because the row two lines above prints all three of its
                      numbers: the bar's own name would be the fourth reading of one fact
                      (§20.1's merge rule, 6.8's double announcement). Drawn and hidden, exactly
                      as the court's shortfall statements are. */}
                  <View
                    style={s.bar}
                    accessibilityElementsHidden
                    importantForAccessibility="no-hide-descendants"
                  >
                    <BalanceBar
                      advantage={chosen.split.gap}
                      tone={balanceTone(chosen.forecast.pct)}
                      size="md"
                      labels={[yours.drawn, theirs.drawn]}
                      accessibilityLabel={balanceLabel(chosen.forecast.pct)}
                    />
                  </View>

                  <Hairline>
                    {/* **The figure, and the words that read out of it.** Part 13's *never
                      colour alone* is what puts §B9's word beside the tinted number, and it is
                      beside rather than beneath it because the two are one claim read left to
                      right: *90% — very even, and this is the evenest these four can be
                      arranged.* Stacked, the figure was a number with three captions under it
                      and the last of them was the only one that said anything actionable. */}
                    <View style={s.reading}>
                      <Text
                        style={[s.figure, { color: BALANCE_INK[balanceTone(chosen.forecast.pct)] }]}
                      >
                        {formatPercent(chosen.forecast.pct)}
                      </Text>

                      <View style={s.readingWords}>
                        <Text style={s.word}>{balanceWord(chosen.forecast.pct)}</Text>

                        {/* **What this arrangement costs against the evenest one**, or that it
                          is the evenest. Both are readings of a response already held — every
                          arrangement crosses — so the sentence beside the figure is the same
                          selection *Even it out* is, said before it is pressed rather than
                          discovered by pressing it. Drawn only where there is a second
                          arrangement to compare against: a singles court has one. */}
                        {evenest === undefined ? null : (
                          <Text style={s.body}>
                            {chosen.isEvenest
                              ? ALREADY_EVENEST
                              : arrangedYourWayLine(formatPercent(evenest.forecast.pct))}
                          </Text>
                        )}

                        {chosen.forecast.provisional ? (
                          <Text style={s.provisional}>{PROVISIONAL_WORD}</Text>
                        ) : null}

                        {/* ADR-0108's rule that the figure and its caveat are one thing. A caveat
                          this build cannot read draws nothing, and `provisional` above still
                          says the figure has one. */}
                        {chosen.forecast.assumption === null ? null : (
                          <Text style={s.body}>
                            {forecastAssumption(chosen.forecast.assumption)}
                          </Text>
                        )}
                      </View>
                    </View>
                  </Hairline>

                  {/* **Where the handles are printed whole**, and the reason a 46pt seat is
                      allowed to cut one to four characters: `the-play-components.md` §5 makes
                      the truncation legal because *"both screens the court appears on already
                      print the handles in full and unavoidably"*, and this is the builder's
                      half of that. One name per line, each in its own box — a list rather than
                      a joined phrase precisely so the layout is here and 64 characters cannot
                      be assumed short.

                      **And it is the route into `SH.whyfit` for somebody already seated**
                      (§20.4.1). The headings are drawn and hidden, because each name that is a
                      button now opens with the side this row's key says — 7.12's own rule for
                      the court's caption and side labels, one card down. */}
                  <Hairline>
                    <View style={s.sides}>
                      <Side
                        heading={SIDE_HEADINGS.yours}
                        name={yours.drawn}
                        strength={chosen.split.yourSide}
                        seated={yours.handles}
                        onOpenRecord={setReading}
                      />
                      <Text style={s.vs} accessibilityElementsHidden importantForAccessibility="no">
                        {VS_WORD}
                      </Text>
                      <Side
                        heading={SIDE_HEADINGS.theirs}
                        name={theirs.drawn}
                        strength={chosen.split.theirSide}
                        tone={balanceTone(chosen.forecast.pct)}
                        seated={theirs.handles}
                        onOpenRecord={setReading}
                      />
                    </View>
                  </Hairline>

                  {/* **The two acts on this four, side by side** — re-arrange them, or empty
                      the court. *Even it out* is drawn shut rather than replaced by a sentence
                      when it would select what is already on screen: the sentence is now beside
                      the figure, where it says what the control would buy, and a row that lost
                      a button on one state would move the other one under the player's thumb.
                      *Start over* was beneath the card and read as a way off the screen. */}
                  {arrangements.length < 2 && !mayStartOver ? null : (
                    <Hairline>
                      <View style={s.acts}>
                        {arrangements.length < 2 ? null : (
                          <Button
                            label={EVEN_IT_OUT_LABEL}
                            variant="secondary"
                            disabled={chosen.isEvenest}
                            onPress={() => {
                              const flattest = evenestArrangement(arrangements);
                              if (flattest !== undefined) setSeating(seatingOf(flattest));
                            }}
                          />
                        )}
                        {/* ***Start over* is absent on a court somebody has accepted** — not
                            disabled, and not redefined to mean *empty it to these two*, which
                            would be a second meaning for one label (ADR-0150 §8). The two acts
                            it sits beside both operate on a court nobody has committed to, and
                            this one is not: discarding the line-up here would leave a court the
                            player cannot rebuild and a challenge they cannot end. */}
                        {mayStartOver ? (
                          <Button
                            label={START_OVER_LABEL}
                            variant="secondary"
                            onPress={() => {
                              discardLineup();
                              setSeating(undefined);
                            }}
                          />
                        ) : null}
                      </View>
                    </Hairline>
                  )}
                </Card>
              )}
            </>
          )}
        </ShellScreen>
      </View>

      {/* `SH.saveav` — the questions ⚡'s own search raised, asked once the latch is off them.
          A **sibling** for the latch's reason: a `Modal` presents in its own window, and the
          screen root behind it says so itself. It carries the sport because the decline route
          takes one on every prompt, and the origin is the only thing that knows which.

          It stays mounted after it is answered rather than only while it is up, so `visible`
          going false has somewhere to hand focus back — which is ⚡, the control that raised
          it. **A fill that filled the court has unmounted ⚡** and replaced it with the send, so
          the ref is empty exactly then; that is the honest nothing rather than a listener
          landed on the app's one irreversible act (`PromptSheet`, `moveAccessibilityFocus`).

          `key` is the minted search id, so one fill is one question and a second ⚡ asks again. */}
      {question === undefined ? null : (
        <PromptSheet
          key={question.search}
          visible={asking}
          raised={question.raised}
          sport={question.sport}
          returnFocusTo={fillControl}
          onAnswered={() => recordAsked(question.sport, question.raised.prompt)}
        />
      )}

      {/* `SH.player`, over the court — **who this person is**, which is what a face is a picture
          of. It reads no global state: the subject, the arrival sport, the distance, the
          reader's own area and the pairing all arrive as props, which is what will let the chat
          header and the game screen open the same sheet with none of the last three.

          The **Fit row is present exactly where a pairing is** — the seat carries a candidate
          only for somebody the origin search returned, so your own face and a withheld seat
          offer none. Taking it hands the court over to `SH.whyfit`: one sheet at a time, rather
          than a modal presented inside a modal's own window.

          **No `returnFocusTo`**, on the pool's own precedent: up to four faces open the same
          sheet, so there is no one control to return to, and a ref per face would be four refs
          to keep in step with a list that changes on every swap. */}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading.subject}
          {...(sport === undefined ? {} : { sport })}
          {...(reading.candidate?.distanceKm === undefined
            ? {}
            : { distanceKm: reading.candidate.distanceKm })}
          {...(record?.envelope.myAreaCode === undefined
            ? {}
            : { viewerAreaCode: record.envelope.myAreaCode })}
          {...(reading.candidate === undefined
            ? {}
            : { tagOverlap: socialTagOverlap(reading.candidate) })}
          {...pairingOf(reading, (pairing) => {
            setReading(undefined);
            setExplaining(pairing);
          })}
        />
      )}

      {/* `SH.whyfit`, over the court — the only place a **seated** player's Fit is explained,
          because the pool removes everybody already on the court from the one surface that
          explains a person. It reads `(candidate, envelope)` off the origin search record and
          nothing else, which is what lets one sheet serve all three of its entry points.

          **One route reaches it now**, and it is the record's own row: the face opens the
          person, and a pairing's arithmetic is a row inside what that opens. */}
      {explained === undefined ? null : (
        <WhyFitSheet
          visible
          onClose={() => setExplaining(undefined)}
          candidate={explained.candidate}
          envelope={explained.envelope}
          name={playerName({ kind: 'player', nickname: explained.candidate.card.nickname })}
        />
      )}

      {/* `SH.propose` — the last thing between a built court and four people being asked.
          Confirming dismisses it and runs the send, whose pending state and whose refusal both
          belong to the pinned CTA rather than to a modal over the seats that have to change. */}
      {sportName === undefined ? null : (
        <ProposeSheet
          visible={proposing}
          onClose={() => setProposing(false)}
          onSend={() => {
            setProposing(false);
            sendTheChallenge();
          }}
          returnFocusTo={sendControl}
          invitees={invitees.map((playerId) => namedPlayer(rows.get(playerId)?.card.nickname))}
          // *"Nothing opens until they accept"* is false for doubles: the first acceptance
          // opens the chat, and the number the sentence quotes is the answers still owed —
          // which is the invitees, because the organiser's own seat is accepted from birth.
          //
          // **And no closer at all on a court that is being completed**, where both sentences
          // are false: somebody has already accepted, so the chat is open and the screen behind
          // this one says so in its own standing line.
          {...(completing !== undefined
            ? {}
            : {
                lineUp:
                  seats > 2
                    ? ({ kind: 'doubles', sportName, stillNeeded: invitees.length } as const)
                    : ({ kind: 'singles' } as const),
              })}
        />
      )}
    </>
  );
}

/**
 * **The Fit row's props, or none at all** — the pairing behind a tapped face, where there is one.
 *
 * A function rather than an expression at the call site because the `undefined` has to be
 * narrowed *before* the callback closes over it: written inline, the closure re-reads the state
 * it was built from and has to re-check a branch the spread has already taken. The figure is not
 * rounded here — `fitRowTitle` rounds where it prints, which is the rule the day a second entry
 * point builds this prop.
 */
function pairingOf(
  read: ReadRecord,
  onExplain: (pairing: Candidate) => void,
): { readonly pairing?: { readonly fit: number; readonly onExplain: () => void } } {
  const pairing = read.candidate;
  return pairing === undefined
    ? {}
    : { pairing: { fit: pairing.fit, onExplain: () => onExplain(pairing) } };
}

/**
 * **A face that has been tapped** — whose record to open, and the pairing behind them if there
 * is one.
 *
 * Narrower than the `SeatedHandle` it is read off, and narrower in the one way that matters: a
 * face with no `subject` is not a control, so a state carrying an optional one would be a sheet
 * that could be opened about nobody. What is dropped with it — the place, the name, the face —
 * is what the *row* draws, and the sheet draws none of it.
 */
interface ReadRecord {
  readonly subject: RecordSubject;
  /** The row the origin search still holds for them. Absent is *no Fit row on the sheet*. */
  readonly candidate?: Candidate;
}

/** A seat nobody has landed in yet — the one value the drawn court substitutes while filling. */
const EMPTY_SEAT: SeatOccupancy = { kind: 'empty' };

/** A handle, or the unknown player's question mark for a seat the record can no longer describe. */
function namedPlayer(nickname: string | undefined): NamedPlayer {
  return nickname === undefined ? { kind: 'unknown' } : { kind: 'player', nickname };
}

/**
 * One seat, as the court draws it.
 *
 * **A seated player whose row the record no longer holds keeps their seat and loses their
 * facts** — the withheld mark, derived rather than stored. Nothing is emptied: emptying is the
 * silent destruction the origin guard exists to prevent, and the marked player stays in the
 * forecast because dropping them would force a second cause for *provisional*.
 */
function toOccupant(
  seat: Seating[number],
  court: {
    /** Your own player id — the account's, read at the screen. `undefined` for the one frame
     *  the launch read is still in flight (`seatFace.tsx`). */
    readonly self: string | undefined;
    readonly rows: ReadonlyMap<string, Candidate>;
    readonly unfilled: UnfilledReason | null;
    /** Who has already said yes to the challenge this builder is completing. Empty in Play. */
    readonly accepted: ReadonlySet<string>;
  },
): CourtSeatOccupant {
  if (seat.kind === 'you') {
    return { kind: 'you', ...(court.self === undefined ? {} : { playerId: court.self }) };
  }
  if (seat.kind === 'empty') return { kind: 'empty', unfilled: court.unfilled };

  const row = court.rows.get(seat.playerId);
  return {
    kind: 'player',
    playerId: seat.playerId,
    // **An accepted seat is not a control**: no clear badge, no press, no pool — and swapping is
    // the only thing that works on it, which *draws* `an acceptance is to the game, not to the
    // side` rather than writing it (ADR-0150 §8). The flag has been on `BuildSeat` since it was
    // written and this is its first producer; `seatLock` and the truth table over it needed no
    // change at all. A hand-seated player in Play has accepted nothing, so the set is empty
    // there and every seat answers as it always did.
    accepted: court.accepted.has(seat.playerId),
    ...(row === undefined
      ? {}
      : {
          nickname: row.card.nickname,
          level: row.card.level,
          ...(row.card.photoUrl === undefined ? {} : { photoUrl: row.card.photoUrl }),
        }),
  };
}

/**
 * One half of the court as a **panel** — who is standing on it, and what it is worth.
 *
 * ## The face is what made the hold deletable, and what it opens has since changed
 *
 * This was a column of words, and a seated player's Fit had a second way in: a long press on
 * the seat ([#285](https://github.com/Raketa02/Raketa/issues/285)). A gesture nothing
 * advertises, nothing announces and the accessibility API cannot perform was carrying nobody
 * it was not — so what it needed was not a second route but a **better first one**. A picture
 * of the person is a target you can see, at the size the design system already asks of a
 * control, and `CourtSeat` and `CourtBuild` drop the gesture on the strength of it.
 *
 * **A face now opens the person rather than the pairing**
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)). Tapping a photograph and receiving a
 * weights-and-contributions table was always slightly wrong: somebody tapping a picture of a
 * person is asking *who is this*. The Fit breakdown is a row inside what opens, which puts a
 * pairing fact behind a label naming a pairing.
 *
 * **And your own face is a control here for the first time**, because nothing served your row
 * and there was therefore nothing behind it to open. It reads the ungated `/players/me/record`,
 * so the one player this screen most exists for — somebody whose reliability number is holding
 * them back — can look the number up and watch it lift.
 *
 * The photograph is `PlayerPhoto`'s photo-or-poster switch, so the face here and the face
 * in the seat are **one drawing of one id** — a second implementation of the poster hash is
 * two faces for one person the day either one changes.
 *
 * ## The face **is** the target, which is the only arrangement that reaches 44
 *
 * The faces sit in a row, and [6.5](../../../../docs/design-system.md#65-touch-targets) bounds
 * horizontal slop by the neighbour: two 27pt faces cannot each grow to 44 into a gap they
 * share, whatever the gap is, because slop that overlaps is delivered to one sibling. Centring
 * a small face inside a 44pt box solves the touch and leaves a picture of a person drawn at
 * the size of a dot, with most of its own control blank around it.
 *
 * So the face is drawn at **`minTouch` itself**. The visual and the reachable area are the
 * same square, there is no slop to bound and nothing to spend — the availability cell's own
 * answer one screen over, and the shape [7.12](../../../../docs/design-system.md#712-the-court)
 * says the clear badge is the single control in this app that cannot have. Two of them plus
 * the gap is 91pt against the 103pt a panel has inside its padding on the narrowest phone,
 * which is the arithmetic `builder.test.tsx` pins.
 *
 * **Every face takes that box, including the ones that are not controls** — a 44pt button
 * beside a smaller one is one row at two rhythms, and which rhythm a face got would then be
 * decided by whether the record still describes the person in that seat.
 *
 * The key is the **position**, not the word: two withheld seats on one side both answer `?`,
 * and a key of the name would collapse them into one.
 *
 * ## The two halves are one height, and their contents are centred
 *
 * A panel is as tall as its own words, so a name that wrapped made one half taller than the
 * other and the pair stopped reading as two things being compared. Both are fixed: the row
 * **stretches** them to one height, and the name is `handleStem`'s — one line, because the
 * comparison is what the panel is for and a second line of it is what broke the comparison.
 *
 * ## Everything that is not a face is drawn and hidden
 *
 * The heading, the joined name and the strength are all said again above — the split row
 * states all three as one accessible element (`splitRowLabel`), and each face's own button
 * opens with the side it is on. §20.1's merge rule: what has no action of its own belongs to
 * the action beside it, and a listener stepping through *your side · you + Sergio · 3,15* on
 * the way to two buttons is being read the card twice.
 *
 * ## The bed is the bar's own colour, and only one side has one
 *
 * [7.11](../../../../docs/design-system.md#711-the-balance-bar) already paints these two
 * halves and it paints them unevenly: **yours** is the neutral one and **theirs** carries the
 * tone. That is not a decoration being invented here — it is the same statement the bar four
 * lines above makes, at the size a panel is, which is why the tone comes through
 * `BALANCE_SOFT` / `BALANCE_INK` rather than being chosen again. Yours takes `line2`, the
 * palette's own neutral fill inside a surface, and its heading stays `muted` — 4,62 there,
 * where `paper2` would have put it at 4,49 and under AA.
 */
function Side({
  heading,
  name,
  strength,
  tone,
  seated,
  onOpenRecord,
}: {
  readonly heading: string;
  readonly name: string;
  readonly strength: number;
  /** Absent on your own half, which is the neutral one — see the bed paragraph above. */
  readonly tone?: BalanceBarTone;
  readonly seated: readonly SeatedHandle[];
  readonly onOpenRecord: (seat: ReadRecord) => void;
}) {
  const bed = tone === undefined ? undefined : { backgroundColor: BALANCE_SOFT[tone] };
  const toned = tone === undefined ? undefined : { color: BALANCE_INK[tone] };

  return (
    <View style={[s.side, bed]}>
      <Text
        style={[s.sideHeading, toned]}
        accessibilityElementsHidden
        importantForAccessibility="no"
      >
        {heading}
      </Text>

      <View style={s.faces}>
        {seated.map((seat, at) => {
          const { place, name: who, face, subject } = seat;
          // `PlayerPhoto` hides itself, so a face carries no name of its own and the
          // button's label is the whole of what this control says.
          const drawn =
            face === undefined ? null : (
              <PlayerPhoto
                playerId={face.playerId}
                {...(face.photoUrl === undefined ? {} : { photoUrl: face.photoUrl })}
                box={{ kind: 'face', size: theme.size.minTouch }}
              />
            );

          return subject === undefined ? (
            <View key={at} style={s.faceTarget}>
              {drawn}
            </View>
          ) : (
            <Pressable
              key={at}
              accessibilityRole="button"
              accessibilityLabel={seatedNameLabel(place, {
                name: who,
                self: subject.kind === 'me',
              })}
              onPress={() =>
                onOpenRecord({
                  subject,
                  ...(seat.candidate === undefined ? {} : { candidate: seat.candidate }),
                })
              }
              // 6.6: the photo tile's `.7`, on the box rather than on the picture — the box is
              // the control, and a face that dimmed inside a target that did not would say the
              // two are separate things.
              style={({ pressed }) => [s.faceTarget, pressed ? s.pressed : undefined]}
            >
              {drawn}
            </Pressable>
          );
        })}
      </View>

      <View
        style={s.sideSays}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Text style={s.sideWho} numberOfLines={1}>
          {name}
        </Text>
        <Text style={[s.sideStrength, toned]}>{formatLevel(strength)}</Text>
      </View>
    </View>
  );
}

/**
 * What the court says about itself, **in the visible register** — §11's sentences and the
 * withheld mark, drawn beneath the seats they belong to.
 *
 * ## It is not the seats' spoken names printed, and that was the first draft's mistake
 *
 * §20.4's `{side}, empty. {UnfilledReason}` is a **name** — what one seat announces to a
 * listener navigating by seat — and §11's `Nobody in range was a good enough fit for this
 * seat` is the **sentence**. Printing the first as body copy puts *Their side, empty* on the
 * screen, and hands a listener the same shortfall twice: once on the seat's own button, and
 * again on a line beneath it. So this block is `unfilledSeatLine`'s and
 * `WITHHELD_SEAT_LINE`'s, and it is **hidden from accessibility** — §20.1's rule that
 * everything with no action of its own merges into the nearest action above it, which here is
 * the seat that already says it.
 *
 * ## Distinct sentences, because the seats are where *per seat* lives
 *
 * The shortfall is a fact about the pool and the mask rather than about a position, so *"the
 * reason is the line-up's own and the same one on every open seat in one answer"* — three
 * holes would otherwise print one sentence three times. Where two seats genuinely differ, both
 * lines are drawn. Which seat each belongs to is on the court: a hole is visibly a hole, and
 * its own name carries its own code.
 */
function courtStatements(court: {
  readonly seated: Seating;
  readonly shortfall: ReadonlyMap<number, UnfilledReason> | undefined;
  readonly withheld: ReadonlySet<string>;
}): readonly string[] {
  const said = court.seated.flatMap((seat, at) => {
    if (seat.kind === 'empty') {
      const reason = court.shortfall?.get(at);
      return reason === undefined ? [] : [unfilledSeatLine(reason)];
    }

    return seat.kind === 'player' && court.withheld.has(seat.playerId) ? [WITHHELD_SEAT_LINE] : [];
  });

  return [...new Set(said)];
}

const s = StyleSheet.create({
  root: { flex: 1 },
  action: { gap: theme.space.sm },
  /** The court is a fixed width (`size.court.build`), so it is centred rather than stretched. */
  court: { alignSelf: 'center' },
  /**
   * The split: a strength on each edge and the gap between them, three columns on one line.
   *
   * The two sides `flex` and the gap does not, so a long handle is spent on the box it is in
   * rather than on pushing the middle figure off centre.
   */
  split: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    marginTop: theme.space.sm,
  },
  splitSide: { flex: 1 },
  splitTheirs: { alignItems: 'flex-end' },
  sideLevel: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  gapWord: { ...theme.type.tag, color: theme.color.muted, textAlign: 'center' },
  gapLevel: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted, textAlign: 'center' },
  bar: { marginTop: theme.space.xs },
  /** The figure and its words, read left to right. */
  reading: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  readingWords: { flex: 1, gap: theme.space.xxs },
  acts: { flexDirection: 'row', gap: theme.space.xs },
  failure: { gap: theme.space.sm },
  body: { ...theme.type.tiny, color: theme.color.ink },
  /**
   * The swap line, and the one sentence on this screen that is centred.
   *
   * Every other `body` here is a statement about something beside it — a shortfall under the
   * seat it is about, a caveat under the figure it qualifies — and a left edge is what ties
   * each of them to what it describes. This one is about **the whole graphic below it**, has
   * no single thing to sit against, and reads as a caption on the court rather than a note in
   * the column. `muted` for the same reason: it is an instruction the player needs once.
   */
  swapHint: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
  provisional: { ...theme.type.tiny, color: theme.color.muted },
  /**
   * The two panels and the joint between them. They share the row equally and it does not.
   *
   * **Stretched, not centred**: two halves being compared are one height whatever is written
   * in them, which is `alignItems`'s default and is stated here because it was the bug. The
   * word between them centres itself instead.
   */
  sides: { flexDirection: 'row', gap: theme.space.xs },
  vs: { ...theme.type.tag, color: theme.color.muted, alignSelf: 'center' },
  /**
   * A half of the court, as a block. `radius.note` rather than `radius.card`: 4.2's rule is
   * that the bigger surface is the rounder one, and this is a bed inside a card.
   *
   * `line2` is the neutral one — the palette's fill inside a surface — and the other half
   * paints over it with the bar's tone. See `Side`.
   */
  side: {
    flex: 1,
    backgroundColor: theme.color.line2,
    borderRadius: theme.radius.note,
    padding: theme.space.sm,
    gap: theme.space.xxs,
    alignItems: 'center',
  },
  sideHeading: { ...theme.type.eyebrow, color: theme.color.muted },
  faces: { flexDirection: 'row', gap: theme.space.xxs },
  // 6.5's floor as the drawing itself: the face is `minTouch`, so the visual and the
  // reachable area are one square and there is no slop to bound. See `Side`.
  faceTarget: { width: theme.size.minTouch, height: theme.size.minTouch },
  sideSays: { alignItems: 'center', alignSelf: 'stretch' },
  sideWho: { ...theme.type.tiny, color: theme.color.ink, textAlign: 'center' },
  sideStrength: {
    ...theme.num.m,
    ...theme.tabular,
    color: theme.color.ink,
    textAlign: 'center',
  },
  pressed: { opacity: 0.7 },
});
