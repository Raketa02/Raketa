/**
 * Put the two viewer-owned regions back, whole.
 *
 * The other half of `applyNowUpdate`, and deliberately a different rule. That one
 * replaces **one card where it already sits** and may never move anything, because
 * order is a property of the composed screen (`ADR-0032`) and a client rebuilding
 * a region would be deciding a card's place — the one judgement `ADR-0070` keeps
 * on the server.
 *
 * This is the case that ADR carves out: *"an accepted offer changes three things
 * at once — the offer is gone, the match belongs in the strip"*. The regions are
 * still not the client's opinion — they arrived **composed by the server** at the
 * instant of the write, under the chip that was tapped, and this puts them where
 * they belong. Taking a seat is the first act in the product that can do it, and
 * the two regions arrive together or not at all.
 *
 * **The shelves are not touched, and that is stated rather than left to the
 * type.** A seat answer holds no shelf, so there is nothing to apply there — but a
 * later session reaching for *the same match, wherever it appears* would be
 * re-ordering a ranked list from a write, and a match she has just joined would
 * move under her thumb while she was looking at it. The shelf copy of that match
 * is corrected by the one card instead, which `applyNowUpdate` identifies by the
 * match rather than by its position.
 *
 * **The debt line is not touched either**, for the plainer reason that a seat
 * claim moves no money: what she owes changes when a payment does, and the next of
 * `ADR-0054`'s four asks is what collects it.
 */

import type { ComposedScreen, ScreenRegions } from '../domain/ComposedScreen';

export function applySeatRegions(screen: ComposedScreen, regions: ScreenRegions): ComposedScreen {
  return { ...screen, offers: regions.offers, yourMatches: regions.yourMatches };
}
