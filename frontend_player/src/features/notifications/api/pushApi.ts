/**
 * The wire adapter for one registered phone. One path, one method, no answer.
 *
 * **`PUT` and not `POST`**, which is the backend's own reasoning and is why
 * there is no idempotency key here and no retry decision to make: the address of
 * one phone is a thing that is *set*, and the same handset re-registers on every
 * sign-in, every token rotation and every settings change. A second identical
 * registration is the same statement made twice.
 *
 * **204, and nothing comes back.** `ADR-0074`'s update is for acts taken **off
 * Now**, and this moves no card — so there is no cache to write, nothing to
 * invalidate, and nothing on any screen that changes because it succeeded.
 *
 * Nothing here decides anything: what to send is the use-case's, when to send is
 * the hook's, and whether the OS would answer at all is `shared/lib/notifications`'.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type RegisterDeviceRequest = components['schemas']['RegisterDeviceRequest'];

export interface RegisterDeviceOptions {
  readonly body: RegisterDeviceRequest;
  readonly signal?: AbortSignal;
}

/** Tell the platform where this phone is, and what it can be sent. */
export function registerDevice({ body, signal }: RegisterDeviceOptions): Promise<void> {
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/push/device',
    authenticated: true,
    body,
    signal,
  });
}
