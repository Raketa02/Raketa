/**
 * ***Fill the seat*** — the challenge screen's ⚡, pressed on a game
 * ([#419](https://github.com/Raketa02/Raketa/issues/419),
 * [ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
 *
 * **The fill flow, whole, and no fork of it.** The act is `features/play`'s `useFillChallengeSeats`
 * — it mints a search, records it, seats the line-up into the Play session — and the push is to
 * the builder under the challenge, `fillRoute`, which sends `POST /challenges/{id}/seats` and pops
 * back to wherever it was pushed from. That is `ChallengeScreen`'s `fillTheSeats` exactly, with
 * one input read off a different record: **who has already said yes** comes from the game's seats
 * rather than the challenge's, because the game's court is the court as it stands now and the
 * challenge's is the arrangement as it was sent. So the composer folds `seatedOthers` off the game
 * and hands it in as `accepted`; this file never learns what a game is.
 *
 * ## Two surfaces, one control
 *
 * The Now card's wide door on *Needs a player* and the primary act on the game screen for it are
 * the same press, so they are the same component — composed by `features/plans` into the card's
 * footer as the door, and into the screen's `fill` slot directly under the card
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §4). What differs is how it is drawn, and that is the card's to say: the door takes the card's
 * accent and its width, and the act takes the screen's. The word is `theActsWords.ts`' — read
 * here and on the card, and it cannot live in either feature.
 *
 * ## Only while the agreed moment is ahead
 *
 * Nobody may be seated into a game whose moment has passed: the builder's send would be refused
 * with `game_moment_has_passed`, and the newcomer's yes with the same. So the door stands down
 * off that instant (`momentHasPassed`) rather than opening a builder that cannot send — and a
 * court still short of a player then is the hour's to call off (ADR-0175 §3). On the screen it
 * is a prop and not a mount: a fill in flight whose rule flips under it still pushes the builder
 * its answer earned. On the card the footer's own rule — no wide door, and the row is not drawn
 * — unmounts it instead, and what such a fill loses is only its push: the search is recorded
 * either way, and a rail is not a screen anybody was waiting on.
 *
 * ## What a refusal costs — `actRefusal`'s fold
 *
 * The fill's own refusals are the search's, and they are handled as the challenge screen handles
 * them: a code that means *this court is not what the screen thought it was* **re-reads and says
 * nothing** — the composer's games list, the one clock every fold on the screen is against —
 * `challenge_not_found` leaves, and everything else is **said** in the sentence every write in
 * this feature says it with. On the card the note is drawn inside the footer, over the door: a
 * card on a rail has no other slot, and a door that failed silently would be a dead door.
 */

import { router } from 'expo-router';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { useFillChallengeSeats } from '@/features/play/types';
import { offlineMessage } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { Button, Note, theme, type ButtonVariant } from '@/shared/ui';
import { FILL_THE_SEAT } from '@/shared/vocabulary/theActsWords';
import type { Sport } from '@/shared/vocabulary/sport';

import { actRefusal } from '../domain/actRefusal';
import { fillRoute } from '../schemas/routeParams';

import { actOnRefusal } from './actOnRefusal';
import { challengeErrorMessage } from './challengeErrorMessage';

export interface FillTheSeatProps {
  /** The challenge behind the game — the court the fill completes. */
  readonly challengeId: string;
  /** The game's sport. The record is stamped with it; the request never carries it. */
  readonly sport: Sport;
  /**
   * Everybody in a seat but the reader, in the court's order — the seats a fill may never take
   * out, read off the **game** by whoever composes this.
   */
  readonly accepted: readonly string[];
  /**
   * Whether the fill is offered right now — the composer's rule, the agreed moment being ahead.
   * Off, nothing is drawn unless a fill is already in flight; see the module note.
   */
  readonly offered: boolean;
  /** What a stale tap costs: **a re-read, never a toast.** The composer holds the games read. */
  readonly onReRead: () => void;
  /** How the control is drawn: the card's accent as the door, the screen's `primary` as the act. */
  readonly variant?: ButtonVariant;
  /** The door's own width on the card; nothing on the screen, where the act takes the column. */
  readonly style?: StyleProp<ViewStyle>;
}

export function FillTheSeat({
  challengeId,
  sport,
  accepted,
  offered,
  onReRead,
  variant = 'primary',
  style,
}: FillTheSeatProps) {
  const fill = useFillChallengeSeats();
  const online = useIsOnline();

  /**
   * The press: the fill, then **the builder pushed onto its answer** — *Find a game*'s own shape.
   * The push is in this `onSuccess`, which runs after the hook's: the Play session has begun and
   * the line-up is seated by the time the route changes, so the builder never renders a frame of
   * an empty court it is about to fill.
   */
  function go(): void {
    fill.reset();
    fill.mutate(
      { kind: 'challenge', sport, completing: { challengeId, accepted } },
      {
        onSuccess: ({ record }) =>
          router.push({ pathname: fillRoute(challengeId), params: { search: record.searchId } }),
        onError: (error) => actOnRefusal(error, onReRead),
      },
    );
  }

  const refusal = fill.error === null ? undefined : actRefusal(fill.error);

  if (!offered && !fill.isPending) return null;

  return (
    <View style={[s.block, style]}>
      {refusal?.kind === 'SAY_SO' ? (
        <Note variant="coral" accessibilityRole="alert">
          {challengeErrorMessage(refusal.error)}
        </Note>
      ) : null}

      {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}

      <Button
        label={FILL_THE_SEAT}
        variant={variant}
        size="lg"
        busy={fill.isPending}
        disabled={!online}
        onPress={go}
      />
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
});
