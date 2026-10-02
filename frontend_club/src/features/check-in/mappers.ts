/**
 * **A check-in, wire to view and back.** The only file in this feature that imports a generated
 * type (ADR-0187 §6); everything else reads the view models it makes.
 */

import type { components } from '@/generated/schema';
import { clubClock, clubHour, type ClubHour } from '@/features/bookings/mappers';
import type { Sport } from '@/features/club-details/mappers';
import { clubDay } from '@/features/courts/mappers';

type WireCheckedIn = components['schemas']['CheckInResponse'];
type WireCheckInBody = components['schemas']['CheckInRequest'];

/** **A player the desk checked in**, and the game they are there for: *19:00 · Court 2 · Padel*. */
export interface CheckedIn {
  readonly hour: ClubHour;
  readonly court: string;
  readonly sport: Sport;
  /** `null` for an account that can no longer be named. */
  readonly player: string | null;
}

export function toCheckedIn(wire: WireCheckedIn): CheckedIn {
  return {
    hour: clubHour(wire.starts_at, wire.ends_at),
    court: wire.court_name,
    sport: wire.sport,
    player: wire.player.name,
  };
}

export function toCheckInBody(code: string): WireCheckInBody {
  return { code };
}

/**
 * **Why a code checked nobody in**: the backend's code or the page's own, with what the backend
 * said about it. A code for another day names the game's hour (`details.starts_at`); a player
 * checked in already, when (`details.checked_in_at`).
 */
export interface CheckInRefusal {
  readonly code: string;
  /** Another day's game: its local day and the hour it starts, `null` when not said. */
  readonly game: Pick<ClubHour, 'day' | 'from'> | null;
  /** When the player was checked in already, on the club's clock (`18:52`), `null` when not said. */
  readonly checkedInAt: string | null;
  /** Nothing was wrong with the code: the server could not be asked, so the same code may go again. */
  readonly mayTryAgain: boolean;
}

/** An instant the backend wrote in `details`, or `null` when it wrote none it could mean. */
function validInstant(text: string | undefined): string | null {
  return text === undefined || Number.isNaN(Date.parse(text)) ? null : text;
}

export function toCheckInRefusal(
  code: string,
  details: Readonly<Record<string, string>> | undefined,
): CheckInRefusal {
  const startsAt = validInstant(details?.starts_at);
  const checkedInAt = validInstant(details?.checked_in_at);
  return {
    code,
    game:
      startsAt === null ? null : { day: clubDay(Date.parse(startsAt)), from: clubClock(startsAt) },
    checkedInAt: checkedInAt === null ? null : clubClock(checkedInAt),
    mayTryAgain: code === 'backend_unreachable' || code === 'backend_failed',
  };
}
