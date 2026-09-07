/**
 * The photos step's one piece of orchestration: pick, upload, and keep the workbench honest.
 *
 * **Nothing here decides anything.** The ceiling, the order, what promotion means and which
 * ids the draft ends up with are `photoCollection`'s, with their own tests and no renderer;
 * sending one photo is `uploadProfilePhoto`'s. What is left is the sequencing a screen
 * cannot express and a pure function must not: asking the OS, opening the picker, and
 * running the uploads.
 *
 * ## One photo at a time, in one queue
 *
 * Every upload is appended to a single promise chain, so a player who picks three sends
 * three requests one after another and a retry never runs beside one already in flight.
 * That is what makes *one failure costs one photo* true: three parallel uploads on a
 * phone's uplink is how all three time out together.
 *
 * ## An upload outlives the screen
 *
 * No `AbortSignal` is passed. The draft is the part's, not the step's — a player who
 * presses continue while a photo is still going should arrive at step three and find it
 * arrived, rather than have it cancelled by unmounting the row it was drawn in. Nothing
 * leaks: the chain ends when the last upload does, and every result is written through the
 * store, which is cleared with the part.
 *
 * ## Every pick goes through the platform's crop frame
 *
 * Both acts open the picker with `PROFILE_PHOTO_ASPECT`, so what reaches the row is what the
 * player framed rather than whatever the camera happened to hold. The consequence is worth
 * knowing before reading `add`: **a cropping pick answers with one picture**, because the OS
 * crop UI is attached to a single choice (`ImagePickingPort`). So adding three photos is
 * three presses of the add control rather than one multi-select, and the ceiling is still the
 * ceiling — `addPhotos` still refuses a surplus, because the limit is honoured on the far
 * side of a boundary this app does not own.
 *
 * There is **no re-crop of a photo already held**: that needs pixel work and a second native
 * module, so *edit* is the picker opened again on the same slot. The step says so in the
 * words it puts on the control (`photoStepPresentation`).
 *
 * ## The picker is opened whatever the permission says
 *
 * The port does not consult one and neither does this — on iOS the system picker opens
 * with no grant at all, so refusing on the app's side would refuse a player the phone would
 * have let through. The permission is asked for first, just in time, and it is only read
 * **afterwards**, to explain an empty answer: nothing came back *and* we were not allowed
 * is the one case worth a sentence. Nothing came back and we were is a player who backed
 * out, which needs none.
 */

import { useCallback, useRef, useState } from 'react';

import { isAppError, unknownFailure, type AppError } from '@/shared/errors';
import { ensurePermission, useImagePicking, type PermissionState } from '@/shared/lib/platform';

import {
  addPhotos,
  PROFILE_PHOTO_ASPECT,
  recordUpload,
  removePhoto,
  promoteToProfile,
  replacePhoto,
  slotsLeft,
  type ProfilePhoto,
} from '../domain/photoCollection';
import { useProfileDraft } from '../store/profileDraft.store';
import { uploadProfilePhoto } from '../use-cases/uploadProfilePhoto';

/**
 * What the step may say about the photo library, which is less than the OS distinguishes.
 *
 * `undetermined` and `denied` are one case here — *ask again by pressing the control* —
 * because that is the only difference a sentence could carry, and there is none: both are
 * answered by the next press opening the prompt. `blocked` is the case that needs its own
 * words, because pressing again achieves nothing and only Settings will.
 */
export type PhotoAccess = 'granted' | 'refused' | 'blocked';

/** What the last press on the add control ran into, if anything. */
export interface PhotoStepStanding {
  /** The ceiling refused part of a pick. Cleared by the next press that changes anything. */
  readonly refusedAtTheCeiling: boolean;
  /** What the OS said about the photo library, once it has been asked. */
  readonly access: PhotoAccess;
}

const READY: PhotoStepStanding = { refusedAtTheCeiling: false, access: 'granted' };

function accessFrom(permission: PermissionState): PhotoAccess {
  if (permission === 'granted') return 'granted';
  return permission === 'blocked' ? 'blocked' : 'refused';
}

/** Whatever went wrong, as the one error family a screen is allowed to render. */
function asAppError(cause: unknown): AppError {
  return isAppError(cause) ? cause : unknownFailure('The photo could not be uploaded.', cause);
}

export function useProfilePhotos() {
  const picking = useImagePicking();
  const photos = useProfileDraft((state) => state.photos);
  const changePhotos = useProfileDraft((state) => state.changePhotos);
  const [standing, setStanding] = useState<PhotoStepStanding>(READY);

  /**
   * The queue, as one promise every upload is appended to.
   *
   * A ref rather than state: nothing renders from it, and re-rendering when an upload
   * starts would redraw the row for a fact the row does not show.
   */
  const queue = useRef<Promise<void>>(Promise.resolve());

  const send = useCallback(
    (photo: ProfilePhoto) => {
      // Removed while it waited its turn. Uploading it would put bytes in the store that
      // nothing will ever name, and write a result onto a tile that is gone.
      const held = useProfileDraft.getState().photos;
      if (!held.some((candidate) => candidate.uri === photo.uri)) return Promise.resolve();

      return uploadProfilePhoto({
        uri: photo.uri,
        mimeType: photo.mimeType,
        onProgress: (progress) =>
          changePhotos((current) =>
            recordUpload(current, photo.uri, { kind: 'uploading', progress }),
          ),
      }).then(
        // The verdict is written down with the id and nothing here reads it. Whether a
        // flagged photo is worth a sentence — and which one — is the step's, and the
        // queue that runs the uploads has no business holding an opinion about it.
        ({ photoId, review }) =>
          changePhotos((current) =>
            recordUpload(current, photo.uri, { kind: 'uploaded', photoId, review }),
          ),
        (cause: unknown) =>
          changePhotos((current) =>
            recordUpload(current, photo.uri, { kind: 'failed', error: asAppError(cause) }),
          ),
      );
    },
    [changePhotos],
  );

  const enqueue = useCallback(
    (queued: readonly ProfilePhoto[]) => {
      for (const photo of queued) {
        queue.current = queue.current.then(() => send(photo));
      }
    },
    [send],
  );

  /**
   * Open the picker with the crop frame, having asked for the library first.
   *
   * The one sequence both acts share, and the only thing either of them does to the device.
   * `limit` is still the room the collection has even though a cropping pick answers with at
   * most one: the number is what the picker is *opened with*, the port owns what a crop frame
   * does to it, and a caller lying about the room to match the platform's behaviour would be
   * the ceiling stated in two places that could disagree.
   */
  const pickOne = useCallback(
    async (limit: number) => {
      const permission = await ensurePermission(picking);
      const picked = await picking.pickImages({ limit, cropTo: PROFILE_PHOTO_ASPECT });

      return { permission, picked };
    },
    [picking],
  );

  const add = useCallback(async () => {
    setStanding(READY);

    const room = slotsLeft(useProfileDraft.getState().photos);
    // Not reachable through the row — at three there is no add control at all — but the
    // ceiling is a rule rather than a layout, and a rule that only holds where the layout
    // agrees with it is one waiting for a second caller.
    if (room === 0) {
      setStanding({ refusedAtTheCeiling: true, access: 'granted' });
      return;
    }

    const { permission, picked } = await pickOne(room);

    if (picked.length === 0) {
      setStanding({ refusedAtTheCeiling: false, access: accessFrom(permission) });
      return;
    }

    const held = useProfileDraft.getState().photos;
    const addition = addPhotos(
      held,
      picked.map((image) => ({ uri: image.uri, mimeType: image.mimeType })),
    );

    setStanding({ refusedAtTheCeiling: addition.refused > 0, access: 'granted' });
    changePhotos(() => addition.photos);
    enqueue(addition.photos.slice(held.length));
  }, [changePhotos, enqueue, pickOne]);

  /**
   * Swap one photo for another the player picks and crops now, **keeping its place**.
   *
   * It opens the picker for **one** slot rather than for the room the row has left, and that
   * is not the same number: a replacement takes a position that is already occupied, so a
   * collection at the ceiling can still take one. Which is also why nothing here consults
   * `slotsLeft` and why the ceiling refusal cannot fire — `replacePhoto` swaps in place and
   * the count does not move.
   *
   * The rule is `replacePhoto`'s, including its two ways of doing nothing, and the empty
   * answer is read exactly as the add control's is: nothing came back **and** we were not
   * allowed is the one case worth a sentence.
   */
  const replace = useCallback(
    async (uri: string) => {
      setStanding(READY);

      const { permission, picked } = await pickOne(1);
      const arrival = picked[0];

      if (arrival === undefined) {
        setStanding({ refusedAtTheCeiling: false, access: accessFrom(permission) });
        return;
      }

      const held = useProfileDraft.getState().photos;
      const replaced = replacePhoto(held, uri, {
        uri: arrival.uri,
        mimeType: arrival.mimeType,
      });
      // The picture is already held, or the one it would have replaced is gone. Either way
      // nothing changed, so nothing is sent.
      if (replaced === held) return;

      changePhotos(() => replaced);
      enqueue(replaced.filter((photo) => !held.some((was) => was.uri === photo.uri)));
    },
    [changePhotos, enqueue, pickOne],
  );

  const retry = useCallback(
    (uri: string) => {
      setStanding(READY);
      const photo = useProfileDraft.getState().photos.find((held) => held.uri === uri);
      if (photo === undefined || photo.upload.kind !== 'failed') return;

      changePhotos((current) => recordUpload(current, uri, { kind: 'uploading', progress: 0 }));
      enqueue([photo]);
    },
    [changePhotos, enqueue],
  );

  const promote = useCallback(
    (uri: string) => {
      setStanding(READY);
      changePhotos((current) => promoteToProfile(current, uri));
    },
    [changePhotos],
  );

  const remove = useCallback(
    (uri: string) => {
      // The ceiling refusal goes with it: removing one is exactly what the refusal asked
      // for, and a message still on screen after it was acted on is a message that lies.
      setStanding(READY);
      changePhotos((current) => removePhoto(current, uri));
    },
    [changePhotos],
  );

  return { photos, standing, add, replace, retry, promote, remove };
}
