/**
 * **A *You're In* row** — a yes of the reader's on a game still filling in this group
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3.2; mock 13; the mechanics
 * §10.2).
 *
 * ```
 * ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   mint, 1.5pt
 * ┃ Padel · Saturday 15:00                    ┃   the title — and the door to the details
 * ┃ Bonarka Arena · book by Sat 13:00         ┃   or, amber, *waiting for the club*
 * ┃ [TK] [  ] [  ] [  ]            [ Withdraw ] ┃   everybody In, then the open seats dashed
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **The row is the live yes, and its squares are the game's read** (`useProposal`): the live yes
 * says the game, the club and the book-by; who is In — the reader among them — how many seats are
 * open, whether an On request club is deciding and whether the reader may withdraw are the game's
 * details, read for the row. Until they land the row draws what the yes says, with no squares and
 * no *Withdraw*: ***Withdraw*** is free and silent, and **hidden while the club decides** (A3.2) —
 * the details' own `actions` say which (`mayWithdraw`), and a withdrawal while the club decides
 * would call the request off with no sheet in front of it. Leaving then happens from the details.
 * **One read a row**: the live yes carries neither who is In nor the club's turn (owed to the
 * backend's live-yes read).
 */

import { View } from 'react-native';

import { showToast } from '@/shared/store/toast.store';
import { Button } from '@/shared/ui';

import type { DeckPerson } from '../domain/deck';
import type { ProposalDetails } from '../domain/details';
import { mayWithdraw, squaresOfYes } from '../domain/fillIn';
import type { LiveYes } from '../domain/liveYes';
import { gameDayOf } from '../domain/when';
import { useWithdrawYes } from '../hooks/useGroupDeck';
import { useProposal } from '../hooks/useProposal';

import { clubName, refusalMessage } from './deckPresentation';
import { FILL_IN_COPY } from './fillInCopy';
import { rowTitle, yesRowLabel, yesWhen } from './fillInPresentation';
import { FillInRow } from './FillInRow';
import { FillInSquares } from './FillInSquares';

export interface YoureInRowProps {
  readonly yes: LiveYes;
  /** The read's clock. */
  readonly now: number;
  readonly onOpen: () => void;
  readonly onHold: (person: DeckPerson) => void;
}

export function YoureInRow({ yes, now, onOpen, onHold }: YoureInRowProps) {
  const details = useProposal(yes.proposalId).data ?? undefined;
  const withdraw = useWithdrawYes(yes.groupId, (error) =>
    showToast({ message: refusalMessage(error), tone: 'bad' }),
  );

  const day = gameDayOf(yes.startsAt, now);
  const waiting = details?.status === 'WAITING_FOR_THE_CLUB';

  return (
    <FillInRow
      frame="yours"
      label={yesRowLabel(yes, day, waiting)}
      title={rowTitle(yes, day)}
      club={clubName(yes)}
      when={yesWhen(yes, waiting)}
      waiting={waiting}
      onOpen={onOpen}
      testID={`youre-in-${yes.proposalId}`}
    >
      {details === undefined ? <View /> : <Squares details={details} onHold={onHold} />}
      {mayWithdraw(details) ? (
        <Button
          label={FILL_IN_COPY.withdraw}
          variant="secondary"
          size="md"
          busy={withdraw.isPending}
          onPress={() => withdraw.mutate(yes.proposalId)}
        />
      ) : null}
    </FillInRow>
  );
}

/** Everybody In, then the open seats dashed — off the game's details. */
function Squares({
  details,
  onHold,
}: {
  readonly details: ProposalDetails;
  readonly onHold: (person: DeckPerson) => void;
}) {
  const { people, open } = squaresOfYes(details);
  return <FillInSquares people={people} open={open} question={false} onHold={onHold} />;
}
