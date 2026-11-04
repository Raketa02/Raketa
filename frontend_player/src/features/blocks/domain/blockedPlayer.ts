/**
 * **Somebody the reader blocked** — the one shape this feature holds
 * ([#587](https://github.com/Raketa02/Raketa/issues/587);
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
 * §3).
 *
 * The uniform-strict escape hatch (ADR-0009): a block has no rule this client is entitled to
 * apply. What it reaches — one court, and nothing else — is the server's, and what the record says
 * about it is the server's `blocked_by_you`. So this is a type, and the list it fills is the
 * server's, in the server's order: **newest first**.
 *
 * Only the reader's **own** blocks are ever here. Nothing on this platform says who blocked the
 * reader, and nothing in this feature could hold it.
 */

export interface BlockedPlayer {
  readonly playerId: string;
  /** Their nickname, whole and never with an @, and never a familiar form of it (ADR-0199 §1). */
  readonly name: string;
  /** Absent where they have no photograph — the face draws their generated poster. */
  readonly photoUrl?: string;
}
