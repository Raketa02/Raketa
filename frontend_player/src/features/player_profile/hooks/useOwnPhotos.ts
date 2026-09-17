/**
 * The You tab's photo workbench — the workbench's second home
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2): seeded from the profile, held beside the read, and **written on every change to the
 * row** — a promotion, a removal, an upload that landed — because the step has no *Save* and
 * the row is the state.
 *
 * ## What the step's bench derives, this one sends
 *
 * The step's workbench yields the draft's `photoIds` on every change (`profileDraft.store`).
 * This one yields **the photos the profile should hold now** (`standingPhotos`), and that
 * list's changing is what sends `PUT /players/me/photos`: a change to the pictures that did
 * not change the ids — a progress tick, a failure, a photo picked and still on its way, a
 * replacement still on its way in a slot that goes on standing for the photo it replaces —
 * sends nothing, because the profile cannot hold a photo the server has not named yet. When
 * that upload lands, the ids change, and that is the write.
 *
 * ## One write in flight, and the latest list wins
 *
 * A player rearranging three photographs sends three `PUT`s, each idempotent, and the last
 * one is the state — but two in flight at once could land in either order, and the server's
 * `concurrent_modification` refuses one without saying which. So writes are serialised here:
 * one in flight, and when it settles the bench is read again and sent again if it moved
 * meanwhile. On success the cache holds the route's answer; on failure the row keeps what
 * the player did, the screen says why, and the next change — or *Try again* — sends the
 * current list, never the one that failed.
 *
 * ## The bench is a ref, and the render is its mirror
 *
 * The uploads run in a queue that outlives any render and reads the bench between renders
 * (`useProfilePhotos`), so the list of record lives in a ref, changed synchronously, and the
 * state beside it is what a render draws. That is also what lets an upload begun on this
 * screen land after the player has left it: the ref is still written, the ids change, and the
 * write goes out — the step's *an upload outlives the screen*, kept.
 *
 * ## Seeded once, by construction
 *
 * The seed is the profile's photos with their signed addresses, and it is taken at mount:
 * the screen mounts this only once every address is in (`PhotosScreen`), so the first render
 * already holds the row, and a later refetch of the profile does not re-seed a bench the
 * player is rearranging — the week screen's *draft until the button*, without the button.
 */

import { useCallback, useRef, useState } from 'react';

import {
  photoIds,
  samePhotoIds,
  standingPhotos,
  type ProfilePhoto,
} from '../domain/photoCollection';

import { useProfilePhotos, type PhotoBench } from './useProfilePhotos';
import { useChangePhotos } from './useProfileSurface';

export function useOwnPhotos(seed: readonly ProfilePhoto[]) {
  const write = useChangePhotos();
  const { mutateAsync, reset } = write;
  /** The bench of record — read by the queue between renders, so never a render's copy. */
  const held = useRef<readonly ProfilePhoto[]>(seed);
  /** The bench as a render draws it. */
  const [photos, setPhotos] = useState<readonly ProfilePhoto[]>(seed);
  /** The ids the profile is known to hold: the seed's, then each answer's. */
  const landed = useRef<readonly string[]>(photoIds(standingPhotos(seed)));
  const inFlight = useRef(false);
  /** Whether the last write was refused — mirrored here because `send` runs between renders. */
  const refused = useRef(false);

  const send = useCallback(() => {
    if (inFlight.current) return;
    const now = standingPhotos(held.current);
    if (samePhotoIds(photoIds(now), landed.current)) {
      // Back where the profile already is — a refusal about a list nobody holds any more
      // has nothing left to say.
      if (refused.current) {
        refused.current = false;
        reset();
      }
      return;
    }

    inFlight.current = true;
    // `mutateAsync` rather than `mutate` with callbacks: those fire only while this is
    // mounted, and an upload that lands after the player has left still has to be written.
    mutateAsync(now).then(
      (answer) => {
        landed.current = photoIds(answer);
        inFlight.current = false;
        refused.current = false;
        // The row may have moved while this was out.
        send();
      },
      () => {
        inFlight.current = false;
        refused.current = true;
        // Nothing re-sends a list that was just refused: the screen says why off
        // `write.error`, and the next change — or `retryWrite` — sends the row as it then is.
      },
    );
  }, [mutateAsync, reset]);

  const current = useCallback(() => held.current, []);
  const changePhotos = useCallback(
    (change: (photos: readonly ProfilePhoto[]) => readonly ProfilePhoto[]) => {
      held.current = change(held.current);
      setPhotos(held.current);
      send();
    },
    [send],
  );

  const bench: PhotoBench = { photos, current, changePhotos };
  const workbench = useProfilePhotos(bench);

  return {
    ...workbench,
    /** The last write's failure, or nothing; the screen says it and offers `retry`. */
    writeError: write.error,
    writing: write.isPending,
    /** Send the row as it stands now — after a failure, the one control that resends it. */
    retryWrite: send,
  };
}
