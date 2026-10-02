'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';

import { readRequestCount } from '../actions';

/** How often an open page asks whether a request arrived or ran out. */
const WATCH_MS = 30_000;

/**
 * **Keeps the frame's badge true.** The frame is drawn once and not again as the desk moves
 * between pages, while a request can arrive, or run out unanswered, with nobody acting. So on
 * each page the desk opens, and every half minute while the page is in view, it asks how many
 * wait; a count other than the one drawn draws everything again, the badge with it. It draws
 * nothing of its own.
 */
export function RequestsWatch({ count }: { count: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const checkedOn = useRef(pathname);

  useEffect(() => {
    let current = true;
    const check = async () => {
      if (document.visibilityState !== 'visible') return;
      const now = await readRequestCount();
      if (current && now !== null && now !== count) router.refresh();
    };
    // The page the frame was drawn with was counted with it; any other is asked about.
    if (checkedOn.current !== pathname) {
      checkedOn.current = pathname;
      void check();
    }
    const timer = window.setInterval(() => void check(), WATCH_MS);
    return () => {
      current = false;
      window.clearInterval(timer);
    };
  }, [pathname, count, router]);

  return null;
}
