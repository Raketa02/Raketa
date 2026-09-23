/**
 * **Your own yeses, as a list of who** — and the one question a card asks of it: *did I say yes
 * to this person?*
 *
 * ## An outgoing yes is a tag only, and it is the reader's own list that says so
 *
 * The deck collects people and the builder spends them
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8). An **incoming** yes reaches the list Karol picks from as a code on the row —
 * `inclusion_reason`, the engine's admission, worded *Wants to play you* — because the server is
 * the only side that knows it. An **outgoing** yes needs no code: Ania's yes to Karol is already
 * on the wire as her own `GET /interest` outgoing list, so *You said yes* on his card is a
 * comparison the client makes between two things it holds. No nudge travels with it — her yes
 * says nothing about his willingness, and the served order is the order.
 *
 * ## The list is ids and never a screen
 *
 * *No list of your yeses* is one of §8's refusals, and holding the ids here does not reopen it:
 * what a sport's list is used for is a lookup, one card at a time, and nothing draws it as a
 * list. It is held **per sport** because a yes is per sport — saying yes to somebody in padel
 * says nothing about tennis — and it is `readonly string[]` rather than a `Set` so that Query
 * can hold and structurally share it like every other value it caches.
 *
 * ## The one patch, on a tap's own answer
 *
 * A yes on the deck is the moment the reader's list changes, and the reply already says how:
 * one-sided, and the person is now outgoing; mutual, and they never were — a mutual is answered
 * the instant it is written and the wire files it under `mutual`, so *You said yes* must not be
 * drawn on somebody the reader has already matched. {@link outgoingAfterYes} is that patch as a
 * rule, so the hook that applies it holds no arithmetic of its own — Part 7's *prefer
 * response-driven updates* on the one list in this tab a tap moves.
 *
 * ## The mutual list crosses too, for one reader, and it is the same shape
 *
 * The mutual list stopped at the mapper for as long as nothing drew it — *You said yes* is the
 * one tag that must never be drawn from it. The radar's record sheet gave it a reader
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4): opened on somebody the reader is matched with, the sheet's foot says *You're matched* and
 * offers the chat instead of two buttons, and *matched* is a fact the reader holds — their own
 * yes, come back — exactly as *said yes* is. So the ids cross the same way, per sport and as a
 * lookup ({@link matchedWith}), the same patch lands on the tap's own reply
 * ({@link mutualAfterYes}), and nothing draws the list as a list: *no list of your yeses*
 * covers the ones that came back too.
 */

import type { Sport } from '@/shared/vocabulary/sport';

/**
 * Who you have said *Let's play* to and who has not yet answered, per sport.
 *
 * **Partial by design**, like the standing beside it: an absent sport is *nobody there*, which
 * is what the route means by sending no rows for it.
 */
export type OutgoingInterest = Readonly<Partial<Record<Sport, readonly string[]>>>;

/**
 * Who has said *Let's play* back to you, per sport — the mutuals, as ids and nothing more.
 *
 * The outgoing list's shape under its own name, because the two are read by different rules
 * and a caller handed one where the other was meant is exactly the tag the module note refuses.
 * Partial for the same reason: an absent sport is *matched with nobody there*.
 */
export type MutualInterest = Readonly<Partial<Record<Sport, readonly string[]>>>;

/**
 * Whether the reader has a live yes towards this person in this sport.
 *
 * `undefined` is *the list has not been read yet*, and it answers **no** for everybody rather
 * than withholding the card: a tag missing for a moment is a smaller lie than a tag drawn on a
 * guess, and the read lands within the screen's own lifetime.
 */
export function saidYesTo(
  outgoing: OutgoingInterest | undefined,
  sport: Sport,
  playerId: string,
): boolean {
  return outgoing?.[sport]?.includes(playerId) ?? false;
}

/**
 * The list after a yes of the reader's own — see the module note.
 *
 * @param mutual what the tap's reply said: a mutual is off the list, a one-sided yes is on it.
 */
export function outgoingAfterYes(
  outgoing: OutgoingInterest,
  yes: { readonly sport: Sport; readonly playerId: string },
  mutual: boolean,
): OutgoingInterest {
  const held = outgoing[yes.sport] ?? [];
  const without = held.filter((id) => id !== yes.playerId);
  return { ...outgoing, [yes.sport]: mutual ? without : [...without, yes.playerId] };
}

/**
 * Whether the reader is **matched** with this person in this sport — their yes came back.
 *
 * `undefined` is *the list has not been read yet* and answers **no**, as `saidYesTo` does: a
 * foot drawing two buttons for a beat over a match is a smaller lie than one drawing a chat
 * door on a guess, and the read lands within the sheet's own lifetime.
 */
export function matchedWith(
  mutual: MutualInterest | undefined,
  sport: Sport,
  playerId: string,
): boolean {
  return mutual?.[sport]?.includes(playerId) ?? false;
}

/**
 * The mutual list after a yes of the reader's own — the other half of {@link outgoingAfterYes}.
 *
 * A reply of `mutual` is the instant the two lists change places: the person leaves the
 * outgoing list there and arrives here, so a sheet opened on them a moment later says
 * *You're matched* off the reply and not off a refetch. A one-sided yes changes nothing here.
 */
export function mutualAfterYes(
  mutual: MutualInterest,
  yes: { readonly sport: Sport; readonly playerId: string },
  wasMutual: boolean,
): MutualInterest {
  if (!wasMutual) return mutual;
  const held = mutual[yes.sport] ?? [];
  if (held.includes(yes.playerId)) return mutual;
  return { ...mutual, [yes.sport]: [...held, yes.playerId] };
}
