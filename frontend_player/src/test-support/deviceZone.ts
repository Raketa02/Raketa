/**
 * Move the device's zone under a test, and put it back.
 *
 * `process.env` is declared **read-only** for the app (`shared/config/process-env.d.ts`), on
 * purpose: the app reads three `EXPO_PUBLIC_*` values off it at launch and writes nothing, and a
 * narrow declaration is what keeps `@types/node`'s `fs` and `Buffer` from looking available in a
 * runtime that has neither. The suites about the platform's day are the one place a write is
 * wanted — they move the device's zone to prove the conversions never consult it — and this is
 * the one place that write is made, so the declaration stays narrow and the cast stays in one
 * file rather than in every suite about days.
 *
 * Read-only is a fact about the app's process and not about jest's: under jest `process.env` is
 * a plain object of the test's own, and assigning `undefined` deletes nothing and stringifies
 * nothing, which is why *put it back* is one assignment.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */
export function setDeviceZone(zone: string | undefined): void {
  // A `Readonly` index signature is assignable to a mutable one; the readonly-ness is the app's
  // promise about its own reads, and this is the one write a test is licensed to make.
  const env: Record<string, string | undefined> = process.env;
  env.TZ = zone;
}
