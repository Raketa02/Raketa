/**
 * The live channel, over a faked `XMLHttpRequest`.
 *
 * **The socket is the only thing stubbed**, which is the seam `test-support/transport.ts` uses for
 * `fetch`: `react-native-sse` runs for real, so what is under test includes its frame parsing and
 * its re-poll — the two things this port's design leans on, and neither of which a mocked library
 * would exercise. Above it everything runs for real too, including `shared/lib/http`'s credential
 * minting and the app's own single-flight rotation.
 *
 * The four failures ADR-0147 §8 collapses into one — a severed stream, a dead subscriber, a Redis
 * outage and a phone with no signal — are the cases below, and the point of the file is that they
 * come out the same. It is also the only place the reconnect production runs **every fifteen
 * minutes** is exercised at all: it is the hardest-to-test path in the design, which is exactly why
 * the record made it the path that always runs.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';

import { configureHttp, resetHttp } from '@/shared/lib/http';

import { deviceLiveStream, REOPEN_MS, type LiveNudge, type LiveStreamStatus } from './liveStream';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const STREAM_URL = `https://api.test.raketa.invalid/api/v1/conversations/${ROOM}/stream`;

/** A nudge, as the route writes one. */
function frame(lastSeq: number, conversationId = ROOM): string {
  return JSON.stringify({ v: 1, conversation_id: conversationId, last_seq: lastSeq });
}

/**
 * One socket the library opened, with the four ways a server can behave on it.
 *
 * Modelled on the real thing rather than on what the library happens to call: a streaming response
 * sits at `LOADING` with a status while more body arrives, and reaches `DONE` when it ends —
 * **tidily or not**, which is the distinction the whole port is built around.
 */
class FakeSocket {
  static readonly UNSENT = 0;
  static readonly OPENED = 1;
  static readonly HEADERS_RECEIVED = 2;
  static readonly LOADING = 3;
  static readonly DONE = 4;

  method = '';
  url = '';
  readonly headers: Record<string, string> = {};
  readyState = FakeSocket.UNSENT;
  status = 0;
  responseText = '';
  timeout = 0;
  aborted = false;
  onreadystatechange: (() => void) | null = null;
  onerror: (() => void) | null = null;

  open(method: string, url: string): void {
    this.method = method;
    this.url = url;
    this.readyState = FakeSocket.OPENED;
  }

  setRequestHeader(name: string, value: string): void {
    this.headers[name] = value;
  }

  send(): void {
    sockets.push(this);
  }

  abort(): void {
    this.aborted = true;
  }

  /**
   * **Headers back, plus the frame the route always writes the moment a stream opens.**
   *
   * The two are one call because on the wire they are: a body-less `LOADING` transition is what a
   * real XHR reports at `HEADERS_RECEIVED`, and this route's first act is a nudge carrying the
   * room's current `last_seq` (ADR-0147 §3). That is also what makes resume correct without
   * `Last-Event-ID` being load-bearing.
   */
  answer(lastSeq = 0): void {
    this.status = 200;
    this.write(frame(lastSeq));
  }

  /** One frame written into the open response. */
  write(body: string): void {
    this.responseText += `data: ${body}\n\n`;
    this.readyState = FakeSocket.LOADING;
    this.onreadystatechange?.();
  }

  /** The server ended the response tidily — **which is what a token expiry looks like.** */
  end(): void {
    this.readyState = FakeSocket.DONE;
    this.onreadystatechange?.();
  }

  /** Refused, with a status: a stale credential, or a room that is no longer there. */
  refuse(status: number): void {
    this.status = status;
    this.readyState = FakeSocket.DONE;
    this.onreadystatechange?.();
  }

  /** No answer at all — a severed connection, a deploy, a subscriber that died. */
  sever(): void {
    this.status = 0;
    this.readyState = FakeSocket.DONE;
    this.onerror?.();
  }
}

let sockets: FakeSocket[] = [];
let stops: (() => void)[] = [];
let realXhr: typeof XMLHttpRequest;
/** The app's own rotation, so a test can prove it was asked once and with which generation. */
let refresh: jest.Mock;
let token: string;
let generation: number;

/**
 * Follow the room, and register the teardown so a failing assertion cannot leak one.
 *
 * A channel that outlives its test stays subscribed to `focusManager` and `onlineManager`, so the
 * next test's `beforeEach` wakes it and it opens sockets into *that* test's array — one failure
 * then reads as five. Held here rather than in each case for exactly that reason.
 */
function followTheRoom() {
  const statuses: LiveStreamStatus[] = [];
  const nudges: LiveNudge[] = [];

  const stop = deviceLiveStream.follow({
    conversationId: ROOM,
    onStatus: (status) => statuses.push(status),
    onNudge: (one) => nudges.push(one),
  });
  stops.push(stop);

  return { statuses, nudges, stop };
}

/**
 * Let the library's connect timer fire — it opens on a `setTimeout`, never inline.
 *
 * **One millisecond and not nought**, which is a fake-timer fact rather than a fudge:
 * `@sinonjs/fake-timers` schedules a zero-delay timer created *during* a tick at `now + 1` so a
 * self-rescheduling timer cannot spin for ever. So a connect scheduled from inside an earlier
 * advance is due a millisecond later, and `advanceTimersByTimeAsync(0)` would step over it.
 */
async function connectAttempt(): Promise<void> {
  await jest.advanceTimersByTimeAsync(1);
}

/** Wait out this module's own retry, and then the library's connect timer inside it. */
async function retryAttempt(): Promise<void> {
  await jest.advanceTimersByTimeAsync(REOPEN_MS);
  await connectAttempt();
}

/** The last socket opened, which is the one a server behaves on. */
function latest(): FakeSocket {
  const socket = sockets.at(-1);
  if (socket === undefined) throw new Error('no socket was opened');
  return socket;
}

beforeEach(() => {
  jest.useFakeTimers();
  sockets = [];
  stops = [];
  realXhr = globalThis.XMLHttpRequest;
  globalThis.XMLHttpRequest = FakeSocket as unknown as typeof XMLHttpRequest;

  token = 'access-1';
  generation = 1;
  refresh = jest.fn(async () => {
    token = 'access-2';
    generation = 2;
    return 'retry' as const;
  });

  configureHttp({
    current: () => ({ accessToken: token, generation }),
    refresh,
    abandon: async () => {},
  });

  focusManager.setFocused(true);
  onlineManager.setOnline(true);
});

afterEach(() => {
  for (const stop of stops) stop();
  globalThis.XMLHttpRequest = realXhr;
  resetHttp();
  focusManager.setFocused(undefined);
  onlineManager.setOnline(true);
  jest.useRealTimers();
});

describe('opening the channel', () => {
  it('follows the room’s own route, with the credential in the header and never in the URL', async () => {
    const { statuses } = followTheRoom();

    expect(statuses).toEqual(['connecting']);

    await connectAttempt();

    expect(sockets).toHaveLength(1);
    expect(latest().method).toBe('GET');
    expect(latest().url).toBe(STREAM_URL);
    expect(latest().headers.Authorization).toBe('Bearer access-1');
    expect(latest().headers.Accept).toBe('text/event-stream');
    // ADR-0147 §6: a credential in a query string is a credential in the load balancer's log.
    expect(latest().url).not.toContain('access-1');
  });

  it('says it is live once the server answers, and not before', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();

    expect(statuses).toEqual(['connecting']);

    latest().answer();

    expect(statuses).toEqual(['connecting', 'live']);
  });

  /**
   * **A client that has been away catches up in one step**, because the route's own opening frame
   * is a nudge like any other and the answer to a nudge is a re-read.
   */
  it('treats the frame the stream opens with as news', async () => {
    const { nudges } = followTheRoom();
    await connectAttempt();

    latest().answer(12);

    expect(nudges).toEqual([{ conversationId: ROOM }]);
  });

  /** There is nothing to authorise an attempt with, and nothing about waiting would be honest. */
  it('reports lost and opens nothing where there is no session', async () => {
    resetHttp();

    const { statuses } = followTheRoom();
    await connectAttempt();

    expect(statuses).toEqual(['lost']);
    expect(sockets).toEqual([]);
  });
});

describe('a frame', () => {
  /**
   * **The room, and nothing else.** `last_seq` is read to know the frame is a nudge and dropped
   * here, so nothing above this port can page from it — which is what makes a lost frame free.
   */
  it('reaches the app as the room that moved, with no number on it', async () => {
    const { nudges } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().write(frame(7));

    expect(nudges).toEqual([{ conversationId: ROOM }, { conversationId: ROOM }]);
  });

  it('is delivered once per frame, in order', async () => {
    const { nudges } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().write(frame(7));
    latest().write(frame(8));

    expect(nudges).toHaveLength(3);
  });

  /**
   * **Not gated on `v`.** Every version of a nudge asserts the same one thing, so refusing an
   * unknown one would drop news on the day the envelope grows a field — the single failure this
   * design exists to make impossible.
   */
  it('is still news when the envelope version is one this build has never seen', async () => {
    const { nudges } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().write(JSON.stringify({ v: 9, conversation_id: ROOM, last_seq: 4 }));

    expect(nudges).toHaveLength(2);
  });

  it('is dropped where what arrived is not a nudge at all', async () => {
    const { nudges } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().write('not json');
    latest().write(JSON.stringify({ v: 1 }));
    latest().write(JSON.stringify({ v: 1, conversation_id: 4, last_seq: 'nine' }));

    expect(nudges).toHaveLength(1);
  });
});

describe('the reconnect that production runs every fifteen minutes', () => {
  /**
   * **A tidy close raises no event**, so the library's own re-poll is what notices — and it goes
   * out with the credential that has just expired, which is what produces the `401` this port acts
   * on. The player sees *not live* for one beat, which is the dividend ADR-0147 §6 named.
   */
  it('rotates the credential and opens again, once', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();
    latest().end();

    // Silent so far: nothing in the library says a tidy close happened.
    expect(statuses).toEqual(['connecting', 'live']);

    await jest.advanceTimersByTimeAsync(REOPEN_MS);

    expect(sockets).toHaveLength(2);
    expect(latest().headers.Authorization).toBe('Bearer access-1');

    latest().refuse(401);

    expect(statuses).toEqual(['connecting', 'live', 'lost']);

    await connectAttempt();

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(refresh).toHaveBeenCalledWith(1);
    expect(sockets).toHaveLength(3);
    expect(latest().headers.Authorization).toBe('Bearer access-2');

    latest().answer();

    expect(statuses).toEqual(['connecting', 'live', 'lost', 'connecting', 'live']);
  });

  /**
   * **A server whose subscriber has died hands out streams that end the moment they open**, and
   * ADR-0147 §8's whole point is that such a chat must *look* not-live rather than up to date. The
   * re-poll that discovers the close is thrown away rather than kept — kept, the status would
   * never leave `live` while nothing at all was being delivered.
   */
  it('reports a tidy close as lost, however well the re-poll goes', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();
    latest().end();

    expect(statuses).toEqual(['connecting', 'live']);

    // The library's own re-poll, and this time the server accepts it — and closes it again.
    await jest.advanceTimersByTimeAsync(REOPEN_MS);
    expect(sockets).toHaveLength(2);
    latest().answer();

    expect(statuses).toEqual(['connecting', 'live', 'lost']);
    expect(sockets[1]?.aborted).toBe(true);

    // And what follows is this module's own attempt, with a credential it minted.
    await retryAttempt();

    expect(sockets).toHaveLength(3);
    expect(statuses).toEqual(['connecting', 'live', 'lost', 'connecting']);
  });

  /**
   * A credential minted seconds ago and refused again is a refusal, not an expiry — the
   * `401 → refresh → 401` loop, which the port refuses to enter and does not resolve either: the
   * read path the player is waiting on is what is allowed to end a session over it.
   */
  it('rotates once per channel and then stops asking', async () => {
    followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().refuse(401);
    await connectAttempt();
    expect(sockets).toHaveLength(2);

    latest().refuse(401);
    await jest.advanceTimersByTimeAsync(REOPEN_MS * 3);

    expect(refresh).toHaveBeenCalledTimes(1);
    expect(sockets).toHaveLength(2);
  });

  /**
   * The library schedules its own re-poll **after** dispatching the failure, so a close made from
   * inside that dispatch is undone by a timer this module never sees — and the socket that timer
   * opens has no listeners on it. This is the assertion that the second close in `drop` works.
   */
  it('leaves no orphan socket polling behind a channel it dropped', async () => {
    followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().refuse(404);
    await jest.advanceTimersByTimeAsync(REOPEN_MS * 4);

    expect(sockets).toHaveLength(1);
  });
});

describe('all four failures produce the same thing', () => {
  /** A severed connection — a deploy, or the close a server makes when its subscriber has died. */
  it('a severed stream is lost, and another attempt follows', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().sever();

    expect(statuses).toEqual(['connecting', 'live', 'lost']);

    await retryAttempt();

    expect(sockets).toHaveLength(2);
    expect(refresh).not.toHaveBeenCalled();
  });

  it('a server that is broken is lost, and another attempt follows', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().refuse(503);

    expect(statuses).toEqual(['connecting', 'live', 'lost']);

    await retryAttempt();

    expect(sockets).toHaveLength(2);
  });

  /**
   * **A phone with no signal is the fourth, and it joins the other three here.** No attempt is
   * made — `onlineManager` has already established there is nothing to attempt over — and the
   * status is `lost` rather than `connecting`, because there is no handshake in progress and
   * nothing about waiting would be honest.
   */
  it('a phone with no signal is lost, and attempts nothing until it is back', async () => {
    onlineManager.setOnline(false);

    const { statuses } = followTheRoom();
    await connectAttempt();

    expect(statuses).toEqual(['lost']);
    expect(sockets).toEqual([]);

    onlineManager.setOnline(true);
    await connectAttempt();

    expect(statuses).toEqual(['lost', 'connecting']);
    expect(sockets).toHaveLength(1);
  });

  /**
   * A refusal that is not about the credential will be refused again for ever — a destroyed room
   * answers `404` to every attempt — and the read path beside this one is what takes the screen
   * away.
   */
  it('a refusal that is not about the credential is not repeated', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();

    latest().refuse(404);
    await jest.advanceTimersByTimeAsync(REOPEN_MS * 4);

    expect(statuses).toEqual(['connecting', 'live', 'lost']);
    expect(sockets).toHaveLength(1);
  });
});

describe('the background', () => {
  /**
   * ADR-0147 §9: iOS severs a backgrounded app's connections, so the channel is closed on the way
   * out and re-opened on the way in — **the same code path as any other reconnect.** `closed` is a
   * status of its own because a deliberate close is not news about the room, and *not live* is
   * drawn only in the foreground.
   */
  it('closes the channel deliberately, and re-opens on the way back', async () => {
    const { statuses } = followTheRoom();
    await connectAttempt();
    latest().answer();

    focusManager.setFocused(false);

    expect(statuses).toEqual(['connecting', 'live', 'closed']);
    expect(sockets[0]?.aborted).toBe(true);

    focusManager.setFocused(true);
    await connectAttempt();

    expect(statuses).toEqual(['connecting', 'live', 'closed', 'connecting']);
    expect(sockets).toHaveLength(2);
    // A fresh bag, because the one the closed channel held may be a quarter of an hour old.
    expect(latest().headers.Authorization).toBe('Bearer access-1');
  });
});

describe('stopping', () => {
  it('closes the channel and reports nothing afterwards', async () => {
    const { statuses, nudges, stop } = followTheRoom();
    await connectAttempt();
    latest().answer();

    const said = statuses.length;
    const heard = nudges.length;

    stop();
    await jest.advanceTimersByTimeAsync(REOPEN_MS * 4);

    expect(sockets[0]?.aborted).toBe(true);
    expect(sockets).toHaveLength(1);

    // The lifecycle managers are no longer listened to either.
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    onlineManager.setOnline(false);
    await retryAttempt();

    expect(statuses).toHaveLength(said);
    expect(nudges).toHaveLength(heard);
    expect(sockets).toHaveLength(1);
  });
});
