'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import type { FormState } from '@/ui/forms';

import {
  toCheckedIn,
  toCheckInBody,
  toCheckInRefusal,
  type CheckedIn,
  type CheckInRefusal,
} from './mappers';
import { checkCode, readCode, type CodeField, type Via } from './schemas';

/**
 * **The last code's answer.** A typed code the page refused before asking goes under the box
 * (`refusals`); every other answer, whichever way the code came, is said once, between the
 * camera and the box: the player checked in, or why not.
 */
export interface CheckInState extends FormState<CodeField> {
  /** How the last code came in: a typed one checked in empties the box for the next. */
  readonly via: Via | null;
  readonly checkedIn: CheckedIn | null;
  readonly refusal: CheckInRefusal | null;
}

function answer(via: Via, answered: Pick<CheckInState, 'checkedIn' | 'refusal'>): CheckInState {
  return { via, ...answered, refusals: {}, formRefusal: null };
}

/**
 * **Check a player in** on the game's day, from what the camera read off their QR code or the
 * short code typed under it. Money never depends on it: a scan only says the player was there,
 * and a player checked in can never be reported as not coming. Bookings shows it at once.
 */
export async function checkIn(_previous: CheckInState, form: FormData): Promise<CheckInState> {
  const posted = readCode(form);
  const refused = checkCode(posted);
  if (refused !== null) {
    // A typed code's own fault goes under the box; a QR code that is somebody else's, over all.
    if (posted.via === 'typed') {
      return {
        ...answer('typed', { checkedIn: null, refusal: null }),
        refusals: { code: refused },
      };
    }
    return answer('camera', { checkedIn: null, refusal: toCheckInRefusal(refused, undefined) });
  }

  const outcome = await writeAsClub((api, auth) =>
    api.POST('/api/v1/club/check-ins', { ...auth, body: toCheckInBody(posted.code) }),
  );
  if (!outcome.ok) {
    // A 404 or a 409 may mean Bookings is out of date (checked in already, called off).
    if (outcome.error.status === 404 || outcome.error.status === 409) revalidatePath('/bookings');
    return answer(posted.via, {
      checkedIn: null,
      refusal: toCheckInRefusal(outcome.error.code, outcome.error.details),
    });
  }
  revalidatePath('/bookings');
  return answer(posted.via, { checkedIn: toCheckedIn(outcome.data), refusal: null });
}
