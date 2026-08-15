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
  readonly restore: () => void;
}

/** A JSON response, typed against whatever the caller says the route returns. */
export function json<T>(body: T, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
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

/** A server that accepts the connection and never answers. Drives the timeout path. */
export function neverResponds(): Responder {
  return () => new Promise<Response>(() => {});
}

function keyOf(method: string, path: string): string {
  return `${method.toUpperCase()} ${path}`;
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
      headers,
      body: typeof init?.body === 'string' ? JSON.parse(init.body) : undefined,
    };
    requests.push(recorded);

    const responder = routes.get(keyOf(method, path));
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
    if (signal == null) return response;

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
    restore() {
      global.fetch = original;
    },
  };
}

function abortError(): Error {
  const error = new Error('Aborted');
  error.name = 'AbortError';
  return error;
}
