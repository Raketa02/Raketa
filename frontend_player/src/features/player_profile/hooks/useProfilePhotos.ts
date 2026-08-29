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
  recordUpload,
  removePhoto,
  promoteToProfile,
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

    const permission = await ensurePermission(picking);
    const picked = await picking.pickImages({ limit: room });

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
  }, [changePhotos, enqueue, picking]);

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

  return { photos, standing, add, retry, promote, remove };
}
