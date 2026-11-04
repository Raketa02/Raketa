/**
 * **Every sentence the administrator area composes from a value** — and every name a control is
 * spoken by. The fixed sentences are `administratorCopy.ts`, beside this; copy is code, and
 * nothing is inlined in a component.
 *
 * `groups`' two rules hold here too: **a nickname is said whole** (ADR-0199 §1), and **a counted phrase
 * goes through `counted()`**. What is borrowed from `groups` — *N members*, *Want to join · N*, a
 * request's Levels — is read inside these functions and never at module load, because the feature
 * barrels form a cycle.
 */

import type { HeldProfiles } from '@/features/auth/types';
import { GROUP_NAME_MAX, membersLine } from '@/features/groups/types';
import { sportLabel } from '@/features/onboarding/types';
import { codeMessage, type AppError } from '@/shared/errors';
import { counted } from '@/shared/formatting/counted';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { sentenceList } from '@/shared/formatting/sentenceList';
import type { Sport } from '@/shared/vocabulary/sport';

import type { HandedGroup } from '../domain/handovers';
import { WHATSAPP_SIZE, type AdministeredGroup } from '../domain/officialGroup';
import { isRemoval } from '../hooks/useRemovalWatch';

import { ADMINISTRATOR_COPY } from './administratorCopy';

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
      whatsapp_size_invalid: `The group size is a whole number from ${WHATSAPP_SIZE.min} to ${WHATSAPP_SIZE.max}.`,
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

/**
 * *11 members, 23% of the group size* — the members card, spoken whole: the count is Info's
 * members row's own words (`membersLine`), since the people in an official group are its members
 * as they are a player group's; the ring draws the share without words, and may pass 100% when more
 * have arrived than the size said.
 */
export function membersCardLabel(count: number, share: number): string {
  return `${membersLine(count)}, ${formatPercent(share)} of the group size`;
}

/** *Ogrody 33 removed you as an administrator.* — and what happens next, for an account with nothing else. */
export function removedMessage(
  clubName: string,
  { signedOut }: { readonly signedOut: boolean },
): string {
  const removed = `${clubName} removed you as an administrator.`;
  return signedOut ? `${removed} You’re signed out.` : removed;
}

/**
 * **The handover sheet's title** (ADR-0192 §2): *Ogrody 33 made you the administrator of Ogrody 33
 * Club* — the club, and the group by its whole name; several handed at once are counted, and named
 * in the body.
 */
export function handoverTitle(clubName: string, groups: readonly HandedGroup[]): string {
  const [only] = groups;
  const what =
    groups.length === 1 && only !== undefined
      ? only.groupName
      : counted(groups.length, 'group', 'groups');
  return `${clubName} made you the administrator of ${what}`;
}

/** **What running it means now**, and — for several — which they are. */
export function handoverBody(groups: readonly HandedGroup[]): string {
  if (groups.length === 1) {
    return (
      'You answer who asks to join it and look after its settings now. Its players, its link ' +
      'and who can join stay as they were.'
    );
  }
  const names = sentenceList(groups.map((group) => group.groupName));
  return `${names}. You answer who asks to join them and look after their settings now.`;
}

/** *2 people are waiting for your answer.* — the queue the handover gave, or nothing to say. */
export function handoverWaiting(groups: readonly HandedGroup[]): string | undefined {
  const waiting = groups.reduce((sum, group) => sum + group.waitingCount, 0);
  if (waiting === 0) return undefined;
  return `${counted(waiting, 'person is', 'people are')} waiting for your answer.`;
}

/** **A profile's row, spoken** — who, then which hat: *tomek.k, Player*, *Ogrody 33, Administrator*. */
export function profileRowLabel(title: string, role: string): string {
  return `${title}, ${role}`;
}

/** **The chip's name** — what it does, and the profile it shows now. */
export function switcherChipLabel(worn: string): string {
  return `${ADMINISTRATOR_COPY.switcher.chip}, now ${worn}`;
}

/** **The invitation sheet's title** (club 5): the club, and what it is asking. */
export function invitationTitle(clubName: string): string {
  return `${clubName} wants to make you an administrator`;
}

/**
 * **What accepting does, next to what the account holds** (club 5). The mock's sentence is a
 * player's; an account that does not play and runs another club's groups is told the same thing
 * about the profile it has.
 */
export function invitationBody(profiles: HeldProfiles): string {
  const [club] = profiles.administers;
  const nextTo = profiles.actsAsPlayer
    ? ', next to your player profile'
    : club === undefined
      ? ''
      : `, next to ${club.clubName}`;
  return `It becomes a second profile on this account${nextTo}. You switch between them from You.`;
}

/**
 * **Accepting refused** — by the codes the route documents, with the club named where it is the one
 * to ask; anything else is the category's sentence, and Accept stays to be pressed again.
 */
export function invitationRefusal(clubName: string, error: AppError): string {
  return codeMessage(
    {
      invitation_expired: `This invitation has expired. Ask ${clubName} to send a new one.`,
      invitation_not_found: 'This invitation isn’t open any more.',
    },
    error,
  );
}

/** Whether a refusal means the invitation is gone, so there is nothing left to accept. */
export function invitationEnded(error: AppError | null): boolean {
  return error?.code === 'invitation_expired' || error?.code === 'invitation_not_found';
}
