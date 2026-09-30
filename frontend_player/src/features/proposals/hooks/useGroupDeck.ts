/**
 * **A group's deck, and the writes that answer it** — the Games tab's read and its three answers
 * ([#553](https://github.com/Raketa02/Raketa/issues/553)).
 *
 * | | |
 * | --- | --- |
 * | `useGroupDeck` | `GET /pools/{id}/deck` for the sport and the kind the deck is on |
 * | `useAnswerCard` | `POST /proposals/{id}/yes` or `/no` — a swipe, a button, or the details' *I'm in* |
 * | `useWithdrawYes` | `DELETE /proposals/{id}/yes` — the details' *Withdraw* |
 * | `useDropCard` | the answered card off the read the moment it has flown |
 * | `useRereadDeck` | the group's decks marked stale — after the intent question is answered |
 *
 * ## The kind is chosen, and then corrected by what the intent shows
 *
 * The switch hands in the kind the player chose. The read says which segments their intent shows,
 * and a choice it does not show is read again for the segment it does (`resolveKind`): a player
 * whose intent is For fun is never shown an empty Competitive deck because the switch last stood
 * there. Two queries rather than one, keyed by what each asks for — the first is the question the
 * switch put, and the second is asked only when its answer says the question was the wrong one.
 *
 * ## The app's defaults, and one reason each is right
 *
 * The thirty-second `staleTime` and the refetch on focus are what bring a card another player has
 * said yes to back with their tile In when the player returns (the mechanics §6.4). **Nothing polls
 * while the tab is open**: a read that reordered the deck under a thumb would put a different card
 * under it, and the one a player is reading is the one they are about to answer.
 *
 * ## An answer re-reads the group's decks when the server has it
 *
 * Every answer invalidates the group's root — every sport, both kinds — on settling: a yes moves
 * the badge across segments, and a refusal that returns a card is the server putting it back. The
 * card itself leaves the read the moment it has **flown** (`useDropCard`), not the moment the
 * answer is sent, because the stage holds the card in flight until then (`GamesDeck`).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { resolveKind, withoutCard, type GroupDeck } from '../domain/deck';
import type { GameKind } from '../domain/vocabulary';
import { answerCard, withdrawYes, type AnswerToCard } from '../use-cases/answers';
import { readGroupDeck } from '../use-cases/deckReads';

import { deckKeys } from './deckKeys';

function deckQuery(groupId: string, sport: Sport, kind: GameKind, enabled = true) {
  return {
    queryKey: deckKeys.deck(groupId, sport, kind),
    queryFn: ({ signal }: { signal: AbortSignal }) =>
      readGroupDeck(groupId, sport, kind, { signal }),
    enabled,
  };
}

/**
 * The deck for the sport the page is on and the kind the switch chose — corrected to a kind the
 * player's intent shows. `kind` is the one the answer is for.
 */
export function useGroupDeck(groupId: string, sport: Sport, chosen: GameKind) {
  const asked = useQuery<GroupDeck, AppError>(deckQuery(groupId, sport, chosen));
  const kind = resolveKind(chosen, asked.data?.segments);
  const corrected = useQuery<GroupDeck, AppError>(deckQuery(groupId, sport, kind, kind !== chosen));

  return { read: kind === chosen ? asked : corrected, kind };
}

/** **The Games tab's badge** — cards where somebody is already In with you, across the segments. */
export function useGamesBadge(groupId: string, sport: Sport, chosen: GameKind): number {
  return useGroupDeck(groupId, sport, chosen).read.data?.gamesBadge ?? 0;
}

/** Take a card that has flown off the read it was dealt on — see the module note. */
export function useDropCard(groupId: string, sport: Sport, kind: GameKind) {
  const client = useQueryClient();
  return (proposalId: string) => {
    client.setQueryData<GroupDeck>(deckKeys.deck(groupId, sport, kind), (held) =>
      held === undefined ? held : withoutCard(held, proposalId),
    );
  };
}

/** Mark every deck read for this group stale, so the one on screen is read again. */
export function useRereadDeck(groupId: string) {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: deckKeys.group(groupId) });
}

/** What a caller is told of a refused write — the refusal, and which answer it refused. */
export type OnRefused<Variables> = (error: AppError, refused: Variables) => void;

/**
 * **The refusal handler, on the mutation rather than on the call.** A player answers the next card
 * while the last answer is still in flight, and TanStack drops a `mutate` call's own callbacks when
 * a later call is made on the same mutation — so a refusal handed to `mutate` would go unsaid for
 * every card but the last. The mutation's own `onError` fires for every call; it reads the caller's
 * handler through a ref, so the handler can close over the screen's state.
 */
function useRefusalRef<Variables>(onRefused: OnRefused<Variables> | undefined) {
  const latest = useRef(onRefused);
  useEffect(() => {
    latest.current = onRefused;
  });
  return (error: AppError, refused: Variables) => latest.current?.(error, refused);
}

/**
 * **One answer to a card.** Not retried — every mutation's rule, although both routes are safe to
 * repeat — and held while offline (`networkMode: 'online'`), so the card stays gone and the answer
 * is sent when the connection returns.
 */
export function useAnswerCard(groupId: string, onRefused?: OnRefused<AnswerToCard>) {
  const client = useQueryClient();
  const refused = useRefusalRef(onRefused);

  return useMutation<void, AppError, AnswerToCard>({
    mutationFn: answerCard,
    onError: refused,
    onSettled: () => client.invalidateQueries({ queryKey: deckKeys.group(groupId) }),
  });
}

/** **Withdraw a yes** — free and silent until the game fills. */
export function useWithdrawYes(groupId: string, onRefused?: OnRefused<string>) {
  const client = useQueryClient();
  const refused = useRefusalRef(onRefused);

  return useMutation<void, AppError, string>({
    mutationFn: withdrawYes,
    onError: refused,
    onSettled: () => client.invalidateQueries({ queryKey: deckKeys.group(groupId) }),
  });
}
