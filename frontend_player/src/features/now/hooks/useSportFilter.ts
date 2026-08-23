/**
 * The selected chip, and the one rule about how long it lasts.
 *
 * The visit boundary is driven from **`focusManager`**, not from `AppState`
 * directly. `shared/lib/platform` already wires that manager to the only thing
 * "focus" means on a phone, and reading it here means the filter's idea of *away*
 * and Query's idea of *arrival* cannot drift apart — one subscription source, two
 * readers. `ADR-0054` calls those managers configuration rather than machinery,
 * and this keeps them that.
 *
 * Nothing here is a timer. The subscription fires when the OS says the app
 * changed state and at no other moment.
 */

import { focusManager } from '@tanstack/react-query';
import { useEffect } from 'react';

import type { SportFilter } from '../mappers/codes';
import { useSportFilterStore } from '../store/sportFilter.store';

export interface SportFilterSelection {
  readonly selected: SportFilter;
  readonly select: (sport: SportFilter) => void;
}

export function useSportFilter(): SportFilterSelection {
  const selected = useSportFilterStore((state) => state.selected);
  const select = useSportFilterStore((state) => state.select);
  const left = useSportFilterStore((state) => state.left);
  const returned = useSportFilterStore((state) => state.returned);

  useEffect(
    () =>
      focusManager.subscribe((focused) => {
        // `Date.now()` rather than a passed clock: this is the device's own time
        // and nothing on the wire is being compared against it.
        if (focused === true) returned(Date.now());
        if (focused === false) left(Date.now());
      }),
    [left, returned],
  );

  return { selected, select };
}
