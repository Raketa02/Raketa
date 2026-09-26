/**
 * **Every sentence the administrator area composes from a value** — and every name a control is
 * spoken by. The fixed sentences are `administratorCopy.ts`, beside this; copy is code, and
 * nothing is inlined in a component.
 *
 * `groups`' two rules hold here too: **a name is said whole** (ADR-0171 §4), and **a counted phrase
 * goes through `counted()`**. What is borrowed from `groups` — *N members*, *Want to join · N*, a
 * request's Levels, the share sentence — is read inside these functions and never at module load,
 * because the feature barrels form a cycle.
 */

import { GROUP_NAME_MAX, membersLine, personName, shareMessage } from '@/features/groups/types';
import { sportLabel } from '@/features/onboarding/types';
import { codeMessage, type AppError } from '@/shared/errors';
import { dayDate } from '@/shared/date/calendarDay';
import { counted } from '@/shared/formatting/counted';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import type { Sport } from '@/shared/vocabulary/sport';

import { WHATSAPP_SIZE, type AdministeredGroup, type OfficialGroup } from '../domain/officialGroup';
import type { JoinedWhen } from '../domain/officialGroupRules';
import { isRemoval } from '../hooks/useRemovalWatch';

import { ADMINISTRATOR_COPY } from './administratorCopy';

/** The separator every composed line here uses — the mocks' middle dot. */
const DOT = ' · ';

/** *Ogrody 33 · Administrator* — the area's eyebrow, drawn upper case (club 17). */
export function administratorEyebrow(clubName: string): string {
  return `${clubName}${DOT}${ADMINISTRATOR_COPY.role}`;
}

/** *Ogrody 33 · Official* — an official group's page, drawn upper case (club 11, 18). */
export function officialEyebrow(clubName: string): string {
  return `${clubName}${DOT}${ADMINISTRATOR_COPY.official}`;
}

/** *1 waiting* — the amber tag on a card. */
export function waitingTag(count: number): string {
  return `${count} waiting`;
}

/** *Tennis, Padel* — sports by name, for a listener who cannot see the dots. */
function sportsList(sports: readonly Sport[]): string {
  return sports.map(sportLabel).join(', ');
}

/**
 * *Padel, Tennis, Squash* — a group's row on the You tab, under its name: the one of its settings
 * the Groups tab's read carries. Nothing where no sport this build can name is left.
 */
export function settingsRowLine(group: Pick<AdministeredGroup, 'sports'>): string | undefined {
  return group.sports.length === 0 ? undefined : sportsList(group.sports);
}

/** *Ogrody 33 Club, 11 members, 1 waiting, plays Padel, Tennis, Ogrody 33* — a card, spoken. */
export function officialCardLabel(card: AdministeredGroup): string {
  const waiting = card.waitingCount > 0 ? [waitingTag(card.waitingCount)] : [];
  const plays = card.sports.length > 0 ? [`plays ${sportsList(card.sports)}`] : [];
  return [card.name, membersLine(card.memberCount), ...waiting, ...plays, card.homeClub.name].join(
    ', ',
  );
}

/** *A whole number from 2 to 1024* — the size field's rule, said when what is typed is not one. */
export function whatsAppSizeRule(): string {
  return `A whole number from ${WHATSAPP_SIZE.min} to ${WHATSAPP_SIZE.max}`;
}

/** *The sports Ogrody 33 offers. Players see this group's games in them.* — under the Sports card. */
export function sportsCardLine(clubName: string): string {
  return `The sports ${clubName} offers. Players see this group’s games in them.`;
}

/**
 * **A refused create or settings save, in the form's words** — the server checks the four fields in
 * the form's order and names the one it refused (`details.field`); the screen says this on that
 * field, and anything the form cannot name under the button. The limits are the domain's, so a
 * sentence cannot state another. A function rather than a table, so `groups`' limit is read when a
 * refusal is said.
 */
function settingsRefusal(error: AppError): string {
  return codeMessage(
    {
      group_name_invalid: `Give the group a name of up to ${GROUP_NAME_MAX} characters.`,
      whatsapp_size_invalid: `The WhatsApp group size is a whole number from ${WHATSAPP_SIZE.min} to ${WHATSAPP_SIZE.max}.`,
      group_sports_required: 'Pick at least one sport the group plays.',
      sport_not_offered_by_club: 'The club doesn’t offer one of those sports any more. Pick again.',
      ...ADMINISTRATOR_COPY.settings.refused,
    },
    error,
  );
}

/** The fields a refusal can be said on. Anything else is said under the button. */
const FORM_FIELDS = ['name', 'whatsapp_size', 'sports'] as const;
export type FormField = (typeof FORM_FIELDS)[number];

/** Which field a refused create or save names, if it names one of the form's. */
function refusedField(error: AppError): FormField | undefined {
  const field = error.details?.['field'];
  return FORM_FIELDS.find((known) => known === field);
}

/** A refusal in the form's words, and the field it is said on — none: under the button. */
export interface FormRefusal {
  readonly words: string;
  readonly field?: FormField;
}

/**
 * **What a refused create or settings save says, and where** — or nothing: no refusal, or a
 * removal, which is the area's to answer, once (`useRemovalWatch`), and not the form's as well.
 * One reading for both forms, so they cannot say a refusal differently.
 */
export function formRefusal(error: AppError | null): FormRefusal | undefined {
  if (error === null || isRemoval(error)) return undefined;
  const field = refusedField(error);
  return { words: settingsRefusal(error), ...(field === undefined ? {} : { field }) };
}

/** A refused answer to a request — answered from another phone, or a group that moved on. */
export const REQUEST_REFUSALS = {
  join_request_not_found: 'That request isn’t waiting any more.',
  group_not_found: 'This isn’t a group you run any more.',
} as const satisfies Readonly<Record<string, string>>;

/** The message Post to WhatsApp types, and the sheet carries when there is no WhatsApp. */
export function postMessage(group: Pick<OfficialGroup, 'name' | 'link'>): string {
  return shareMessage(group.name, group.link);
}

/** *11 players* — the players card's count (club 18, 19). */
export function playersLine(count: number): string {
  return counted(count, 'player', 'players');
}

/**
 * *anyone with the link joins · 23% of the WhatsApp group* — under the count (club 11): who gets
 * in, and how much of the WhatsApp crowd has arrived, which passes 100% when it has.
 */
export function playersCardLine(group: Pick<OfficialGroup, 'joinPolicy'>, share: number): string {
  const policy =
    group.joinPolicy === 'ANYONE'
      ? ADMINISTRATOR_COPY.group.anyoneJoins
      : ADMINISTRATOR_COPY.group.youApprove;
  return `${policy}${DOT}${formatPercent(share)} of the WhatsApp group`;
}

/** *11 players, anyone with the link joins · 23% of the WhatsApp group* — the card, spoken whole. */
export function playersCardLabel(count: string, line: string): string {
  return `${count}, ${line}`;
}

/** *this week*, or *7 Sep* — when a player joined (club 18, 19). */
export function joinedLabel(when: JoinedWhen): string {
  return when.kind === 'this-week' ? ADMINISTRATOR_COPY.group.thisWeek : dayDate(when.day);
}

/** *Ania Kowalczyk, joined 7 Sep* — a player's row, spoken. It opens nothing. */
export function playerRowLabel(name: string | null, when: JoinedWhen | undefined): string {
  const who = personName(name);
  return when === undefined ? who : `${who}, joined ${joinedLabel(when)}`;
}

/** *Ogrody 33 removed you as an administrator.* — and what happens next, for an account with nothing else. */
export function removedMessage(
  clubName: string,
  { signedOut }: { readonly signedOut: boolean },
): string {
  const removed = `${clubName} removed you as an administrator.`;
  return signedOut ? `${removed} You’re signed out.` : removed;
}
