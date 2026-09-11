/**
 * The read and the one write.
 *
 * | | |
 * | --- | --- |
 * | `useOpenCards` | `GET /sportsmanship` — the courts still waiting for your stars |
 * | `useAnswerCard` | `POST /sportsmanship/{game_id}` — everybody from one game, answered once |
 *
 * ## The write is not optimistic, and it does not override `networkMode`
 *
 * *Does this act carry a deadline the player chose?* — the app's own test, and the answer is
 * no. The seven days a card stands for run from the **game**, not from the tap, so a send held
 * until the connection returns closes the same card it would have closed a minute earlier.
 * The challenge send is the one act in the app that answers yes, and it is the only one that
 * sets `networkMode: 'always'`. This one pauses like everything else, and the card renders
 * `offlineMessage('resumes')` at the control that is waiting.
 *
 * Nor is it optimistic. **Submitting closes the card for ever**, so an optimistic removal that
 * had to be rolled back would put a card the player believes they answered back in front of
 * them with a draft they can no longer trust — and the whole cost of a rollback here is one
 * refetch of a list that is usually empty.
 *
 * ## It invalidates on settled rather than on success
 *
 * Both endings say the same thing about the list. A success closes the card; the refusal that
 * matters — `you_have_already_rated_this_game` — says it was **already** closed, which is a
 * list this client is holding a stale copy of. Branching on the code to decide would put a
 * wire code in a hook to save one read of a list that is usually empty; refetching either way
 * is one line and cannot get the branch wrong.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { OpenCard } from '../domain/card';
import { answerTheCard, type CardAnswer } from '../use-cases/answerTheCard';
import { readOpenCards } from '../use-cases/readOpenCards';

import { cardKeys } from './cardKeys';

export function useOpenCards() {
  return useQuery<readonly OpenCard[], AppError>({
    queryKey: cardKeys.open(),
    queryFn: ({ signal }) => readOpenCards({ signal }),
  });
}

/** *How were they* — one card, everybody on it, and it closes on the way out. */
export function useAnswerCard() {
  const client = useQueryClient();

  return useMutation<void, AppError, CardAnswer>({
    mutationFn: answerTheCard,
    onSettled: () => {
      void client.invalidateQueries({ queryKey: cardKeys.open() });
    },
  });
}
