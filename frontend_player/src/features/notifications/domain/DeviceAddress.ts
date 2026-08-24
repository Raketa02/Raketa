/**
 * One phone that has told the platform where to reach it.
 *
 * Three facts and no fourth: where to send, which store the app came from, and
 * what Time Sensitive is set to. The backend's `PushDevice` is the same three
 * plus the moment it was registered, which is the server's to stamp.
 *
 * **`timeSensitive` is reported and never acted on** (`ADR-0065`). Nothing in
 * this app reads it back, branches on it, or shows it: a player who has revoked
 * keeps her standby priority, still gets the seat, and still sees the line when
 * she next looks. It is here so that *if a large fraction of players revoke, we
 * would learn it* — which is the only reason the field exists on either side.
 *
 * The two vocabularies are the OS's, and `mappers/codes.ts` pins them equal to
 * the contract's in both directions.
 */

import type { DeviceKind, TimeSensitiveReading } from '@/shared/lib/notifications';

export interface DeviceAddress {
  /** Opaque to us and to the server. An address that is also a capability. */
  readonly token: string;
  readonly platform: DeviceKind;
  readonly timeSensitive: TimeSensitiveReading;
}
