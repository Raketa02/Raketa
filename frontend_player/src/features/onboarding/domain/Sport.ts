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
 * The picker renders the sports the *server* says it serves, so this constant is not the
 * list anything is drawn from. It exists to derive the type below, and for the route-param
 * schema, which has to validate a sport before anything trusts it.
 *
 * **The order is not decoration.** It is the backend registry's order, and the collection
 * form of `/assessments/in-progress` sorts by it — so "the first unfinished run" means the
 * same thing at both ends without either restating the other's list.
 *
 * The type is derived from the list rather than declared beside it, so the two cannot
 * disagree.
 */
export const SPORTS = ['padel', 'tennis', 'squash', 'badminton'] as const;

export type Sport = (typeof SPORTS)[number];
