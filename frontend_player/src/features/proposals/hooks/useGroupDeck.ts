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
 * | `useRereadGroupGames` | the decks, Fill in, the games' details and the live yeses — a pull |
 * | `useAnswersOnTheirWay` | the cards whose answers are still on their way — hidden from a read |
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
 * said yes to back with their tile In when the player returns (the mechanics §6.4), and every
 * answer re-reads the deck, in turn (below). **Nothing polls while the tab is open.** It once could
 * not — a read that reordered the deck would put a different card under the thumb — and since
 * 2026-10-12 none can, because `GamesDeck` keeps the card being read on top; what stops a poll now
 * is its price. A deck read is the whole deck recomputed on the server, tens of queries, and a poll
 * pays that for every open deck whether anything changed or not. Another player's yes reaching a
 * deck nobody is answering is a nudge to the players on that card, owed to the backend.
 *
 * ## An answer re-reads the group's decks when the server has it
 *
 * Every answer invalidates the group's root — every sport, both kinds — on settling: a yes moves
 * the badge across segments, and a refusal that returns a card is the server putting it back. A yes
 * and a withdraw re-read the player's live yeses too, which You › Payments lists (#554). The
 * card itself leaves the read the moment it has **flown** (`useDropCard`), not the moment the
 * answer is sent, because the stage holds the card in flight until then (`GamesDeck`).
 */

import {
  useMutation,
  useMutationState,
  useQuery,
  useQueryClient,
  type QueryClient,
  type QueryKey,
} from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { resolveKind, withoutCard, type GroupDeck } from '../domain/deck';
import { isRescue, type YesAnswer, type YesOn } from '../domain/fill';
import type { GameKind } from '../domain/vocabulary';
import { answerCard, withdrawYes, type AnswerToCard } from '../use-cases/answers';
import { readGroupDeck } from '../use-cases/deckReads';

import { proposalKeys } from './proposalKeys';
import { useLatest } from './useLatest';

function deckQuery(groupId: string, sport: Sport, kind: GameKind, enabled = true) {
  return {
    queryKey: proposalKeys.deck(groupId, sport, kind),
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

/** Take a card off the read it was dealt on — its segment's count and the badge following it. */
export function dropCard(
  client: QueryClient,
  {
    groupId,
    sport,
    kind,
  }: { readonly groupId: string; readonly sport: Sport; readonly kind: GameKind },
  proposalId: string,
) {
  client.setQueryData<GroupDeck>(proposalKeys.deck(groupId, sport, kind), (held) =>
    held === undefined ? held : withoutCard(held, proposalId),
  );
}

/** Take a card that has flown off the read it was dealt on — see the module note. */
export function useDropCard(groupId: string, sport: Sport, kind: GameKind) {
  const client = useQueryClient();
  return (proposalId: string) => dropCard(client, { groupId, sport, kind }, proposalId);
}

/** Mark every deck read for this group stale, so the one on screen is read again. */
export function useRereadDeck(groupId: string) {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: proposalKeys.group(groupId) });
}

/**
 * **A pull on the group page's Games or Fill in** — what a yes settling re-reads (`reread`): the
 * group's decks and its Fill in, the games' details *You're In*'s rows draw their squares from, and
 * the live yeses that are *You're In*. Only the reads on screen go out at once; the rest are marked
 * stale. Settles once they have, so the pull's spinner stops when the tab is drawn again.
 */
export function useRereadGroupGames(groupId: string): () => Promise<void> {
  const client = useQueryClient();
  return () => reread(client, groupId, { yeses: true }).then(() => undefined);
}

/** What a caller is told of a refused write — the refusal, and which answer it refused. */
export type OnRefused<Variables> = (error: AppError, refused: Variables) => void;

/**
 * **One answer, and the card it was given on** — carried so the yes's answer can be read against
 * the card it filled (*It's a game!* draws its faces), whichever screen sent it, and so a rescue's
 * answer goes to its booking.
 */
export interface AnswerOnCard<Card extends YesOn = YesOn> extends Omit<AnswerToCard, 'rescue'> {
  readonly card?: Card;
}

/** What a caller is told of a yes's answer — the fill's to read (`useFill().answered`). */
export type OnAnswered<Card extends YesOn = YesOn> = (
  answer: YesAnswer,
  asked: AnswerOnCard<Card>,
) => void;

/*
 * **The handlers sit on the mutation rather than on the call.** A player answers the next card
 * while the last answer is still in flight, and TanStack drops a `mutate` call's own callbacks when
 * a later call is made on the same mutation — so a refusal handed to `mutate` would go unsaid for
 * every card but the last. The mutation's own callbacks fire for every call; they read the
 * caller's handlers as of its last render (`useLatest`), so a handler can close over the screen's
 * state.
 */

/**
 * **One answer to a card.** Not retried — every mutation's rule, although both routes are safe to
 * repeat — and held while offline (`networkMode: 'online'`), so the card stays gone and the answer
 * is sent when the connection returns. **A yes's answer is handed on** (`onAnswered`): a yes the
 * card called a free vote can still be the one that fills the game, if the others got there first.
 */
export function useAnswerCard<Card extends YesOn = YesOn>(
  groupId: string,
  onRefused?: OnRefused<AnswerOnCard<Card>>,
  onAnswered?: OnAnswered<Card>,
) {
  const client = useQueryClient();
  const handlers = useLatest({ onRefused, onAnswered });

  return useMutation<YesAnswer | null, AppError, AnswerOnCard<Card>>({
    mutationKey: proposalKeys.answers(),
    mutationFn: ({ proposalId, said, card }) =>
      answerCard({ proposalId, said, rescue: card !== undefined && isRescue(card) }),
    onSuccess: (answer, asked) => {
      if (answer !== null) handlers.current.onAnswered?.(answer, asked);
    },
    onError: (error, asked) => handlers.current.onRefused?.(error, asked),
    onSettled: (_answer, _error, { said }) => reread(client, groupId, { yeses: said === 'yes' }),
  });
}

/**
 * **Withdraw a yes** — free and silent until the game fills. Home is read again too: a full game
 * gone back to filling is on it, and a withdrawal takes it off (Q106, #629).
 */
export function useWithdrawYes(groupId: string, onRefused?: OnRefused<string>) {
  const client = useQueryClient();
  const handlers = useLatest({ onRefused });

  return useMutation<void, AppError, string>({
    mutationFn: withdrawYes,
    onError: (error, proposalId) => handlers.current.onRefused?.(error, proposalId),
    onSettled: () => rereadAfterWithdrawing(client, groupId),
  });
}

/**
 * What an answer settling re-reads: the group's decks and its Fill in, and every game's details,
 * always — the details answered are drawn from their own read now (#557) — and the player's live
 * yeses when the answer could have moved them — a yes adds one and a withdraw takes one away (You ›
 * Payments, #554); a no never touched a yes. Awaited, so the answer is pending until the deck or the
 * details on screen have been read again — **in turn** (`readAgainInTurn`).
 */
export function reread(
  client: QueryClient,
  groupId: string,
  { yeses }: { readonly yeses: boolean },
) {
  return Promise.all([
    readAgainInTurn(client, proposalKeys.group(groupId)),
    readAgainInTurn(client, proposalKeys.proposals()),
    ...(yeses ? [readAgainInTurn(client, proposalKeys.liveYeses())] : []),
  ]);
}

/**
 * **Read again, in turn** — after a write the reads must show. A read already on its way is let
 * land rather than thrown away, and since it may have started before the write did, one more read
 * follows it; every write that settles while that one is out shares it.
 *
 * TanStack's default throws the read away and starts another (`cancelRefetch`). A player answering
 * faster than the deck is read then never sees one land — every answer cancels the read the last
 * one asked for, so another player's yes waits for them to stop — and the server does each
 * cancelled read's work all the same, which is the load that grows with the players. The phone's
 * own re-reads on focus and on reconnect already let a read land (`cancelRefetch: false`); this is
 * the same, with the one read more a write needs. A read that predates an answer cannot deal its
 * card back meanwhile: the deck hides a card whose answer is on its way (`useAnswersOnTheirWay`).
 */
export async function readAgainInTurn(client: QueryClient, queryKey: QueryKey): Promise<void> {
  // Each read waits for its own only — never a deck for a Fill in still retrying beside it.
  await Promise.all(
    client
      .getQueryCache()
      .findAll({ queryKey })
      .map(async (query) => {
        const one = { queryKey: query.queryKey, exact: true } as const;
        await client.refetchQueries({ ...one, fetchStatus: 'fetching' }, { cancelRefetch: false });
        await client.invalidateQueries(one, { cancelRefetch: false });
      }),
  );
}

/**
 * **The cards whose answers are on their way** — sent from the deck, the details or the fill, and
 * not yet settled with the reads that show them. A read that set out before an answer reached the
 * server still deals its card, and the deck draws none of them (`GamesDeck`).
 */
export function useAnswersOnTheirWay(): ReadonlySet<string> {
  const answering = useMutationState({
    filters: { mutationKey: proposalKeys.answers(), status: 'pending' },
    select: (mutation) => answeredCard(mutation.state.variables),
  });
  return new Set(answering.filter((proposalId) => proposalId !== undefined));
}

/** The card an answer is about — `AnswerOnCard`'s own id, or the fill's booked yes's card's. */
function answeredCard(asked: unknown): string | undefined {
  if (typeof asked !== 'object' || asked === null) return undefined;
  if ('proposalId' in asked && typeof asked.proposalId === 'string') return asked.proposalId;
  return 'card' in asked ? answeredCard(asked.card) : undefined;
}

/**
 * **What a yes taken back re-reads** — an answer's, the live yeses among them, and Home: a game
 * waiting for one payment is on it, and so is a full game gone back to filling (Q106), and the yes
 * taken back takes either off.
 */
export function rereadAfterWithdrawing(client: QueryClient, groupId: string) {
  return Promise.all([
    reread(client, groupId, { yeses: true }),
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
  ]);
}
