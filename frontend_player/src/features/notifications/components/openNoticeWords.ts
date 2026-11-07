/**
 * **What opening a notice says, when it cannot** (#758) — handed into `useOpenNotice` by the two
 * places a notice is opened from, the list and the host (banner and push), since the words are
 * copy and a hook names none (`useOfficialGroupWrites`' `refusal`, the same seam). Here rather
 * than in `notificationsCopy`, which the shell reads at module load and keeps to shared formatting
 * and vocabulary: the sport is named by `onboarding`'s words for it, and a failure by the error
 * family's recovery sentence.
 *
 * ***Level asked*'s questionnaire did not start**: *You have a padel level already.* when the player
 * got one since the ask (`sport_already_rated`) — neutral, held to be read, since nothing went wrong
 * — and any other failure's recovery sentence, as a failure.
 */

import { sportInLine } from '@/features/onboarding/types';
import { recoveryMessage } from '@/shared/errors';

import type { OpenNoticeWords } from '../hooks/useOpenNotice';

import { alreadyRatedLine } from './notificationsCopy';

export const OPEN_NOTICE_WORDS: OpenNoticeWords = {
  unstarted: (sport, error) =>
    error.code === 'sport_already_rated'
      ? { message: alreadyRatedLine(sportInLine(sport)), hold: 'read' }
      : { message: recoveryMessage(error), tone: 'bad' },
};
