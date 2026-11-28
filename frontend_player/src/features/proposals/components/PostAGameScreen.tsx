/**
 * ***Post a game*** — full screen over the group, scrolling, the bar still under it
 * ([#558](https://github.com/Rakieta02/Rakieta/issues/558); the screens A5; mocks 15–35; the
 * mechanics §9; the backend's #546).
 *
 * ```
 * ‹ Post a game
 * SPORT   [● Padel 10] [● Tennis 4] …
 * KIND    [ Competitive | For fun · friendly ]
 * WHO     [ Anyone | Men | Women | Mixed pairs ]         Mixed pairs in doubles only
 * LEVEL · narrow it, not widen it   [− 2,56 +] ── [− 2,86 +]
 * WHEN (i)                                 [‹] This week [›]
 *   the grid — a cell opens its sheet
 * [          Post — you're In          ]
 *   Pick an hour with a court on the map first.
 * ```
 *
 * **The draft is the store's** (`postDraft.store`), kept while the player stays in the group: the
 * group's page hands in the sports the reader may post in here, the sport it is on and the kind its
 * switch stands on, and this screen keeps what the player chooses over them. **The kind defaults to
 * the player's intent** — the switch's kind as the deck corrects it (`useGroupDeck`'s), a read the
 * page has already made — until they choose one. Choosing a sport puts the level range back to the
 * engine's and clears the pick; choosing a kind re-seeds the range, the engine's window being the
 * kind's (`withSport`, `withKind`).
 *
 * **The grid is the server's** — every count, colour and flag — read for exactly what the controls
 * ask; the last answer stays drawn while the next is read, within a sport and a week. A cell opens
 * its sheet (`SlotSheet`); a court tapped there is the pick. A fit tapped opens their record **in the
 * sheet's place** — two sheets are never up at once — and closing the record brings the sheet back.
 *
 * ***Post — you're In*** is shut until a court is picked, with the helper under it; once picked, the
 * helper says what the post will be. Pressed with nothing saved to pay with, the payment setup opens
 * (the fill's, `setUpFirst`) and the post goes once a method is; a guard the server answers with is
 * said in the helper's place (`postRefusal`) — the live yeses, two live posts, the week's games, a
 * game at that hour, nobody free, the court gone. **Posted**, the draft is forgotten, a toast says how
 * many best fits have it, and the player **lands** on the group's page on You’re in, where the new
 * game is (`onLanded`, #848) — from either door.
 *
 * **Backing out is not landing** (#848): the chevron, the hardware back and the swipe return to the
 * page as it was, on the tab this screen was opened from, which the chevron names (`backLabel`) —
 * both the group page's to know, so both are handed in. A post settling after the player backed out
 * toasts and leaves the page where they are.
 *
 * **Joining from a sheet** is the fill's, as every yes is: a rescue's *Pay 30 zł* counts its ten
 * seconds behind *Undo* and pays; a post's *I'm in* is a free vote — or, on its last seat, *Pay 32
 * zł* and the fill too (`waitsForUndo` on *Book it now*, Q124). The sheet closes first, then the
 * player lands on You’re in, as a post does — the post's yes is there, and a rescue's *It's a game!*
 * rises over the page with the page left on You’re in under it — the toast following them there.
 */

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import {
  Button,
  Chip,
  Note,
  ScreenHeader,
  Segment,
  behindOverlay,
  courtSeatCount,
  theme,
  useTabBarReach,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';
import { sportLabel } from '@/features/onboarding/types';

import { yesOnRow, type SeatToFill } from '../domain/fillIn';
import type { YesOn } from '../domain/fill';
import {
  UNNARROWED,
  draftSport,
  draftWho,
  isPickedCourt,
  levelAsk,
  whoOffered,
  withKind,
  withNarrowing,
  withPick,
  withSport,
  withWeek,
  withWho,
  withoutPick,
  yesOnPost,
  type CellAt,
  type FreeCourt,
  type PostDraft,
  type PostingAsk,
  type PostingCell,
  type PostingSlot,
  type PostPick,
  type PostStillFilling,
  type SlotFit,
} from '../domain/posting';
import { GAME_KINDS, type GameKind } from '../domain/vocabulary';
import { useFill } from '../hooks/useFill';
import { useFillYes } from '../hooks/useFillYes';
import { useAnswerCard, useGroupDeck } from '../hooks/useGroupDeck';
import { useLatest } from '../hooks/useLatest';
import { usePostAGame, usePostingGrid, usePostingSlot } from '../hooks/usePosting';
import { draftFor, usePostDraftStore } from '../store/postDraft.store';

import { LINE_JOIN, refusalMessage } from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { LevelSteppers } from './LevelSteppers';
import { POSTING_COPY } from './postingCopy';
import { PostingGrid } from './PostingGrid';
import {
  gridRefusal,
  pickLine,
  postRefusal,
  postedToast,
  sportChipSpoken,
} from './postingPresentation';
import { ReadFailed } from './ReadFailed';
import { SlotSheet } from './SlotSheet';

const COPY = POSTING_COPY;

/** A sport the reader may post in here, and how many of the group's members are rated in it. */
export interface PostingSport {
  readonly sport: Sport;
  readonly rated: number;
}

export interface PostAGameScreenProps {
  readonly groupId: string;
  /** The sports the reader is rated in that the group plays, in the registry's order. */
  readonly sports: readonly PostingSport[];
  /** The sport the group's page is on — the draft's, until one is chosen. */
  readonly openingSport: Sport;
  /** The kind the group's switch stands on — corrected by the reader's intent. */
  readonly chosen: GameKind;
  /** The chevron's name — the tab a back-out returns to (*Back to Games*, #848). */
  readonly backLabel: string;
  /** Back to the group's page as it was, on the tab this screen was opened from. */
  readonly onLeave: () => void;
  /** Back to the group's page on You’re in — after a post, or a join from a sheet (#848). */
  readonly onLanded: () => void;
}

/** Doubles — four on the court — where *Mixed pairs* is offered. Read off the court's seats. */
function isDoubles(sport: Sport): boolean {
  return courtSeatCount(sport) === 4;
}

export function PostAGameScreen({
  groupId,
  sports,
  openingSport,
  chosen,
  backLabel,
  onLeave,
  onLanded,
}: PostAGameScreenProps) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const draft = usePostDraftStore((state) => draftFor(state, groupId));
  const keepIn = usePostDraftStore((state) => state.keep);
  const forget = usePostDraftStore((state) => state.forget);
  const keep = (change: (now: PostDraft) => PostDraft) => keepIn(groupId, change);

  const sport = draftSport(
    draft,
    sports.map((one) => one.sport),
    openingSport,
  );
  const doubles = isDoubles(sport);
  const intentKind = useGroupDeck(groupId, sport, chosen).kind;
  const kind = draft.kind ?? intentKind;
  const who = draftWho(draft, doubles);

  // The ask is the controls and the bounds the draft holds — no engine's window needed: the
  // steppers alone read it, off a grid that is always this sport's and this kind's.
  const ask: PostingAsk = { sport, kind, who, ...levelAsk(draft.narrowing) };
  const grid = usePostingGrid(groupId, ask, draft.week);

  // A narrowed bound the server will not take — its window moved under the draft — goes back.
  const gridCode = grid.error?.code;
  useEffect(() => {
    if (gridCode === 'level_range_too_wide' || gridCode === 'level_range_inverted') {
      keepIn(groupId, (now) => withNarrowing(now, UNNARROWED));
    }
  }, [gridCode, groupId, keepIn]);

  // The picked court's club and share are its slot's read — the pick holds only the choice.
  const pickedSlot = usePostingSlot(groupId, ask, draft.pick);
  const pickedCourt = pickedSlot.data?.freeCourts.find((court) => isPickedCourt(court, draft.pick));

  const [open, setOpen] = useState<CellAt>();
  const [record, setRecord] = useState<{ readonly playerId: string; readonly back: CellAt }>();
  // A guard is about the pick it was said for: a new pick, a removed one or a new sport clears it.
  const [guarded, setGuarded] = useState<{ readonly words: string; readonly pick: PostPick }>();
  const guard = guarded !== undefined && guarded.pick === draft.pick ? guarded.words : undefined;
  const readAt = grid.data === undefined ? Date.now() : Date.parse(grid.data.readAt);

  // Land only from a screen still up: a post settling after the player backed out must neither pop
  // the group's page too nor turn it under them.
  const here = useRef(true);
  useEffect(
    () => () => {
      here.current = false;
    },
    [],
  );
  const land = useCallback(() => {
    if (here.current) onLanded();
  }, [onLanded]);

  const fill = useFill();
  const fillYes = useFillYes({ groupId, sport, kind });

  const post = usePostAGame(groupId, {
    onPosted: (posted) => {
      forget(groupId);
      showToast({ message: postedToast(posted) });
      land();
    },
    onRefused: (error, asked) => {
      if (error.code === 'payment_method_required') fill.setUpThen(() => sendLater.current());
      setGuarded({ words: postRefusal(error), pick: asked.pick });
    },
  });

  const send = () => {
    if (draft.pick === undefined) return;
    setGuarded(undefined);
    post.mutate({ ask, pick: draft.pick });
  };
  const sendLater = useLatest(send);

  const pressPost = () => {
    const pick = draft.pick;
    if (post.isPending || pick === undefined) return;
    if (fillYes.setUpFirst(() => sendLater.current())) {
      setGuarded({ words: COPY.paymentFirst, pick });
      return;
    }
    send();
  };

  // ---- Joining from a sheet --------------------------------------------------

  const answer = useAnswerCard(
    groupId,
    (error, asked) => {
      if (fillYes.takesRefusal(error, asked, () => landPostLater.current(asked.card))) return;
      showToast({ message: refusalMessage(error), tone: 'bad' });
    },
    fillYes.onAnswered,
  );

  const landPost = (card: YesOn | undefined) => {
    if (card === undefined) return;
    if (fillYes.waits(card)) {
      fill.book({ card, dealtIn: { groupId, sport, kind } });
      return;
    }
    answer.mutate({ proposalId: card.proposalId, said: 'yes', card });
  };
  const landPostLater = useLatest(landPost);

  /** The yes on a post the sheet listed — once a method is saved, if the setup must open first. */
  const joinPost = (row: PostStillFilling) => {
    setOpen(undefined);
    const card = yesOnPost(row);
    if (fillYes.held(card)) {
      showToast({ message: FILL_COPY.undo.oneAtATime, hold: 'read' });
      return;
    }
    const go = () => {
      landPostLater.current(card);
      land();
    };
    if (fillYes.setUpFirst(go)) return;
    go();
  };

  /** A rescue's seat — ten seconds behind *Undo*, then paid; the toast follows the player out. */
  const joinRescue = (row: SeatToFill) => {
    setOpen(undefined);
    const seat = yesOnRow(row);
    if (fillYes.held(seat)) {
      showToast({ message: FILL_COPY.undo.oneAtATime, hold: 'read' });
      return;
    }
    const go = () => {
      fill.book({ card: seat, dealtIn: { groupId, sport: row.sport, kind: row.kind } });
      land();
    };
    if (fillYes.setUpFirst(go)) return;
    go();
  };

  // ---- The pick --------------------------------------------------------------

  const pickCourt = (court: FreeCourt, slot: PostingSlot) => {
    setOpen(undefined);
    keep((now) =>
      withPick(now, {
        week: now.week,
        day: slot.day,
        range: slot.range,
        clubId: court.club.id,
        startsAt: court.startsAt,
      }),
    );
  };

  const openCell = (cell: PostingCell) => setOpen({ day: cell.day, range: cell.range });

  const openFit = (fit: Pick<SlotFit, 'playerId'>) => {
    if (open === undefined) return;
    setRecord({ playerId: fit.playerId, back: open });
    setOpen(undefined);
  };

  const closeRecord = () => {
    const back = record?.back;
    setRecord(undefined);
    setOpen(back);
  };

  const overlay = open !== undefined || record !== undefined;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.screen} {...behindOverlay(overlay)}>
        <ScreenHeader title={COPY.title} onBack={onLeave} backLabel={backLabel} />
        <ScrollView contentContainerStyle={[s.body, { paddingBottom: reach + theme.space.xxxl }]}>
          <Control label={COPY.sport}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={s.chips}
            >
              {sports.map((one) => (
                <Chip
                  key={one.sport}
                  label={sportLabel(one.sport)}
                  count={one.rated}
                  dot={theme.sport[one.sport]}
                  selected={one.sport === sport}
                  accessibilityLabel={sportChipSpoken(one.sport, one.rated)}
                  onPress={() => {
                    if (one.sport !== sport) {
                      keep((now) => withSport(now, one.sport, isDoubles(one.sport)));
                    }
                  }}
                />
              ))}
            </ScrollView>
          </Control>

          <Control label={COPY.kind}>
            <Segment
              options={GAME_KINDS.map((key) => ({
                key,
                label: COPY.kinds[key],
                accessibilityLabel: COPY.kindsSpoken[key],
              }))}
              selected={kind}
              onSelect={(next) => {
                if (next !== kind) keep((now) => withKind(now, next));
              }}
            />
          </Control>

          <Control label={COPY.who}>
            <Segment
              options={whoOffered(doubles).map((key) => ({ key, label: COPY.whoLabels[key] }))}
              selected={who}
              onSelect={(next) => keep((now) => withWho(now, next))}
            />
          </Control>

          <Control label={COPY.level} aside={COPY.levelAside}>
            <LevelSteppers
              engine={grid.data?.engineLevelRange}
              narrowing={draft.narrowing}
              onNarrow={(narrowing) => keep((now) => withNarrowing(now, narrowing))}
            />
          </Control>

          <PostingGrid
            week={draft.week}
            onWeek={(week) => keep((now) => withWeek(now, week))}
            grid={grid.data}
            pick={draft.pick}
            onCell={openCell}
            placeholder={
              <GridPlaceholder
                error={grid.error}
                paused={grid.fetchStatus === 'paused'}
                onRetry={() => void grid.refetch()}
              />
            }
          />

          <View style={s.post}>
            <Button
              label={COPY.post}
              size="lg"
              disabled={draft.pick === undefined}
              busy={post.isPending}
              busyLabel={COPY.posting}
              onPress={pressPost}
            />
            {guard === undefined ? (
              <Text style={s.helper}>
                {draft.pick === undefined
                  ? COPY.pickFirst
                  : pickLine(draft.pick, pickedCourt, readAt)}
              </Text>
            ) : (
              <Text style={[s.helper, s.guard]} accessibilityRole="alert">
                {guard}
              </Text>
            )}
          </View>
        </ScrollView>
      </View>

      <SlotSheet
        groupId={groupId}
        ask={ask}
        cell={open}
        readAt={readAt}
        pick={draft.pick}
        onPick={pickCourt}
        onUnpick={() => {
          setOpen(undefined);
          keep(withoutPick);
        }}
        onFit={openFit}
        onJoinRescue={joinRescue}
        onJoinPost={joinPost}
        onClose={() => setOpen(undefined)}
      />

      {record === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={closeRecord}
          subject={{ kind: 'player', playerId: record.playerId }}
          sport={sport}
          groupId={groupId}
        />
      )}
    </SafeAreaView>
  );
}

/** A control's form label — `flab`, uppercase — and its quiet aside, over the control. */
function Control({
  label,
  aside,
  children,
}: {
  readonly label: string;
  readonly aside?: string;
  readonly children: ReactNode;
}) {
  return (
    <View style={s.control}>
      <Text accessibilityRole="header">
        <Text style={s.flab}>{label}</Text>
        {aside === undefined ? null : (
          <Text style={s.aside}>
            {LINE_JOIN}
            {aside}
          </Text>
        )}
      </Text>
      {children}
    </View>
  );
}

/** What the grid's place says without a read: the spinner, offline, or why it could not be read. */
function GridPlaceholder({
  error,
  paused,
  onRetry,
}: {
  readonly error: AppError | null;
  readonly paused: boolean;
  readonly onRetry: () => void;
}) {
  if (paused) return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  if (error !== null) {
    const said = gridRefusal(error);
    return said === undefined ? (
      <ReadFailed error={error} onRetry={onRetry} />
    ) : (
      <Note variant="coral">{said}</Note>
    );
  }
  return <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  // Its end is the bar's reach and `xxxl`, set where the reach is read.
  body: { padding: theme.size.gutter, gap: theme.space.lg },
  control: { gap: theme.space.sm },
  flab: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  aside: { ...theme.type.rlLabel, color: theme.color.muted },
  chips: { gap: theme.space.xs },
  post: { gap: theme.space.sm },
  helper: { ...theme.type.rlLabel, color: theme.color.muted, textAlign: 'center' },
  guard: { color: theme.color.coralInk },
});
