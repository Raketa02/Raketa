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

import { sportLabel } from '@/features/onboarding/types';
import { useProfileSurface } from '@/features/player_profile/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage } from '@/shared/errors';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { playerName } from '@/shared/formatting/playerName';
import {
  BALANCE_INK,
  Button,
  Card,
  Chip,
  Note,
  behindOverlay,
  courtSeatCount,
  theme,
} from '@/shared/ui';

import type { Candidate, RelaxedAsk, RungOffer } from '../domain/candidate';
import { arrangementFor, seatOccupant, seatingToDraw } from '../domain/forecast';
import { poolLadder } from '../domain/poolLadder';
import { orderPool, pickable, poolSortRow } from '../domain/poolOrder';
import type { SortOption } from '../domain/vocabulary';
import { sentWeekForOrigin } from '../domain/workingWeek';
import { useForecast, useSearchRecord } from '../hooks/useBuilder';
import { useReadSearchBack, useTakeRung } from '../hooks/usePool';
import { usePlaySession } from '../store/playSession.store';

import { rungOfferLabel } from './accessibilityPresentation';
import { balanceTone, balanceWord } from './balancePresentation';
import { builderEyebrow } from './builderPresentation';
import { CandidateCard } from './candidate/CandidateCard';
import { CandidateCardSocial } from './candidate/CandidateCardSocial';
import { useHeldWait } from './heldWait';
import { playErrorMessage } from './playErrorMessage';
import {
  POOL_FORECAST_HEADING,
  POOL_LADDER_BODY,
  POOL_LINEUP_COST,
  POOL_NO_RECORD_BODY,
  POOL_NO_RECORD_TITLE,
  POOL_TITLE,
  READING_AGAIN_LABEL,
  READ_AGAIN_LABEL,
  poolLadderTitle,
  replacingLine,
  rungCount,
  takenRungLine,
  terminalReachLine,
  zeroRungLine,
} from './poolPresentation';
import { SearchingLatch } from './SearchingLatch';
import {
  forecastAssumption,
  poolDescription,
  relaxationOffer,
  sortLabel,
} from './searchPresentation';
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

  const record = useSearchRecord(searchId);
  const reread = useReadSearchBack();
  const climb = useTakeRung();

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

  const drawn = orderPool(pickable(record?.candidates ?? [], members), sort);

  const ladder = poolLadder({
    rows: record?.candidates.length ?? 0,
    offers: record?.envelope.rungOffers ?? null,
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
  const sentWeek = origin === undefined ? undefined : sentWeekForOrigin(origin.week, profile?.week);

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
   * Add somebody, discharging the replacement if this visit was against an occupied seat.
   *
   * Nobody drawn here is on the court — `pickable` took them out — so the person leaving the
   * seat is never the person arriving in it, and there is no self-replacement to guard against.
   */
  function add(candidate: Candidate) {
    if (replacing !== undefined) unseat(replacing);
    seatPlayer(searchId, candidate.playerId);
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
        quotes: { sportName, profileWeek: profile?.week ?? [] },
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
      <View style={s.root} {...behindOverlay(latched || explaining !== undefined)}>
        <ShellScreen
          title={POOL_TITLE}
          eyebrow={
            sportName === undefined || origin === undefined
              ? undefined
              : builderEyebrow({ sportName, seats, mode: origin.mode })
          }
        >
          {record === undefined || sportName === undefined ? (
            <Note title={POOL_NO_RECORD_TITLE}>
              <Text style={s.body}>{POOL_NO_RECORD_BODY}</Text>
            </Note>
          ) : (
            <>
              {/* What replaces *back*: the widening, and the profile it did not touch. */}
              {taken === undefined ? null : (
                <Note variant="info">
                  <Text style={s.body}>{takenRungLine(taken)}</Text>
                </Note>
              )}

              {/* The running forecast — **the one surface `provisional` is about**. The tinted
                  figure, §B9's balance word beneath it because Part 13 forbids colour alone,
                  and the assumption as the sentence under both. */}
              {chosen === undefined ? null : (
                <Card>
                  <Text style={s.eyebrow}>{POOL_FORECAST_HEADING}</Text>
                  <Text
                    style={[s.figure, { color: BALANCE_INK[balanceTone(chosen.forecast.pct)] }]}
                  >
                    {formatPercent(chosen.forecast.pct)}
                  </Text>
                  <Text style={s.word}>{balanceWord(chosen.forecast.pct)}</Text>
                  {chosen.forecast.assumption === null ? null : (
                    <Text style={s.body}>{forecastAssumption(chosen.forecast.assumption)}</Text>
                  )}
                </Card>
              )}

              <Text style={s.body}>{poolDescription({ ...record.envelope.pool, sportName })}</Text>

              {/* Said rather than assumed: the court is one screen away, so a silent swap of
                  one handle for another is a destruction found out about afterwards. */}
              {replacing === undefined ? null : (
                <Text style={s.body}>
                  {replacingLine(
                    playerName(nameOf(record.candidates, replacing) ?? { kind: 'unknown' }),
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
                    action="ADD_TO_COURT"
                    onAction={() => add(candidate)}
                    onWhyFit={() => setExplaining(candidate)}
                  />
                ) : (
                  <CandidateCardSocial
                    key={candidate.playerId}
                    candidate={candidate}
                    envelope={record.envelope}
                    action="ADD_TO_COURT"
                    onAction={() => add(candidate)}
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
          name={playerName({ kind: 'player', nickname: explaining.card.nickname })}
        />
      )}

      {sportName === undefined ? null : (
        <SearchingLatch
          visible={latched}
          status={poolRankingStatus({ playersInRange, sportName })}
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
): { readonly kind: 'player'; readonly nickname: string } | undefined {
  const nickname = rows.find((row) => row.playerId === playerId)?.card.nickname;
  return nickname === undefined ? undefined : { kind: 'player', nickname };
}

const s = StyleSheet.create({
  root: { flex: 1 },
  failure: { gap: theme.space.sm },
  sorts: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  rung: { gap: theme.space.xxs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  centred: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
});
