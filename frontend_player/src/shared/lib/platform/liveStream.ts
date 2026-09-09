/**
 * The live channel, behind a port. **The only module that imports `react-native-sse`.**
 *
 * A conversation stays current on its own because the server writes a **nudge** into
 * `GET /conversations/{id}/stream` whenever the room moves, and the nudge carries no content at
 * all
 * ([ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
 * §3). This is the whole of the app's first real-time surface.
 *
 * ## Why it is a port, and why the port is this shape
 *
 * The same two reasons `location.ts` gives, and the second is again the one that decided it: a
 * transport cannot be driven from a test, so a screen that opened its own socket is a screen no
 * suite can put in front of a severed one — and a capability the app reaches through exactly one
 * file is a capability whose behaviour can be read in one sitting. The linter enforces the
 * boundary and `scripts/test-import-boundaries.sh` proves the linter still does.
 *
 * **It owns the route as well as the transport, and that is not an accident.** A port taking an
 * arbitrary path would be a *generic SSE client*, and the only thing that buys is a second stream
 * — for the Chats list — which ADR-0147's *never build* list forbids by name. There is one live
 * channel on this platform, it is a conversation's, and this is it.
 *
 * **What crosses upward is the room and never the number.** The frame carries `last_seq`, and this
 * module reads it to know a frame *is* a nudge and then drops it: above here a client fetches from
 * **its own** high-water mark through the ordinary read path, and a number handed up is a number
 * somebody eventually pages from. ADR-0147 §3 wanted that rule to stop being a rule anybody keeps;
 * inside this app the port is where it becomes one nothing above can express.
 *
 * ## Three states, and a fourth that is not a failure
 *
 * {@link LiveStreamStatus} is what the screen folds — `features/conversations/domain/liveState.ts`
 * — and the arms exist because *not live* is drawn **only in the foreground and only after a
 * connect attempt has failed**. `connecting` is what makes the second condition expressible;
 * `closed` is what makes the first one, because a stream closed on the way to the background was
 * closed **deliberately** and is not news about the room.
 *
 * ## The reconnect, and the one thing about it that is easy to get wrong
 *
 * **The server closes the stream at the access token's `exp`**, roughly every fifteen minutes
 * (ADR-0147 §6), so reconnecting is the ordinary path rather than the exceptional one. Two
 * consequences are built in here:
 *
 * - **Every attempt asks for its credential again.** `streamAttempt` mints a fresh bag per
 *   attempt, and a `401` is answered by the app's own single-flight rotation and then one more
 *   attempt. A channel that captured its headers once would reconnect for ever with the token that
 *   had just expired.
 * - **A clean close raises no event, so the library's own re-poll is what detects it.**
 *   `react-native-sse` dispatches `error` on a refusal and `close` only when *we* close, so a
 *   server that ends the response tidily — which is exactly what expiry does — is silent. Its
 *   `pollingInterval` is kept for that one job and **never as the recovery**: whichever way that
 *   re-poll goes, this module takes over. Refused, it produces the `401` the rotation answers;
 *   accepted, it is thrown away, because a channel that quietly re-opened would sit at `live` for
 *   ever in front of a **dead subscriber**, whose streams end the moment they open — *looking up
 *   to date* being the one failure ADR-0147 §8 exists to prevent. So there is never more than one
 *   scheduler against one room, and every attempt carries a credential this module minted.
 *
 * ## Offline is not a state of its own
 *
 * It **composes with `networkState`** rather than adding a rule (ADR-0147 §10): no attempt is made
 * while `onlineManager` says there is nothing to attempt over, and the status is `lost` rather
 * than `connecting`, because there is no handshake in progress and nothing about waiting is
 * honest. *A severed stream, a dead subscriber, a Redis outage and a phone with no signal all
 * produce the same thing* — and this is where the fourth one joins the other three.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import EventSource from 'react-native-sse';
import { z } from 'zod';

import type { components } from '@/generated/schema';
import { rotateStreamCredential, streamAttempt } from '@/shared/lib/http';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

/** What the channel is doing. Folded into what the room draws by `domain/liveState.ts`. */
export type LiveStreamStatus =
  /** An attempt is in flight, and none has failed since the last one succeeded. */
  | 'connecting'
  /** Open. Frames arrive as the room moves. */
  | 'live'
  /** An attempt failed, the channel was severed, or there is no connection to make one over. */
  | 'lost'
  /** Not following, deliberately: the app is in the background. */
  | 'closed';

/**
 * One frame, as it reaches the app: **the room that moved, and nothing else.**
 *
 * The wire's `v` and `last_seq` stop at this module — see the note above. What a reader does with
 * one of these is re-read from its own cursor, which is an act that cannot be wrong about a
 * number it does not have.
 */
export interface LiveNudge {
  readonly conversationId: string;
}

export interface FollowLive {
  /** The room to follow. One stream per open conversation, and never one for a list. */
  readonly conversationId: string;
  /** Called for every frame. The answer is an invalidation, never a render. */
  readonly onNudge: (nudge: LiveNudge) => void;
  /** Called on every transition, and once on the way in. */
  readonly onStatus: (status: LiveStreamStatus) => void;
}

/**
 * What the app may ask the device to keep open.
 *
 * One operation, because there is one question: *follow this room until I say stop*. Screens
 * depend on this interface through `useLiveStream()`; {@link deviceLiveStream} is the one
 * implementation that talks to a socket, and a test substitutes `fakeLiveStream()` from
 * `src/test-support/platform.ts`.
 */
export interface LiveStreamPort {
  /** Follow one room. The returned function stops it and reports nothing afterwards. */
  readonly follow: (ask: FollowLive) => () => void;
}

/**
 * How long after a channel ends before another is opened.
 *
 * It is handed to the library as its `pollingInterval` **and** used for this module's own retries,
 * so the two paths cannot drift into two different reconnect rhythms. Three seconds against a
 * fifteen-minute expiry is a rounding error on the reconnect that always runs, and against a
 * deploy severing every connection it is a wait nobody watching a chat would call a wait.
 */
export const REOPEN_MS = 3000;

/** The one route this port follows. See the module note on why it is here and not in `api/`. */
function streamPath(conversationId: string): string {
  return `/api/v1/conversations/${conversationId}/stream`;
}

/**
 * The frame, validated. **A stream body is untrusted input**, so it is parsed rather than cast —
 * the rule this app already applies to a deep link or a route param.
 *
 * It is **not gated on `v`**. The version is what a *later* shape is told apart by, and every
 * version of a nudge asserts the same one thing, because ADR-0147 §3 says a frame carries no
 * content ever. Refusing an unknown version would drop news on the day the envelope grows a
 * field, which is the single failure the nudge exists to make impossible; what is checked is that
 * all three fields are there and the right kinds, which is what makes it a nudge at all.
 */
const NUDGE = z.object({
  v: z.number(),
  conversation_id: z.string(),
  last_seq: z.number(),
});

/**
 * The parse and the contract, held equal by the compiler.
 *
 * ADR-0147 §7 requires the client to read this envelope as the **generated** type rather than a
 * hand-written mirror of it, and the operation's own `200` generates as `unknown` because a stream
 * body is not a response model — so the shape is asserted here, by name, and a field added,
 * removed or retyped on the contract fails `pnpm typecheck` in this file.
 */
export const LIVE_NUDGE_AGREES: Exact<
  z.infer<typeof NUDGE>,
  components['schemas']['LiveNudgeSchema']
> = true;

/** The room a frame names, or nothing where what arrived was not a nudge. */
function nudgeOf(data: string | null): LiveNudge | undefined {
  if (data === null) return undefined;

  let frame: unknown;
  try {
    frame = JSON.parse(data);
  } catch {
    return undefined;
  }

  const parsed = NUDGE.safeParse(frame);
  return parsed.success ? { conversationId: parsed.data.conversation_id } : undefined;
}

/**
 * Whether another attempt could succeed, from the status the transport reported.
 *
 * `0` is *no answer at all* — a severed connection, a DNS failure, a deploy — and a `5xx` is a
 * server that may be there in three seconds. **Everything else is a refusal**, and repeating a
 * refused request is a loop: a room that has been destroyed answers `404` to every attempt for
 * ever, and the read path beside this one is what takes the screen away. The `401` is not here
 * because it is answered by a rotation rather than by a retry.
 */
function worthRepeating(status: number): boolean {
  return status === 0 || status >= 500;
}

export const deviceLiveStream: LiveStreamPort = { follow };

function follow({ conversationId, onNudge, onStatus }: FollowLive): () => void {
  let source: EventSource | null = null;
  let reopen: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;
  /** Which rotation the open attempt's credential came from. */
  let sentWith = 0;
  /**
   * Whether this channel has already spent its one rotation.
   *
   * A freshly-rotated credential refused again is the `401 → refresh → 401` loop, and the module
   * note says why a stream is not the surface that ends a session over it. One rotation per
   * channel, and a second refusal is simply a refusal.
   */
  let rotated = false;

  function say(status: LiveStreamStatus): void {
    if (!stopped) onStatus(status);
  }

  /**
   * Tear the channel down without hearing about it: our own `close` is not news.
   *
   * **It closes twice, and the second one is the load-bearing one.** `react-native-sse` schedules
   * its own re-poll *after* dispatching the event that brought us here, so a close made from inside
   * that dispatch is undone a line later by a timer this module never sees — and that timer opens a
   * socket with every listener already removed, for ever, every `REOPEN_MS`. Closing again once the
   * dispatch has finished is what actually stops it: `close()` clears the timer unconditionally and
   * dispatches nothing the second time. The first call is kept because it aborts the request now
   * rather than a microtask from now.
   */
  function drop(): void {
    if (reopen !== null) {
      clearTimeout(reopen);
      reopen = null;
    }

    const closing = source;
    source = null;
    if (closing === null) return;

    closing.removeAllEventListeners();
    closing.close();
    queueMicrotask(() => closing.close());
  }

  function reopenIn(ms: number): void {
    if (reopen !== null) clearTimeout(reopen);
    reopen = setTimeout(() => {
      reopen = null;
      settle();
    }, ms);
  }

  /**
   * Follow, stop following, or leave it alone — whichever the device is asking for now.
   *
   * One function for the way in, the return from the background, the reconnect and the retry, so
   * there is one place that decides whether a channel should exist and every trigger goes through
   * it. ADR-0147 §9: re-opening on foreground is *the same code path as any other reconnect*.
   */
  function settle(): void {
    if (stopped) return;

    if (!focusManager.isFocused()) {
      drop();
      say('closed');
      return;
    }

    if (!onlineManager.isOnline()) {
      drop();
      say('lost');
      return;
    }

    if (source === null) open();
  }

  function open(): void {
    const attempt = streamAttempt(streamPath(conversationId));

    if (attempt === undefined) {
      // No session to follow with. Nothing to wait for either: the tree above this screen is
      // already on its way to the sign-in stack.
      say('lost');
      return;
    }

    sentWith = attempt.generation;
    say('connecting');

    const opened = new EventSource(attempt.url, {
      headers: { ...attempt.headers },
      // The library's own re-poll, kept for exactly one path: a server that ends the response
      // tidily raises no event, so this is what notices an expiry. See the module note.
      pollingInterval: REOPEN_MS,
      // The library defaults to half a second before the first connect. There is nothing to
      // debounce — this is called when a room opens, and the room is waiting for it.
      timeoutBeforeConnection: 0,
    });
    source = opened;

    /**
     * How many times **this** connection has been open — per `EventSource` and never per follow,
     * because what it counts is one object's own re-polls. See the listener below.
     */
    let opens = 0;

    // Every listener asks whether it is still the current channel. A frame from a channel this
    // module has already dropped is news about a socket rather than about the room.
    opened.addEventListener('open', () => {
      if (source !== opened) return;

      opens += 1;

      // **A second open on one channel is how a tidy close is learned, and there is no other
      // way.** The library re-polls only because the response ended, and a response the server
      // ended raises no event at all — so a re-open is proof of a close that nothing announced.
      //
      // It is answered by throwing the connection away rather than keeping it, and that is what
      // makes ADR-0147 §8 true of a **dead subscriber**: such a server hands out streams that end
      // the moment they open, and a channel that quietly re-opened each time would sit at `live`
      // for ever while delivering nothing — *looking up to date* is the one failure that clause
      // exists to prevent. Kept, it would also be wrong about the credential: the library re-opens
      // with the bag this channel was built with, which by then may be a quarter of an hour old.
      if (opens > 1) {
        drop();
        say('lost');
        reopenIn(REOPEN_MS);
        return;
      }

      rotated = false;
      say('live');
    });

    opened.addEventListener('message', (event) => {
      if (source !== opened) return;

      const nudge = nudgeOf(event.data);
      if (nudge !== undefined) onNudge(nudge);
    });

    opened.addEventListener('error', (event) => {
      if (source !== opened) return;

      const status = event.type === 'error' ? event.xhrStatus : 0;
      drop();
      say('lost');

      if (status === 401) {
        // Answered by a rotation rather than by a retry, and once: a credential minted seconds
        // ago and refused again is a refusal, not an expiry.
        if (!rotated) {
          rotated = true;
          void rotateThenOpen();
        }
      } else if (worthRepeating(status)) {
        reopenIn(REOPEN_MS);
      }
    });
  }

  /** Rotate through the app's one refresh, then attempt again with what it minted. */
  async function rotateThenOpen(): Promise<void> {
    const again = await rotateStreamCredential(sentWith);
    if (stopped) return;

    if (again) settle();
    else reopenIn(REOPEN_MS);
  }

  const unwatchFocus = focusManager.subscribe(() => settle());
  const unwatchOnline = onlineManager.subscribe(() => settle());

  settle();

  return () => {
    stopped = true;
    unwatchFocus();
    unwatchOnline();
    drop();
  };
}
