/**
 * The send's **one override** of the app-wide mutation defaults, and the reason it is here
 * rather than in `queryClient.ts`.
 *
 * ## Why the global pause is wrong for this one act
 *
 * `networkMode: 'online'` — the app-wide default — **pauses** an offline mutation and resumes it on reconnect, and every
 * other feature in this app wants exactly that. The send does not, and the difference is not
 * taste: a challenge's **answer window is derived at send and recorded**, so a send tapped at
 * 23:55 on a dead connection and resumed at 00:10 carries a deadline nobody chose — and it is
 * the same mechanism that answers *midnight passes while the week still reads tonight*. That
 * answer depends on the tap and the send being **one moment**, and the pause is the one thing
 * that splits them.
 *
 * So this act fails now. The disabled button rides on top and is **not** the mechanism:
 * `docs/architecture.md` Part 11 is explicit that *"button disabling is UX, not correctness"*,
 * so the button alone would leave the paused queue reachable.
 *
 * ## The deck keeps the pause, and the asymmetry is correct
 *
 * A pass is an append-only durable row with no deadline, and a mutual-born challenge has **no
 * answer window at all** — so a queue of deck answers draining on reconnect is the behaviour
 * you want. The test that separates them is *does this act carry a deadline the player chose*,
 * never the HTTP verb.
 *
 * **Two `networkMode` values in one tab is deliberate.** Written down here and in
 * `the-play-screens.md` §11 because, left unexplained, the next reader unifies them.
 *
 * ## What is not here
 *
 * No `retry`: the app-wide mutation default is already `retry: false`, and repeating it would
 * be a second place for one decision to be changed. No `Idempotency-Key` either — one open
 * challenge per pair across sports is a rule that does not expire, a key does, and a key
 * beside the rule would be a second mechanism for one fact.
 *
 * Sanctioned by Part 7 in writing: *"data classes that differ override it in their own feature
 * hook, which is where that decision belongs."*
 */

export const SEND_MUTATION_OPTIONS = {
  /** Fail now. A deadline derived at send may not be derived at a reconnect. */
  networkMode: 'always',
} as const;
