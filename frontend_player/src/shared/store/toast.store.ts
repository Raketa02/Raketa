/**
 * The toast queue — app-wide, and the first occupant of this folder.
 *
 * [9.3](../../../docs/design-system.md#93-layer-order) requires a **single root-level
 * overlay host**: `zIndex` in React Native is scoped to the parent, so a toast rendered
 * where it was triggered renders inside whatever card triggered it. One host means one
 * queue, and a queue living inside a feature would be that feature owning every other
 * feature's toasts — which is why this is `shared/` and not `features/play/`.
 *
 * It is app-wide **ephemeral UI state**, which is the one row of `docs/architecture.md`'s
 * ownership table Zustand is for. It holds no server data and no loading flag, so nothing in
 * Part 8 is bent to put it here.
 *
 * ## One at a time, and the rest wait
 *
 * A **queue**, not a stack. The prototype appended toasts to a column and let three sit
 * there at once; `the-words.md` §20.10 makes the announcement queued, and a screen showing
 * three sentences while a listener is being read one is the two channels disagreeing about
 * what just happened. Nineteen toasts fire from the Play tab alone, so the case is real.
 *
 * ## Politeness is the queue's, and one message interrupts
 *
 * `announceForAccessibility` **interrupts** on both platforms, and one landing mid-card cuts
 * a listener off in the middle of the reason lines they were listening to. Part 13's
 * requirement therefore names its mechanism more precisely rather than gaining an exception:
 * every toast announces, **queued**.
 *
 * **One announcement interrupts and earns it, and it jumps the queue as well as the voice.**
 * The send confirmation is the whole of what tells a player that the one irreversible act in
 * the feature succeeded — the destination it lands on is a placeholder with nothing on it to
 * say so — and it is fired *after* that destination mounts, so the platform's own
 * screen-change notification does not clobber it. §20.10's *"it does not queue behind
 * anything"* is therefore two things, not one: it is spoken with `queue: false`, **and** it is
 * placed in front of everything not yet shown. A politeness flag alone would still have left
 * it waiting two holds to be drawn. The message already on screen keeps its place — pulling a
 * sentence out from under a reader is the interruption this amendment exists to stop.
 * It is the single exception, and a second one is an amendment rather than a call-site
 * decision.
 *
 * The store carries the politeness and the host performs it: what a message is worth is a
 * property of the message, and the thing that speaks is a component.
 */

import { create } from 'zustand';

import { type Announcement } from '@/shared/ui/overlay';

/** 9.2's three, and there is no fourth. `ok` is `mintInk`, per Rule C. */
export type ToastTone = 'base' | 'ok' | 'bad';

export interface Toast {
  readonly id: string;
  readonly message: string;
  readonly tone: ToastTone;
  /**
   * Whether this message may wait its turn. `queued` everywhere; `interrupting` is the send
   * confirmation and nothing else — see the module docblock, and `the-words.md` §20.10, where
   * that exception is argued.
   *
   * The type is `overlay.tsx`'s rather than a second name for it: the store carries what a
   * message is worth and the host performs it, and two spellings of one concept that are only
   * coupled by the call between them are two things to keep in step.
   */
  readonly politeness: Announcement;
}

export interface ToastRequest {
  readonly message: string;
  readonly tone?: ToastTone;
  readonly politeness?: Announcement;
}

interface ToastQueueState {
  /** Oldest first. The head is what the host is showing. */
  readonly queue: readonly Toast[];
  readonly show: (request: ToastRequest) => void;
  /** Takes the given message off the front. Called by the host when its hold elapses. */
  readonly dismiss: (id: string) => void;
  readonly clear: () => void;
}

/** Ids are the queue's own and never the message's: two identical sentences are two toasts. */
let nextId = 0;

export const useToastQueue = create<ToastQueueState>((set) => ({
  queue: [],
  show: ({ message, tone = 'base', politeness = 'queued' }) =>
    set((state) => {
      const toast: Toast = { id: `toast-${(nextId += 1)}`, message, tone, politeness };
      // **An interrupting message takes the head, and it is not only an announcement flag.**
      // §20.10's exception is that the send confirmation *"does not queue behind anything,
      // because there is nothing left on screen to tell the listener the challenge went"* —
      // and a queue that only changed how it spoke would still make it wait up to two holds
      // to be spoken at all. It goes in front of what has not been shown yet; the one already
      // on screen keeps its place, because pulling a sentence out from under a reader is the
      // interruption this whole amendment exists to stop.
      const [showing, ...waiting] = state.queue;
      if (toast.politeness === 'interrupting' && showing !== undefined) {
        return { queue: [showing, toast, ...waiting] };
      }
      return { queue: [...state.queue, toast] };
    }),
  dismiss: (id) => set((state) => ({ queue: state.queue.filter((toast) => toast.id !== id) })),
  clear: () => set({ queue: [] }),
}));

/**
 * Raise a toast from anywhere, including outside React.
 *
 * The eight sentences that name somebody fire from use-cases and mutation callbacks rather
 * than from render, and a hook cannot be called there. This is the same shape
 * `shared/lib/auth` uses for the session it is read out of two worlds.
 */
export function showToast(request: ToastRequest): void {
  useToastQueue.getState().show(request);
}
