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
 * ## What is deliberately not here
 *
 * **Where a completed search goes.** The searching latch is bound to this response
 * ([#269](https://github.com/Raketa02/Raketa/issues/269)) and the builder behind it reads the
 * record ([#271](https://github.com/Raketa02/Raketa/issues/271)); a destination invented
 * before either exists is one this screen has to un-decide twice. What ships here is the act,
 * the record it leaves under `searchKeys.detail(id)`, and the questions it raises.
 *
 * **The prompt sheet.** `SH.saveav` is [#275](https://github.com/Raketa02/Raketa/issues/275)'s.
 * What this ticket owes it is the ordering, and the ordering is now **structural**: the
 * prompts come off the search's own response, so by the time there is anything to ask, the
 * search has already run. *"It never blocks"* is true by construction rather than by a screen
 * remembering to sequence a sheet after a request.
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
 */

import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

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
  useDeclarePlayIntent,
  useProfileOptions,
  useProfileSurface,
  widestRadiusFigure,
} from '@/features/player_profile/types';
import { ShellScreen } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { AvailabilityGrid, Button, Chip, Note, RadiusSlider, theme } from '@/shared/ui';
import { cellLabel, dayLabel, dayPartHead } from '@/shared/vocabulary/availabilityPresentation';
import { DAY_PARTS, WEEKDAYS } from '@/shared/vocabulary/week';

import { findAGameStanding } from '../domain/findAGame';
import { PLAY_INTENTS, SEARCH_MODES } from '../domain/vocabulary';
import { differsFromProfile, isTicked } from '../domain/workingWeek';
import { useFindAGame } from '../hooks/useFindAGame';
import type { FindAGameAsk } from '../use-cases/findAGame';
import { usePlayPreferences } from '../store/playPreferences.store';
import { usePlaySession } from '../store/playSession.store';

import { playErrorMessage } from './playErrorMessage';
import {
  DECLARATION_BODY,
  FIND_A_GAME_TITLE,
  LOADING_PROFILE_LABEL,
  MODE_HEADING,
  NO_RATED_SPORT_LINE,
  RADIUS_IS_YOUR_PROFILE,
  RETRY_READ_LABEL,
  SEARCHING_LABEL,
  SPORT_HEADING,
  WEEK_CHANGED_FROM_PROFILE,
  WEEK_HEADING,
  declarationOptionLabel,
  declarationTitle,
  intentLabel,
  modeControlLabel,
  modeLabel,
  searchControlLabel,
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
  const enter = usePlaySession((state) => state.enter);
  const toggleWeekCell = usePlaySession((state) => state.toggleWeekCell);

  /**
   * The radius the player is looking at, **before it is the profile's** — and only until then.
   *
   * Route-local because nothing has been written yet: leaving without searching discards it,
   * which is the truthful behaviour for a control whose value only reaches the server as the
   * first half of pressing *Search*. It is deliberately **not** a third Play store — a value
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

  const search = useFindAGame();
  const declare = useDeclarePlayIntent();
  const radiusWrite = useChangeSearchRadius();

  const profile = profileSurface.data;
  const bounds = options.data?.searchRadius;
  const radiusKm = chosenRadiusKm ?? profile?.searchRadiusKm;

  const rated = useMemo(() => (ratings.data ?? []).map((rating) => rating.sport), [ratings.data]);
  const standing = findAGameStanding(rated, sport, profile?.playIntents ?? {});
  const sportName = standing.kind === 'no-rated-sport' ? undefined : sportLabel(standing.sport);

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
  const paused = reads.some((read) => read.fetchStatus === 'paused' && !read.isSuccess);
  const readError = profileSurface.error ?? ratings.error ?? options.error;
  const ready = profile !== undefined && bounds !== undefined && radiusKm !== undefined;

  const searchLabel = searchControlLabel(standing);

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
          quotes: {
            sportName: sportLabel(standing.sport),
            slotsOnProfile: profile.week.length,
          },
        }
      : undefined;

  return (
    <ShellScreen
      title={FIND_A_GAME_TITLE}
      action={
        searchLabel === undefined ? undefined : (
          <View style={s.action}>
            {/* The failed act's own control is the retry — `retryTarget`'s *the-search*, since
                nothing was minted and there is no record to re-read. So the sentence goes
                above the button that already exists rather than beside a second one. */}
            {search.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {playErrorMessage(search.error)}
              </Note>
            ) : null}
            {search.isPaused || radiusWrite.isPaused ? (
              <Note variant="amber">{offlineMessage('resumes')}</Note>
            ) : null}

            <Button
              label={searchLabel}
              size="lg"
              disabled={ask === undefined}
              busy={search.isPending}
              busyLabel={SEARCHING_LABEL}
              onPress={() => {
                if (ask === undefined) return;
                // The chosen radius has done its job: the profile now holds whatever the
                // server made of it, and the slider reads that from here on.
                search.mutate(ask, { onSuccess: () => setChosenRadiusKm(undefined) });
              }}
            />
          </View>
        )
      }
    >
      {/* Paused, not loading: `networkMode: 'online'` holds a query rather than failing it,
          so an offline player would otherwise watch a spinner forever. */}
      {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      {!ready && !paused && readError === null ? (
        <ActivityIndicator accessibilityLabel={LOADING_PROFILE_LABEL} color={theme.color.muted} />
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

      {standing.kind === 'no-rated-sport' && ratings.isSuccess ? (
        <Note>{NO_RATED_SPORT_LINE}</Note>
      ) : null}

      {standing.kind === 'no-rated-sport' ? null : (
        <View style={s.section}>
          <Text style={s.heading}>{SPORT_HEADING}</Text>
          <View style={s.chips}>
            {rated.map((offered) => (
              <Chip
                key={offered}
                label={sportLabel(offered)}
                selected={offered === standing.sport}
                onPress={() => chooseSport(offered)}
              />
            ))}
          </View>
        </View>
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
          carries only what was declared and the difference is free. */}
      {standing.kind === 'undeclared' && sportName !== undefined ? (
        <Note title={declarationTitle(sportName)}>
          <Text style={s.body}>{DECLARATION_BODY}</Text>
          {declare.error !== null ? (
            <Text style={s.failureLine} accessibilityRole="alert">
              {playErrorMessage(declare.error)}
            </Text>
          ) : null}
          <View style={s.answers}>
            {PLAY_INTENTS.map((intent) => (
              <Button
                key={intent}
                label={intentLabel(intent)}
                accessibilityLabel={declarationOptionLabel(intent, sportName)}
                variant="secondary"
                disabled={declare.isPending}
                onPress={() =>
                  declare.mutate({ sport: standing.sport, intent, surface: 'SEARCH_SWITCH' })
                }
              />
            ))}
          </View>
        </Note>
      ) : null}

      {week === undefined || profile === undefined ? null : (
        <View style={s.section}>
          <Text style={s.heading}>{WEEK_HEADING}</Text>
          <AvailabilityGrid
            columnHeads={DAY_PARTS.map(dayPartHead)}
            // The marker is a comparison against the profile's own week, made on every tap —
            // not a flag a toggle sets, which is what makes a slot ticked and unticked stop
            // reporting itself as changed. It is not `KEEP_THESE_TIMES`, which compares the
            // post-rung grid a search actually ran on and only the backend can compute.
            footnote={improvised ? WEEK_CHANGED_FROM_PROFILE : undefined}
            rows={WEEKDAYS.map((day) => ({
              key: String(day),
              label: dayLabel(day),
              cells: DAY_PARTS.map((part) => ({
                key: `${day}-${part}`,
                selected: isTicked(week, { day, part }),
                onPress: () => toggleWeekCell({ day, part }),
                accessibilityLabel: cellLabel({ day, part }),
              })),
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
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  action: { gap: theme.space.sm },
  failure: { gap: theme.space.sm },
  failureLine: { ...theme.type.tiny, color: theme.color.coralInk },
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  body: { ...theme.type.tiny, color: theme.color.ink },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
  answers: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
