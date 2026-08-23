/**
 * The key that makes leaving safe to send twice.
 *
 * `ADR-0030` requires a destructive command to carry one, keyed
 * `(command, idempotency key)` with a 24-hour expiry; `ADR-0086` has the client
 * generate it and states what it is **not** — the version `ADR-0074` refused,
 * *"which would make the phone hold a rule about its own staleness"*. A key
 * encodes no rule and states no belief about freshness. It answers one case a
 * version could not: a phone that loses the answer to a departure it already
 * made, whose naive retry would otherwise be reported to her as a refusal.
 *
 * **One key per visit to the screen, not one per press.** That is the whole
 * design: a press that times out, a backgrounded app, a tap she was not sure
 * registered — all of them re-send the same key, and the server hands back what
 * the first one did rather than applying a second departure. A key minted per
 * press would make the second attempt a fresh command, and the aggregate would
 * refuse it as *she has already left* — true, and the wrong thing to tell somebody
 * who is asking whether her first tap worked.
 *
 * **It is random rather than derived, and that is the trade.** A key spelled from
 * the player and the match — `player:match` — would survive a process death and
 * answer `ADR-0086`'s case completely, and it would also be **guessable from
 * public data**: a person card carries a player id and Now carries match ids, so
 * anybody could file that key first and turn a stranger's departure into
 * `IdempotencyKeyIsAnothers`. Griefing an irreversible money act is the worse
 * failure, so the key is unguessable and the residual is stated: a departure whose
 * answer is lost *and* whose app is then killed re-asks under a new key and is
 * answered with the recomposed screen — which says she has left. She is never
 * charged twice; the aggregate refuses that on its own. Filed as
 * `Raketa02/Raketa#117`.
 *
 * **`Math.random` and no new dependency.** The key needs to be unguessable enough
 * that nobody stumbles onto one, not cryptographically unpredictable — it is
 * scoped by the server to the player who first used it, so the whole of what
 * randomness buys here is collision avoidance. `expo-crypto` would be a dependency
 * added for one string.
 */

/** Base-36 digits per draw. Two draws is ~20 characters of entropy. */
const RADIX = 36;

/**
 * A key for one intent to leave one match.
 *
 * The match id leads so that a key is legible in a server log as *which match* —
 * the log is keyed on the whole string, so the prefix costs nothing and the first
 * question anybody asks of a stuck departure is which match it was.
 */
export function departureRequestKey(matchId: string, draw: () => number = Math.random): string {
  return `${matchId}:${digits(draw())}${digits(draw())}`;
}

function digits(value: number): string {
  // The leading `0.` is not entropy.
  return value.toString(RADIX).slice(2);
}
