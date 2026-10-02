'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import type { AnswerBy } from '../mappers';

const SECOND_MS = 1000;

/**
 * **What is left of a request's time to answer**, in milliseconds, ticking every second.
 *
 * It starts from what the backend said when the page was read (`answer_by` less `read_at`) and
 * runs down by the time this browser has been showing it, so a browser whose clock is set wrong
 * neither shortens nor lengthens it, and the server and the browser draw the same first figure.
 * Once it runs out the page is read again: the request is called off as unanswered from that
 * moment, and the frame's badge goes down.
 */
export function useCountdown(answerBy: AnswerBy): number {
  const router = useRouter();
  const initial = answerBy.at - answerBy.readAt;
  const [left, setLeft] = useState(initial);
  const [readFrom, setReadFrom] = useState(initial);

  // The page was read again: the countdown starts again from what it says now.
  if (readFrom !== initial) {
    setReadFrom(initial);
    setLeft(initial);
  }

  useEffect(() => {
    if (initial <= 0) return undefined;
    const shown = Date.now();
    const timer = window.setInterval(() => {
      const now = initial - (Date.now() - shown);
      setLeft(now);
      if (now <= 0) {
        window.clearInterval(timer);
        router.refresh();
      }
    }, SECOND_MS);
    return () => window.clearInterval(timer);
  }, [initial, router]);

  return left;
}
