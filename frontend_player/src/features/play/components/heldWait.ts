/**
 * A wait bound to its act, and an **answer held long enough to read** — §J6's minimum display,
 * as one helper ([#228](https://github.com/Raketa02/Raketa/issues/228) §9).
 *
 * Two Play screens wait on an answer and both want the same two beats: up **because a request
 * is in flight**, then up a little longer *"so a fast answer does not flash past."* The pool's
 * floor is 1100 ms and the engine fill's is 650 with a stagger over it
 * (`theme.motion.hold`) — one mechanism with two numbers, and a floor written twice is a
 * floor that drifts.
 *
 * ## The floor runs from the answer, not from the press
 *
 * That is the whole of it, and it is the opposite of what the first draft did. The thing that
 * must not flash past is the **answer**: the count on a searching latch is
 * `players_in_range` off the response, so a floor measured from the press would print it for
 * whatever was left of 1100 ms — 1050 ms on a search that came back at once, and **nothing at
 * all** on any search slower than the floor, which is most of them. The number would have been
 * implemented and never seen.
 *
 * So the wait is `running`, then the floor. `the-play-screens.md` §3 licenses exactly this and
 * bounds it: *"the animation is presentation over a completed answer, and the client may take
 * its time"*, against *"the server never delays to make a search feel substantial."* Nothing
 * here delays a request or a response; it holds a finished one on screen.
 *
 * **`CalculatingScreen`'s floor is measured the other way and stays that way.** It holds a
 * *sentence to read* while a rating comes into existence, so its beat starts when the player
 * presses. This one holds an *answer* to read, so its beat starts when the answer exists. The
 * two are the same mechanism pointed at different things, which is why neither is the other's
 * copy.
 *
 * **It is not skipped under reduced motion.** A held screen is not an animation: nothing moves,
 * and the player who asked the OS to calm things down is the last one who should be given a
 * flash where an answer came into existence (`motion.hold`'s own docstring). What *does*
 * collapse is a stagger drawn over the floor, which is motion and is named where it is drawn
 * (`searchingWait`).
 *
 * ## Why the timer is a ref, and why the hold rises with the act
 *
 * The hold is raised on the **rising** edge and lowered only by the timer the falling edge
 * starts. Raising it on the falling edge instead would leave one commit where the request has
 * finished and the hold has not yet begun — a latch that blinks out and back in at the exact
 * moment the answer lands. And the timeout is owned by a ref, cleared only on unmount, because
 * an effect keyed on `running` clears its timer on every edge including the one it is timing.
 *
 * ## Where it lives
 *
 * `docs/architecture.md`: *"Do not move code to `shared/` because two files use it… keep code
 * local until its cross-feature ownership is proven."* Both waits are Play's; the second
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)) is not built yet, and onboarding's
 * floor is the differently-anchored one above. It moves the day a third feature needs it.
 */

import { useEffect, useRef, useState } from 'react';

/**
 * @param running whether the act this wait is over is in flight.
 * @param floorMs how long the answer is held on screen after the act finishes.
 * @returns whether the wait is still up.
 */
export function useHeldWait(running: boolean, floorMs: number): boolean {
  const [held, setHeld] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const wasRunning = useRef(false);

  useEffect(() => {
    const started = running && !wasRunning.current;
    const finished = !running && wasRunning.current;
    wasRunning.current = running;

    // A second act inside the first one's floor takes the floor over rather than being cut
    // short by it: the timer belongs to the answer that started it.
    if (started) {
      setHeld(true);
      clearTimeout(timer.current);
    }

    if (finished) timer.current = setTimeout(() => setHeld(false), floorMs);
  }, [running, floorMs]);

  // The one cleanup, and it is the unmount. A timer cleared when the act finished would be
  // the floor cancelled by the answer it exists to hold.
  useEffect(() => () => clearTimeout(timer.current), []);

  return running || held;
}
