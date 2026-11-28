/**
 * Coming **back to a screen** — the navigator's focus, claimed the way `useOnForeground` claims
 * the app's.
 *
 * ## Why the app's focus is not enough
 *
 * `focusManager` is wired to `AppState` (`appState.ts`), so a query re-reads when the app comes
 * to the front. It does **not** re-read when a player comes back to a screen from one pushed
 * over it: a stack keeps the screen under the top one **mounted**, so popping is neither a
 * mount nor a foreground, and a query that is already active does not refetch on staleness
 * alone. The symptom is a list that was true when the player left it and is stale when they
 * return — the Chats tab reading *Waiting on 2 answers* under a room in which the second answer
 * had just landed as a line ([#429](https://github.com/Rakieta02/Rakieta/issues/429) A5, A6).
 * Switching tabs happened to repair it, because a tab press replaces the stack and the remount
 * re-read; *back* never did.
 *
 * ## A return, not a focus
 *
 * `useFocusEffect` fires on the way **in** as well, and a mount is not a return —
 * `useOnForeground`'s own rule, for its reason: a screen that wants something to happen when it
 * opens can simply do it, and the app's mount posture (`staleTime`, `refetchOnMount`) is where
 * that decision already lives. So the callback runs only on a focus that follows a **blur** —
 * the player left this screen and came back — and never on the first focus, whether that is
 * the mount or a deep link's landing.
 *
 * ## Not `focusManager`
 *
 * TanStack's manager is one boolean for the whole app and it means *at the front*; teaching it
 * to mean *this screen is on top* would make every query in the app refetch on every pop,
 * which is the cost this hook exists to place on the one screen that pays it. A screen says
 * what its return re-reads.
 *
 * The callback is read through a ref, so one subscription still calls what the screen means
 * now rather than the closure it was made with — `useOnForeground`'s rule again, and what keeps
 * an inline callback off the effect's dependency list.
 */

import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef } from 'react';

/**
 * Run something each time the player comes back to this screen from one pushed over it.
 *
 * Nothing runs on the way in. Called from any component under a navigator's screen; the screen
 * it answers for is the nearest one.
 */
export function useOnReturn(run: () => void): void {
  const latest = useRef(run);
  const left = useRef(false);

  useEffect(() => {
    latest.current = run;
  }, [run]);

  useFocusEffect(
    useCallback(() => {
      if (left.current) latest.current();

      return () => {
        left.current = true;
      };
    }, []),
  );
}
