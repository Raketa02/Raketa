/**
 * One person's record, read through whichever door the reader came to it by.
 *
 * A pass-through with a mapping, which is what ADR-0009's uniform-strict escape hatch is for:
 * **there is no rule this client is entitled to apply to a record.** Who may read one is
 * decided against a prior disclosure the client cannot see; which sport the sheet is about is
 * resolved by the server and stated back; and the one refusal names nothing on purpose. A
 * client that re-derived any of it would be a second spelling of a safety gate.
 *
 * What is here is the one branch that **is** the client's: which of the two routes to ask.
 * Your own face reads the ungated `/players/me/record` — the parameterised route would answer
 * a healthy account asking about itself, and refuse the held player this screen exists for.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getOwnRecord, getPlayerRecord, type Cancellable } from '../api/playerRecordApi';
import type { PlayerRecord, RecordSubject } from '../domain/playerRecord';
import { toPlayerRecord } from '../mappers/playerRecordMappers';

export interface RecordRead extends Cancellable {
  readonly subject: RecordSubject;
  /** Which sport the reader arrived from, where they arrived from one. */
  readonly sport?: Sport;
}

export function readPlayerRecord({ subject, sport, signal }: RecordRead): Promise<PlayerRecord> {
  const ask = {
    ...(sport === undefined ? {} : { sport: toWireSport(sport) }),
    ...(signal === undefined ? {} : { signal }),
  };

  return (subject.kind === 'me' ? getOwnRecord(ask) : getPlayerRecord(subject.playerId, ask)).then(
    toPlayerRecord,
  );
}
