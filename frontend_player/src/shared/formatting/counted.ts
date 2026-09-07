/**
 * A count and the thing it counts — **one helper, so no sentence hardcodes an `s`**.
 *
 * Every counted phrase in the app routes through here: *3 slots you both ticked*, *5 weighted
 * terms*, *waiting on 1 answer*. Written out at each call site they are a ternary per
 * sentence, and the ternary is what a market with real plural rules has to find and replace —
 * Polish alone has three forms, so *"1 slot / 2 slots"* is not a rule, it is English's rule
 * spelled twenty times ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §4,
 * §19).
 *
 * **This is not localisation and does not pretend to be.** It is the seam localisation needs:
 * one function every counted phrase already calls, so the day plural forms arrive they arrive
 * here rather than in every module that ever counted something. That is the same argument
 * `ratingFormat` beside it makes about the decimal comma.
 */

/**
 * `3 slots`, `1 slot`.
 *
 * Both forms are given by the caller because both are copy — a helper that derived the plural
 * by adding an `s` would be the hardcoded `s` moved somewhere harder to find.
 */
export function counted(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}
