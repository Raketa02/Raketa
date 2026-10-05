/**
 * **Why a removal was refused, read off the refusal** — `payment_method_in_use` carries
 * `details.live_yeses` and `details.upcoming_games` (#536), and `AppError.details` is an untyped
 * dictionary no generator can see, so it is parsed here like any other input from outside
 * (docs/architecture.md Part 9). A details block that does not parse is a refusal with no counts,
 * which the screen still says in words.
 */

import { z } from 'zod';

import type { MethodInUse } from '../domain/vocabulary';

const count = z.number().int().nonnegative();

const methodInUseDetails = z.object({ live_yeses: count, upcoming_games: count });

export function methodInUseFrom(details: unknown): MethodInUse | null {
  const parsed = methodInUseDetails.safeParse(details);
  return parsed.success
    ? { liveYeses: parsed.data.live_yeses, upcomingGames: parsed.data.upcoming_games }
    : null;
}
