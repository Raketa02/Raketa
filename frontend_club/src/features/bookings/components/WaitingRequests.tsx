'use client';

import { useActionState, useState } from 'react';

import { Card } from '@/ui/Card';
import { formatZloty } from '@/ui/format';
import { SectionHeader } from '@/ui/SectionHeader';

import { actOnBooking } from '../actions';
import { BOOKINGS_COPY, shortDay, sportAndKind } from '../copy';
import type { WaitingRequest } from '../mappers';

import { ActNotice, NOTHING_DONE } from './ActNotice';
import { askedAbout, type Asked } from './Asked';
import styles from './Bookings.module.css';
import { RefuseDialog } from './RefuseDialog';
import { RequestActions } from './RequestActions';

const COPY = BOOKINGS_COPY;

/**
 * **Waiting for your answer** (the screens B2, the mechanics §16.8): what Overview shows once the
 * club is live, every full game asking for one of its courts, the one due first, first, each
 * with its hour, court, sport, players, price and countdown, and *Accept* or *Refuse*. Answered,
 * it goes, and what came of it is said over the list.
 */
export function WaitingRequests({ requests }: { requests: readonly WaitingRequest[] }) {
  const [state, act, acting] = useActionState(actOnBooking, NOTHING_DONE);
  const [refusing, setRefusing] = useState<Asked | null>(null);

  return (
    <Card labelledBy="waiting-title">
      <SectionHeader id="waiting-title" title={COPY.waiting.title} lead={COPY.waiting.lead} />
      <ActNotice state={state} />
      {requests.length === 0 ? (
        <p className={styles.none}>{COPY.waiting.none}</p>
      ) : (
        <ul className={styles.requests}>
          {requests.map((request) => {
            const game = askedAbout(request);
            return (
              <li key={request.id} className={styles.waiting}>
                <div className={styles.about}>
                  <p className={styles.waitingWhen}>
                    {shortDay(request.hour.day)} · {request.hour.from}–{request.hour.until} ·{' '}
                    {request.court}
                  </p>
                  <p>{sportAndKind(request.sport, request.kind)}</p>
                  <p className={styles.lead}>
                    {request.players.map((player) => player ?? COPY.nameless).join(', ')}
                  </p>
                  <p className={styles.price}>
                    {COPY.waiting.price(
                      formatZloty(request.priceGrosze),
                      formatZloty(request.shareGrosze),
                    )}
                  </p>
                </div>
                <RequestActions
                  id={request.id}
                  name={game.name}
                  answerBy={request.answerBy}
                  action={act}
                  pending={acting}
                  onRefuse={() => setRefusing(game)}
                />
              </li>
            );
          })}
        </ul>
      )}
      <RefuseDialog game={refusing} action={act} onClose={() => setRefusing(null)} />
    </Card>
  );
}
