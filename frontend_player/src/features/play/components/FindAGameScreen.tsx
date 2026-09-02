/**
 * **Find a game** — the screen behind ⚡, and the whole of what a search is asked for.
 *
 * A sport, a mode, a week and a radius, and a control that runs one
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)). Four facts, and **each of them has
 * a different lifetime**, which is the one thing about this screen that is easy to get wrong:
 *
 * | On screen | Where it lives | Written back |
 * | --- | --- | --- |
 * | sport | `playPreferences` — the process | never |
 * | mode | `playPreferences` — the process | never |
 * | the week | `playSession` — the visit | never; it travels as `availability_override` |
 * | the radius | route-local, over the profile's | **on the search**, because the wire has no per-search radius |
 *
 * The first three are Play's own and the fourth is the profile's, and the asymmetry is not a
 * loose end: `RunSearchRequest` carries no radius and never will — *"a radius supplied by a
 * phone is a gate evaluated on a lie"* — so the only way a slider here can mean anything is
 * for the profile to hold what it shows before the search runs. `use-cases/findAGame` is where
 * that is sequenced and argued.
 *
 * ## The two seeds happen on entry, and neither happens during a render
 *
 * §G6 bug #5 is the prototype *"rendering the screen mutates state"* — the grid cloned inside
 * its own render — and the fix it names is *"seed the grid on navigation, not on render."*
 * Both doors into Play **replace** the stack and the reset empties `playSession`, so an entry
 * is a well-defined moment; what this screen adds is that the profile is a network read, so
 * the moment is *when the read lands* rather than *when the component mounts*. Both seeds are
 * effects and both are guarded — the week's on the working copy being absent, the mode's by
 * `seedIfAbsent` itself — so a refetch cannot reclaim a week a player has been editing or put
 * them back on the sport they arrived on.
 *
 * ## The wait is a latch over this screen, and never a route
 *
 * `SearchingLatch` is drawn as a **sibling of the screen root** while the search is in flight
 * and for as long afterwards as the floor stands
 * ([#269](https://github.com/Raketa02/Raketa/issues/269)). It is not a destination, so this
 * screen keeps its place underneath it and there is nothing to go back to — which is what
 * dissolved the prototype's *no back button and no escape*: the wait ends on the response, and
 * a refusal ends it over the court card that failed.
 *
 * **Two states are not a wait, and both would otherwise strand a player under it.** A refusal
 * has nothing to hold for, and a **paused** mutation is not in flight at all —
 * `networkMode: 'online'` holds the request until the connection returns, so a latch bound to
 * `isPending` alone would cover the screen for as long as the player is offline, in front of
 * the amber sentence saying the search resumes.
 *
 * ## Where a completed search goes, and when
 *
 * **Through the sheet, where the search raised a question.** `SH.saveav` asks it after the
 * latch lifts and before the court is pushed ([#275](https://github.com/Raketa02/Raketa/issues/275)):
 * the prompts ride on the search's own response, so *"it never blocks"* is arithmetic rather
 * than an ordering a screen remembers — the search has run before there is anything to ask.
 * What the sheet stands in front of is the **court**, and it stands there because the three
 * values these questions are about — the week, the radius and the declaration — are all edited
 * on *this* screen. **Dismissing it is a decline and is written like any other answer**, and
 * one prompt's *yes* keeps the player here rather than going on: `REFRESH_YOUR_TIMES` carries
 * no value to write, so accepting it is a request for the grid.
 *
 * The **builder**, pushed with the id the search just minted
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)) — and pushed **when the latch
 * lifts**, not when the mutation succeeds. The two are different moments and the difference is
 * the whole of what the latch is: it is *over the screen that launched it*, so the beat that
 * holds the count belongs to this screen and the court is what the wait lifts onto. Pushing on
 * the response instead would put the court under the latch, and the number the wait exists to
 * print would be drawn over a screen the player has already left.
 *
 * The push is the screen's rather than the hook's for the same reason: the navigation and the
 * wait are one arrangement, and only the component holding both can keep them in step.
 *
 * ## What is deliberately not here
 *
 * **The origin guard's confirmation.** `changingSport` and `changingMode` are the two triggers
 * this screen owns, and both answer *go* until a line-up exists — which nothing on this branch
 * can yet build. The modal lands with the screens that can seat somebody
 * ([#271](https://github.com/Raketa02/Raketa/issues/271),
 * [#272](https://github.com/Raketa02/Raketa/issues/272)), which is also where it can be driven
 * by a test rather than only by a unit call.
 *
 * **A back control.** *Back from Find a game leaves Play entirely* is a fact about the
 * **stack** — Now is underneath, put there by the reset — so the platform's own gesture already
 * lands where it should and 10.3 makes the chevron opt-in for exactly this case.
 *
 * **A pinned CTA.** `ShellScreen`'s action slot is empty here, and the search runs off
 * `CourtEntryCard` at the foot of the page instead. The control *is* a picture of the court
 * the search opens onto — which is what a player is actually asking for, and what a button
 * saying *Search* left as a surprise — and a card-sized control pinned above the tab bar would
 * take a third of the screen off the week it is drawn from. It is the one way through for a
 * competitive game; *Match me* is the other half of `PlaySegment` and reaches the deck.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import { sportLabel, useSkillRatings } from '@/features/onboarding/types';
import {
  RADIUS_LABEL,
  radiusAtFraction,
  radiusFigure,
  radiusFraction,
  radiusWords,
  spokenRadius,
  steppedRadius,
  topOfScale,
  useChangeSearchRadius,
  useProfileOptions,
  useProfileSurface,
  widestRadiusFigure,
} from '@/features/player_profile/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import {
  AvailabilityGrid,
  Button,
  Note,
  RadiusSlider,
  behindOverlay,
  courtSeatCount,
  theme,
} from '@/shared/ui';
import { dayLabel, dayPartHead } from '@/shared/vocabulary/availabilityPresentation';
import { DAY_PARTS, WEEKDAYS } from '@/shared/vocabulary/week';

import { findAGameStanding } from '../domain/findAGame';
import { SEARCH_MODES } from '../domain/vocabulary';
import { differsFromProfile, isTicked, sameCell } from '../domain/workingWeek';
import { useOutstandingInterest } from '../hooks/useDeck';
import { useFindAGame } from '../hooks/useFindAGame';
import type { FindAGameAsk } from '../use-cases/findAGame';
import { usePlayPreferences } from '../store/playPreferences.store';
import { usePlaySession } from '../store/playSession.store';

import { BUILDER_ROUTE } from './BuilderScreen';
import { CourtEntryCard } from './CourtEntryCard';
import { DeclarationInterstitial } from './DeclarationInterstitial';
import { searchWeekCellLabel } from './accessibilityPresentation';
import { PromptSheet, type AfterThePrompt } from './PromptSheet';
import { SportChips } from './SportChips';
import { useHeldWait } from './heldWait';
import { PlaySegment } from './PlaySegment';
import { playErrorMessage } from './playErrorMessage';
import { SearchingLatch } from './SearchingLatch';
import { poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';
import {
  FIND_A_GAME_TITLE,
  LOADING_PROFILE_LABEL,
  MODE_HEADING,
  NO_RATED_SPORT_LINE,
  NOBODY_IS_CONTACTED_BY_SEARCHING,
  RADIUS_IS_YOUR_PROFILE,
  RETRY_READ_LABEL,
  WEEK_HEADING,
  modeControlLabel,
  modeLabel,
  searchControlLabel,
  weekFootnote,
} from './findAGamePresentation';

export function FindAGameScreen() {
  const profileSurface = useProfileSurface();
  const ratings = useSkillRatings();
  const options = useProfileOptions();

  const sport = usePlayPreferences((state) => state.sport);
  const mode = usePlayPreferences((state) => state.mode);
  const chooseSport = usePlayPreferences((state) => state.chooseSport);
  const chooseMode = usePlayPreferences((state) => state.chooseMode);
  const seedIfAbsent = usePlayPreferences((state) => state.seedIfAbsent);

  const week = usePlaySession((state) => state.week);
  // `addedCell` here rather than the store's own name: this screen asks *is this the cell* of
  // each of twenty-one squares, and the answer it hands the grid is a boolean of the same name.
  const addedCell = usePlaySession((state) => state.addedForThisSearch);
  const clearAddedForThisSearch = usePlaySession((state) => state.clearAddedForThisSearch);
  const enter = usePlaySession((state) => state.enter);
  const toggleWeekCell = usePlaySession((state) => state.toggleWeekCell);

  /**
   * The radius the player is looking at, **before it is the profile's** — and only until then.
   *
   * Route-local because nothing has been written yet: leaving without searching discards it,
   * which is the truthful behaviour for a control whose value only reaches the server as the
   * first half of pressing the card. It is deliberately **not** a third Play store — a value
   * that outlived the screen would be a distance the profile does not hold and the next search
   * would silently save.
   *
   * **It is dropped the moment a search lands**, and that is the half that is easy to miss.
   * The write path re-checks the range and the step and answers with the radius *as the
   * profile now holds it*, which `useChangeSearchRadius` puts in the cache — so a chosen value
   * left standing would shadow the server's own correction, draw a distance the profile does
   * not hold, and re-send the corrected-away number on every later search. Clearing it hands
   * the slider back to the profile, which is where the answer now is.
   */
  const [chosenRadiusKm, setChosenRadiusKm] = useState<number | undefined>(undefined);

  /**
   * Where the prompt sheet returns focus to — **the week**, which is what it is about.
   *
   * Part 13 returns a listener to the control that opened a modal; this one is opened by an
   * *answer* rather than by a press, so there is no trigger and the grid is the honest
   * target: three of the four questions are about a value edited on this screen, and the
   * fourth's *yes* is a request for this very control.
   */
  const weekSection = useRef<View | null>(null);

  const search = useFindAGame();
  const radiusWrite = useChangeSearchRadius();
  /**
   * The **Match me count**, for the segment above — and the one read on this screen that is
   * allowed to move on its own.
   *
   * It is not gated on anything: a count that failed or has not landed simply draws no count,
   * which is the same thing the segment says at nought. There is nothing to retry and nothing
   * to report, because the number labels the *other* half of the control.
   */
  const interest = useOutstandingInterest();

  const profile = profileSurface.data;
  const bounds = options.data?.searchRadius;
  const radiusKm = chosenRadiusKm ?? profile?.searchRadiusKm;

  const rated = useMemo(() => (ratings.data ?? []).map((rating) => rating.sport), [ratings.data]);
  const standing = findAGameStanding(rated, sport, profile?.playIntents ?? {});
  const sportName = standing.kind === 'no-rated-sport' ? undefined : sportLabel(standing.sport);
  /**
   * The count on the segment, **filtered by the sport on screen**, so the number labels the
   * deck it sits above. An absent entry is *nothing outstanding there*, which is nought.
   */
  const outstandingHere =
    standing.kind === 'no-rated-sport' ? 0 : (interest.data?.[standing.sport] ?? 0);

  /**
   * Fill the grid in from the profile — **once, when the read lands.**
   *
   * `enter` is unconditional by design, so the guard is here: the reset has already emptied
   * the store, which makes an absent working copy the definition of *this visit has not
   * started*. Without it every profile refetch would throw away a week being edited.
   */
  useEffect(() => {
    if (week !== undefined || profile === undefined) return;
    enter(profile.week);
  }, [week, profile, enter]);

  /**
   * Open the mode on the declaration — through `mode_for_intent`, and only the first time.
   *
   * `seedIfAbsent` is the guard rather than this call site, because *"a player who switched to
   * tennis"* must not be put back on padel by arriving from ⚡ again. The mode is seeded from
   * the sport the screen opens on and is **never re-seeded**: a toggle re-derived from the
   * declaration would agree with it on every first search, and ADR-0094's drift backstop —
   * written for the sticky-tab case — would have nothing left to catch.
   */
  useEffect(() => {
    if (profile === undefined || standing.kind === 'no-rated-sport') return;
    seedIfAbsent(standing.sport, profile.playIntents[standing.sport]);
  }, [profile, standing, seedIfAbsent]);

  const reads = [profileSurface, ratings, options];
  const readsPaused = reads.some((read) => read.fetchStatus === 'paused' && !read.isSuccess);
  const readError = profileSurface.error ?? ratings.error ?? options.error;
  const ready = profile !== undefined && bounds !== undefined && radiusKm !== undefined;

  /**
   * The Sport's own seat count, and `undefined` where there is no Sport to count.
   *
   * Read off `Court`'s coordinates rather than stated here — *"the seat count is the Sport"* —
   * because every sentence on the card below branches on it and a four written down beside a
   * court would be the one place a squash court gets told to build one.
   */
  const seats = standing.kind === 'no-rated-sport' ? undefined : courtSeatCount(standing.sport);
  const searchLabel = seats === undefined ? undefined : searchControlLabel(standing, { seats });

  /**
   * The wait — up because a request is in flight, then holding the answer long enough to read.
   *
   * `useHeldWait` is bound to the act and the floor runs **after** it, so the count off the
   * response is drawn for the same beat whether the search took fifty milliseconds or five
   * seconds. Nothing here delays a request. The pool's floor takes no collapse and is not
   * offered one: a held screen is not an animation, so there is nothing for reduced motion to
   * skip and no question to put to the OS (`searchingWait`).
   *
   * The two subtractions are the two states that are not a wait. A **refusal** has nothing to
   * hold for — the sentence and the retry are already over the court card below — and a
   * **paused** write is not in flight at all: `networkMode: 'online'` holds it until the
   * connection returns, and a latch over that would bury the amber sentence that says so under
   * a screen with no way off it.
   */
  const writesPaused = search.isPaused || radiusWrite.isPaused;
  const held = useHeldWait(search.isPending && !writesPaused, searchingFloorMs({ kind: 'pool' }));
  const latched = held && !writesPaused && search.error === null;

  /**
   * The count, and the only shape it can arrive in.
   *
   * `undefined` until the search has succeeded, so the latch's first phase has a headline and
   * nothing to print — §B14's number came off a timer before the response existed, and this is
   * that fixed as a type rather than as a rule (#269).
   */
  const playersInRange = search.isSuccess ? search.data.playersInRange : undefined;

  const minted = search.isSuccess ? search.data.record.searchId : undefined;

  /**
   * **The question this search raised, and the beat it is asked in.**
   *
   * The **first** prompt and never a stack of them: the response orders them in the
   * vocabulary's own order precisely so *"a client rendering the first one it understands gets
   * the same one twice for the same search"* (`run_shortlist_search._raised`).
   *
   * It is asked **after the latch and before the court**, which is this screen's arrangement
   * and the reason the push below is not simply bound to the response. *It never blocks* is
   * about the search, and the search has already run — what the sheet stands in front of is
   * the court, on the screen the question is about: the week, the radius and the declaration
   * are all edited here, and a sheet asking about them over the builder would be a question
   * about a screen the player had already left.
   *
   * Keyed by the **search id**, so a second search asks again and a re-render of a screen the
   * player has come back to asks nothing.
   */
  const [answer, setAnswer] = useState<{
    readonly searchId: string;
    readonly next: AfterThePrompt;
  }>();
  const answeredThis = answer?.searchId === minted ? answer : undefined;
  const raised = search.isSuccess ? search.data.prompts[0] : undefined;
  const asking = !latched && answeredThis === undefined ? raised : undefined;

  /**
   * **The wait lifts onto the court** — once there is nothing left to ask, and unless the
   * player asked to be handed back to their week instead.
   *
   * The id is the effect's dependency rather than the success flag, so a second search pushes
   * a second court and a re-render of a screen the player has come back to pushes nothing: a
   * search that already sent somebody to the builder has the same id it had then. Leaving Play
   * while the latch is up unmounts this screen and pushes nothing at all, which is correct —
   * the reset has ended the session the court would have been built in.
   */
  const mayGoOn = raised === undefined || answeredThis?.next === 'carry-on';
  useEffect(() => {
    if (minted === undefined || latched || !mayGoOn) return;
    router.push({ pathname: BUILDER_ROUTE, params: { search: minted } });
  }, [minted, latched, mayGoOn]);

  /**
   * The comparison, made **once** and read twice.
   *
   * The marker under the grid and the override on the request are the same question — *is this
   * the week the profile holds* — and two call sites comparing two weeks each is two chances
   * to compare a different pair. It is a comparison rather than a flag a toggle sets, which is
   * what makes a slot ticked and unticked stop reporting itself as changed.
   */
  const improvised =
    week !== undefined && profile !== undefined && differsFromProfile(week, profile.week);

  /**
   * **The ask, or the absence of one** — and therefore the one place *may this search run* is
   * decided.
   *
   * Both halves used to be spelled out twice, once in a `disabled={…}` and once as a guard at
   * the top of the press handler, which is the shape the profile commit's `mayFinish` exists
   * to refuse: *a rule, not a `disabled` expression*. Built as a value, the control has
   * nothing left to decide — it is enabled when there is something to send.
   */
  const ask: FindAGameAsk | undefined =
    profile !== undefined &&
    week !== undefined &&
    radiusKm !== undefined &&
    standing.kind === 'searchable'
      ? {
          origin: { sport: standing.sport, mode, week },
          // `undefined` is what makes the request omit the override entirely rather than send
          // a grid the profile already holds.
          sentWeek: improvised ? week : undefined,
          radiusKm,
          profileRadiusKm: profile.searchRadiusKm,
          quotes: { sportName: sportLabel(standing.sport), profileWeek: profile.week },
        }
      : undefined;

  return (
    <>
      {/* Both overlays are **siblings** of the screen they cover, never children:
          `behindOverlay` hides everything inside the element carrying it, and an overlay
          rendered in there would hide itself along with the screen. The wrapper exists only to
          carry those two props, because `ShellScreen` takes none — `ResultScreen` spreads them
          on its own `SafeAreaView` and needs no wrapper at all. */}
      <View style={s.root} {...behindOverlay(latched || asking !== undefined)}>
        <ShellScreen title={FIND_A_GAME_TITLE}>
          {/* Paused, not loading: `networkMode: 'online'` holds a query rather than failing it,
              so an offline player would otherwise watch a spinner forever. */}
          {readsPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

          {!ready && !readsPaused && readError === null ? (
            <ActivityIndicator
              accessibilityLabel={LOADING_PROFILE_LABEL}
              color={theme.color.muted}
            />
          ) : null}

          {readError !== null ? (
            <View style={s.failure}>
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(readError)}
              </Note>
              <Button
                label={RETRY_READ_LABEL}
                variant="secondary"
                onPress={() => {
                  void profileSurface.refetch();
                  void ratings.refetch();
                  void options.refetch();
                }}
              />
            </View>
          ) : null}

          {/* Play's two ways through the tab. It is drawn on both screens rather than in the
              shell, because the count on it is sport-filtered and the sport is this screen's
              ([#270](https://github.com/Raketa02/Raketa/issues/270)). */}
          <PlaySegment active="find" outstanding={outstandingHere} />

          {standing.kind === 'no-rated-sport' && ratings.isSuccess ? (
            <Note>{NO_RATED_SPORT_LINE}</Note>
          ) : null}

          {standing.kind === 'no-rated-sport' ? null : (
            <SportChips rated={rated} selected={standing.sport} onChoose={chooseSport} />
          )}

          {standing.kind === 'no-rated-sport' ? null : (
            <View style={s.section}>
              <Text style={s.heading}>{MODE_HEADING}</Text>
              <View style={s.answers}>
                {SEARCH_MODES.map((offered) => (
                  <Button
                    key={offered}
                    label={modeLabel(offered)}
                    accessibilityLabel={modeControlLabel(offered)}
                    variant={offered === mode ? 'dark' : 'secondary'}
                    selected={offered === mode}
                    onPress={() => chooseMode(offered)}
                  />
                ))}
              </View>
            </View>
          )}

          {/* ADR-0094's one-tap interstitial: *permanent, not a migration path*. It is what makes
              every searcher having declared true rather than intended, and it is opened here
              knowingly — before `play_intent_not_declared` refuses — because the profile read
              carries only what was declared and the difference is free. The deck is refused by
              the same code and draws the same question, so the block is a component. */}
          {standing.kind === 'undeclared' && sportName !== undefined ? (
            <DeclarationInterstitial
              sport={standing.sport}
              sportName={sportName}
              declaredOn="SEARCH_SWITCH"
            />
          ) : null}

          {week === undefined || profile === undefined ? null : (
            <View style={s.section} ref={weekSection}>
              <Text style={s.heading}>{WEEK_HEADING}</Text>
              <AvailabilityGrid
                columnHeads={DAY_PARTS.map(dayPartHead)}
                // Two facts, one sentence, decided in the copy deck: the marker is a comparison
                // against the profile's own week made on every tap — not a flag a toggle sets,
                // which is what makes a slot ticked and unticked stop reporting itself as
                // changed — and the plus is the cell a rung added to the search that ran.
                // Neither is `KEEP_THESE_TIMES`, which compares the post-rung grid a search
                // actually ran on and only the backend can compute.
                footnote={weekFootnote({ improvised, addedForThisSearch: addedCell !== undefined })}
                rows={WEEKDAYS.map((day) => ({
                  key: String(day),
                  label: dayLabel(day),
                  cells: DAY_PARTS.map((part) => {
                    const cell = { day, part };
                    // A cell the player never ticked, standing for this search alone. Pressing
                    // it is an ordinary tick — and the store drops the mark on that press,
                    // because from then on the cell is the player's own ask.
                    const added = addedCell !== undefined && sameCell(addedCell, cell);

                    return {
                      key: `${day}-${part}`,
                      selected: isTicked(week, cell),
                      addedForThisSearch: added,
                      onPress: () => toggleWeekCell(cell),
                      accessibilityLabel: searchWeekCellLabel(cell, added),
                    };
                  }),
                }))}
              />
            </View>
          )}

          {bounds === undefined || radiusKm === undefined ? null : (
            <View style={s.section}>
              <Text style={s.heading}>{RADIUS_LABEL}</Text>
              <Text style={s.body}>{RADIUS_IS_YOUR_PROFILE}</Text>
              <RadiusSlider
                value={radiusKm}
                minimum={bounds.minimumKm}
                maximum={topOfScale(bounds)}
                fraction={radiusFraction(radiusKm, bounds)}
                onSlideTo={(fraction) => setChosenRadiusKm(radiusAtFraction(fraction, bounds))}
                onIncrement={() => setChosenRadiusKm(steppedRadius(radiusKm, bounds, 'increment'))}
                onDecrement={() => setChosenRadiusKm(steppedRadius(radiusKm, bounds, 'decrement'))}
                figure={radiusFigure(radiusKm)}
                widestFigure={widestRadiusFigure(bounds)}
                words={radiusWords(radiusKm)}
                accessibilityLabel={RADIUS_LABEL}
                accessibilityValueText={spokenRadius(radiusKm)}
              />
            </View>
          )}

          {/* **The way onto the court**, and the whole of the act this screen offers.
              It is in the page rather than in `ShellScreen`'s pinned slot: the control is a
              picture of the court a search opens, and a court pinned above the tab bar would
              be a CTA the height of a card standing over the week it is drawn from. */}
          {standing.kind === 'no-rated-sport' ||
          searchLabel === undefined ||
          seats === undefined ||
          sportName === undefined ? null : (
            <View style={s.section}>
              {/* The failed act's own control is the retry — `retryTarget`'s *the-search*, since
                  nothing was minted and there is no record to re-read. So the sentence goes
                  above the control that already exists rather than beside a second one. */}
              {search.error !== null ? (
                <Note variant="coral" accessibilityRole="alert">
                  {playErrorMessage(search.error)}
                </Note>
              ) : null}
              {writesPaused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

              <CourtEntryCard
                sport={standing.sport}
                sportName={sportName}
                seats={seats}
                label={searchLabel}
                disabled={ask === undefined}
                onPress={() => {
                  if (ask === undefined) return;
                  // This search cites no offer, so it runs on the week above and nothing
                  // else: the cell a rung added belonged to the list it widened, and from
                  // here on the mark would be about a search nobody is holding (#283).
                  clearAddedForThisSearch();
                  // The chosen radius has done its job: the profile now holds whatever the
                  // server made of it, and the slider reads that from here on.
                  search.mutate(ask, { onSuccess: () => setChosenRadiusKm(undefined) });
                }}
              />

              {/* True of both halves of Play, and the last word the screen says. */}
              <Text style={s.footnote}>{NOBODY_IS_CONTACTED_BY_SEARCHING}</Text>
            </View>
          )}
        </ShellScreen>
      </View>

      {/* A screen with no sport to search in has no search, and therefore no wait. */}
      {sportName === undefined ? null : (
        <SearchingLatch
          visible={latched}
          status={poolRankingStatus({ playersInRange, sportName })}
        />
      )}

      {/* A **sibling** for the latch's reason — a `Modal` presents in its own window, and the
          screen root behind it says so itself. It carries the sport because the decline route
          takes one on every prompt and only this screen knows which chip the search ran on.

          It is **mounted for as long as the search that raised it**, rather than only while it
          is up: `visible` going false is what returns focus to the grid, and a sheet that
          unmounted instead would drop a listener at the top of the screen.

          `key` is the search id, so one sheet is one question. It is a statement of that rule
          rather than the mechanism behind it — a second search is pending before it succeeds,
          which already takes `raised` away and unmounts this — and the rule is what the sheet's
          *answered once* guard depends on. */}
      {raised === undefined || minted === undefined || standing.kind !== 'searchable' ? null : (
        <PromptSheet
          key={minted}
          visible={asking !== undefined}
          raised={raised}
          sport={standing.sport}
          returnFocusTo={weekSection}
          onAnswered={(next) => setAnswer({ searchId: minted, next })}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  failure: { gap: theme.space.sm },
  failureLine: { ...theme.type.tiny, color: theme.color.coralInk },
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  body: { ...theme.type.tiny, color: theme.color.ink },
  answers: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  footnote: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
