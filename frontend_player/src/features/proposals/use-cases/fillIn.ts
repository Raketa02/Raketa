/**
 * **A group's Fill in, read** (#545, #557) — a pass-through: which rescues the reader is offered,
 * in what order and until when, is the server's projection, and nothing about it is decided on the
 * way in.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getFillIn, type Cancellable } from '../api/proposalsApi';
import type { FillIn } from '../domain/fillIn';
import { toFillIn } from '../mappers/fillInMappers';

export async function readFillIn(
  groupId: string,
  sport: Sport,
  options: Cancellable = {},
): Promise<FillIn> {
  return toFillIn(await getFillIn(groupId, toWireSport(sport), options));
}
