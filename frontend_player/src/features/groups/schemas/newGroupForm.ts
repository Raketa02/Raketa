/**
 * **The New group form's one schema** — what the form holds, checked, and the group it creates
 * (CLAUDE.md's *the form + one Zod schema*).
 *
 * *Create the group* is pressable exactly when this answers a group (story 14): **a name that is
 * not only spaces, of at most 40 characters, and a home club** — required, PRD #500 overriding
 * play 4 by name. The name goes out **trimmed**, which is what the server keeps; it also collapses
 * runs of whitespace, which is the server's to do and is not repeated here.
 */

import { z } from 'zod';

import { GROUP_NAME_MAX, type NewGroup, type SearchedClub } from '../domain/group';
import type { JoinPolicy } from '../domain/vocabulary';

/** What the form holds while a player fills it in. */
export interface NewGroupForm {
  readonly name: string;
  /** Chosen from home-club search, or not yet. */
  readonly homeClub: SearchedClub | undefined;
  readonly joinPolicy: JoinPolicy;
}

const NewGroupSchema = z
  .object({
    name: z.string().trim().min(1).max(GROUP_NAME_MAX),
    homeClub: z.object({ id: z.string().min(1) }),
    joinPolicy: z.enum(['ANYONE', 'PEOPLE_I_APPROVE']),
  })
  .transform((form): NewGroup => ({
    name: form.name,
    homeClubId: form.homeClub.id,
    joinPolicy: form.joinPolicy,
  }));

/** The group the form would create, or `undefined` while it cannot create one. */
export function newGroupFrom(form: NewGroupForm): NewGroup | undefined {
  const parsed = NewGroupSchema.safeParse(form);
  return parsed.success ? parsed.data : undefined;
}
