/**
 * **A group's deck, read** — a pass-through, honestly: the deck is the server's projection, dealt
 * and ordered there (`ReadGroupDeck`, #539), and nothing about it is decided on the way in. The
 * uniform-strict escape hatch, not an invariant invented to fill the folder.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getGroupDeck, type Cancellable } from '../api/proposalsApi';
import type { GroupDeck } from '../domain/deck';
import type { GameKind } from '../domain/vocabulary';
import { toGroupDeck, toWireKind } from '../mappers/deckMappers';

export async function readGroupDeck(
  groupId: string,
  sport: Sport,
  kind: GameKind,
  options: Cancellable = {},
): Promise<GroupDeck> {
  return toGroupDeck(await getGroupDeck(groupId, toWireSport(sport), toWireKind(kind), options));
}
