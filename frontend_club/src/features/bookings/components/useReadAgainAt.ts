'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * **Reads the page again once a time the backend gave comes**, and nothing until then.
 *
 * It waits for `at` less `readAt` from when this browser first showed it, as a request's
 * countdown runs, so a browser whose clock is set wrong neither shortens nor lengthens the wait.
 * A yes waiting on one player's payment reads called off from its time on, if the payment has
 * not come in, and the page says so without the desk pressing anything.
 */
export function useReadAgainAt(due: { readonly at: number; readonly readAt: number }): void {
  const router = useRouter();
  const wait = due.at - due.readAt;

  useEffect(() => {
    if (wait <= 0) return undefined;
    const timer = window.setTimeout(() => router.refresh(), wait);
    return () => window.clearTimeout(timer);
  }, [wait, router]);
}
