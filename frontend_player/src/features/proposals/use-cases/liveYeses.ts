/**
 * **A player's live yeses, read** (#554) — a pass-through: which yeses are live, in what order, is
 * the server's projection (`ReadLiveYeses`, #539), and nothing about it is decided on the way in.
 */

import { getLiveYeses, type Cancellable } from '../api/proposalsApi';
import type { LiveYeses } from '../domain/liveYes';
import { toLiveYeses } from '../mappers/liveYesMappers';

export async function readLiveYeses(options: Cancellable = {}): Promise<LiveYeses> {
  return toLiveYeses(await getLiveYeses(options));
}
