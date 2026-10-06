/**
 * **Words for acts two features both name** — one spelling, in a module neither of them owns.
 *
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §22.7 lists the doors this
 * map adds and says of the chat door *"one act, one spelling"*. That rule is what puts a verb
 * here rather than in the feature that happens to draw it first: `We played` is the Now card's
 * footer verb **and** the control that reveals the grid on a game screen leading with its plan,
 * and those are `features/plans` and `features/games` — the two features between which
 * [ADR-0149](../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §1 draws a **one-way** arrow.
 *
 * **The one-way arrow is exactly why a shared home is the answer and not a nicety.** Those two
 * features already reach each other at load time — a game screen mounts the shell, which mounts
 * the tab that mounts the rail — so a word read from `features/games` while `features/plans` is
 * being evaluated reads a half-built module and gets `undefined`, with nothing but a rendered
 * screen to notice. `OPEN_THE_CHAT` gets away with living in `features/conversations` because of
 * the direction of *its* edge rather than by design; this one has no such luck, and the honest
 * answer is the semantic home `docs/architecture.md` already names for a concept two features
 * share.
 *
 * **It is a word and not a rule.** Nothing here decides when a control is drawn — the card's
 * `doorOf` and the screen's `EntryLead` do — and nothing here knows what it opens.
 */

/**
 * **The door to saying a game happened** — the Now card's footer verb, and the control that
 * reveals the grid on an arm leading with the plan.
 *
 * The card's button navigates to the grid and the screen's reveals it, and
 * [`the-loop-screens.md`](../../../../docs/specs/the-loop/the-loop-screens.md) §5.2's rule over
 * both is the same promise: *the verb names what you arrive at.*
 */
export const WE_PLAYED = 'We played';
