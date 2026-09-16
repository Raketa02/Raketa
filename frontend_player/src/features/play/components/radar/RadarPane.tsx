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
 * ## The card opens the record, and the record has a foot here
 *
 * A tap on a card opens `PlayerRecordSheet` exactly as the deck's *i* does — the subject, the
 * sport, the distance, the reader's own area off the envelope and the overlap by the deck's
 * own function — and the record's fit row hands over to `WhyFitSheet` with the reading's
 * envelope. **What the deck's sheet does not have is the foot** (ADR-0174 §4,
 * [#464](https://github.com/Raketa02/Raketa/issues/464)): `RadarSheetFoot` fills the sheet's
 * one slot with *Not today* and *Let's play*, or with the relation that already stands — a
 * liker's line above the two, the reader's own yes beside *Not today*, a match with its chat
 * door, a shared court's own line and no buttons. The foot reads the relation; this pane owns
 * what a press does.
 *
 * ## An answer from the sheet is the deck's, with the reading for its origin
 *
 * *Let's play* and *Not today* post through the deck's own use cases with the **reading's**
 * `search_id` (`hooks/useRadarAnswers`), and the same decision runs first: at the ceiling, a
 * yes on somebody who carries no `inclusion_reason` is withheld and the deck's own sentence is
 * said (`domain/yesBudget`, `CAP_REACHED_SENTENCE`); a liker's yes goes whatever the count.
 * **The sheet closes first, on every press** — a `Modal` would sit over the yes screen the
 * reply may push, and over the toast — and then the row is marked on the press: the card's last
 * line reads *You said yes ›* or *Not today ›*, the person stays on the radar, and a refusal
 * takes the mark back. The outcomes are the deck's, through the deck's own copy: a pass and a
 * one-sided yes are spoken, a mutual naming no chat is the one toast, and a mutual naming a
 * challenge is the yes screen, pushed by the mutation's own success and never from a callback
 * the closed sheet would drop. A refused answer's sentence, and the amber *resumes* while a
 * write is held offline, sit in the gutter under the header — the pane has no scroller for
 * them to sit above the card in.
 *
 * ## The chat door is pushed from here, after the sheet is down
 *
 * *Open the chat* on a matched foot names a room the conversations feature found for the
 * court; the pane closes the sheet and pushes `CONVERSATION_ROUTE`, for the reason above.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import { CONVERSATION_ROUTE } from '@/features/conversations/types';
import { sportLabel } from '@/features/onboarding/types';
import { PlayerRecordSheet, useOwnFace } from '@/features/player_record/types';
import { playerName } from '@/shared/formatting/playerName';
import { Note, ScreenHeader, behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { selectionOn, type RadarAnswer, type RadarRow } from '../../domain/reading';
import { socialTagOverlap } from '../../domain/socialTagOverlap';
import { yesesToGive } from '../../domain/yesBudget';
import { useOutstandingInterest } from '../../hooks/useInterest';
import { useRadarNo, useRadarYes } from '../../hooks/useRadarAnswers';
import { useReading } from '../../hooks/useReading';
import { selectedIn, useRadarView } from '../../store/radarView.store';
import { AnswerNotes } from '../AnswerNotes';
import { DeckPill } from '../DeckPill';
import { PlayersToggle } from '../PlayersToggle';
import { SportChips } from '../SportChips';
import { sayPassed, sayYesOutcome, withheldAtTheCap } from '../answerFeedback';
import { NO_RATED_SPORT_LINE, wantToPlayYouChip, type PlayersPane } from '../deckPresentation';
import { WhyFitSheet } from '../whyfit/WhyFitSheet';

import { RadarField, type RadarStatus } from './RadarField';
import { RadarGround } from './RadarGround';
import { RadarSheetFoot } from './RadarSheetFoot';

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
  const interest = useOutstandingInterest();
  const yes = useRadarYes();
  const no = useRadarNo();

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

  /** Where this sport stands against its cap — the one number the ceiling is read from. */
  const standingHere = sport === undefined ? undefined : interest.data?.[sport];
  const give = standingHere === undefined ? undefined : yesesToGive(standingHere);
  const answerPaused = yes.isPaused || no.isPaused;
  const answerError = yes.error ?? no.error;

  /**
   * One answer from the sheet: withheld at the ceiling, or sent with the reading's origin.
   *
   * The sheet closes first, whichever it is. The decision and the words are the deck's own,
   * through `answerFeedback` — the one place the press side of an answer is spelled — and the
   * write is `useRadarAnswers`' (the module note).
   */
  const answer = (said: RadarAnswer, row: RadarRow) => {
    setOpened(undefined);
    if (sport === undefined || envelope === undefined) return;
    if (said === 'yes' && withheldAtTheCap({ give, inclusionReason: row.inclusionReason })) return;

    const name = playerName({ kind: 'player', name: row.card.name });
    const write = { sport, playerId: row.playerId, searchId: envelope.searchId };

    if (said === 'no') {
      sayPassed(name);
      no.mutate(write);
      return;
    }

    // The spoken line and the one toast are the press's; the screen is the mutation's own,
    // pushed from its success whether or not this pane is still there to hear the reply.
    yes.mutate(write, { onSuccess: (reply) => sayYesOutcome(name, reply) });
  };

  const openChat = (conversationId: string) => {
    setOpened(undefined);
    router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId } });
  };

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

          {/* Paused, not failed — the mark stays; refused — the mark is back off the card and the
              sentence says why. In the gutter: the pane has no scroller for them to sit above a
              card in. */}
          {answerPaused || answerError !== null ? (
            <View style={[s.gutter, s.notes]}>
              <AnswerNotes paused={answerPaused} error={answerError} />
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
          in hand, and the foot the deck's sheet never has (the module note). */}
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
          foot={
            <RadarSheetFoot
              row={opened}
              sport={sport}
              onAnswer={(said) => answer(said, opened)}
              onOpenChat={openChat}
            />
          }
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
  notes: { gap: theme.space.sm },
  waiting: { flex: 1 },
});
