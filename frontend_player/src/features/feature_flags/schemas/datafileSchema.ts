/**
 * **Reading a datafile** — external input, from two places the app does not control: the flags
 * host, and the device's own storage, where a datafile saved by an older build may be waiting.
 *
 * Both are checked the same way before the SDK sees them. The SDK checks the envelope too, but its
 * answer to a bad one is to report it and **carry on with an empty datafile** — which would turn
 * every feature over to its code default and push out a good datafile the app already had. A
 * refusal here keeps that one in use instead (ADR-0180 §10).
 *
 * Only the envelope is checked. What a feature's rules say is the SDK's to read and the flags
 * repo's specs to prove; a Zod copy of Featurevisor's format would be a second reading of a
 * format another repository owns.
 */

import { z } from 'zod';

import { isReadableSchemaVersion, type Datafile } from '../domain/featureFlags';

/**
 * The envelope `createFeaturevisor` requires, and nothing more.
 *
 * `passthrough` rather than `strip`: `featurevisorVersion` and `variables` ride along untouched,
 * because the SDK is handed exactly what the flags repo built.
 */
const DatafileEnvelope = z
  .object({
    schemaVersion: z.string(),
    revision: z.string(),
    segments: z.record(z.unknown()),
    features: z.record(z.unknown()),
  })
  .passthrough();

/**
 * Why a value is not a datafile this build reads. `unknown-schema-version` is the refusal
 * ADR-0180 §10 names: a well-formed datafile in a format this build does not read. `malformed` is
 * anything that is not a datafile at all — the serve script's error page, a truncated write, a
 * value from before this key existed.
 */
export type DatafileRefusal = 'malformed' | 'unknown-schema-version';

export type DatafileReading =
  | { readonly readable: true; readonly datafile: Datafile }
  | { readonly readable: false; readonly reason: DatafileRefusal };

/** Check an untrusted value, and say whether it is a datafile this build reads. */
export function readDatafile(raw: unknown): DatafileReading {
  const parsed = DatafileEnvelope.safeParse(raw);

  if (!parsed.success) return { readable: false, reason: 'malformed' };

  if (!isReadableSchemaVersion(parsed.data.schemaVersion)) {
    return { readable: false, reason: 'unknown-schema-version' };
  }

  return { readable: true, datafile: parsed.data };
}
