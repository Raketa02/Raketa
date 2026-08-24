/**
 * The wire's closed vocabularies for one registered phone, and the pin that
 * keeps them equal to what the OS can actually answer.
 *
 * Same rule as Now's `mappers/codes.ts`: every alias is the union
 * `openapi-typescript` emits from `backend/openapi.player.json`, re-exported
 * under the name this feature uses, and **nothing is retyped** — a hand-written
 * copy of a wire enum is a copy of whatever somebody last remembered.
 *
 * What is new here is that the same two vocabularies exist on the **other**
 * side as well: `shared/lib/notifications` says what the phone can report, and
 * the backend says what the wire will accept. Those are two independent sources
 * for one set of values, so they are pinned **equal in both directions** below.
 * A fourth `TimeSensitiveSetting` on the contract then fails `pnpm typecheck`
 * here — where the fix is a reader that can produce it — rather than compiling
 * into a client that can never send it.
 */

import type { components } from '@/generated/schema';
import type { DeviceKind, TimeSensitiveReading } from '@/shared/lib/notifications';

/**
 * What `UNNotificationSettings.timeSensitiveSetting` said, as reported.
 *
 * **Nothing branches on it** (`ADR-0065`): the cascade does not demote a player
 * who has revoked, and neither does this client. It is observability, and
 * `notSupported` is a fourth value rather than a synonym for a refusal.
 */
export type TimeSensitiveSetting = components['schemas']['TimeSensitiveSetting'];

/** Which store the app came from, which is which fields a message carries. */
export type DevicePlatform = components['schemas']['Platform'];

/** The body `PUT /api/v1/push/device` takes. */
export type RegisterDeviceRequest = components['schemas']['RegisterDeviceRequest'];

/**
 * `true` only when `T` is a closed union — an index signature answers `false`.
 *
 * Two lines, and a local copy rather than a promotion: Now's `mappers/codes.ts`
 * holds the same pair and does not export them, and this app's rule is to keep a
 * thing local until cross-feature ownership is proven rather than to move it
 * because a second file wanted it.
 */
export type IsClosedUnion<T extends string> = string extends T ? false : true;

/** A compile error unless `T` is `true`. */
export type AssertTrue<T extends true> = T;

/** Mutual assignability — narrower on either side is a failure, not a pass. */
export type Equal<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;

/** Fails to compile if either code ever arrives as a bare string. */
export type CodesAreClosed = AssertTrue<
  IsClosedUnion<TimeSensitiveSetting> & IsClosedUnion<DevicePlatform>
>;

/**
 * The contract and the phone name the same three settings and the same two
 * platforms. Either side growing, shrinking or renaming a value fails here.
 */
export type TimeSensitiveMatchesTheOs = AssertTrue<
  Equal<TimeSensitiveSetting, TimeSensitiveReading>
>;
export type PlatformMatchesTheOs = AssertTrue<Equal<DevicePlatform, DeviceKind>>;
