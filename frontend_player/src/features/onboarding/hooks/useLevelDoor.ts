/**
 * **The door where play begins, as a hook** — what it offers, and walking through it
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §2, §5,
 * [#730](https://github.com/Rakieta02/Rakieta/issues/730)).
 *
 * What it offers is `levelDoor`'s rule, off two reads: the first unfinished run, and that run's
 * own step — the question she is on is its count, replayed from the transcript. **Nothing is
 * offered until both have answered**, so a door never says *Get your level* and then turns into
 * *Carry on*. A read that fails offers the picker: starting a sport with an unfinished run hands
 * that run back, so the worst the fallback costs is one screen.
 *
 * **Walking through is a `replace`**, as every door into the questionnaire is (`useAddASport`): the
 * questionnaire is a sibling group of the app's tree, and the way back is the pass ending, which
 * the gate reads off the origin. *Carry on* begins a pass of the run's one sport, here and before
 * the route is written, so the question screen reads its position on its first render; the picker
 * begins its own pass, on its own start. A latch keeps a second press from a second departure.
 */

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useCallback, useRef } from 'react';

import { levelDoor, type DoorOffer } from '../domain/levelDoor';
import type { DoorOrigin } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { sportsPickerRoute } from './sportsPickerRoute';
import { assessmentQuery } from './useAssessment';
import { useRunInProgress } from './useRunInProgress';

export interface LevelDoorControl {
  /** What the door offers — `undefined` while either read is out. */
  readonly door: DoorOffer | undefined;
  /**
   * **A read is waiting for the connection**, with nothing cached to answer from — so the door
   * cannot say which it is, and says why rather than drawing nothing for as long as it lasts.
   */
  readonly offline: boolean;
  /** Walk through it. A second press while the first departs does nothing. */
  readonly open: () => void;
}

export function useLevelDoor(from: DoorOrigin): LevelDoorControl {
  const router = useRouter();
  const beginPass = useOnboardingPass((state) => state.begin);
  const run = useRunInProgress();
  const found = run.data ?? undefined;
  const step = useQuery({
    ...assessmentQuery(found?.assessmentId ?? ''),
    enabled: found !== undefined,
  });

  const door = offered();
  function offered(): DoorOffer | undefined {
    if (run.isError) return levelDoor(undefined, undefined);
    if (!run.isSuccess) return undefined;
    if (found === undefined) return levelDoor(undefined, undefined);
    if (step.isError) return levelDoor(found, undefined);
    return step.isSuccess ? levelDoor(found, step.data) : undefined;
  }

  const departing = useRef(false);
  const open = useCallback(() => {
    if (door === undefined || departing.current) return;
    departing.current = true;
    if (door.kind === 'start') {
      router.replace(sportsPickerRoute(from));
      return;
    }
    beginPass([door.run.sport], from);
    router.replace({
      pathname: '/question/[assessmentId]',
      params: { assessmentId: door.run.assessmentId, sport: door.run.sport },
    });
  }, [beginPass, door, from, router]);

  // Paused, not loading: `networkMode: 'online'` holds a query rather than failing it.
  const offline =
    door === undefined && (run.fetchStatus === 'paused' || step.fetchStatus === 'paused');

  return { door, offline, open };
}
