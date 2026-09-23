/**
 * **The dismissal's door** — *Remove this row*, met from a **`Called off` row** by anybody the
 * court asked
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md),
 * [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §5).
 *
 * **The game card's act, met as a door of the challenge's own.** The act is `useDismissCourt` —
 * `POST /challenges/{id}/dismissal`, recorded on the game exactly as the Now card's trash records
 * it, and admitted for everybody with a seat on the court, because an invitee still deciding when
 * the court was called off has a row and never had a card. What this file is, is the door a row
 * reveals, on `RemovalDoor`'s shape: a render prop handing the surface an `ActDoor`. Whether the
 * door is offered at all is not this file's: the row asks `mayDismiss`, one rule in `challenge.ts`.
 *
 * ## No sheet, so the door's `open` is the act
 *
 * ADR-0172 §5's reason, unchanged by widening what the act clears: it removes a court from the
 * reader's own lists and nothing from the record, nobody else's row or rail moves, and a
 * confirmation would put the withdraw's ceremony on the least consequential act in the app. So
 * there is nothing for `useActDoor` to keep up, and the button a swipe reveals sends on the
 * press. A second press while the first is in flight sends nothing: the server would answer it
 * as done, and the row is about to go.
 *
 * ## Success is the reply, and the card goes with the row
 *
 * `useDismissCourt` drops this court's row from the challenge list and — through the one write
 * the games list lets another feature make — its card from the games list, then re-reads both.
 * So the row is gone the moment the reply lands and before any re-read, as the leaver's is, and
 * the Now card is gone with it. **A refusal is the re-read and no words**, the trash's own
 * posture: the row a listener is on is not the row the server holds, and the fold the re-read
 * lands on is the answer.
 */

import { useRef, type ReactNode } from 'react';
import type { View } from 'react-native';

import type { ActDoor } from '../hooks/useActDoor';
import { useDismissCourt } from '../hooks/useChallenge';

import { REMOVE_THIS_ROW } from './challengePresentation';

/** The name the row's accessibility action goes by — see `ActDoorAsk.actionName`. */
const DISMISS_ACTION = 'remove-this-row';

export interface DismissalDoorProps {
  /** The called-off court — the id the act is about. */
  readonly challengeId: string;
  /** The game it became, so its card can go on the reply; absent where the row carries none. */
  readonly gameId?: string;
  /** The surface, drawn around the door it is handed. */
  readonly children: (door: ActDoor) => ReactNode;
}

export function DismissalDoor({ challengeId, gameId, children }: DismissalDoorProps) {
  const dismiss = useDismissCourt();
  const control = useRef<View>(null);

  function open(): void {
    if (dismiss.isPending) return;
    dismiss.mutate(gameId === undefined ? { challengeId } : { challengeId, gameId });
  }

  return (
    <>
      {children({
        label: REMOVE_THIS_ROW,
        open,
        control,
        action: { name: DISMISS_ACTION, label: REMOVE_THIS_ROW },
        onAccessibilityAction: (event) => {
          if (event.nativeEvent.actionName === DISMISS_ACTION) open();
        },
      })}
    </>
  );
}
