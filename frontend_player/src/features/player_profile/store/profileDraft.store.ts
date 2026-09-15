/**
 * The profile draft, while the player is inside onboarding's second part.
 *
 * In memory, never persisted, and **never sent anywhere until the commit** — which is what
 * makes it the part's checkpoint rather than a cache of one
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). Killing
 * the app takes the draft with it, and the next launch starts the part again at step one
 * with nothing in it. That is the accepted cost of not building a server-owned draft, and
 * it is bounded by eight short steps.
 *
 * **The rules live in `domain/ProfileDraft`**, so they are testable without a store and
 * without a renderer. This holds values and nothing else — the same split the onboarding
 * pass uses.
 *
 * ## Two values, one lifetime, and one of them is derived
 *
 * The draft is the answers. Beside it is the photos step's **workbench**: the pictures
 * the player picked, each with the upload it is in the middle of. Those are not an answer —
 * a local `file://` URI is worthless to the server and an upload in flight has nothing to
 * commit — but they have to outlive the screen, because walking to step four and back must
 * find the same three tiles rather than an empty row.
 *
 * They live in **one** store because they share one lifetime and one invariant: the draft's
 * `photoIds` are *derived* from the workbench, by `changePhotos` and nowhere else. Two
 * stores would mean two things to reset and a sync that can be forgotten, and forgetting it
 * would commit a photo the player deleted or lose one they added.
 *
 * ## Absent is a state, and it is the load-bearing one
 *
 * `draft` is `undefined` when the player is not in the part, exactly as `pass` is undefined
 * between walks. That absence is what a step other than the first checks: a link naming
 * `/radius` with no part running is not a shortcut into the middle of a flow, it is a
 * player about to commit a profile built from six screens they never saw. Turning them
 * away needs a way to tell *not in the part* from *in the part, having answered nothing* —
 * and an empty draft cannot tell those apart, which is why entering is explicit.
 *
 * ## The commit key is the part's, and that is what makes it work
 *
 * Beside the draft is the key the commit will be sent under. It is minted when the part is
 * entered and lives exactly as long as the draft, which is the property the whole defence
 * rests on: a double tap and a retry after a failure both send the key the *first* attempt
 * sent, so the server serves one profile whatever the finger and the connection do. Minting
 * one per press would be eight presses and eight profiles waiting to happen; a disabled button
 * is only the courtesy.
 *
 * It goes with the draft when the part ends, for the same reason the workbench does: a new
 * part is a new commit, and a key held over from the last one would ask the server to
 * replay a profile built from answers nobody gave this time.
 *
 * Nothing from the backend enters this store. The served tag vocabulary and radius bounds
 * are TanStack Query's; what is here is only what the player has said.
 */

import { create } from 'zustand';

import { emptyDraft, recordAnswer, type ProfileDraft } from '../domain/ProfileDraft';
import { uploadedPhotoIds, type ProfilePhoto } from '../domain/photoCollection';

/**
 * A name for one commit, in the alphabet the route accepts (1–128 characters).
 *
 * `Math.random` is right here and would be wrong for a credential — the same call the
 * correlation id in `shared/lib/http` makes, for the same reason. This is an opaque handle
 * a player's own commit is filed under, not a secret and not a guess anybody benefits from
 * making: idempotency is answered from that player's own profile stream, so the key has to
 * be stable across attempts and unique across parts, and nothing more.
 */
function newCommitKey(): string {
  const random = () => Math.random().toString(36).slice(2, 12);
  return `profile-commit-${random()}${random()}`;
}

interface ProfileDraftState {
  /** Undefined outside the part. See above — absence is the state that makes this work. */
  readonly draft: ProfileDraft | undefined;
  /**
   * The photos the player picked, in their order, each with its own upload.
   *
   * Empty outside the part as well as inside it before anything is picked, and that is
   * fine: unlike the draft, nothing has to tell those two apart — `draft` already does.
   */
  readonly photos: readonly ProfilePhoto[];
  /**
   * What the commit at the end of the part will be sent under. Undefined outside the part,
   * exactly as the draft is — see above for why one press must not mint its own.
   */
  readonly commitKey: string | undefined;
  /**
   * Enter the part, **only if it is not already running**.
   *
   * Called by the first step, which is the only door in: the entry gate redirects there
   * and every other step turns a stranger away to it. Conditional because walking *back*
   * to step one is an ordinary move, and beginning again there would wipe the answers
   * the player walked back past.
   */
  readonly enterIfAbsent: () => void;
  /** Record what one step answered. A no-op outside the part — there is nothing to write to. */
  readonly answer: (answer: Partial<ProfileDraft>) => void;
  /**
   * Change the workbench, and write the ids it now yields into the draft.
   *
   * A **function** of the current photos rather than a new list, because three uploads
   * finish whenever they finish: two callbacks that each read the photos, changed one and
   * wrote the whole list back would have the later one erase the earlier one's photo.
   *
   * The draft is updated in the same set, from `uploadedPhotoIds`, so there is no moment
   * when the two disagree and no caller that can forget to do it.
   */
  readonly changePhotos: (
    change: (photos: readonly ProfilePhoto[]) => readonly ProfilePhoto[],
  ) => void;
  /**
   * Back to no part running.
   *
   * Two endings reach this. **The commit** calls it once the server has the answers, so
   * nothing is left holding a draft the part has finished with — and so that a key which
   * has already produced a profile cannot be sent again under a different set of answers.
   * The other is process death, which clears an in-memory store without anybody asking it
   * to; the suites that need a clean one use this to stand in for it.
   */
  readonly reset: () => void;
}

export const useProfileDraft = create<ProfileDraftState>((set, get) => ({
  draft: undefined,
  photos: [],
  commitKey: undefined,
  enterIfAbsent: () => {
    if (get().draft !== undefined) return;
    // The workbench and the key are cleared with the draft, never separately: a new part
    // that inherited the last one's tiles would show a player photographs they did not pick
    // this time, and one that inherited its key would ask the server to replay it.
    set({ draft: emptyDraft(), photos: [], commitKey: newCommitKey() });
  },
  // Dropped rather than starting a part, for the reason the pass drops a rating recorded
  // with no pass running: every screen that can answer was reached through the one that
  // enters, so this guards against a future caller rather than a case the flow produces.
  answer: (answer) =>
    set((state) =>
      state.draft === undefined ? state : { draft: recordAnswer(state.draft, answer) },
    ),
  changePhotos: (change) =>
    set((state) => {
      if (state.draft === undefined) return state;
      const photos = change(state.photos);
      return { photos, draft: recordAnswer(state.draft, { photoIds: uploadedPhotoIds(photos) }) };
    }),
  reset: () => set({ draft: undefined, photos: [], commitKey: undefined }),
}));
