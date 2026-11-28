/**
 * **Edit group's one schema** — the New group form's Name and Who can join, checked, and what a
 * save sends ([#514](https://github.com/Rakieta02/Rakieta/issues/514), story 75).
 *
 * *Save* is pressable when this answers **and** the answer differs from the group
 * (`detailsUnchanged`). The name is New group's rule, shared rather than restated; the home club
 * is not here, because it never changes (ADR-0183 §2).
 */

import { z } from 'zod';

import type { GroupDetails } from '../domain/group';

import { GroupNameSchema, JoinPolicySchema } from './newGroupForm';

const GroupDetailsSchema = z.object({ name: GroupNameSchema, joinPolicy: JoinPolicySchema });

/**
 * What a save would send — the form's two fields, the name trimmed — or `undefined` while the form
 * cannot be saved. The form holds the same two fields it sends, unchecked.
 */
export function groupDetailsFrom(form: GroupDetails): GroupDetails | undefined {
  const parsed = GroupDetailsSchema.safeParse(form);
  return parsed.success ? parsed.data : undefined;
}
