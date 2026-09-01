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
 * ## A swap is a selection, and only membership costs a round trip
 *
 * `ForecastResponse` returns **all three** arrangements, so trading two seats picks a different
 * one out of a response already held: instant, with no request. What is asked for is a
 * *membership* — add, replace, remove — and `searchKeys.forecast` sorts the ids into its key so
 * seat order cannot mint a second entry for one question
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §11).
 *
 * **No forecast arithmetic runs here**, and the check for that is looking for arithmetic. The
 * only numbers this file computes are seat counts. The percentage, its word, its tone, whether
 * it is provisional and which arrangement is the evenest are all read.
 *
 * ## Two things it deliberately does not draw
 *
 * **The balance bar.** [7.11](../../../../docs/design-system.md#711-the-balance-bar) takes an
 * *advantage* — your side's strength minus theirs — and nothing on a line-up serves one: the
 * two side strengths are the engine's working, and deriving them from the seated players'
 * levels would be the client computing the shape of a forecast it was handed. The figure, the
 * word and the tone are the served figure read through `balancePresentation`, which is the
 * whole of what §11.3 permits. The bar belongs where a served advantage exists — the candidate
 * card's `LEVEL_FIT` evidence, where it already is.
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

import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
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
  useOpenPair,
  useSendChallenge,
  type ProposedCourt,
  type SendRefusal,
} from '@/features/challenges/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { ShellScreen, landOnNow } from '@/features/shell/types';
import { offlineMessage } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import {
  BALANCE_INK,
  Button,
  Card,
  Hairline,
  Note,
  Row,
  Switch,
  behindOverlay,
  courtSeatCount,
  theme,
  useCollapsedPresentation,
  useLiveRegion,
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
  type Seating,
} from '../domain/forecast';
import { seatPlaces, withheldSeats, type SeatPlace } from '../domain/lineup';
import type { UnfilledReason } from '../domain/vocabulary';
import { sentWeekForOrigin } from '../domain/workingWeek';
import { useFillSeats, useForecast, useSearchRecord } from '../hooks/useBuilder';
import { useReadSearchBack } from '../hooks/usePool';
import { usePlaySession } from '../store/playSession.store';

import {
  PLAY_LIVE_REGIONS,
  SWAP_TOGGLE_LABEL,
  courtSummaryLabel,
  provisionalForecastAnnouncement,
  seatedNameLabel,
} from './accessibilityPresentation';
import { balanceTone, balanceWord } from './balancePresentation';
import {
  ALREADY_EVENEST,
  EVEN_IT_OUT_LABEL,
  FILLING_LABEL,
  FORECASTING_LABEL,
  NO_RECORD_BODY,
  NO_RECORD_TITLE,
  PICK_PLAYERS_LABEL,
  PROVISIONAL_WORD,
  RETRY_FORECAST_LABEL,
  SIDE_HEADINGS,
  START_OVER_LABEL,
  SWAP_TOGGLE_DESCRIPTION,
  TWO_WAYS_BODY,
  TWO_WAYS_TITLE,
  builderEyebrow,
  builderTitle,
  fillSeatsLabel,
  forecastHeading,
  seatsOpenLine,
} from './builderPresentation';
import { CourtBuild } from './court/CourtBuild';
import { PromptSheet } from './PromptSheet';
import type { CourtSeatOccupant } from './court/CourtSeat';
import {
  WITHHELD_SEAT_LINE,
  groupReasonLine,
  optimisedForLine,
  unfilledSeatLine,
} from './courtPresentation';
import { useHeldWait } from './heldWait';
import { playErrorMessage } from './playErrorMessage';
import { SearchingLatch } from './SearchingLatch';
import { forecastAssumption } from './searchPresentation';
import { engineFillStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';
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
  const { width } = useWindowDimensions();
  const collapsed = useCollapsedPresentation();

  /**
   * Where each of them is standing. **Absent is not empty** — it is *whatever the arrangement
   * says*, which is what lets an answer land without this screen writing a seating down.
   */
  const [seating, setSeating] = useState<Seating | undefined>(undefined);
  const [swapping, setSwapping] = useState(false);

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
   * **Whose Fit is being explained** — `SH.whyfit`, over the court rather than over a list.
   *
   * The row itself and not an id, for the reason the pool and the deck both hold one: the
   * sheet takes `(candidate, envelope)` and reads no global state, so a screen holding an id
   * would be looking the same row up again on every render of a sheet that is already holding
   * it. Route-local with the seating and the refusal, and gone the moment the court pops.
   *
   * **Two routes reach it and neither is the other's fallback**: a name on the forecast card
   * is the route, and a hold on the seat is a shortcut duplicating it.
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

  const filled = seatsFilled(seated);
  const open = seats - filled;
  const places = seatPlaces(seated.map(toBuildSeat));

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

  const occupants: readonly CourtSeatOccupant[] = seated.map((seat, at) =>
    toOccupant(seat, { self, rows, unfilled: shortfall?.get(at) ?? null }),
  );

  /** Everybody about to be asked: the court minus you, in seat order. Nobody invites themselves. */
  const invitees = seatedIds(seated);

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
   */
  const sentWeek = origin === undefined ? undefined : sentWeekForOrigin(origin.week, profile?.week);

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
  const latched = held && !fill.isPaused && fill.error === null;
  const playersInRange = fill.isSuccess ? fill.data.playersInRange : undefined;

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
   * Keyed by the **search the fill minted**, exactly as Find a game keys by the one its search
   * minted — and unlike the deck, which needs a wider key because a deal is not a press. ⚡ is,
   * so a second press is a second question worth asking.
   */
  const [answeredFor, setAnsweredFor] = useState<string | undefined>(undefined);
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
  const asking = question !== undefined && !latched && answeredFor !== question.search;

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
      {
        origin,
        lockedSeats: members,
        sentWeek,
        // The profile's own week may not have landed, and that is stated rather than replaced
        // with an empty one: the prompt that would have quoted it is dropped instead of drawn
        // against a grid nobody holds (`use-cases/fillSeats`).
        quotes: { sportName: sportLabel(origin.sport), profileWeek: profile?.week },
      },
      {
        onSuccess: ({ record: answer }) => {
          // Both halves of one act: the answer's own search becomes the origin, and the people
          // it seated become the line-up. `seatAll` is one write for one answer.
          setAnsweredSearchId(answer.searchId);
          setSeating(undefined);
          seatAll(answer.searchId, seatedIds(courtSeating(answer.court)));
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

    send.mutate(
      { searchId: originSearchId, court: courtWithYou(seated, self) satisfies ProposedCourt },
      {
        onSuccess: () => {
          // The stack goes first and the sentence second, in that order and not the other:
          // `landOnNow` ends the Play session and mounts the destination, and the toast is
          // spoken from the host's effect on the commit after it — so the platform's own
          // screen-change notification does not clobber the one announcement that interrupts.
          landOnNow();
          showToast({ message: CHALLENGE_SENT, tone: 'ok', politeness: 'interrupting' });
        },
        onError: (error) => {
          const next = sendRefusal(error);
          setRefusal(next);
          startTheReRead(next);
        },
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
        {...behindOverlay(latched || proposing || explained !== undefined || asking)}
      >
        <ShellScreen
          title={builderTitle({ seats, filled })}
          eyebrow={
            sportName === undefined || origin === undefined
              ? undefined
              : builderEyebrow({ sportName, seats, mode: origin.mode })
          }
          action={
            origin === undefined ? undefined : open === 0 ? (
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
                    busy={send.isPending}
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
                    label={fillSeatsLabel({ seats, filled })}
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
              {optimised === undefined ? null : (
                <Note variant="info">
                  <Text style={s.body}>{optimised}</Text>
                </Note>
              )}

              {filled > 1 ? (
                <Card>
                  <Switch
                    label={SWAP_TOGGLE_LABEL}
                    description={SWAP_TOGGLE_DESCRIPTION[swapping ? 'on' : 'off']}
                    checked={swapping}
                    onChange={setSwapping}
                  />
                </Card>
              ) : null}

              <CourtBuild
                sport={sport}
                width={width - theme.size.gutter * 2}
                summary={courtSummaryLabel({ sportName, filled, seats })}
                seats={occupants}
                swapping={swapping}
                onOpenPool={openPool}
                onSwap={(from, to) => setSeating(swapSeats(seated, from, to))}
                onClear={(at) => {
                  const seat = seated[at];
                  if (seat?.kind === 'player') unseat(seat.playerId);
                }}
                // The shortcut. Which seats carry it, and that none does under a swap, are
                // `CourtBuild`'s: the rule sits beside the truth table it is an exception to,
                // and it is read off the occupants this lookup's rows built — so a seat that
                // offered the gesture has a row here, and an absent one is *nothing to
                // explain* rather than a case owed a sentence.
                onHold={(at) => {
                  const seat = seated[at];
                  if (seat?.kind === 'player') setExplaining(rows.get(seat.playerId));
                }}
              />

              {open > 0 ? <Text style={s.centred}>{seatsOpenLine(open)}</Text> : null}

              {/* The court's own statement of its shortfall. The remedy is the pool, one tap
                  away on the seat itself and on the control beneath it — and the block is
                  hidden from a listener, because every seat already announces its own (§20.1's
                  merge rule; see `courtStatements`). */}
              {courtStatements({ seated, shortfall, withheld }).map((line) => (
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
              {record.court?.dock == null ? null : (
                <Note variant="amber">
                  <Text style={s.body}>{unfilledSeatLine(record.court.dock)}</Text>
                </Note>
              )}

              {open > 0 ? (
                <Note title={TWO_WAYS_TITLE}>
                  <Text style={s.body}>{TWO_WAYS_BODY}</Text>
                </Note>
              ) : null}

              {/* Paused, not loading. `networkMode: 'online'` holds the forecast rather than
                  failing it, and `isFetching` is **false** while it waits — so a screen that
                  drew only the spinner would answer a swap made offline with nothing at all:
                  no number, no sentence and no reason why (Part 11's amendment names this
                  request by name). */}
              {forecast.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

              {forecast.isFetching ? (
                <ActivityIndicator
                  accessibilityLabel={FORECASTING_LABEL}
                  color={theme.color.muted}
                />
              ) : null}

              {forecast.error === null ? null : (
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

              {chosen === undefined ? null : (
                <Card>
                  <Text style={s.eyebrow}>{forecastHeading(seats)}</Text>

                  {/* The figure, then the words **beneath** it. Part 13's *never colour alone*
                      is what puts §B9's word there, and the ticket puts *Provisional* under the
                      tinted number in one word — so both read down from the figure rather than
                      standing beside it. */}
                  <Text
                    style={[s.figure, { color: BALANCE_INK[balanceTone(chosen.forecast.pct)] }]}
                  >
                    {formatPercent(chosen.forecast.pct)}
                  </Text>
                  <Text style={s.word}>{balanceWord(chosen.forecast.pct)}</Text>
                  {chosen.forecast.provisional ? (
                    <Text style={s.provisional}>{PROVISIONAL_WORD}</Text>
                  ) : null}

                  {/* ADR-0108's rule that the figure and its caveat are one thing. A caveat this
                      build cannot read draws nothing, and `provisional` above still says the
                      figure has one. */}
                  {chosen.forecast.assumption === null ? null : (
                    <Text style={s.body}>{forecastAssumption(chosen.forecast.assumption)}</Text>
                  )}

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
                    <Row
                      label={SIDE_HEADINGS.yours}
                      labelHidden
                      value={
                        <Names
                          seated={handlesOn('yours', seated, places, rows)}
                          onExplain={setExplaining}
                        />
                      }
                    />
                    <Row
                      label={SIDE_HEADINGS.theirs}
                      labelHidden
                      value={
                        <Names
                          seated={handlesOn('theirs', seated, places, rows)}
                          onExplain={setExplaining}
                        />
                      }
                      divided
                    />
                  </Hairline>

                  {record.court?.groupReason == null ? null : (
                    <Hairline>
                      <Text style={s.body}>{groupReasonLine(record.court.groupReason)}</Text>
                    </Hairline>
                  )}

                  {arrangements.length < 2 ? null : (
                    <Hairline>
                      {chosen.isEvenest ? (
                        <Text style={s.body}>{ALREADY_EVENEST}</Text>
                      ) : (
                        <Button
                          label={EVEN_IT_OUT_LABEL}
                          variant="secondary"
                          onPress={() => {
                            const evenest = evenestArrangement(arrangements);
                            if (evenest !== undefined) setSeating(seatingOf(evenest));
                          }}
                        />
                      )}
                    </Hairline>
                  )}
                </Card>
              )}

              {lineup === undefined ? null : (
                <Button
                  label={START_OVER_LABEL}
                  variant="secondary"
                  onPress={() => {
                    discardLineup();
                    setSeating(undefined);
                  }}
                />
              )}
            </>
          )}
        </ShellScreen>
      </View>

      <SearchingLatch visible={latched} status={engineFillStatus({ playersInRange })} />

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
          onAnswered={() => setAnsweredFor(question.search)}
        />
      )}

      {/* `SH.whyfit`, over the court — the only place a **seated** player's Fit is explained,
          because the pool removes everybody already on the court from the one surface that
          explains a person. It reads `(candidate, envelope)` off the origin search record and
          nothing else, which is what lets one sheet serve all three of its entry points.

          **No `returnFocusTo`**, on the pool's own precedent: up to four names and four seats
          open the same sheet, so there is no one control to return to, and a ref per name
          would be four refs to keep in step with a list that changes on every swap. */}
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
          lineUp={
            // *"Nothing opens until they accept"* is false for doubles: the first acceptance
            // opens the chat, and the number the sentence quotes is the answers still owed —
            // which is the invitees, because the organiser's own seat is accepted from birth.
            seats > 2
              ? { kind: 'doubles', sportName, stillNeeded: invitees.length }
              : { kind: 'singles' }
          }
        />
      )}
    </>
  );
}

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
    // A hand-seated player has accepted nothing, and nothing else can seat one today: opening
    // the builder from an accepted challenge is out of scope, so the lock that would fire here
    // has no producer and the truth table keeps its arm for the day it does.
    accepted: false,
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
 * One printed handle, with **the two things that decide whether it is a control**.
 *
 * The place, because the button opens with the same two words the seat's own spoken name does
 * and `seatedNameLabel` composes from the code rather than from the heading the row draws. And
 * the row behind it, because that is both the test — *is there a breakdown to open* — and the
 * whole of what `SH.whyfit` is handed.
 */
interface SeatedHandle {
  readonly place: SeatPlace;
  /** §15's whole handle, or the unknown's question mark. Never cut short here. */
  readonly name: string;
  /**
   * The row the record still holds for them. **Absent is plain text**: you have no candidate
   * row because no route serves a searcher their own, and a withheld player has one field and
   * no card — so there is nothing behind the name and it is not a button (`seatIsExplainable`,
   * the same rule the seat's hold reads).
   */
  readonly candidate?: Candidate;
}

/**
 * The handles on one half of the court, **whole**.
 *
 * §15's `playerName()` is the one formatter, and this returns a **list**: *"a formatter that
 * returns one string has decided the layout, and this one must not"* — at 64 characters a join
 * produces a phrase no row can hold. A seat the record can no longer describe answers the
 * unknown's question mark, which is the same word the seat itself draws.
 */
function handlesOn(
  half: 'yours' | 'theirs',
  seated: Seating,
  places: readonly SeatPlace[],
  rows: ReadonlyMap<string, Candidate>,
): readonly SeatedHandle[] {
  const mine = half === 'yours';

  return seated.flatMap<SeatedHandle>((seat, at) => {
    const place = places[at];
    if (place === undefined || mine !== (place !== 'THEIR_SIDE')) return [];
    if (seat.kind === 'you') return [{ place, name: playerName({ kind: 'you' }) }];
    if (seat.kind === 'empty') return [];

    const row = rows.get(seat.playerId);
    const who: NamedPlayer =
      row === undefined ? { kind: 'unknown' } : { kind: 'player', nickname: row.card.nickname };

    return [{ place, name: playerName(who), ...(row === undefined ? {} : { candidate: row }) }];
  });
}

/**
 * One name per line, each truncating in its own box and none of them joined — **and each a
 * button where there is a breakdown behind it.**
 *
 * The target is the **line**, built to 6.5's minimum rather than granted a `hitSlop`: the names
 * are stacked with no gap, so vertical slop is bounded by a neighbour 0pt away and there is
 * none to take. That is the tick-box row's answer to the same arithmetic — *the row is the
 * surface* — and here the surface is one name.
 *
 * **Every line takes that box, including the ones that are not controls.** A 44pt button
 * beside a 15pt line is one column at two rhythms, and which rhythm a line gets would then be
 * decided by whether the record still describes the person standing in that seat — a layout
 * that moves when a row is withheld. The box is the column's, and the target is a consequence
 * of it rather than the reason for it.
 *
 * The key is the **position**, not the word: two withheld seats on one side both answer `?`,
 * and a key of the name would collapse them into one line.
 */
function Names({
  seated,
  onExplain,
}: {
  readonly seated: readonly SeatedHandle[];
  readonly onExplain: (candidate: Candidate) => void;
}) {
  return (
    <View>
      {seated.map(({ place, name, candidate }, at) =>
        candidate === undefined ? (
          <View key={at} style={s.handleTarget}>
            <Text style={s.handle}>{name}</Text>
          </View>
        ) : (
          <Pressable
            key={at}
            accessibilityRole="button"
            accessibilityLabel={seatedNameLabel(place, { name, fit: candidate.fit })}
            onPress={() => onExplain(candidate)}
            // 6.6: the chip's `.7`, on the target rather than on the word — the line is the
            // control, so a word that dimmed alone would say the two are separate things.
            style={({ pressed }) => [s.handleTarget, pressed ? s.pressed : undefined]}
          >
            <Text style={s.handle}>{name}</Text>
          </Pressable>
        ),
      )}
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
  failure: { gap: theme.space.sm },
  body: { ...theme.type.tiny, color: theme.color.ink },
  centred: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
  provisional: { ...theme.type.tiny, color: theme.color.muted },
  // The whole handle, and the one place on this screen it is not cut short.
  handle: { ...theme.type.rlValue, color: theme.color.ink, textAlign: 'right' },
  // 6.5's floor, as geometry rather than as slop, and the column's one rhythm — see `Names`.
  handleTarget: {
    minHeight: theme.size.minTouch,
    minWidth: theme.size.minTouch,
    justifyContent: 'center',
  },
  pressed: { opacity: 0.7 },
});
