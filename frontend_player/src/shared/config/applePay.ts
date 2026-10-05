/**
 * **The Apple Pay merchant identifier — none yet** (#552; the mechanics §12.4, open items O4, O6).
 *
 * One value, read in two places that must agree: `app.config.ts` hands it to Stripe's config plugin,
 * which writes it into the build's entitlements, and `shared/lib/platform/payments.tsx` hands it to
 * Stripe at runtime and offers an iPhone Apple Pay only while it is set. It is an entitlement a
 * personal Apple team cannot sign, so it waits for the Apple Developer membership; until then an
 * iPhone offers a card and BLIK.
 *
 * **This module imports nothing**, for `appIdentity.ts`'s reason: Node loads it while Expo evaluates
 * `app.config.ts`, before Metro exists.
 */

export const APPLE_PAY_MERCHANT: string | null = null;

/** The merchants Stripe's config plugin writes into the entitlements — none adds none. */
export const APPLE_PAY_MERCHANTS: readonly string[] =
  APPLE_PAY_MERCHANT === null ? [] : [APPLE_PAY_MERCHANT];
