/**
 * **The notices, off the wire and back** — the three choices, a listed notice, the bell's number
 * (#627), and where a tap goes from the facts a notice names (#559).
 *
 * A notice's sport and kind are narrowed here, once, for the list's rows and a push's payload alike:
 * a code this build cannot name is a notice still listed, in the words the backend wrote, and
 * nowhere to open — the app has no deck, no colour and no words for a sport it does not know.
 */

import { toSport } from '@/features/onboarding/types';
import type { GameKind } from '@/features/proposals/types';
import type { components } from '@/generated/schema';

import type { NotificationChoices } from '../domain/choices';
import {
  homeTargetOf,
  targetOf,
  type Notice,
  type NoticeTarget,
  type RecentNotices,
} from '../domain/notice';
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

/**
 * Where a tap goes — **Home for a notice that opens Home** (#727, #731), whatever its kind, since
 * it names nothing a later release could have meant differently — **with Needs your answer up for a
 * friend request and a friends game invitation** (#817, `homeTargetOf`), whose cards wait there
 * now; **the record of the person a
 * notice names for one that opens a record** (#753), and nowhere when it names nobody; **the
 * questionnaire of the sport an ask names, and the picker of the group and sport it names** (#758),
 * nowhere without them; `undefined` for a game's notice, a sport or a kind this build cannot name,
 * or a game's notice that names no game.
 */
export function toTarget(facts: SentFacts): NoticeTarget | undefined {
  const { opens, gameId, poolId } = facts;
  if (opens === 'HOME') return homeTargetOf(toNoticeKind(facts.kind));
  if (opens === 'RECORD') {
    const playerId = facts.playerId ?? null;
    return playerId === null ? undefined : { opens: 'record', playerId };
  }
  const sport = facts.sport === null ? undefined : toSport(facts.sport);
  if (opens === 'QUESTIONNAIRE') {
    return sport === undefined ? undefined : { opens: 'questionnaire', sport };
  }
  if (opens === 'PICKER') {
    return sport === undefined || poolId === null
      ? undefined
      : { opens: 'picker', groupId: poolId, sport };
  }
  if (gameId === null || poolId === null) return undefined;
  const notice = toNoticeKind(facts.kind);
  const kind = facts.gameKind === null ? undefined : toKind(facts.gameKind);
  if (notice === undefined || sport === undefined || kind === undefined) return undefined;
  return targetOf(notice, opens, { gameId, poolId, sport, kind });
}

export function toNotice(wire: Schemas['NoticeSchema']): Notice {
  const target = toTarget({
    kind: wire.kind,
    opens: wire.opens,
    gameId: wire.game_id,
    poolId: wire.pool_id,
    sport: wire.sport,
    gameKind: wire.game_kind,
    playerId: wire.player_id,
  });
  return {
    id: wire.notice_id,
    kind: wire.kind,
    title: wire.title,
    body: wire.body,
    givenAt: wire.given_at,
    isNew: wire.new,
    yourOwn: wire.your_own,
    ...(target === undefined ? {} : { target }),
  };
}

/**
 * The list and the bell's number, from one read. `last_opened_at` is left on the wire: a row's own
 * `new` already says which ones came since, by the server's order rather than a clock.
 */
export function toRecentNotices(wire: Schemas['RecentNoticesResponse']): RecentNotices {
  return { notices: wire.notices.map(toNotice), newCount: wire.new_count };
}
