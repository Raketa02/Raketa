/**
 * **The stub backend**: the club surface as a small HTTP server that answers with payloads typed
 * from the generated contract and records every request it receives (ADR-0187 §6).
 *
 * The website's server layer is pointed at it by `API_URL`, so the pages under test reach it the
 * way they reach the real backend: over HTTP, from the server, never from the browser. A test
 * installs a handler per operation with {@link StubBackend.on}, whose reply the compiler checks
 * against that operation's declared responses, and reads what arrived with
 * {@link StubBackend.requests}.
 *
 * It also serves the map's tiles, so no test fetches OpenStreetMap.
 */

import http from 'node:http';
import type { AddressInfo } from 'node:net';

import type { components, paths } from '../../src/generated/schema';

type Method = 'get' | 'put' | 'post' | 'delete';
type Path = keyof paths;

/** The methods a path actually declares. */
export type MethodOf<P extends Path> = {
  [M in Method]: paths[P][M] extends never | undefined ? never : M;
}[Method];

type Operation<P extends Path, M extends Method> = NonNullable<paths[P][M]>;
type Responses<O> = O extends { responses: infer R } ? R : never;
type Json<R> = R extends { content: { 'application/json': infer B } } ? B : undefined;
type RequestBody<O> = O extends { requestBody: { content: { 'application/json': infer B } } }
  ? B
  : O extends { requestBody?: { content: { 'application/json': infer B } } }
    ? B
    : undefined;

export type ErrorBody = components['schemas']['ErrorResponse'];

/**
 * A reply this operation declares, or an error envelope under a status the backend sends without
 * declaring it per route: the bearer check's `401`, and a failure's `5xx`. And `422` with the
 * envelope: the contract declares FastAPI's `HTTPValidationError` there, but the backend answers
 * every `422` with the envelope (`validation_error`). `drop` closes the connection unanswered,
 * which is what an unreachable backend looks like from the website.
 */
export type Reply<P extends Path, M extends MethodOf<P>> =
  | {
      [S in keyof Responses<Operation<P, M>>]: {
        status: S;
        body: Json<Responses<Operation<P, M>>[S]>;
      };
    }[keyof Responses<Operation<P, M>>]
  | { status: 401 | 422 | 500 | 503; body: ErrorBody }
  | { status: 'drop' };

export interface Received<P extends Path = Path, M extends Method = Method> {
  readonly method: M;
  readonly path: P;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: M extends MethodOf<P> ? RequestBody<Operation<P, M>> : unknown;
  /** When it arrived, in milliseconds since the stub started. */
  readonly at: number;
}

type AnyReply = { status: number | 'drop'; body?: unknown };
type AnyHandler = (request: Received) => AnyReply | Promise<AnyReply>;

/** A 1 × 1 transparent PNG: every tile the map asks for. */
const TILE = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
  'base64',
);

/** An error envelope, as every backend refusal is shaped. */
export function refusal(code: string, field?: string): ErrorBody {
  return {
    code,
    message: `stub: ${code}`,
    trace_id: 'stub-trace',
    details: field === undefined ? null : { field },
  };
}

export class StubBackend {
  private readonly handlers = new Map<string, AnyHandler>();
  private readonly log: Received[] = [];
  private readonly started = Date.now();
  /** Tiles served since the last reset. */
  tiles = 0;

  private constructor(private readonly server: http.Server) {}

  static async start(port: number): Promise<StubBackend> {
    const server = http.createServer((request, response) => {
      void stub.handle(request, response);
    });
    const stub = new StubBackend(server);
    await new Promise<void>((resolve, reject) => {
      server.once('error', reject);
      server.listen(port, '127.0.0.1', () => resolve());
    });
    return stub;
  }

  get port(): number {
    return (this.server.address() as AddressInfo).port;
  }

  stop(): Promise<void> {
    this.server.closeAllConnections();
    return new Promise((resolve) => this.server.close(() => resolve()));
  }

  /** Forget every handler and every request: each test starts from nothing. */
  reset(): void {
    this.handlers.clear();
    this.log.length = 0;
    this.tiles = 0;
  }

  on<P extends Path, M extends MethodOf<P>>(
    method: M,
    path: P,
    handler: (request: Received<P, M>) => Reply<P, M> | Promise<Reply<P, M>>,
  ): void {
    this.handlers.set(`${method.toUpperCase()} ${path}`, handler as unknown as AnyHandler);
  }

  /** Every request that arrived for one operation, oldest first. */
  requests<P extends Path, M extends MethodOf<P>>(method: M, path: P): Received<P, M>[] {
    return this.log.filter(
      (request) => request.method === method && request.path === path,
    ) as unknown as Received<P, M>[];
  }

  /** Every request that arrived, of any kind, tiles aside. */
  all(): readonly Received[] {
    return this.log;
  }

  private async handle(request: http.IncomingMessage, response: http.ServerResponse) {
    const url = new URL(request.url ?? '/', 'http://stub');
    if (request.method === 'GET' && url.pathname.startsWith('/tiles/')) {
      this.tiles += 1;
      response.writeHead(200, { 'content-type': 'image/png', 'cache-control': 'no-store' });
      response.end(TILE);
      return;
    }

    const chunks: Buffer[] = [];
    for await (const chunk of request) chunks.push(chunk as Buffer);
    const raw = Buffer.concat(chunks).toString('utf8');
    const headers: Record<string, string> = {};
    for (const [name, value] of Object.entries(request.headers)) {
      if (typeof value === 'string') headers[name] = value;
    }
    const received = {
      method: (request.method ?? 'GET').toLowerCase() as Method,
      path: url.pathname as Path,
      headers,
      body: raw === '' ? undefined : (JSON.parse(raw) as unknown),
      at: Date.now() - this.started,
    } as Received;
    this.log.push(received);

    const handler = this.handlers.get(`${request.method} ${url.pathname}`);
    const reply: AnyReply =
      handler === undefined
        ? { status: 404, body: refusal('stub_no_handler') }
        : await handler(received);

    if (reply.status === 'drop') {
      request.socket.destroy();
      return;
    }
    if (reply.body === undefined) {
      response.writeHead(reply.status, { 'content-length': '0' });
      response.end();
      return;
    }
    const json = JSON.stringify(reply.body);
    response.writeHead(reply.status, { 'content-type': 'application/json' });
    response.end(json);
  }
}
