/**
 * **The stub backend**: the public surface as a small HTTP server that answers with payloads
 * typed from the generated contract and records every request it receives (ADR-0187 §6).
 *
 * The site's server layer is pointed at it by `API_URL`, so the pages under test reach it the way
 * they reach the real backend: over HTTP, from the server, never from the browser. A test
 * installs a handler per operation with {@link StubBackend.on}, whose reply the compiler checks
 * against that operation's declared responses, and reads what arrived with
 * {@link StubBackend.requests}. An operation is named by its path as the contract writes it,
 * `{code}` and all, and a handler reads the ids it was called with in `params`.
 *
 * Beside the API it is **the stand-in photo storage**, at `/storage/`: a face the public surface
 * answers with is a signed link there, which expires, as the backend's are links into MinIO.
 *
 * This is the public site's own copy of the club website's stub, and changes on its own.
 */

import http from 'node:http';

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
 * declaring it per route: a failure's `5xx`, and `422` with the envelope (the contract declares
 * FastAPI's `HTTPValidationError` there, but the backend answers every `422` with the envelope).
 * `drop` closes the connection unanswered, which is what an unreachable backend looks like from
 * the site.
 */
export type Reply<P extends Path, M extends MethodOf<P>> =
  | {
      [S in keyof Responses<Operation<P, M>>]: {
        status: S;
        body: Json<Responses<Operation<P, M>>[S]>;
      };
    }[keyof Responses<Operation<P, M>>]
  | { status: 422 | 500 | 503; body: ErrorBody }
  | { status: 'drop' };

export interface Received<P extends Path = Path, M extends Method = Method> {
  readonly method: M;
  /** The path as the request named it, ids and all. */
  readonly path: string;
  /**
   * The path's ids, by the names the operation's template gives them: as a handler receives the
   * request, and as {@link StubBackend.requests} returns it.
   */
  readonly params: Readonly<Record<string, string>>;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: M extends MethodOf<P> ? RequestBody<Operation<P, M>> : unknown;
}

type AnyReply = { status: number | 'drop'; body?: unknown };
type AnyHandler = (request: Received) => AnyReply | Promise<AnyReply>;

/**
 * The ids a path holds in the places a template names, or `null` when the path is not one of the
 * template's.
 */
function paramsOf(template: string, path: string): Record<string, string> | null {
  const source = template
    .split(/(\{\w+\})/)
    .map((part) =>
      /^\{\w+\}$/.test(part)
        ? `(?<${part.slice(1, -1)}>[^/]+)`
        : part.replace(/[.*+?^$()|[\]\\]/g, '\\$&'),
    )
    .join('');
  const match = new RegExp(`^${source}$`).exec(path);
  if (match === null) return null;
  return Object.fromEntries(
    Object.entries(match.groups ?? {}).map(([name, value]) => [name, decodeURIComponent(value)]),
  );
}

/** An error envelope, as every backend refusal is shaped: `field` names the control it is about. */
export function refusal(code: string, field?: string): ErrorBody {
  return {
    code,
    message: `stub: ${code}`,
    trace_id: 'stub-trace',
    details: field === undefined ? null : { field },
  };
}

/** Where the stand-in photo storage answers, beside the API as MinIO answers beside the backend. */
const STORAGE = '/storage/';

/** A photograph the stand-in storage holds. */
interface StoredFile {
  readonly bytes: Buffer;
  readonly type: string;
}

export class StubBackend {
  private readonly handlers = new Map<string, AnyHandler>();
  private readonly log: Received[] = [];
  private readonly files = new Map<string, StoredFile>();
  /** The signatures still good, as `<key>?signature=<n>`: S3's presigned links, which expire. */
  private readonly signed = new Set<string>();
  private readonly opened: string[] = [];
  private signatures = 0;

  private constructor(
    private readonly server: http.Server,
    private readonly origin: string,
  ) {}

  static async start(port: number): Promise<StubBackend> {
    const server = http.createServer((request, response) => {
      void stub.handle(request, response);
    });
    const stub = new StubBackend(server, `http://127.0.0.1:${port}`);
    await new Promise<void>((resolve, reject) => {
      server.once('error', reject);
      server.listen(port, '127.0.0.1', () => resolve());
    });
    return stub;
  }

  stop(): Promise<void> {
    this.server.closeAllConnections();
    return new Promise((resolve) => this.server.close(() => resolve()));
  }

  /** Forget every handler, request and photograph: each test starts from nothing. */
  reset(): void {
    this.handlers.clear();
    this.log.length = 0;
    this.files.clear();
    this.signed.clear();
    this.opened.length = 0;
  }

  /**
   * **The stand-in photo storage**: keep a photograph under `key`, outside the contract, as the
   * backend keeps one in MinIO, always a JPEG. It is reached only by a link {@link signedLink}
   * mints.
   */
  store(key: string, jpeg: Buffer): void {
    this.files.set(key, { bytes: jpeg, type: 'image/jpeg' });
  }

  /**
   * A fresh signed link to a stored photograph, as the backend mints one for each response that
   * carries a face. It works until {@link expireSignedLinks}, as a presigned link works for
   * minutes, so whoever keeps one instead of reading again is refused.
   */
  signedLink(key: string): string {
    this.signatures += 1;
    const signed = `${encodeURIComponent(key)}?signature=${this.signatures}`;
    this.signed.add(signed);
    return `${this.origin}${STORAGE}${signed}`;
  }

  /** Every signed link minted so far stops working: the minutes have passed. */
  expireSignedLinks(): void {
    this.signed.clear();
  }

  /** Every link the storage was opened by, oldest first, as `<key>?signature=<n>`. */
  storageOpened(): string[] {
    return [...this.opened];
  }

  /**
   * A signed link's photograph, `403` once the link has expired, as S3 refuses one, or `404` when
   * nothing is stored under the key.
   */
  private serveStored(url: URL, response: http.ServerResponse): void {
    const signed = `${url.pathname.slice(STORAGE.length)}${url.search}`;
    this.opened.push(signed);
    const file = this.files.get(decodeURIComponent(url.pathname.slice(STORAGE.length)));
    if (file === undefined) {
      response.writeHead(404, { 'content-type': 'text/plain' });
      response.end('NoSuchKey');
      return;
    }
    if (!this.signed.has(signed)) {
      response.writeHead(403, { 'content-type': 'text/plain' });
      response.end('Request has expired');
      return;
    }
    response.writeHead(200, { 'content-type': file.type, 'content-length': file.bytes.length });
    response.end(file.bytes);
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
    return this.log.flatMap((request) => {
      const params = request.method === method ? paramsOf(path, request.path) : null;
      return params === null ? [] : [{ ...request, params }];
    }) as unknown as Received<P, M>[];
  }

  /**
   * The handler whose method and path template the request fits, or the stub's own 404. Where two
   * templates fit, the one with fewer ids wins.
   */
  private answer(received: Received): AnyReply | Promise<AnyReply> {
    let best: { handler: AnyHandler; params: Record<string, string> } | undefined;
    for (const [key, handler] of this.handlers) {
      const [method, template] = key.split(' ') as [string, string];
      const params =
        method === received.method.toUpperCase() ? paramsOf(template, received.path) : null;
      if (params === null) continue;
      if (best === undefined || Object.keys(params).length < Object.keys(best.params).length) {
        best = { handler, params };
      }
    }
    return best === undefined
      ? { status: 404, body: refusal('stub_no_handler') }
      : best.handler({ ...received, params: best.params });
  }

  private async handle(request: http.IncomingMessage, response: http.ServerResponse) {
    const url = new URL(request.url ?? '/', 'http://stub');
    if (url.pathname.startsWith(STORAGE)) {
      this.serveStored(url, response);
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
      path: url.pathname,
      params: {},
      headers,
      body: raw === '' ? undefined : (JSON.parse(raw) as unknown),
    } as Received;
    this.log.push(received);

    const reply: AnyReply = await this.answer(received);

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
