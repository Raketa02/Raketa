/**
 * **An official group's form, and its one schema** — New official group's (club 10, plus the Sports
 * card; [#516](https://github.com/Rakieta02/Rakieta/issues/516), PRD #500 story 125) and the group's
 * settings' ([#517](https://github.com/Rakieta02/Rakieta/issues/517), story 131), which ask the same
 * four things.
 *
 * *Create the group* and *Save* are pressable only when this answers settings:
 *
 * - **the name** — the player group's own rule, `GroupNameSchema`: trimmed, 1–40 characters;
 * - **who can join** — *Anyone* or *People I approve*;
 * - **the WhatsApp group size** — **required**, typed as text and read as a whole number from 2 to
 *   1024; `whatsAppSizeFrom` answers the same reading on its own, so the field can say when what is
 *   typed is not one;
 * - **the sports** — **required**, at least one, and **only the club's**, answered in the registry's
 *   order whatever order they were ticked in.
 *
 * The server checks all four again, in the same order, and refuses each under its own field.
 */

import { z } from 'zod';

import { GroupNameSchema, JoinPolicySchema, type JoinPolicy } from '@/features/groups/types';
import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import { WHATSAPP_SIZE, type OfficialGroupSettings } from '../domain/officialGroup';

export interface OfficialGroupForm {
  readonly name: string;
  readonly joinPolicy: JoinPolicy;
  /** As typed — the field is text. */
  readonly whatsAppSize: string;
  readonly sports: readonly Sport[];
}

const WhatsAppSizeSchema = z
  .string()
  .trim()
  .regex(/^\d+$/)
  .transform(Number)
  .pipe(z.number().int().min(WHATSAPP_SIZE.min).max(WHATSAPP_SIZE.max));

/** The typed size as a WhatsApp group size, or nothing where it is not a whole number from 2 to 1024. */
export function whatsAppSizeFrom(typed: string): number | undefined {
  const parsed = WhatsAppSizeSchema.safeParse(typed);
  return parsed.success ? parsed.data : undefined;
}

function officialGroupSchema(clubSports: readonly Sport[]) {
  return z
    .object({
      name: GroupNameSchema,
      joinPolicy: JoinPolicySchema,
      whatsAppSize: WhatsAppSizeSchema,
      sports: z
        .array(z.enum(SPORTS))
        .min(1)
        .refine((sports) => sports.every((sport) => clubSports.includes(sport))),
    })
    .transform((form): OfficialGroupSettings => ({
      name: form.name,
      joinPolicy: form.joinPolicy,
      whatsAppSize: form.whatsAppSize,
      sports: SPORTS.filter((sport) => form.sports.includes(sport)),
    }));
}

/**
 * The group to create, or nothing while the form is not one yet. `clubSports` are the sports the
 * club offers — the only ones a group may declare.
 */
export function officialGroupSettingsFrom(
  form: OfficialGroupForm,
  clubSports: readonly Sport[],
): OfficialGroupSettings | undefined {
  const parsed = officialGroupSchema(clubSports).safeParse(form);
  return parsed.success ? parsed.data : undefined;
}
