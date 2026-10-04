/**
 * The groups feature's codes, **spelled as the contract spells them** and held equal to the
 * generated unions in `mappers/wireVocabulary.ts` — so a code added, renamed or removed on the
 * wire fails `pnpm typecheck` in the one file whose job is saying so.
 */

/**
 * **Which kind of group** ([ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
 * §2–§3): a **Player group**, a player's own with an Owner, or an **Official group** — a club's,
 * one per WhatsApp group, run by one of its Administrators, with no Owner and the sports it
 * declares.
 */
export type GroupKind = 'PLAYER' | 'OFFICIAL';

/**
 * What a group is to the person reading it
 * ([ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
 * §9). **A declined request reads `NONE`** — nothing tells anybody it was declined.
 */
export type GroupRelation = 'MEMBER' | 'REQUESTED' | 'NONE';

/** Who gets in: **Anyone**, the default, or **People I approve** (ADR-0183 §7). */
export type JoinPolicy = 'ANYONE' | 'PEOPLE_I_APPROVE';

/** What a search's text was read as — so an empty answer can say which empty it is. */
export type ReadAs = 'TEXT' | 'LINK';
