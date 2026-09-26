/**
 * **The Adult attestation, on an account that already exists** — *Start playing*'s first step
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §4–§5). A pass-through, as the uniform-strict rule allows: the attestation is one boolean the
 * player gives, and the only value this app sends is `true` — the form refuses before a round trip,
 * and the server again by code.
 */

import { postAdultAttestation } from '../api/authApi';

export async function attestAdult(): Promise<void> {
  await postAdultAttestation({ adult_attested: true });
}
