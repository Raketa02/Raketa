/**
 * Sending one file, over the same socket, the same headers and the same 401 rotation as
 * every other request.
 *
 * It is a second **verb**, not a second networking path: `sendOnce` and `sendWithRotation`
 * are `httpClient`'s and are shared unchanged, and what is here is only the two things a
 * file makes different — where the bytes come from, and what a screen can be told while
 * they are in flight.
 *
 * ## Reading the file is this module's job because `fetch` is
 *
 * A picked image arrives from `ImagePickingPort` as a local `file://` URI, and turning one
 * into bytes is a `fetch` — the global every other file in the app is banned from touching.
 * So it happens here, beside the send, rather than in the feature that owns the photos.
 *
 * ## Progress is stages, and deliberately not bytes
 *
 * **React Native's `fetch` cannot report how much of a body has gone out.** Byte-level
 * progress needs `XMLHttpRequest`'s `upload.onprogress` or a native uploader, and either
 * one would be a second transport with its own headers, its own timeout and its own copy
 * of the rotation — the exact thing `shared/lib/http` exists to prevent, bought for a bar
 * that is on screen for a couple of seconds.
 *
 * So an upload reports the stages it genuinely passes through: the bytes are read off the
 * device, then they are sent. A screen drawing that gets a bar that moves for real reasons
 * and never claims a percentage nobody measured. `UPLOAD_STAGES` names them so a caller
 * can say *stage 1 of 2* rather than divide by a magic number.
 */

import { AppError } from '@/shared/errors';

import { buildUrl, sendOnce, sendWithRotation, type Attempt, type HttpMethod } from './httpClient';
import { TIMEOUT_MS } from './timeouts';

/**
 * What an upload passes through, in order. Two, and only two, because they are the two
 * this client can actually observe — see the module note.
 */
export const UPLOAD_STAGES = ['reading', 'sending'] as const;

export type UploadStage = (typeof UPLOAD_STAGES)[number];

/**
 * How far along an upload is, as a fraction between 0 and 1.
 *
 * `0` is *nothing has happened yet*, `1` is *the server has answered*. It is called at
 * least once before anything is sent, so a caller may draw from the first callback rather
 * than having to invent a starting value.
 */
export type UploadProgress = (fraction: number) => void;

export interface HttpUploadRequest {
  /** Path only, rooted at the API host — `/api/v1/photos`. */
  readonly path: string;
  /** A local `file://` URI, as `ImagePickingPort` hands one over. */
  readonly uri: string;
  /**
   * What the bytes are, sent as `Content-Type`.
   *
   * The backend reads **only** this header to decide whether it will accept the format,
   * and decodes the bytes themselves afterwards — so it is the caller's job to name a
   * type the endpoint accepts, and a wrong one is a refusal rather than a corruption.
   */
  readonly contentType: string;
  readonly authenticated: boolean;
  readonly signal?: AbortSignal;
  readonly onProgress?: UploadProgress;
}

/**
 * The file could not be read off the device.
 *
 * `retryable-by-user` rather than `terminal`: the URI a picker hands back can stop
 * resolving for reasons that pass — an iCloud original still downloading is the common
 * one — and the screen this reaches offers exactly that retry.
 */
function unreadableFile(uri: string, cause: unknown): AppError {
  return new AppError(
    'unknown',
    'retryable-by-user',
    // The URI, never the bytes: a path is a diagnostic, and the picture is the player's.
    `The image at ${uri} could not be read from the device.`,
    { cause },
  );
}

/**
 * The bytes behind a local URI.
 *
 * Not inside the timeout: the timeout policy bounds how long the *server* may take, and a
 * read from local storage that hangs is a device fault a request timeout would misreport
 * as an unreachable API.
 */
async function readBytes(uri: string, signal?: AbortSignal): Promise<Blob> {
  try {
    const file = await fetch(uri, { signal });
    return await file.blob();
  } catch (cause) {
    // A cancelled read is not a failure — the same exception the request path makes.
    if (signal?.aborted === true) throw cause;
    throw unreadableFile(uri, cause);
  }
}

const UPLOAD_METHOD: HttpMethod = 'POST';

/**
 * Send one file and return the decoded response.
 *
 * The body is a `Blob`, which matters: `sendWithRotation` may send it twice when a token
 * rotates underneath it, and a stream could only be sent once.
 */
export async function httpUpload<T>(request: HttpUploadRequest): Promise<T> {
  const url = buildUrl(request.path);
  const report = request.onProgress ?? (() => {});

  report(0);
  const body = await readBytes(request.uri, request.signal);
  report(1 / UPLOAD_STAGES.length);

  const send = (): Promise<Attempt> =>
    sendOnce({
      method: UPLOAD_METHOD,
      url,
      body,
      contentType: request.contentType,
      authenticated: request.authenticated,
      signal: request.signal,
      timeoutMs: TIMEOUT_MS.upload,
    });

  const answer = await sendWithRotation<T>(request.authenticated, send);
  report(1);
  return answer;
}
