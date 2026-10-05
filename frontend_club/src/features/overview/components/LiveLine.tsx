'use client';

import { useEffect, useState } from 'react';

import { Notice } from '@/ui/Notice';

import { noteToldLive } from '../actions';
import { OVERVIEW_COPY } from '../copy';

/**
 * ***You're live — your courts can now be booked through Raketa***, said once (the screens B2).
 * Drawn, it asks the server to remember it was said, which draws the page again as told; the
 * line stays until the desk leaves the page, because it holds what it was first drawn with. A
 * club no longer live is forgotten as told, so it is told again when it is.
 */
export function LiveLine({ live, told }: { live: boolean; told: boolean }) {
  const [say] = useState(live && !told);

  useEffect(() => {
    if (live !== told) void noteToldLive(live);
  }, [live, told]);

  return say ? <Notice tone="success">{OVERVIEW_COPY.live}</Notice> : null;
}
