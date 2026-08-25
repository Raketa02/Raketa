/**
 * Sending a file: what it shares with every other request, and the two things only it has.
 *
 * The rotation, the auth header and the error mapping are `httpClient`'s and are covered
 * there — what is asserted here is that an upload really does go through them rather than
 * around them, plus the local read and the stages a screen draws from.
 */

import { AppError } from '@/shared/errors';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  type Transport,
} from '@/test-support/transport';

import { configureHttp, resetHttp } from './httpClient';
import { httpUpload } from './httpUpload';
import { TIMEOUT_MS } from './timeouts';

let transport: Transport;

const PHOTO_URI = 'file:///photos/one.jpg';
const PHOTOS_PATH = '/api/v1/photos';

function credentialsFor(accessToken: string | undefined) {
  return {
    current: () => (accessToken === undefined ? undefined : { accessToken, generation: 1 }),
    refresh: () => Promise.resolve('unavailable' as const),
    abandon: () => Promise.resolve(),
  };
}

function upload(overrides: Partial<Parameters<typeof httpUpload>[0]> = {}) {
  return httpUpload<{ photo_id: string }>({
    path: PHOTOS_PATH,
    uri: PHOTO_URI,
    contentType: 'image/jpeg',
    authenticated: true,
    ...overrides,
  });
}

beforeEach(() => {
  transport = installTransport();
  resetHttp();
  configureHttp(credentialsFor('token-1'));
});

afterEach(() => {
  transport.restore();
  resetHttp();
  jest.useRealTimers();
});

describe('the request an upload makes', () => {
  it('reads the local file first, then posts its bytes to the API', async () => {
    transport.on('POST', PHOTOS_PATH, () => json({ photo_id: 'photo-1' }));

    await upload();

    expect(transport.requests.map((request) => `${request.method} ${request.path}`)).toEqual([
      `GET ${PHOTO_URI}`,
      `POST ${PHOTOS_PATH}`,
    ]);
  });

  it('names the format in Content-Type, which is what the endpoint reads', async () => {
    transport.on('POST', PHOTOS_PATH, () => json({ photo_id: 'photo-1' }));

    await upload({ contentType: 'image/png' });

    expect(transport.requestsTo('POST', PHOTOS_PATH)[0]?.headers['Content-Type']).toBe('image/png');
  });

  it('carries the access token and a correlation id, like every other request', async () => {
    transport.on('POST', PHOTOS_PATH, () => json({ photo_id: 'photo-1' }));

    await upload();

    const sent = transport.requestsTo('POST', PHOTOS_PATH)[0];
    expect(sent?.headers.Authorization).toBe('Bearer token-1');
    expect(sent?.headers['X-Request-ID']).toMatch(/^[A-Za-z0-9._-]{1,64}$/);
  });

  it('gets the upload timeout, not the interactive one — an uplink is the slow half', async () => {
    jest.useFakeTimers();
    transport.on('POST', PHOTOS_PATH, neverResponds());

    const pending = upload();
    // Assert before advancing, or an unhandled rejection escapes the microtask queue.
    const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });

    // Past the interactive timeout, and the upload is still running. The async form is
    // what lets the local read — two promises deep — settle between the two advances.
    await jest.advanceTimersByTimeAsync(TIMEOUT_MS.request + 1);
    expect(transport.requestsTo('POST', PHOTOS_PATH)).toHaveLength(1);

    await jest.advanceTimersByTimeAsync(TIMEOUT_MS.upload);
    await assertion;
  });
});

describe('what a screen is told while it waits', () => {
  it('reports the stages it can actually observe, in order, ending at one', async () => {
    transport.on('POST', PHOTOS_PATH, () => json({ photo_id: 'photo-1' }));
    const seen: number[] = [];

    await upload({ onProgress: (fraction) => seen.push(fraction) });

    expect(seen).toEqual([0, 0.5, 1]);
  });

  it('stops at the stage that failed rather than completing', async () => {
    transport.on('POST', PHOTOS_PATH, () => errorResponse(413, 'image_too_large'));
    const seen: number[] = [];

    await expect(upload({ onProgress: (fraction) => seen.push(fraction) })).rejects.toBeInstanceOf(
      AppError,
    );

    expect(seen).toEqual([0, 0.5]);
  });
});

describe('a file that cannot be read', () => {
  it('fails as an AppError the player may retry, never as a raw rejection', async () => {
    transport.on('GET', PHOTO_URI, () => Promise.reject(new TypeError('no such file')));

    const failure = await upload().then(
      () => undefined,
      (error: AppError) => error,
    );

    expect(failure).toBeInstanceOf(AppError);
    expect(failure?.recovery).toBe('retryable-by-user');
  });

  it('never reaches the API — there is nothing to send', async () => {
    transport.on('GET', PHOTO_URI, () => Promise.reject(new TypeError('no such file')));

    await upload().catch(() => undefined);

    expect(transport.requestsTo('POST', PHOTOS_PATH)).toHaveLength(0);
  });
});

describe('the backend refusing the image', () => {
  it('arrives as an AppError carrying the code the tile branches on', async () => {
    transport.on('POST', PHOTOS_PATH, () => errorResponse(400, 'unsupported_image_format'));

    const failure = await upload().then(
      () => undefined,
      (error: AppError) => error,
    );

    expect(failure?.code).toBe('unsupported_image_format');
  });
});
