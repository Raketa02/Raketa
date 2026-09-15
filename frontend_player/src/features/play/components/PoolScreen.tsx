/**
 * **The pool** — the full ranked list, and the one screen the relaxation ladder is on.
 *
 * Every remedy the court states routes here ([#271](https://github.com/Raketa02/Raketa/issues/271)),
 * because this is where the list can be read in full and where the search itself can be
 * widened. The two screens are one journey: the court says *why* a seat is empty in the four
 * `UnfilledReason` codes and offers *Pick players myself*, and the offer that answers it lives
 * on the surface with room to draw it ([#223](https://github.com/Raketa02/Raketa/issues/223) §2).
 *
 * ## The ladder is here and nowhere else, and every *widen* sentence is gated
 *
 * The specs pointed every thin-result state at a settings screen — *"widen the radius in
 * You"* — because the prototype had no offer to point at. It is struck from this screen's copy
 * entirely: pointing a player at a settings screen while a one-tap widening with a true count
 * sits on the same screen is the product being unhelpful on purpose, and **taking a rung and
 * changing your saved radius stay deliberately different acts** (ADR-0099). What survives that
 * sentence is the deck's genuinely-empty state, which the ladder does not reach.
 *
 * `radius_clamp` gates the *sentence* and never the offers. The bit says a widening offer hit
 * the slider's ceiling, not that the searcher is at it — the engine clamps such a rung down to
 * 50 km and offers it anyway — so what the bit decides is which terminal copy is written when
 * there is nothing left to offer: the reach **stated as a fact**, rather than an instruction
 * addressed to somebody who cannot carry it out. Suppressing that sentence silently would
 * leave a player staring at a short list with no account of why there is nothing to do.
 *
 * ## Taking a rung replaces the list, and what replaces *back* is a sentence
 *
 * Two search rows joined by `offered_by_search_id` are one screen. A player holding both would
 * be diffing two lists to find the four people that differ, which is the engine's job — so
 * this screen swaps which record it is reading and leaves a **standing statement** in its
 * place, naming the widening and the profile it did not touch (§6). The way out is changing
 * the ask again.
 *
 * One climb per search screen, and **the bound is the engine's**: a search that took a rung is
 * offered none, and its `rung_offers` is `[]` rather than `null`. This screen therefore needs
 * no memory of how far it has climbed — it renders what it was handed, and the terminal
 * sentence is written from `radius_clamp` plus the rung it knows it sent (§7).
 *
 * ## What this screen holds, and what it refuses to
 *
 * Four `useState`s and no store. **The pending seat replacement is one of them**, and it needs
 * no clearing rule: the court **pops** rather than pushes, so this route unmounts and takes it
 * with it — G7's *"leaving the pool halfway through replacing somebody should be forgotten"* is
 * satisfied by a navigation decision already taken, and a store would reintroduce exactly the
 * bug it was meant to prevent ([#228](https://github.com/Raketa02/Raketa/issues/228) §6).
 *
 * The **membership** is `playSession`'s, the **rows** are Query's under
 * `searchKeys.detail(id)`, and the **re-read is this screen's own act** — *"with the origin
 * already in hand"*, which is the sentence `useBuilder` wrote when it declined to fetch. It is
 * also what makes a withheld seat real: the record is immutable and the gates are live, so a
 * re-read is the only moment a row the product has since agreed not to show can leave the list
 * and a seat on the court behind can go blank.
 *
 * ## Two cards, one shape, and no float
 *
 * The competitive card is photo-left with a head-to-head row and the social card is media-top
 * with fact rows, and **the pool draws one shape twice** — same radius, no shadow. #219's
 * float reaches the deck alone: every clause of its argument is about a card that translates
 * and rotates out under a thumb, and a row in a scrolling list does neither
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §3).
 *
 * ## A climb raises questions, and the hinge is drawn where the evidence is
 *
 * `POST /searches` raises prompts wherever it is called, and taking a rung calls it — so this
 * is the fourth surface `SH.saveav` reaches ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 * The sheet is asked once **this screen's own latch lifts**, over the widened list: a climb
 * replaces the list in place, so there is no push for it to stand in front of.
 *
 * **`KEEP_THIS_RADIUS` here is the ladder's own argument finished, not a contradiction of it.**
 * Taking a rung and changing your saved radius stay deliberately different acts, and this
 * screen is where the difference is written down twice already — in the standing statement
 * naming *the profile it did not touch*, and in `takeRung` writing no radius. What the engine
 * offers after the climb is the third: the number, asked for rather than taken, on the one
 * screen where the player can see what the widening bought. A sheet that names the value and
 * says what *not now* costs is the opposite of the silent conflation ADR-0099 refuses.
 *
 * **`REFRESH_YOUR_TIMES` never reaches here**, because *"there is no grid on this screen"* —
 * the same sentence that sends a rung's added cell two pushes back to Find a game. The
 * use-case drops it.
 *
 * ## What it deliberately does not draw
 *
 * **A seat-impact line, and an *Evenest* chip.** Both read `CandidateSchema.would_be_forecast`,
 * which nothing in the backend has ever written and which is *"omitted on every shortlist"* —
 * this surface exactly. The pool ranks people for a seat; *what this candidate would do to the
 * balance* is the court's question, and the court has `POST /forecasts`
 * ([#231](https://github.com/Raketa02/Raketa/issues/231) §4).
 *
 * **A client-side `+12`.** §C5 specified the Best-fit comparator as *"the fit score plus 12 for
 * anyone who said yes to you in Match me"*. The server already lifted them, in the engine, as
 * an **admission** rather than a bonus — so re-applying it here would score the wire's own
 * ranking a second time. `poolOrder` sorts on the printed number and nothing else.
 *
 * **Nor a pin.** For a while a liker was forced to the top of the served order
 * ([#310](https://github.com/Raketa02/Raketa/issues/310)); ADR-0169 §8 removed it — *a yes
 * informs; it never takes over* — and `poolOrder`'s module note is where both the bonus and the
 * pin are argued against, because a reader arriving on the trail of #231 arrives here first.
 * What a yes does on this screen is a **tag**, in either direction: *Wants to play you* off the
 * row's admitting code, and *You said yes* off the reader's own outgoing list, which this screen
 * reads from the same `GET /interest` the deck reads and asks one person at a time.
 *
 * **The cell a times rung adds — which is recorded here and drawn nowhere near here.** #223 §8
 * requires that the offered slot **visibly ticks**, marked as this-search-only, because
 * otherwise the week the player just filled in disagrees with the search that ran. There is no
 * grid on this screen and a tick drawn where nobody is looking is not the requirement, so what
 * this screen does is hand the cell to `playSession` and let *Find a game* mark it on the grid
 * it owns ([#283](https://github.com/Raketa02/Raketa/issues/283)). **It never names the cell in
 * prose either**: `takenRungLine` says *outside your week* rather than a Saturday morning, and
 * the grid two pushes back is the one surface that shows which square it was.
 *
 * **A second live region over the running figure.** §20.9's third region announces the forecast
 * because it changes while focus is elsewhere, and that is as true here as on the court — but
 * the court is **still mounted underneath this route** and already holds the region, and
 * `announce` is imperative, so it fires from behind a screen the platform has marked hidden.
 * Claiming it here as well would say one change twice. The region stays the builder's, and
 * `PLAY_LIVE_REGIONS.provisionalForecast` records that it now covers two surfaces.
 */

import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage } from '@/shared/errors';
import { playerName } from '@/shared/formatting/playerName';
import { Button, Chip, Note, behindOverlay, courtSeatCount, theme } from '@/shared/ui';

import type { Candidate, RelaxedAsk, RungOffer } from '../domain/candidate';
import { arrangementFor, seatOccupant, seatingToDraw, seatsFilled } from '../domain/forecast';
import { carriedOnto } from '../domain/lineup';
import { poolLadder } from '../domain/poolLadder';
import { saidYesTo } from '../domain/outgoingInterest';
import { bestMatchId, orderPool, pickable, poolSortRow } from '../domain/poolOrder';
import { alreadyAsked } from '../domain/raisedPrompt';
import type { SortOption } from '../domain/vocabulary';
import { sentWeekForOrigin } from '../domain/workingWeek';
import { useForecast, useSearchRecord } from '../hooks/useBuilder';
import { useOutgoingInterest } from '../hooks/useInterest';
import { useReadSearchBack, useTakeRung } from '../hooks/usePool';
import { usePlaySession } from '../store/playSession.store';

import { rungOfferLabel } from './accessibilityPresentation';
import { CandidateCard } from './candidate/CandidateCard';
import { CandidateCardSocial } from './candidate/CandidateCardSocial';
import { useHeldWait } from './heldWait';
import { playErrorMessage } from './playErrorMessage';
import {
  POOL_LADDER_BODY,
  POOL_LINEUP_COST,
  POOL_NO_RECORD_BODY,
  POOL_NO_RECORD_TITLE,
  POOL_TITLE,
  READING_AGAIN_LABEL,
  READ_AGAIN_LABEL,
  leavingLine,
  poolLadderTitle,
  replacingLine,
  rungCount,
  takenRungLine,
  terminalReachLine,
  zeroRungLine,
} from './poolPresentation';
import { PoolHeader } from './PoolHeader';
import { PromptSheet } from './PromptSheet';
import { SearchingLatch } from './SearchingLatch';
import { poolDescription, relaxationOffer, sortLabel } from './searchPresentation';
import { poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';
import { WhyFitSheet } from './whyfit/WhyFitSheet';

/**
 * The widening this screen took, as the header states it.
 *
 * `profileRadiusKm` is the **offering** search's own radius, and that is the profile's number
 * rather than a coincidence: a search that took a rung is offered none, so the search that made
 * this offer can only have been the strict one. Holding it here rather than reading the profile
 * back keeps the sentence a statement about the pair of searches on screen.
 */
type TakenRung = RelaxedAsk & { readonly profileRadiusKm: number };

export interface PoolScreenProps {
  /** The search this pool was opened on — validated by the route (`schemas/routeParams.ts`). */
  readonly arrivalSearchId: string;
  /** The seat the visit is against. An index no court has reads as no seat at all. */
  readonly arrivalSeat: number;
}

export function PoolScreen({ arrivalSearchId, arrivalSeat }: PoolScreenProps) {
  const lineup = usePlaySession((state) => state.lineup);
  const seatPlayer = usePlaySession((state) => state.seat);
  const seatAll = usePlaySession((state) => state.seatAll);
  const unseat = usePlaySession((state) => state.unseat);
  const addForThisSearch = usePlaySession((state) => state.addForThisSearch);
  const clearAddedForThisSearch = usePlaySession((state) => state.clearAddedForThisSearch);
  const profileSurface = useProfileSurface();

  /**
   * Which record this list is. It moves **once**, when a rung is taken — the widened search is
   * the session's current search, and the strict one keeps its own cache entry for the court
   * one push below to go on drawing from.
   */
  const [searchId, setSearchId] = useState(arrivalSearchId);
  const [taken, setTaken] = useState<TakenRung | undefined>(undefined);
  /**
   * The seat this visit is against, until an add discharges it.
   *
   * `undefined` is *append to the court*, which is what every add after the first one is: the
   * replacement is a single pending act, and it is spent the moment it happens.
   */
  const [pending, setPending] = useState<number | undefined>(arrivalSeat);
  const [sort, setSort] = useState<SortOption | undefined>(undefined);
  const [explaining, setExplaining] = useState<Candidate | undefined>(undefined);

  /**
   * Where the prompt sheet hands focus back — **the standing statement the climb wrote.**
   *
   * Part 13 returns a listener to the control that opened a modal; this sheet is opened by an
   * *answer* rather than by a press, and the rung that caused it is unmounted by its own
   * success — one climb per search screen, so the answer's own `rung_offers` is empty and the
   * ladder is replaced. What replaced it is this sentence, which names the widening the
   * question is about.
   */
  const standingStatement = useRef<View | null>(null);

  const record = useSearchRecord(searchId);
  const reread = useReadSearchBack();
  /**
   * The court's own record re-read beside the list's, when the two are different searches.
   *
   * A mark on a seat the gates no longer admit is derived against **the origin's** live rows
   * (`withheldSeats`), and the read-back that refreshes them is this screen's act — so a pool
   * that re-read only its list would leave a ⚡-built court unmarked. Its own instance, because
   * the failure this screen surfaces and offers to retry is the list's: the court's re-read is
   * for the mark, and a mark that does not appear is the same state as no read-back at all.
   */
  const rereadCourt = useReadSearchBack();
  const climb = useTakeRung();
  /**
   * The reader's own yeses, for the one tag this screen draws from them. The same read the
   * deck holds, and nothing here waits for it: a row is drawn without the tag until the list
   * lands, and gains it without moving (ADR-0169 §8).
   */
  const outgoing = useOutgoingInterest();

  const origin = record?.origin;
  const sport = origin?.sport;
  const seats = sport === undefined ? 0 : courtSeatCount(sport);
  const members = lineup?.seats ?? [];
  const profile = profileSurface.data;

  /**
   * The forecast the header reads, and the seating the pending seat is resolved against.
   *
   * It is asked under the **line-up's** own origin rather than this screen's: the four it is
   * about came off that search, and `POST /forecasts` refuses anybody the cited one never
   * showed. Nothing is computed from it — the percentage, its word, its tone and whether it is
   * provisional are all read.
   */
  const forecast = useForecast(
    origin === undefined || lineup === undefined || members.length === 0
      ? undefined
      : {
          sport: origin.sport,
          mode: origin.mode,
          searchId: lineup.originSearchId,
          players: members,
        },
  );

  const arrangements = forecast.data ?? [];
  const seated = seatingToDraw(arrangements, { seats, members });
  const chosen = arrangementFor(arrangements, seated);

  /**
   * Who the pending seat is holding, if anybody — **the person an add would replace**.
   *
   * Read through the same derivation the court's own default seating takes, because that is
   * the one reading of *seat 2* both screens share: a seating is what you get when you read
   * the membership through the arrangements, and both hold the same two.
   */
  const replacing = seatOccupant(seated, pending);

  /**
   * **Nowhere left to put anybody** — and therefore the state every *Add to the court* on this
   * screen is drawn dead in.
   *
   * The pool does not close on a full court and should not: the rows are still worth reading,
   * the ladder is still worth taking, and the way back is the header's own control. What it
   * must not do is offer an act it cannot carry out — an add against a court with four people
   * on it either silently does nothing or quietly evicts somebody, and both are worse than a
   * control that says no by being dim.
   *
   * **A visit against an occupied seat is exempt**, because there the add *is* the seat: it
   * unseats whoever is in it and puts this person there, so a full court is the ordinary case
   * rather than the blocked one (`add`, below).
   */
  const noSeatLeft = replacing === undefined && seatsFilled(seated) >= seats;

  // Two readings of the same rows, and the **served** order is the input to both: `orderPool`
  // hands it back untouched, and `bestMatchId`'s tie-break is *the row the server served
  // first*, which is a statement about that order rather than about whichever array ends up
  // drawn.
  const offered = pickable(record?.candidates ?? [], members);
  const drawn = orderPool(offered, sort);
  // Answered for every pool and drawn on the competitive one, because the coral tag lives in the
  // competitive card's identity row and the social card has no slot beside the handle for one
  // (#309). A for-fun pool carries its two interest tags and simply no *best match*.
  const bestMatch = bestMatchId(offered, sort);
  // *You said yes* — the reader's own list, asked one person at a time, in the search's sport.
  const saidYes = (candidate: Candidate) =>
    sport !== undefined && saidYesTo(outgoing.data, sport, candidate.playerId);

  /**
   * **Whether the court is bound to some other search than the one this list is.**
   *
   * It is, in two cases: the line-up is ⚡'s, whose record returns exactly the people it seated
   * and is therefore never the list a player picks from (`BuilderScreen`'s `listSearchId`); or a
   * rung was taken and the list moved on while the court stayed on the strict search. Either
   * way a pick has to move the court onto this list — `POST /forecasts` cites one search — and
   * the new origin can vouch only for the rows it returned.
   */
  const elsewhere = lineup !== undefined && lineup.originSearchId !== searchId;
  /** The court's own record, for the names and faces of people this list may not hold. */
  const courtRecord = useSearchRecord(elsewhere ? lineup?.originSearchId : undefined);

  /**
   * The rows the header reads its names and faces off, and your own id for your own poster.
   *
   * The court's own record is read **after** this list's, so a seated player it holds is drawn
   * from it: with the court bound elsewhere, this list may never have shown them at all.
   *
   * `self` is the account's, off `GET /users/me`: no route serves a searcher their own card, so
   * a seat that waited for an answer to name you would sit faceless until one landed.
   */
  const courtRows = [...(record?.candidates ?? []), ...(courtRecord?.candidates ?? [])];
  const rows = new Map(courtRows.map((row) => [row.playerId, row]));
  const self = useCurrentUser().data?.id;

  /**
   * Who a pick keeps on the court, and who it takes off — **decided before the tap, and said.**
   *
   * `staying` is everybody the pick is not replacing. On a court bound to this list they all
   * stay, trivially. On one bound elsewhere the list can vouch only for the rows it returned
   * (`carriedOnto`), and the rest are named in a sentence above the rows rather than found
   * missing from the court afterwards.
   */
  const staying = members.filter((seated) => seated !== replacing);
  const carried = elsewhere
    ? carriedOnto(
        staying,
        (record?.candidates ?? []).map((row) => row.playerId),
      )
    : staying;
  const leaving = staying.filter((seated) => !carried.includes(seated));

  const ladder = poolLadder({
    rows: record?.candidates.length ?? 0,
    // **A pool over a challenge fill has no ladder**, and `null` is already this argument's
    // value for *this answer carries no offers*. Taking a rung is `POST /searches` citing the
    // offer, and that search does not complete a challenge — so the open-challenge gate would
    // exclude the very people sitting on the court, and the first seat taken off the widened
    // list would start a **new** line-up without them (`playSession.seat`'s own rule: a seat
    // from a different search never mixes two). A widening that quietly drops the people who
    // already said yes is not a remedy; on this court the remedies are ⚡ and another seat.
    offers: origin?.completing === undefined ? (record?.envelope.rungOffers ?? null) : null,
  });

  const sportName = sport === undefined ? undefined : sportLabel(sport);
  const sorts = poolSortRow(record?.envelope.sortsAvailable ?? [], sort);

  /**
   * The widened search's own week: **the one the offering search ran on**.
   *
   * Sent unless it can be shown to be the profile's own grid, which is the one case an omitted
   * override already means. Unprovable is *sent* — a rung that quietly ran on a different week
   * from the list it widens would be the two disagreeing silently — and it is ⚡'s own
   * derivation, on the screen that takes the other branch.
   */
  const sentWeek =
    origin?.week === undefined ? undefined : sentWeekForOrigin(origin.week, profile?.week);

  /**
   * Re-read the arrival record, **once**.
   *
   * Arriving is a moment; a render in which the record happens to be held is not, and re-reading
   * from one would put a request behind every re-render of this screen. It is not fired for the
   * widened list, which was minted seconds ago by an act on this screen: re-reading an answer
   * that has just been handed over is Part 7's *"don't immediately refetch what you were just
   * handed"*.
   */
  const readAgain = useRef<() => void>(() => undefined);
  readAgain.current = () => {
    if (record !== undefined) reread.mutate(record);
    if (courtRecord !== undefined) rereadCourt.mutate(courtRecord);
  };

  const readFor = useRef<string | undefined>(undefined);
  const readable = record !== undefined && searchId === arrivalSearchId ? searchId : undefined;
  useEffect(() => {
    if (readable === undefined || readFor.current === readable) return;
    readFor.current = readable;
    readAgain.current();
  }, [readable]);

  /**
   * The pool's own wait — **the same floor `POST /searches` has on Find a game**, because it is
   * the same act: a ranking pass whose count is printed off the answer.
   *
   * A **paused** write is not in flight at all and a refusal has nothing to hold for, which are
   * the two subtractions every latch in this tab makes.
   */
  const held = useHeldWait(climb.isPending && !climb.isPaused, searchingFloorMs({ kind: 'pool' }));
  const latched = held && !climb.isPaused && climb.error === null;
  const playersInRange = climb.isSuccess ? climb.data.playersInRange : undefined;

  /**
   * **The question the climb raised, and the beat it is asked in.**
   *
   * Asked **after the latch lifts**, and there it stops: a climb replaces the list in place, so
   * the sheet stands in front of an answer already on screen rather than in front of a push —
   * the builder's arrangement rather than Find a game's
   * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
   *
   * **Remembered for the visit rather than for the search the climb minted.** It was the
   * minted id, on the argument that taking a rung is a press and a second climb is a second
   * question worth asking — which is true of the press and false of the question. Every prompt
   * that reaches here is about something that outlives the climb, and `KEEP_THESE_TIMES` is
   * about the **working week** a search two screens back has already asked over
   * ([#287](https://github.com/Raketa02/Raketa/issues/287)). The list is `playSession`'s,
   * because what these questions are about is.
   *
   * One value rather than three, so the overlay behind the sheet and the sheet itself cannot
   * disagree about whether one is up.
   */
  const asked = usePlaySession((state) => state.askedQuestions);
  const recordAsked = usePlaySession((state) => state.recordAsked);
  const climbed = climb.isSuccess ? climb.data.record.searchId : undefined;
  const raised = climb.isSuccess ? climb.data.prompts[0] : undefined;
  const question =
    raised === undefined || climbed === undefined || sport === undefined
      ? undefined
      : { raised, sport, search: climbed };
  const asking =
    question !== undefined &&
    !latched &&
    !alreadyAsked(asked, question.sport, question.raised.prompt);

  /**
   * Add somebody, discharging the replacement if this visit was against an occupied seat.
   *
   * Nobody drawn here is on the court — `pickable` took them out — so the person leaving the
   * seat is never the person arriving in it, and there is no self-replacement to guard against.
   */
  function add(candidate: Candidate) {
    if (elsewhere) {
      // The court moves onto this list — one write, the way ⚡ rebinds — carrying the seats it
      // can vouch for and the pick. `seat` would start a line-up of one instead, which is the
      // origin guard's own silent destruction arriving from the pool.
      seatAll(searchId, [...carried, candidate.playerId]);
    } else {
      if (replacing !== undefined) unseat(replacing);
      seatPlayer(searchId, candidate.playerId);
    }
    setPending(undefined);
  }

  function take(offer: RungOffer) {
    if (origin === undefined || record === undefined || sportName === undefined) return;

    climb.mutate(
      {
        origin,
        sentWeek,
        offeredBySearchId: record.searchId,
        rung: offer.rung,
        // `profile?.week` and never `?? []`: an unlanded read is *this build does not hold
        // the profile's week*, and an empty list is *they have unticked every cell*. The
        // mapper drops the prompt that would quote it rather than drawing a diff claiming
        // every slot is new (#247's distinction, on the client's own half of the pair).
        quotes: { sportName, profileWeek: profile?.week },
      },
      {
        onSuccess: ({ record: answer }) => {
          setSearchId(answer.searchId);
          // The sort is the old list's selection, and there is no chip on the new one it is
          // guaranteed to correspond to: `sorts_available` is per answer.
          setSort(undefined);
          // The cell the widening added, handed to the grid it belongs to. Nothing here draws
          // it: this screen has no grid, and #223 §8 asks for the tick where the week was
          // filled in — which is *Find a game*, two pushes back (#283).
          //
          // **Every climb rewrites it, including the ones that add no cell.** A player can
          // leave this pool and open it again against another seat, on the strict record the
          // court still holds, and take a *radius* rung the second time — which runs on the
          // week without the cell. A mark left standing would then be the grid disagreeing
          // with the search that ran, which is the disagreement §8 exists to close.
          if (offer.slot === null) clearAddedForThisSearch();
          else addForThisSearch(offer.slot);
          setTaken(
            offer.ask === 'TIMES'
              ? { ask: 'TIMES', profileRadiusKm: record.envelope.pool.radiusKmUsed }
              : {
                  ask: 'RADIUS',
                  radiusKm: offer.radiusKm,
                  profileRadiusKm: record.envelope.pool.radiusKmUsed,
                },
          );
        },
      },
    );
  }

  return (
    <>
      {/* Both overlays are **siblings** of the screen they cover: `behindOverlay` hides
          everything inside the element carrying it, so one rendered in there would hide itself
          along with the screen. */}
      <View style={s.root} {...behindOverlay(latched || explaining !== undefined || asking)}>
        <ShellScreen
          /* **What this screen is for**, and nothing above it. The pair was tried both ways
             round: the facts promoted to the title with this name dropped, which put the court
             and the pool under one heading; and the facts kept as 10.3's eyebrow over it,
             which read as a caption saying what the header card below already draws — the
             Sport under the court, the seats counted, and both of them in that card's own
             spoken name. */
          title={POOL_TITLE}
          // The court is underneath — this screen **pops** back onto it, which is already how
          // the row's own *back to the court* control returns and why the pending replacement
          // needs no clearing rule. The chevron is that same `back`, one level up the screen
          // rather than inside a card.
          onBack={router.back}
        >
          {record === undefined || sportName === undefined ? (
            <Note title={POOL_NO_RECORD_TITLE}>
              <Text style={s.body}>{POOL_NO_RECORD_BODY}</Text>
            </Note>
          ) : (
            <>
              {/* What replaces *back*: the widening, and the profile it did not touch.

                  It carries the ref the prompt sheet hands focus back to, in a `View` because
                  focus has to land on a **host element** and `Note` is a component. It is the
                  honest target on this screen: the control that raised the sheet was the rung,
                  and a search that took one is offered none — so the ladder it stood in is
                  gone by the time the sheet closes, and this sentence is what took its place. */}
              {taken === undefined ? null : (
                <View ref={standingStatement}>
                  <Note variant="info">
                    <Text style={s.body}>{takenRungLine(taken)}</Text>
                  </Note>
                </View>
              )}

              {/* The court being filled, and what it is worth so far — #299. It replaces the
                  forecast card rather than standing above it: every fact that card drew is in
                  here, and a second one restating them is the screen saying one thing twice. */}
              {sport === undefined ? null : (
                /* Unreachable: `sportName` is `sportLabel(sport)`, so the branch above has
                   already established both. It is here because that implication is not one
                   the compiler can follow, and a non-null assertion would be the same claim
                   made where nothing checks it. */
                <PoolHeader
                  sport={sport}
                  sportName={sportName}
                  seats={seats}
                  seated={seated}
                  rows={rows}
                  self={self}
                  {...(chosen === undefined ? {} : { arrangement: chosen })}
                  onCourt={() => router.back()}
                />
              )}

              <Text style={s.body}>{poolDescription({ ...record.envelope.pool, sportName })}</Text>

              {/* Said rather than assumed: the court is one screen away, so a silent swap of
                  one handle for another is a destruction found out about afterwards. */}
              {replacing === undefined ? null : (
                <Text style={s.body}>
                  {replacingLine(playerName(nameOf(courtRows, replacing) ?? { kind: 'unknown' }))}
                </Text>
              )}

              {/* And whom a pick off this list would take off the court, for the same reason:
                  the court is bound to another search, and this one cannot vouch for them. */}
              {leaving.length === 0 ? null : (
                <Text style={s.body}>
                  {leavingLine(
                    leaving.map((seated) =>
                      playerName(nameOf(courtRows, seated) ?? { kind: 'unknown' }),
                    ),
                  )}
                </Text>
              )}

              {reread.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

              {reread.isPending && !reread.isPaused ? (
                <ActivityIndicator
                  accessibilityLabel={READING_AGAIN_LABEL}
                  color={theme.color.muted}
                />
              ) : null}

              {/* The re-read's retry is `retryTarget`'s **the-record**: a record id exists, so
                  *Try again* re-reads rather than re-running the search — which would mint a
                  new id and orphan the line-up bound to the old one. */}
              {reread.error === null ? null : (
                <View style={s.failure}>
                  <Note variant="coral" accessibilityRole="alert">
                    {playErrorMessage(reread.error)}
                  </Note>
                  <Button
                    label={READ_AGAIN_LABEL}
                    variant="secondary"
                    onPress={() => readAgain.current()}
                  />
                </View>
              )}

              {/* The row is the server's vocabulary drawn verbatim, and it vanishes when there
                  is nothing to offer — a hardcoded row of four would be three-quarters a lie. */}
              {sorts.length === 0 ? null : (
                <View style={s.sorts}>
                  {sorts.map((offered) => (
                    <Chip
                      key={offered}
                      label={sortLabel(offered)}
                      selected={offered === sort}
                      onPress={() => setSort(offered)}
                    />
                  ))}
                </View>
              )}

              {drawn.map((candidate) =>
                record.envelope.mode === 'COMPETITIVE' ? (
                  <CandidateCard
                    key={candidate.playerId}
                    candidate={candidate}
                    envelope={record.envelope}
                    /* The search's Sport, drawn on the photo panel. It is the screen's fact
                       rather than the card's — one value for the whole list, and #309 refuses
                       to put twenty copies of it on `player_card`. */
                    sportName={sportName}
                    /* The same Sport, counted rather than named: the stake boxes are drawn on a
                       singles court and hidden on a doubles one, and the seat count is the
                       answer this screen already holds (#312). */
                    seats={seats}
                    /* Which row wears the coral tag is the ordering rule's answer and never a
                       card's: a component handed one candidate cannot know it is the highest. */
                    bestMatch={candidate.playerId === bestMatch}
                    saidYes={saidYes(candidate)}
                    action="ADD_TO_COURT"
                    onAction={() => add(candidate)}
                    actionDisabled={noSeatLeft}
                    onWhyFit={() => setExplaining(candidate)}
                  />
                ) : (
                  <CandidateCardSocial
                    key={candidate.playerId}
                    candidate={candidate}
                    envelope={record.envelope}
                    saidYes={saidYes(candidate)}
                    action="ADD_TO_COURT"
                    onAction={() => add(candidate)}
                    actionDisabled={noSeatLeft}
                    onWhyFit={() => setExplaining(candidate)}
                  />
                ),
              )}

              {climb.isPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

              {/* A refusal ends the latch over the control that failed, which for a rung is the
                  rung itself: nothing was minted that anybody is holding. */}
              {climb.error === null ? null : (
                <Note variant="coral" accessibilityRole="alert">
                  {playErrorMessage(climb.error)}
                </Note>
              )}

              {/* The ladder, beneath the rows: a thin list is the offers with what there is
                  above them, and an empty one is the offers alone. */}
              {ladder.kind === 'silent' ? null : (
                <Note
                  title={poolLadderTitle({
                    rows: record.candidates.length,
                    radiusKmUsed: record.envelope.pool.radiusKmUsed,
                  })}
                >
                  {ladder.kind === 'exhausted' ? (
                    <Text style={s.body}>
                      {terminalReachLine({
                        radiusKmUsed: record.envelope.pool.radiusKmUsed,
                        playersInRange: record.envelope.pool.playersInRange,
                        radiusClamp: record.envelope.radiusClamp,
                        tookRadiusFrom: taken?.ask === 'RADIUS' ? taken.profileRadiusKm : undefined,
                      })}
                    </Text>
                  ) : (
                    <>
                      <Text style={s.body}>{POOL_LADDER_BODY}</Text>

                      {/* Rule 9's reversibility, said before the act: a widened search is a new
                          search, and `POST /forecasts` refuses a four whose members did not all
                          appear in the search it cites. */}
                      {lineup === undefined ? null : <Text style={s.body}>{POOL_LINEUP_COST}</Text>}

                      {ladder.controls.map((offer) => (
                        <View key={offer.rung} style={s.rung}>
                          {/* **The count is printed on the button** — ADR-0099 §5, and §20.1's
                              merge rule says the same thing about the same two elements: the
                              price has no action of its own, so it belongs in the name of the
                              control it prices rather than beside it as a second stop. */}
                          <Button
                            label={relaxationOffer(offer)}
                            accessibilityLabel={rungOfferLabel(
                              relaxationOffer(offer),
                              rungCount(offer, record.envelope.pool.window),
                            )}
                            variant="secondary"
                            busy={climb.isPending}
                            onPress={() => take(offer)}
                          />
                          <Text
                            style={s.centred}
                            accessibilityElementsHidden
                            importantForAccessibility="no-hide-descendants"
                          >
                            {rungCount(offer, record.envelope.pool.window)}
                          </Text>
                        </View>
                      ))}

                      {/* A control that provably returns an empty list is a control lying about
                          being useful, so the count is said instead of tapped. */}
                      {ladder.statements.map((offer) => (
                        <Text key={offer.rung} style={s.body}>
                          {zeroRungLine(offer)}
                        </Text>
                      ))}
                    </>
                  )}
                </Note>
              )}
            </>
          )}
        </ShellScreen>
      </View>

      {explaining === undefined || record === undefined ? null : (
        <WhyFitSheet
          visible
          onClose={() => setExplaining(undefined)}
          candidate={explaining}
          envelope={record.envelope}
          name={playerName({ kind: 'player', name: explaining.card.name })}
        />
      )}

      {sportName === undefined ? null : (
        <SearchingLatch
          visible={latched}
          status={poolRankingStatus({ playersInRange, sportName })}
        />
      )}

      {/* `SH.saveav` — the questions the climb's own search raised, asked once the latch is off
          them. A **sibling** for the latch's reason: a `Modal` presents in its own window, and
          the screen root behind it says so itself. It carries the sport because the decline
          route takes one on every prompt, and the origin is the only thing that knows which.

          It stays mounted after it is answered rather than only while it is up, so `visible`
          going false has somewhere to hand focus back.

          `key` is the minted search id, so one climb is one question. */}
      {question === undefined ? null : (
        <PromptSheet
          key={question.search}
          visible={asking}
          raised={question.raised}
          sport={question.sport}
          returnFocusTo={standingStatement}
          onAnswered={() => recordAsked(question.sport, question.raised.prompt)}
        />
      )}
    </>
  );
}

/**
 * The handle a row carries, or nothing.
 *
 * A seated player whose row the record no longer holds has no name to print — a withheld row
 * carries one field and no card — so the sentence answers the unknown's own word rather than
 * inventing one, which is the same answer the court's seat gives.
 */
function nameOf(
  rows: readonly Candidate[],
  playerId: string,
): { readonly kind: 'player'; readonly name: string } | undefined {
  const name = rows.find((row) => row.playerId === playerId)?.card.name;
  return name === undefined ? undefined : { kind: 'player', name };
}

const s = StyleSheet.create({
  root: { flex: 1 },
  failure: { gap: theme.space.sm },
  sorts: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  rung: { gap: theme.space.xxs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  centred: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
