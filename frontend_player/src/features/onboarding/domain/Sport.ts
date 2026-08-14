/**
 * The four sports Rakieta rates.
 *
 * A **closed set**, as it is on the backend: adding a sport is a code change and a
 * release, never a row in a table. The wire spells them `PADEL`; this app spells them
 * `padel`, which is also how the theme keys sport identity — so a fifth sport that
 * reached the domain without reaching the design system fails `pnpm typecheck` rather
 * than rendering colourless.
 *
 * The two spellings meet in `mappers/`, and only there.
 *
 * There is no *onboarded player* and there must not be one: **a rating is per sport**, so
 * a player can be rated at padel and unrated at tennis indefinitely. Anything asking "has
 * this player been through onboarding" is really asking "does a rating exist for this
 * sport" and has to ask it that way.
 */

/**
 * Every sport, in the registry's own order.
 *
 * The picker renders the sports the *server* says it serves; this constant exists for the
 * entry gate, which has to ask "is a run in progress?" before any list has been fetched
 * (see `use-cases/findRunInProgress`), and for the route-param schema, which has to
 * validate a sport before anything trusts it.
 *
 * The type is derived from the list rather than declared beside it, so the two cannot
 * disagree.
 */
export const SPORTS = ['padel', 'tennis', 'squash', 'badminton'] as const;

export type Sport = (typeof SPORTS)[number];
