/**
 * **The notices, off the wire and back** — the three choices, a listed notice, and where a tap goes
 * from the facts a notice names (#559).
 *
 * A notice's sport and kind are narrowed here, once, for the list's rows and a push's payload alike:
 * a code this build cannot name is a notice still listed, in the words the backend wrote, and
 * nowhere to open — the app has no deck, no colour and no words for a sport it does not know.
 */

import { toSport } from '@/features/onboarding/types';
import type { GameKind } from '@/features/proposals/types';
import type { components } from '@/generated/schema';

import type { NotificationChoices } from '../domain/choices';
import { targetOf, type Notice, type NoticeTarget } from '../domain/notice';
import { NOTICE_KINDS, type NoticeKind } from '../domain/vocabulary';
import type { SentFacts } from '../schemas/pushNotice';

type Schemas = components['schemas'];

export function toChoices(wire: Schemas['NotificationChoicesSchema']): NotificationChoices {
  return {
    youCompleteIt: wire.you_complete_it,
    challengesForYou: wire.challenges_for_you,
    fillInAlerts: wire.fill_in_alerts,
  };
}

/** All three, every time — the route replaces them. */
export function toChoicesRequest(
  choices: NotificationChoices,
): Schemas['NotificationChoicesSchema'] {
  return {
    you_complete_it: choices.youCompleteIt,
    challenges_for_you: choices.challengesForYou,
    fill_in_alerts: choices.fillInAlerts,
  };
}

const KIND_BY_WIRE: Readonly<Record<Schemas['SearchMode'], GameKind>> = {
  COMPETITIVE: 'competitive',
  FOR_FUN: 'forFun',
};

function toKind(wire: string): GameKind | undefined {
  return Object.hasOwn(KIND_BY_WIRE, wire)
    ? KIND_BY_WIRE[wire as Schemas['SearchMode']]
    : undefined;
}

function toNoticeKind(wire: string): NoticeKind | undefined {
  return NOTICE_KINDS.find((kind) => kind === wire);
}

/** Where a tap goes — `undefined` for a notice, a sport or a kind this build cannot name. */
export function toTarget(facts: SentFacts): NoticeTarget | undefined {
  const notice = toNoticeKind(facts.kind);
  const sport = toSport(facts.sport);
  const kind = toKind(facts.gameKind);
  if (notice === undefined || sport === undefined || kind === undefined) return undefined;
  return targetOf(notice, facts.opens, {
    gameId: facts.gameId,
    poolId: facts.poolId,
    sport,
    kind,
  });
}

export function toNotice(wire: Schemas['NoticeSchema']): Notice {
  const target = toTarget({
    kind: wire.kind,
    opens: wire.opens,
    gameId: wire.game_id,
    poolId: wire.pool_id,
    sport: wire.sport,
    gameKind: wire.game_kind,
  });
  return {
    id: wire.notice_id,
    kind: wire.kind,
    title: wire.title,
    body: wire.body,
    givenAt: wire.given_at,
    ...(target === undefined ? {} : { target }),
  };
}
