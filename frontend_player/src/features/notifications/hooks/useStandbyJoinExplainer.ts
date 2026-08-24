/**
 * The second occasion, wired: a standby join, and whether it carries the sheet.
 *
 * The rule is `domain/askOccasion`'s and is not repeated here — this reads the
 * OS's answer, reads the session flag, and renders the decision as a boolean the
 * sheet takes.
 *
 * **Nothing calls `afterJoin` yet.** No surface in this build joins a standby
 * queue: the contract carries a `DELETE` for a queue place and nothing that
 * takes one, and the backend's own `JoinStandby` has the seed catalog as its
 * only caller. So this hook and the sheet it raises are exercised as a
 * *rendering* and a *rule*, and the act that would reach them is
 * [#132](https://github.com/Raketa02/Raketa/issues/132).
 *
 * It is built now rather than with that act for the reason `ADR-0061` gives the
 * ask two occasions at all: the second one is what makes *Not now* a deferral
 * rather than a refusal, and a deferral with nowhere to return is just a
 * refusal wearing kinder words.
 */

import { useCallback, useState } from 'react';

import { osNotifications } from '@/shared/lib/notifications';

import { explainAtStandbyJoin } from '../domain/askOccasion';
import { useStandbyAskStore } from '../store/standbyAsk.store';

export interface StandbyJoinExplainer {
  readonly visible: boolean;
  /**
   * She has just joined a queue. Raises the sheet if this is the occasion for it.
   *
   * Called **after** the join has landed, never before: the ask is the second
   * thing joining buys her, and a sheet over a join that was then refused would
   * be explaining a message about a queue she is not on.
   */
  readonly afterJoin: () => Promise<void>;
  /** Dismissal, and *Not now*. The same act. */
  readonly dismiss: () => void;
}

export function useStandbyJoinExplainer(): StandbyJoinExplainer {
  const [visible, setVisible] = useState(false);

  const afterJoin = useCallback(async () => {
    const standing = await osNotifications.standing();
    // Read at the moment of asking rather than subscribed to: the flag changes
    // only here, and a subscription would re-render every joinable card on the
    // screen the first time one of them raised the sheet.
    const { askedThisSession, markAsked } = useStandbyAskStore.getState();
    if (!explainAtStandbyJoin({ standing, askedThisSession })) return;

    markAsked();
    setVisible(true);
  }, []);

  const dismiss = useCallback(() => setVisible(false), []);

  return { visible, afterJoin, dismiss };
}
