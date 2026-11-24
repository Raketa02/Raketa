/**
 * The one thing tests fake: the socket.
 *
 * Everything above it runs for real — `shared/lib/http` with its timeouts and
 * correlation ids, error mapping, the mappers, the use-cases, the hooks and the screens.
 * A test that passes here means the flow works end to end minus the network, which is
 * the seam the backend's own `tests/api/` suite uses and the shape this app copies.
 *
 * **Responses are typed from the generated schema.** That is the point of typing them at
 * all: a backend shape change then fails `pnpm typecheck` rather than failing a test run
 * with a confusing assertion, and no test can quietly describe a response the contract
 * does not produce.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import type { components } from '@/generated/schema';

export type Wire = components['schemas'];

/** What the fake server does with one request. */
export type Responder = (request: RecordedRequest) => Response | Promise<Response>;

export interface RecordedRequest {
  readonly method: string;
  /** Path only — the base URL is stripped, so tests name routes the way the API does. */
  readonly path: string;
  /**
   * The whole URL, host included — for the one question `path` cannot answer: **which host**.
   * The app talks to two, the API and the feature-flag datafiles' (ADR-0180 §4), and a request
   * that reached the right path on the wrong one is the bug a stripped path would hide.
   */
  readonly url: string;
  readonly headers: Readonly<Record<string, string>>;
  /** The parsed JSON body, or `undefined` when there was none. */
  readonly body: unknown;
}

export interface Transport {
  /** Answer `METHOD /path` with this responder. A later call replaces an earlier one. */
  readonly on: (method: string, path: string, responder: Responder) => void;
  /** Every request that reached the socket, in order. */
  readonly requests: readonly RecordedRequest[];
  /** Requests for one route — the shape most assertions want. */
  readonly requestsTo: (method: string, path: string) => readonly RecordedRequest[];
  /**
   * **What a stubbed route answers right now, with nothing reaching the socket** — for a fake route
   * the server builds out of another: Home's *TO CONFIRM* rows are the payments to confirm'
   * (`stubHome`). Not recorded, so no suite counts it as a request; `undefined` for a route with no
   * stub. **Called in step**, so a responder built on it answers as quickly as any other: a body
   * awaited inside a responder costs it a turn, and a launch that runs every pending timer then
   * times the request out. Read what `json` was handed with `servedBody`.
   */
  readonly answerNow: (method: string, path: string) => ReturnType<Responder> | undefined;
  /**
   * **Hold every request to a stubbed route on its way** (#872) until the walk ends them — a screen's
   * first read held in flight across the navigation that opens it. **Every request, not the next one**,
   * query strings included (a page's cursor, a sport), and **each deaf to the client's abort**
   * (`deafToAborts`): the harness runs every pending timer on a navigation, the read's 15 s timeout
   * among them, and a read timed out is one that failed and is asked again — not the read in flight a
   * slow server leaves on a phone. **The route's own responder is the one it had when held** — a
   * route held again is answered by the responder both holds stand in for — and ending the hold puts
   * it back for every request after, unless the walk stubbed the route again meanwhile.
   */
  readonly hold: (method: string, path: string) => HeldRoute;
  readonly restore: () => void;
}

/** A route's requests held on their way — see `Transport.hold`. Call inside `act`. */
export interface HeldRoute {
  /** Answer every request held as the route's own responder answers it. */
  readonly land: () => void;
  /** Fail every request held as a lost connection does (`networkFailure`). */
  readonly drop: () => void;
}

/** What each `json` response was built from — for `servedBody`. */
const SERVED = new WeakMap<Response, unknown>();

/** A JSON response, typed against whatever the caller says the route returns. */
export function json<T>(body: T, status = 200): Response {
  const response = new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
  SERVED.set(response, body);
  return response;
}

/**
 * **What a `json` response was built from**, read at once rather than off its body — see
 * `answerNow`. `undefined` for any other response.
 */
export function servedBody(response: Response): unknown {
  return SERVED.get(response);
}

/** The backend's error envelope — the same shape on every failing route. */
export function errorResponse(status: number, code: string, message = 'test failure'): Response {
  const envelope: Wire['ErrorResponse'] = {
    code,
    message,
    trace_id: 'trace-test',
    details: null,
  };
  return json(envelope, status);
}

/** 204, which several routes genuinely return and which has no body to parse. */
export function noContent(): Response {
  return new Response(null, { status: 204 });
}

/**
 * The bytes behind a local `file://` URI, for the one caller that reads one.
 *
 * `httpUpload` turns a picked image into bytes with `fetch`, because `fetch` is what
 * `shared/lib/http` is allowed to touch — so a local read arrives at this fake socket like
 * any other request. It is answered by default rather than stubbed per test: what is under
 * a picker's URI is the device's business, and a suite about a photos screen should not
 * have to describe a filesystem to get one.
 *
 * A test that wants a *failing* read says so, with `transport.on('GET', uri, ...)`.
 */
export function fileBytes(uri: string): Response {
  return new Response(`the bytes of ${uri}`, {
    status: 200,
    headers: { 'Content-Type': 'application/octet-stream' },
  });
}

/**
 * A served Transcript of `answers` entries, for a step fixture that needs one.
 *
 * Every step the backend returns carries the answers already given, so a fixture must
 * carry one too — and its length is `questions_asked`, never anything else. That is the
 * only property of it any fixture here depends on: nothing in the app reads the entries
 * yet, so their copy is filler and deliberately looks like filler. A screen that starts
 * rendering answered questions wants real copy, and should say so by writing it out.
 */
export function transcriptOf(answers: number): Wire['AssessmentStepResponse']['transcript'] {
  return Array.from({ length: answers }, (_unused, index) => ({
    question: {
      id: `answered-${index + 1}`,
      category: 'Answered',
      tier: null,
      situation: `The situation for answer ${index + 1}`,
      text: `The question answered at position ${index + 1}`,
      qualifier: 'Choose the option that fits best.',
      options: [
        { id: 'chosen', text: 'What the player chose' },
        { id: 'other', text: 'What they did not' },
      ],
    },
    option_id: 'chosen',
  }));
}

/**
 * A transport failure — nothing reached the server.
 *
 * React Native's `fetch` rejects with a bare `TypeError` here, which is why the error
 * model classifies it by *what threw* rather than by reading its message.
 */
export function networkFailure(): Responder {
  return () => Promise.reject(new TypeError('Network request failed'));
}

/** Responders that answer through the client's own abort — see `deafToAborts`. */
const DEAF = new WeakSet<Responder>();

/** A route's holding responder, and the route's own it stands in for — see `Transport.hold`. */
const HOLDING = new WeakMap<Responder, Responder>();

/**
 * **A responder deaf to the client's abort** (#871) — for a read a walk holds on its way across a
 * navigation. The harness runs every pending timer on a navigation, the client's 15 s timeout among
 * them, so a held read would time out under it, which no phone does in the instant a screen opens.
 * Deaf, the read stays on its way until the walk answers it. Query's own cancellation still ends it
 * for Query, which stops waiting whatever the socket does.
 */
export function deafToAborts(responder: Responder): Responder {
  DEAF.add(responder);
  return responder;
}

/** A server that accepts the connection and never answers. Drives the timeout path. */
export function neverResponds(): Responder {
  return () => new Promise<Response>(() => {});
}

/**
 * How a route is addressed — **the method and the path, with any query string dropped.**
 *
 * A stub names a route the way the API does, and `?before_seq=12` is an argument to one rather
 * than a second route. What was actually asked for is still on every `RecordedRequest.path`
 * whole, so a suite that wants to assert a cursor reads it there.
 */
function keyOf(method: string, path: string): string {
  const [route] = path.split('?');
  return `${method.toUpperCase()} ${route ?? path}`;
}

/**
 * Install the fake socket. Call in `beforeEach`; `restore()` in `afterEach`.
 *
 * An unstubbed route throws rather than returning a default. A test that silently got a
 * 200 from a route it never described is a test that proves nothing.
 */
export function installTransport(): Transport {
  const routes = new Map<string, Responder>();
  const requests: RecordedRequest[] = [];
  const original = global.fetch;

  const fakeFetch: typeof fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : String(input);
    const path = url.replace(/^https?:\/\/[^/]+/, '');
    const method = (init?.method ?? 'GET').toUpperCase();

    const headers: Record<string, string> = {};
    for (const [name, value] of Object.entries((init?.headers ?? {}) as Record<string, string>)) {
      headers[name] = value;
    }

    const recorded: RecordedRequest = {
      method,
      path,
      url,
      headers,
      body: typeof init?.body === 'string' ? JSON.parse(init.body) : undefined,
    };
    requests.push(recorded);

    const responder = routes.get(keyOf(method, path)) ?? defaultResponderFor(path);
    if (responder === undefined) {
      throw new Error(
        `No stub for ${method} ${path}. Stub it with transport.on(), or the test is ` +
          `asserting against a request it never described.`,
      );
    }

    // Honour cancellation the way a real socket does, so an aborted request rejects
    // rather than resolving after the caller has gone.
    const signal = init?.signal;
    if (signal?.aborted === true) throw abortError();

    const response = responder(recorded);
    if (signal == null || DEAF.has(responder)) return response;

    return Promise.race([
      Promise.resolve(response),
      new Promise<Response>((_resolve, reject) => {
        signal.addEventListener('abort', () => reject(abortError()));
      }),
    ]);
  };

  global.fetch = fakeFetch;

  return {
    on(method, path, responder) {
      routes.set(keyOf(method, path), responder);
    },
    requests,
    requestsTo(method, path) {
      const wanted = keyOf(method, path);
      return requests.filter((r) => keyOf(r.method, r.path) === wanted);
    },
    answerNow(method, path) {
      const responder = routes.get(keyOf(method, path));
      if (responder === undefined) return undefined;
      return responder({ method, path, url: path, headers: {}, body: undefined });
    },
    hold(method, path) {
      const key = keyOf(method, path);
      const stubbed = routes.get(key);
      if (stubbed === undefined) throw new Error(`No stub for ${key} to hold.`);
      // Held already: this hold answers with the route's own, never the other hold's.
      const answer = HOLDING.get(stubbed) ?? stubbed;
      const waiting: {
        readonly request: RecordedRequest;
        readonly resolve: (response: Response | Promise<Response>) => void;
        readonly reject: (failure: Error) => void;
      }[] = [];
      const holding = deafToAborts(
        (request) =>
          new Promise<Response>((resolve, reject) => {
            waiting.push({ request, resolve, reject });
          }),
      );
      HOLDING.set(holding, answer);
      routes.set(key, holding);
      // The route's own answer from now on — unless the walk stubbed it again while it was held.
      const end = (each: (held: (typeof waiting)[number]) => void) => {
        if (routes.get(key) === holding) routes.set(key, answer);
        for (const held of waiting.splice(0)) each(held);
      };
      return {
        land: () =>
          end(({ request, resolve, reject }) => {
            // One responder that throws fails its own request, never the rest held with it.
            try {
              resolve(answer(request));
            } catch (failure) {
              reject(failure instanceof Error ? failure : new Error(String(failure)));
            }
          }),
        drop: () => end(({ reject }) => reject(new TypeError('Network request failed'))),
      };
    },
    restore() {
      global.fetch = original;
    },
  };
}

/** Reads of the device's own storage are answered without a stub — see `fileBytes`. */
function defaultResponderFor(path: string): Responder | undefined {
  return path.startsWith('file://') ? () => fileBytes(path) : undefined;
}

function abortError(): Error {
  const error = new Error('Aborted');
  error.name = 'AbortError';
  return error;
}
