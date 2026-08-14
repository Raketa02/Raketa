/**
 * The one normalized error family. Raw `fetch` rejections and arbitrary backend JSON
 * must never reach a screen — see docs/architecture.md Part 6.
 *
 * Two rules give this file its shape:
 *
 * 1. **Branch on `code`, never on `message`.** `message` is a diagnostic the backend
 *    writes for a log; it changes the moment someone improves the copy or the app is
 *    localized. The backend gives every failure a stable machine-readable `code`, and
 *    that is the only half of the envelope a client may read.
 *
 * 2. **Every error carries a recovery category.** Assigning it is part of adding an
 *    endpoint. Without it every failure ends up behind one generic modal, and the app
 *    cannot tell "try again in a second" from "you typed your password wrong" from
 *    "your session is over".
 */

/**
 * What the app is entitled to *do* about a failure. This is the axis a screen branches
 * on; `kind` is the axis a log line records.
 */
export type Recovery =
  /** Transient and machine-recoverable — the retry policy may handle it unattended. */
  | 'retryable-automatically'
  /** The player can retry, but only they can decide to: it costs data, or repeats a write. */
  | 'retryable-by-user'
  /** The session is over. The ONLY category that may touch the session state machine. */
  | 'requires-reauthentication'
  /** The request was wrong. Fix the input; retrying it unchanged fails identically. */
  | 'requires-user-correction'
  /** The server is in a state that makes this operation meaningless. Reconcile, don't retry. */
  | 'business-conflict'
  /** Nothing the client can do. Report it and stop. */
  | 'terminal';

export type AppErrorKind =
  | 'network-unavailable'
  | 'timeout'
  | 'unauthorized'
  | 'forbidden'
  | 'validation'
  | 'not-found'
  | 'conflict'
  | 'rate-limit'
  | 'server'
  | 'unknown';

export interface AppErrorContext {
  /** The backend's stable identifier, when the failure came from the backend at all. */
  readonly code?: string;
  /** The backend's request id, echoed on `X-Request-ID`. Ties this to a server log. */
  readonly traceId?: string;
  readonly status?: number;
  readonly details?: Readonly<Record<string, unknown>>;
  /** What actually threw, when this wraps a lower-level failure. Never rendered. */
  readonly cause?: unknown;
}

/**
 * Every failure the app can observe, as one type.
 *
 * `message` is deliberately the backend's diagnostic, not user-facing copy: localization
 * goes backend code -> frontend message, so the screen chooses its wording from `code`
 * and `kind`. Rendering `message` directly is a fallback, not the design.
 */
export class AppError extends Error {
  override readonly name = 'AppError';
  readonly kind: AppErrorKind;
  readonly recovery: Recovery;
  readonly code?: string;
  readonly traceId?: string;
  readonly status?: number;
  readonly details?: Readonly<Record<string, unknown>>;

  constructor(
    kind: AppErrorKind,
    recovery: Recovery,
    message: string,
    context: AppErrorContext = {},
  ) {
    super(message, context.cause === undefined ? undefined : { cause: context.cause });
    this.kind = kind;
    this.recovery = recovery;
    this.code = context.code;
    this.traceId = context.traceId;
    this.status = context.status;
    this.details = context.details;
  }

  /**
   * The single question the session state machine is allowed to ask an error.
   *
   * **Not every 4xx is a logout.** A 403 means "you may not do this" — the session is
   * perfectly valid and signing the player out in response is both wrong and
   * infuriating. Only an authentication-invalidating response ends a session.
   */
  get invalidatesSession(): boolean {
    return this.recovery === 'requires-reauthentication';
  }
}

export function isAppError(value: unknown): value is AppError {
  return value instanceof AppError;
}

/** Nothing reached the server. Says nothing about whether the session is still valid. */
export function networkUnavailable(cause?: unknown): AppError {
  return new AppError(
    'network-unavailable',
    'retryable-automatically',
    'The request could not reach the server.',
    { cause },
  );
}

/**
 * The request was abandoned on our side. `fetch` has no default timeout, so this is
 * raised by the timeout policy in shared/lib/http rather than by the platform.
 */
export function timedOut(afterMs: number): AppError {
  return new AppError(
    'timeout',
    'retryable-automatically',
    `The request timed out after ${afterMs}ms.`,
    { details: { afterMs } },
  );
}

/** A failure with no envelope behind it — a decode failure, or a thrown non-Error. */
export function unknownFailure(message: string, cause?: unknown): AppError {
  return new AppError('unknown', 'terminal', message, { cause });
}
