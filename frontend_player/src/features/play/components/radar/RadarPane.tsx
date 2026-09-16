/**
 * **Radar** — the second pane of Players: every player rated in your sport within your reach,
 * at their distance and bearing, with no judgement at all
 * ([ADR-0174](../../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md),
 * [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7).
 *
 * ## Its own frame, on the night
 *
 * The deck pane is a `ShellScreen` on paper. This pane is the same header — the *Deck | Radar*
 * toggle in the lead slot, the chip in the right one, the sport chips beneath where there is a
 * choice — over the app's **third dark surface**, with the field full-bleed under it and no
 * scroller at all: the field takes the drag, and a page that scrolled under a pan would be two
 * things following one finger. Mock 1 draws the toggle over the night too, and the mocks are
 * the design; the toggle, the chip and the chips take their on-dark repaints.
 *
 * ## The reading, and what the frame reads off it
 *
 * `useReading(sport)` — `POST /radar`, held five minutes, refetched on a pane opened past the
 * window, on a sport switch and on a cold start (`hooks/useReading`). The chip is the
 * reading's `pool.want_to_play_you`, **the deck's number by the deck's rule** (§5), through the
 * deck's own sentence, so the two panes never disagree. The reach the geometry is built on is
 * the profile's own radius, known before the reading lands, which is what lets the tile and
 * the rings draw at once under *Looking around…*; the empty sentence's reach is the pool's, as
 * the words say.
 *
 * ## The view is the store's, the selection is the store's, and both outlive this pane
 *
 * `store/radarView` keeps where the radar was left for the life of the process, across the
 * toggle and across tabs; this pane reads it, hands it to the field, and writes back where a
 * gesture, a ±, a flight or ◉ ended. The selection is kept **by sport**, so a sport switch
 * clears it by construction and keeps the view; a selected player absent from the next reading
 * is deselected silently at read (`domain/reading`'s `selectionOn`).
 *
 * ## The card opens the record, read-only, until #464
 *
 * A tap on a card opens `PlayerRecordSheet` exactly as the deck's *i* does — the subject, the
 * sport, the distance, the reader's own area off the envelope and the overlap by the deck's
 * own function — and the record's fit row hands over to `WhyFitSheet` with the reading's
 * envelope. The sheet's foot — *Not today* · *Let's play* and the standing relation — is
 * [#464](https://github.com/Raketa02/Raketa/issues/464)'s; nothing here answers anybody.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import { PlayerRecordSheet, useOwnFace } from '@/features/player_record/types';
import { playerName } from '@/shared/formatting/playerName';
import { Note, ScreenHeader, behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { selectionOn, type RadarRow } from '../../domain/reading';
import { socialTagOverlap } from '../../domain/socialTagOverlap';
import { useReading } from '../../hooks/useReading';
import { selectedIn, useRadarView } from '../../store/radarView.store';
import { DeckPill } from '../DeckPill';
import { PlayersToggle } from '../PlayersToggle';
import { SportChips } from '../SportChips';
import { NO_RATED_SPORT_LINE, wantToPlayYouChip, type PlayersPane } from '../deckPresentation';
import { WhyFitSheet } from '../whyfit/WhyFitSheet';

import { RadarField, type RadarStatus } from './RadarField';
import { RadarGround } from './RadarGround';

export interface RadarPaneProps {
  readonly onPane: (pane: PlayersPane) => void;
  /** The sports the player is rated in, the registry's order — the chips, where there are two. */
  readonly rated: readonly Sport[];
  /** The sport the pane is on, or nothing for a player rated in none. */
  readonly sport: Sport | undefined;
  readonly onChooseSport: (sport: Sport) => void;
  /** The profile's own search radius — the reach. Undefined until the profile has landed. */
  readonly reachKm: number | undefined;
}

export function RadarPane({ onPane, rated, sport, onChooseSport, reachKm }: RadarPaneProps) {
  const me = useCurrentUser().data?.id;
  const own = useOwnFace(me);
  const reading = useReading(sport);

  const view = useRadarView((state) => state.view);
  const selection = useRadarView((state) => state.selection);
  const setView = useRadarView((state) => state.setView);
  const select = useRadarView((state) => state.select);
  const deselect = useRadarView((state) => state.deselect);
  const goHome = useRadarView((state) => state.goHome);

  /** The row the record sheet is open over, and the one the Fit sheet is. */
  const [opened, setOpened] = useState<RadarRow | undefined>(undefined);
  const [explaining, setExplaining] = useState<RadarRow | undefined>(undefined);
  const root = useRef<View>(null);

  const rows = reading.data?.rows;
  const held = selectedIn(selection, sport);
  const selectedId = selectionOn(rows ?? [], held);

  // *A selected player absent from the next reading is deselected silently* (§7.5): the store
  // lets go of them once a reading has answered without them, so a later reading that has
  // them again does not select them back.
  useEffect(() => {
    if (rows !== undefined && held !== undefined && selectedId === undefined) deselect();
  }, [rows, held, selectedId, deselect]);

  // A held reading is drawn whatever else is happening; with none held, a read on its way —
  // the first, or *Try again*'s — is *Looking around…*, and a refusal is the failure. The
  // refetch is read before the error, so the retry's own wait is not spent under the sentence
  // it is meant to answer.
  const status = useMemo<RadarStatus>(() => {
    if (reading.data !== undefined) {
      return {
        kind: 'read',
        rows: reading.data.rows,
        radiusKmUsed: reading.data.envelope.pool.radiusKmUsed,
      };
    }
    if (reading.isFetching) return { kind: 'loading' };
    if (reading.error !== null) return { kind: 'failed', onTryAgain: () => void reading.refetch() };
    return { kind: 'loading' };
  }, [reading]);

  const waiting = reading.data?.envelope.pool.wantToPlayYou ?? 0;
  const sportName = sport === undefined ? undefined : sportLabel(sport);
  const envelope = reading.data?.envelope;

  return (
    <>
      <View style={s.root} {...behindOverlay(opened !== undefined || explaining !== undefined)}>
        <SafeAreaView style={s.frame} edges={['top']} ref={root}>
          <RadarGround />

          <ScreenHeader
            lead={<PlayersToggle pane="radar" onSelect={onPane} onDark />}
            right={
              waiting > 0 ? (
                <DeckPill tone="volt">{wantToPlayYouChip(waiting)}</DeckPill>
              ) : undefined
            }
          />

          {sport === undefined ? (
            <View style={s.gutter}>
              <Note>{NO_RATED_SPORT_LINE}</Note>
            </View>
          ) : null}

          {sport !== undefined && rated.length >= 2 ? (
            <View style={s.gutter}>
              <SportChips rated={rated} selected={sport} onChoose={onChooseSport} onDark />
            </View>
          ) : null}

          {sport === undefined || sportName === undefined || reachKm === undefined ? (
            // Nothing to place anybody on yet: the profile's radius is the reach the field is
            // built on, and it is on its way. The ground and the header stand.
            <View style={s.waiting} />
          ) : (
            <RadarField
              status={status}
              reachKm={reachKm}
              sport={sport}
              sportName={sportName}
              me={
                me === undefined
                  ? undefined
                  : {
                      playerId: me,
                      ...(own.photoUrl === undefined ? {} : { photoUrl: own.photoUrl }),
                    }
              }
              view={view}
              selectedId={selectedId}
              onViewChange={setView}
              onHome={goHome}
              onSelect={(playerId) => select({ sport, playerId })}
              onDeselect={deselect}
              onOpenCard={setOpened}
            />
          )}
        </SafeAreaView>
      </View>

      {/* The record sheet, from a card — the deck's own arrangement with the reading's envelope
          in hand. Read-only here: the foot is #464's. */}
      {opened === undefined || envelope === undefined || sport === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setOpened(undefined)}
          subject={{ kind: 'player', playerId: opened.playerId }}
          sport={sport}
          distanceKm={opened.distanceKm}
          {...(envelope.myAreaCode === undefined ? {} : { viewerAreaCode: envelope.myAreaCode })}
          tagOverlap={socialTagOverlap(opened)}
          pairing={{
            fit: opened.fit,
            onExplain: () => {
              setOpened(undefined);
              setExplaining(opened);
            },
          }}
        />
      )}

      {explaining === undefined || envelope === undefined ? null : (
        <WhyFitSheet
          visible
          onClose={() => setExplaining(undefined)}
          candidate={explaining}
          envelope={envelope}
          name={playerName({ kind: 'player', name: explaining.card.name })}
          returnFocusTo={root}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  frame: { flex: 1, backgroundColor: theme.color.radarGroundEdge },
  gutter: { paddingHorizontal: theme.size.gutter },
  waiting: { flex: 1 },
});
