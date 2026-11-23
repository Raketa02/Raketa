/**
 * **A group's Fill in tab, as it stands** — the rescue board, then the You’re in board, stacked
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3; mocks 11–13). Each board
 * owns its read and that read's states; what the stack decides is only the tab with neither.
 *
 * **Sections only when they have rows** (A3); with neither, the tab is the group's starting card the
 * page hands in (`empty`), as the Games tab's is — and only once both reads have said there is
 * nothing: while either is on its way and nothing is drawn yet, the muted spinner. The floating
 * *+ Post a game* is the page's.
 */

import type { ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { yesesIn } from '../domain/fillIn';
import { useSeatsToFill } from '../hooks/useFillIn';
import { useLiveYeses } from '../hooks/useLiveYeses';

import { FillInBoard } from './FillInBoard';
import { FILL_IN_COPY } from './fillInCopy';
import { isHeld } from './HeldRead';
import { YoureInBoard } from './YoureInBoard';

export interface FillInStackProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** What the tab draws with no rows in either section — the group's starting card. */
  readonly empty: ReactNode;
}

export function FillInStack({ groupId, sport, empty }: FillInStackProps) {
  const rescues = useSeatsToFill(groupId, sport);
  const live = useLiveYeses();

  const seats = rescues.seats ?? [];
  const yeses = live.data === undefined ? [] : yesesIn(live.data.yeses, groupId, sport);
  const seatsHeld = isHeld(rescues.read);
  const yesesHeld = isHeld(live);
  const pending =
    (rescues.seats === undefined && !seatsHeld) || (live.data === undefined && !yesesHeld);

  const nothing = seats.length === 0 && yeses.length === 0 && !seatsHeld && !yesesHeld;

  // Both boards stay mounted whatever is drawn: a board mounted on a refused read reads it again,
  // so one that came and went with the refusal would ask for ever.
  return (
    <View style={[s.board, nothing ? undefined : s.roomForPost]}>
      <FillInBoard groupId={groupId} sport={sport} />
      <YoureInBoard groupId={groupId} sport={sport} />
      {!nothing ? null : pending ? (
        // The starting card only once both reads have said there is nothing — never a first frame.
        <ActivityIndicator accessibilityLabel={FILL_IN_COPY.reading} color={theme.color.muted} />
      ) : (
        empty
      )}
    </View>
  );
}

const s = StyleSheet.create({
  board: { gap: theme.space.lg },
  // Room under the last row for the floating *+ Post a game*, which sits over the page's corner.
  roomForPost: { paddingBottom: theme.size.btnLg + theme.space.lg },
});
