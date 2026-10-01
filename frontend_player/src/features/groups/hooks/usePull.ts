/**
 * **A pull's spinner** — on from the pull until the re-read has settled, and one pull at a time.
 * The group page's Info and the Groups list both pull (#529), each handing in what it re-reads.
 */

import { useRef, useState } from 'react';

export function usePull(reread: () => Promise<void>) {
  const [refreshing, setRefreshing] = useState(false);
  const inFlight = useRef(false);

  async function pull() {
    if (inFlight.current) return;
    inFlight.current = true;
    setRefreshing(true);
    try {
      await reread();
    } catch {
      // A refused re-read is the read's own to say, on what it draws; the spinner only stops.
    } finally {
      inFlight.current = false;
      setRefreshing(false);
    }
  }

  return { refreshing, pull: () => void pull() };
}
