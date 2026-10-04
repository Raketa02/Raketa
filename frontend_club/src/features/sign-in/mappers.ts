/** **Sign-up's body**: the five details and the credentials the desk signs in with. */

import type { Club } from '@/features/club-details/mappers';
import { toDetailsBody } from '@/features/club-details/mappers';
import type { components } from '@/generated/schema';

export function toSignUpBody(
  details: Club,
  email: string,
  password: string,
): components['schemas']['ClubSignUpRequest'] {
  return { ...toDetailsBody(details), email, password };
}
