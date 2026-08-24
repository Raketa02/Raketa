/**
 * Ask what this match's result conversation is doing.
 *
 * A thin pass-through, and `ADR-0009`'s escape hatch covers exactly that: the
 * client has no business rule about what a viewer may do with a result, because
 * `ADR-0048`'s cap and its exclusions are enforced in one place on the server and a
 * client-side opinion about them would be a second, weaker one. The folder is kept
 * for predictability rather than filled with an invented invariant.
 */

import { readResult as fetchResult } from '../api/resultApi';
import type { Result } from '../domain/Result';
import { toResult } from '../mappers/resultMappers';

export interface ReadResultOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

export function readResult({ matchId, signal }: ReadResultOptions): Promise<Result> {
  return fetchResult({ matchId, signal }).then(toResult);
}
