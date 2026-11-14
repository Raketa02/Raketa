/**
 * **The round friend button** — on every card of Home's people rows — **and its worded twin** on a
 * sheet ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows mechanics §11, screens
 * §8; Q29; design-system 7.32).
 *
 * | Relation | Round | Worded | A tap |
 * | --- | --- | --- | --- |
 * | `NONE` | **+**, white | *+ Add friend*, black pill | a request at once — **…** |
 * | `SENT` | **…**, brown | *Request sent*, waiting | *Request sent* · **Cancel request** |
 * | `FRIEND` | **✓**, green | *✓ Friends*, mint | *Remove kuba.w as a friend?* · **Remove friend** · **Keep** |
 * | `ASKED_YOU` | the envelope, volt, a paler halo | *Accept*, coral | accepts at once — **✓** |
 *
 * ## It draws the next mark at once, and the read lands over it
 *
 * **+** turns to **…** and the envelope to **✓** the moment they are pressed (`shownWhilePressed`),
 * and the guess holds **while the write is out — which is until the read under it has landed**:
 * every write here settles once the people lists have read again (`useFriendWrites`), so the read
 * under the button already says what the server did when the guess gives way. Nothing is written into another
 * feature's cache. **A failed write is no longer out**, so the read's own relation is drawn again —
 * *a failed write puts it back*; a refusal that is the state moving (`player_unavailable` from a card
 * read before they turned *Show me to new people* off) re-reads, and the card leaves on that read. Any
 * other refusal is a toast: there is no room for a note under a 24pt mark.
 *
 * Cancelling and removing are a sheet away and silent (the friends mechanics §3.4), and the sheet's
 * act stays busy until the read under it no longer draws the mark that opened it.
 *
 * ## What a write re-reads
 *
 * **Every read that lists people** (`rereadPeopleLists`) — Home's people rows and their See all — as
 * every friends write does, so the guess holds until the row under the button has read again; and
 * Home, and this feature's own lists. A surface whose read of the person is not a people list hands
 * it in (`reread`), as Members and the record do theirs.
 *
 * ## The marks are drawn
 *
 * Archivo ships no ✓ and no envelope (`CLAUDE.md`): the plus and the tick are 6.8's own strokes, the
 * dots three circles, the envelope Feather's `mail`. **Every state has a shape**, never colour alone,
 * and a spoken name saying whom (`roundLabel`).
 */

import Feather from '@expo/vector-icons/Feather';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import type { AppError } from '@/shared/errors';
import { codeMessage } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import { Button, PlusOnSurface, Tick, theme, type ButtonProps } from '@/shared/ui';

import {
  roundPressOf,
  shownWhilePressed,
  type AskedWhere,
  type ImmediatePress,
} from '../domain/friendship';
import type { FriendRelation } from '../domain/vocabulary';
import {
  stateMoved,
  useAcceptFriendRequest,
  useAskToBeFriends,
  useCancelFriendRequest,
  useRemoveFriend,
  type Reread,
} from '../hooks/useFriendWrites';

import { FRIENDS_COPY, removeTitle, roundLabel } from './friendsCopy';
import { TakeBackSheet } from './TakeBackSheet';

const COPY = FRIENDS_COPY;
const SIZE = theme.size.roundFriend;

export interface RoundFriendButtonProps {
  readonly playerId: string;
  /** Their whole nickname — the spoken name and the remove sheet's title. */
  readonly nickname: string;
  /** Where the reader stands with them, as the surface's read said it. */
  readonly relation: FriendRelation;
  /** The row the card stands in — which their Home card names (*Found you among new players*). */
  readonly where: AskedWhere;
  /**
   * **The surface's own read of this person, where it is not a people list** — every write awaits it
   * before it settles. A read that declares `LISTS_PEOPLE` (Home's people rows) needs none: every
   * friend write re-reads it already.
   */
  readonly reread?: Reread;
  /** `round` on a card (the default); `worded` on a sheet's title row. */
  readonly variant?: 'round' | 'worded';
}

export function RoundFriendButton({
  playerId,
  nickname,
  relation,
  where,
  reread,
  variant = 'round',
}: RoundFriendButtonProps) {
  const asking = useAskToBeFriends(playerId, where, reread);
  const accepting = useAcceptFriendRequest(playerId, reread);
  const cancelling = useCancelFriendRequest(playerId, reread);
  const removing = useRemoveFriend(playerId, reread);
  // Which sheet is up, and on which relation it was opened: a read that moves the relation closes
  // it for good, so the same relation coming back later never reopens it without a tap.
  const [sheet, setSheet] = useState<{ readonly which: SheetShown; readonly on: FriendRelation }>();
  if (sheet !== undefined && sheet.on !== relation) setSheet(undefined);
  const self = useRef<View>(null);

  const out: ImmediatePress | undefined = asking.isPending
    ? 'ask'
    : accepting.isPending
      ? 'accept'
      : undefined;
  const shown = shownWhilePressed(relation, out);

  function press() {
    // The next mark is already drawn: a second tap waits for the first to land.
    if (out !== undefined) return;
    const what = roundPressOf(relation);
    switch (what) {
      case 'ask':
        asking.mutate(undefined, { onError: sayRefused });
        return;
      case 'accept':
        accepting.mutate(undefined, { onError: sayRefused });
        return;
      case 'requestSent':
      case 'remove':
        cancelling.reset();
        removing.reset();
        setSheet({ which: what, on: relation });
        return;
    }
  }

  return (
    <>
      <View ref={self} collapsable={false}>
        {variant === 'round' ? (
          <Round relation={shown} nickname={nickname} onPress={press} />
        ) : (
          <Worded relation={shown} nickname={nickname} onPress={press} />
        )}
      </View>

      <TakeBackSheet
        // Gone the moment the read under it no longer draws the mark that opened it.
        visible={sheet?.which === 'requestSent'}
        title={COPY.round.requestSent.title}
        act={COPY.round.requestSent.act}
        busyLabel={COPY.round.requestSent.busy}
        keep={false}
        write={cancelling}
        onAct={() => cancelling.mutate(undefined, { onSuccess: () => setSheet(undefined) })}
        onClose={() => setSheet(undefined)}
        returnFocusTo={self}
      />
      <TakeBackSheet
        visible={sheet?.which === 'remove'}
        title={removeTitle(nickname)}
        body={COPY.record.remove.body}
        act={COPY.record.remove.act}
        busyLabel={COPY.record.remove.busy}
        write={removing}
        onAct={() => removing.mutate(undefined, { onSuccess: () => setSheet(undefined) })}
        onClose={() => setSheet(undefined)}
        returnFocusTo={self}
      />
    </>
  );
}

/** The two sheets a tap can open. */
type SheetShown = Extract<ReturnType<typeof roundPressOf>, 'requestSent' | 'remove'>;

/** A refusal that is not the state moving, said where the button stands: a toast. */
function sayRefused(error: AppError) {
  if (stateMoved(error)) return;
  showToast({ message: codeMessage(COPY.refused, error), tone: 'bad' });
}

interface FaceProps {
  readonly relation: FriendRelation;
  readonly nickname: string;
  readonly onPress: () => void;
}

/**
 * **The round face** — a 24pt circle per relation, the envelope's with its halo, **centred in its own
 * 44pt reach**. The reach is the press's own box, not a `hitSlop`: a touch never lands past its
 * parent's bounds on Android, and a tile clips its corners besides.
 */
function Round({ relation, nickname, onPress }: FaceProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={roundLabel(relation, nickname)}
      onPress={onPress}
      testID={`round-friend-${relation}`}
      style={s.reach}
    >
      {({ pressed }) => (
        <>
          {relation === 'ASKED_YOU' ? <View style={s.halo} testID="round-friend-halo" /> : null}
          <View style={[s.circle, FILL[relation], pressed ? s.pressed : undefined]}>
            <Mark relation={relation} />
          </View>
        </>
      )}
    </Pressable>
  );
}

/** The mark inside the circle — a shape per state, hidden: the name says it. */
function Mark({ relation }: { readonly relation: FriendRelation }) {
  switch (relation) {
    case 'NONE':
      return <PlusOnSurface />;
    case 'SENT':
      return (
        <View style={s.dots}>
          <View style={s.dot} />
          <View style={s.dot} />
          <View style={s.dot} />
        </View>
      );
    case 'FRIEND':
      return <Tick />;
    case 'ASKED_YOU':
      return (
        <Feather
          name="mail"
          size={SIZE.glyph}
          color={theme.color.ink}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      );
  }
}

/**
 * **The worded twin's look per relation** (the screens §8.2; 7.32): *+ Add friend* the black pill,
 * *Request sent* `waiting`, *✓ Friends* `settledSoft`, *Accept* coral — the marks drawn before the words.
 */
const WORDED: Readonly<Record<FriendRelation, Pick<ButtonProps, 'variant' | 'lead' | 'shape'>>> = {
  NONE: { variant: 'dark', lead: 'plus', shape: 'pill' },
  SENT: { variant: 'waiting' },
  FRIEND: { variant: 'settledSoft', lead: 'tick' },
  ASKED_YOU: { variant: 'primary' },
};

/** **The worded twin**, at a sheet's title row (the screens §8.2). */
function Worded({ relation, nickname, onPress }: FaceProps) {
  return (
    <Button
      label={COPY.round.worded[relation]}
      accessibilityLabel={roundLabel(relation, nickname)}
      size="sm"
      onPress={onPress}
      {...WORDED[relation]}
    />
  );
}

/** Each relation's bed — 7.32: white, amber, mint's ink, volt. */
const FILL = StyleSheet.create({
  // White under an ink plus, on a photograph or a pale tile alike (the README's override 9).
  NONE: { backgroundColor: theme.color.surface },
  // Amber — 1.3's *reversible, not yet settled*, which an open request is: white on it 5,70:1.
  SENT: { backgroundColor: theme.color.amber },
  // Rule C: white never on `mint` — its ink carries the tick, 5,84:1.
  FRIEND: { backgroundColor: theme.color.mintInk },
  // A fill, as volt is anywhere; the envelope `ink` on it, 13,96:1.
  ASKED_YOU: { backgroundColor: theme.color.volt },
});

const HALO = SIZE.face + 2 * SIZE.halo;
/** Where the halo stands in the reach, so the circle stays centred in both. */
const HALO_AT = (theme.size.minTouch - HALO) / 2;

const s = StyleSheet.create({
  // 44 × 44, the circle centred in it: the reach is the press's own box (6.5).
  reach: {
    width: theme.size.minTouch,
    height: theme.size.minTouch,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circle: {
    width: SIZE.face,
    height: SIZE.face,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // A volt fill at half strength — a fill, never a stroke (volt's rule), so it reads on any ground.
  halo: {
    position: 'absolute',
    top: HALO_AT,
    left: HALO_AT,
    width: HALO,
    height: HALO,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.volt,
    opacity: 0.5,
  },
  // 6.6: a bed with no darker companion dims.
  pressed: { opacity: 0.7 },
  dots: { flexDirection: 'row', gap: SIZE.dotGap },
  dot: {
    width: SIZE.dot,
    height: SIZE.dot,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.surface,
  },
});
