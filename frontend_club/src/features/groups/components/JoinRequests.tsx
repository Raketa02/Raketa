'use client';

import { useActionState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import fieldStyles from '@/ui/Field.module.css';
import { Notice } from '@/ui/Notice';

import { answerJoinRequest, type AnswerState } from '../actions';
import { answerRefusal, GROUPS_COPY, levelsLine } from '../copy';
import type { GroupRow, JoinRequest } from '../mappers';
import type { Answer } from '../schemas';

import styles from './JoinRequests.module.css';

const COPY = GROUPS_COPY.requests;
const NOTHING_REFUSED: AnswerState = { refusal: null };

/** One answer to one person: a form that is only its button. */
function AnswerButton({
  answer,
  group,
  request,
  name,
  action,
  pending,
}: {
  answer: Answer;
  group: GroupRow;
  request: JoinRequest;
  name: string;
  action: (form: FormData) => void;
  pending: boolean;
}) {
  const approving = answer === 'approve';
  return (
    <form action={action}>
      <input type="hidden" name="answer" value={answer} />
      <input type="hidden" name="group" value={group.id} />
      <input type="hidden" name="player" value={request.id} />
      <input type="hidden" name="name" value={name} />
      <Button
        type="submit"
        tone={approving ? 'ink' : 'secondary'}
        disabled={pending}
        aria-label={approving ? COPY.approveWho(name) : COPY.declineWho(name)}
      >
        {approving ? COPY.approve : COPY.decline}
      </Button>
    </form>
  );
}

/**
 * **Want to join · N** (club mock 20's card, ADR-0191 §1): everybody waiting on the group, in
 * the order they asked, each with *Decline* and *Approve*. The club answers whoever runs the
 * group, and is the only one who can while nobody does, which the line under the title says.
 * Neither answer asks first: approving is what the person asked for, and declining tells them
 * nothing and leaves them free to ask again. Nobody waiting draws nothing.
 */
export function JoinRequests({
  group,
  requests,
}: {
  group: GroupRow;
  requests: readonly JoinRequest[];
}) {
  const [state, action, pending] = useActionState(answerJoinRequest, NOTHING_REFUSED);
  const refused =
    state.refusal === null ? null : <Notice tone="error">{answerRefusal(state.refusal)}</Notice>;
  if (requests.length === 0) return refused;

  return (
    <Card>
      <div className={styles.head}>
        <h2 className={fieldStyles.label}>{COPY.title(requests.length)}</h2>
        <p className={styles.explain}>
          {group.administrator === null ? COPY.nobody : COPY.runBy(group.administrator.name)}
        </p>
      </div>
      {refused}
      <ul className={styles.requests}>
        {requests.map((request) => {
          const name = request.nickname ?? COPY.unnamed;
          return (
            <li key={request.id} className={styles.request}>
              <div className={styles.who}>
                <span className={styles.name}>{name}</span>
                <span className={styles.levels}>{levelsLine(request.levels)}</span>
              </div>
              <div className={styles.answers}>
                {(['decline', 'approve'] as const).map((answer) => (
                  <AnswerButton
                    key={answer}
                    answer={answer}
                    group={group}
                    request={request}
                    name={name}
                    action={action}
                    pending={pending}
                  />
                ))}
              </div>
            </li>
          );
        })}
      </ul>
      <p className={styles.explain}>{COPY.explain}</p>
    </Card>
  );
}
