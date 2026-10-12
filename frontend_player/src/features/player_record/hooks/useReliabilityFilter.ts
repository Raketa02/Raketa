/**
 * **The filter's switch — a save on every tap, settled by the re-read**
 * ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §6, [#662](https://github.com/Raketa02/Raketa/issues/662)).
 *
 * `PUT /players/me/reliability-filter` answers `204` and nothing else: what is saved, and how many
 * players in the player's groups it now hides, is the own record's to say. So the act is two steps
 * and the control is busy through both:
 *
 * - **The segment moves on the tap** — the position asked for is drawn while the save is out
 *   (`tapped`), because a switch that stayed put under a finger reads as a switch that did not
 *   work — and **the re-read settles it**: a success re-reads the own record, which is the one
 *   entry on screen under the switch, and the save counts as pending until that read is in, so the
 *   segment never shows a position the record has not confirmed with its *hides N of M* line.
 * - **A refusal says so and the segment falls back** to what the record says is saved: nothing is
 *   written into the read on a guess, which the notification choices do, because the hides count
 *   is not something this phone can guess.
 * - **A tap on the position already shown writes nothing**: there is nothing to change, and the
 *   route's *an unchanged value records nothing* is the server saying the same.
 *
 * **Saves go one at a time, in the order tapped** (one `scope`), and the latest tap is what is
 * drawn. **Offline, held** and sent on reconnect, with the amber note while the connection is
 * down. Nothing else is re-read: the deck's thirty-second staleness and its refetch on focus
 * bring the thinner deal when the player goes back to it, and a card dealt before the switch that
 * the server now refuses is refused at the yes, which re-reads the deck.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';

import type { ReliabilityFilter } from '../domain/playerRecord';
import { filterPosition, type FilterPosition } from '../domain/reliabilityFilter';
import { setReliabilityFilter } from '../use-cases/setReliabilityFilter';

import { playerRecordKeys } from './playerRecordKeys';

/** The saves' own key, and the scope that runs them in order. */
const SAVES = [...playerRecordKeys.own(), 'reliability-filter', 'save'] as const;

export function useSetReliabilityFilter(filter: ReliabilityFilter) {
  const client = useQueryClient();
  const online = useIsOnline();

  const saving = useMutation<void, AppError, FilterPosition>({
    mutationKey: SAVES,
    scope: { id: SAVES.join(' ') },
    mutationFn: setReliabilityFilter,
    // Pending until the record under the switch says what is saved — see the module note.
    onSuccess: () => client.invalidateQueries({ queryKey: playerRecordKeys.own() }),
  });

  /** The position drawn: the last tap's until it settles, and otherwise what the record says. */
  const shown =
    saving.isPending && saving.variables !== undefined ? saving.variables : filterPosition(filter);

  return {
    shown,
    /** Move the switch to this position and save it — unless it is already there. */
    set: (position: FilterPosition) => {
      if (position !== shown) saving.mutate(position);
    },
    /** The latest tap's refusal, until the next tap. */
    error: saving.error,
    /** A tap is waiting for the connection. */
    heldOffline: saving.isPaused && !online,
  };
}
