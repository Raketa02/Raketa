/**
 * The `sportsmanship` feature's only public surface.
 *
 * **What other players said about being on a court with somebody** — the one thing on a player
 * record the platform cannot count for itself, and the first part of that work with an input
 * surface ([ADR-0158](../../../../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md),
 * [#386](https://github.com/Raketa02/Raketa/issues/386)). This half of it is the asking: a card
 * per settled court, everybody else who was on it, one to five whole stars each, and one press
 * that closes the question for ever.
 *
 * **The word *rating* is Skill rating's** ([`CONTEXT.md`](../../../../CONTEXT.md) ·
 * Sportsmanship), so everything here is spelled *stars* or *the card* — a bare *rating* on this
 * platform still means the μ/σ a player holds in a sport, and these two things stand one
 * section apart on the same tab.
 *
 * **A feature of its own rather than a corner of `games`.** The context is its own on the
 * backend, with its own routes, its own refusals and its own vocabulary, and none of it is
 * about what a game *is*. What crosses the seam is one component and the shape it needs, which
 * is the same seam `play` has with the challenge send: the surface composes, the feature owns
 * the act. That the one surface composing it is now `games`' own result screen changes nothing
 * about the seam — it changes which screen holds the court.
 *
 * **What is exported is what has a caller** — one component and the type of its one prop. The
 * scale, the draft, the join, the copy deck, the read and the write all stay internal: they are
 * the feature.
 */

/**
 * **The card still waiting for your stars**, drawn at the end of the result screen.
 *
 * Renders nothing at all when nothing is waiting, which is most of the time: a card opens the
 * day after the game, only once the score has settled, and closes a week later.
 */
export { StarCardSection, type StarCardSectionProps } from './components/StarCardSection';

/**
 * The evening a card is about, as this feature needs it — a game, its sport, and who was on
 * the court.
 *
 * Declared here rather than taken from `games` so that this feature states its own demand
 * rather than adopting another feature's entity: `GET /sportsmanship` answers **ids and
 * nothing else**, deliberately, and whoever holds the games supplies the words.
 */
export type { RatedCourt, RatedSeat } from './domain/card';

/**
 * *How were they?* — the card's heading, exported for the suites that walk the result screen it
 * stands at the foot of: PLAYED WITH is drawn above it (#754), and a test asserting a sentence it
 * spelled itself passes the day the screen stops saying it.
 */
export { STARS_HEADING } from './components/starsPresentation';
