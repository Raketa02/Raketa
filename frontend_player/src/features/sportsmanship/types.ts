/**
 * The `sportsmanship` feature's only public surface.
 *
 * **What other players said about being on a court with somebody** — the one thing on a player
 * record the platform cannot count for itself, and the first part of that work with an input
 * surface ([ADR-0154](../../../../docs/adr/0154-a-rating-is-one-per-person-and-the-collapse-is-the-key.md),
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
 * the act.
 *
 * **What is exported is what has a caller** — one component and the type of its one prop. The
 * scale, the draft, the join, the copy deck, the read and the write all stay internal: they are
 * the feature.
 */

/**
 * **The cards still waiting for your stars**, drawn in the games list on the Now tab.
 *
 * Renders nothing at all when nothing is waiting, which is most of the time.
 */
export { StarCards, type StarCardsProps } from './components/StarCards';

/**
 * The evening a card is about, as this feature needs it — a game, its sport, and who was on
 * the court.
 *
 * Declared here rather than taken from `games` so that this feature states its own demand
 * rather than adopting another feature's entity: `GET /sportsmanship` answers **ids and
 * nothing else**, deliberately, and whoever holds the games supplies the words.
 */
export type { RatedCourt, RatedSeat } from './domain/card';
