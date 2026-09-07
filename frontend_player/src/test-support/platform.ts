/**
 * Hand-written fakes for the two platform ports.
 *
 * Beside `transport.ts` and for the same reason: a test states what the world outside the
 * app does, and everything inside it runs for real. The socket is one such edge; the OS
 * permission dialog and the photo picker are two more, and neither can be driven from a
 * test at all — a native module has no JS implementation underneath it.
 *
 * These are **fakes, not mocks**: they behave like the thing they replace rather than
 * recording that they were called. A test sets what the player will answer and what the
 * device holds, then exercises the screen. That is what makes them worth having — a stub
 * that returns `'granted'` unconditionally proves a screen works only for players who say
 * yes, which is the case that was never in doubt.
 *
 * The device behaviour they model, and which is easy to get wrong by hand:
 *
 * - **A blocked permission cannot be asked for again.** The OS answers instantly and
 *   negatively without showing anything, so `requestPermission()` ignores the answer the
 *   test set. A screen that loops on "ask again" against a blocked permission loops
 *   forever, and this is where that gets caught.
 * - **A refused location produces no fix.** `getCurrentPositionAsync` genuinely fails
 *   without permission, so the real port answers `null` and this one does too.
 * - **A cropping pick answers with one picture.** The OS crop frame is attached to a single
 *   choice, so `allowsEditing` and multi-select cannot both be honoured — a fake that handed
 *   back three from a cropping pick would prove a step works against a picker that does not
 *   exist. See `FakeImagePicking.library`.
 * - **Picking is not gated on the permission**, and deliberately so — the real port does
 *   not consult one either. On iOS the system picker opens without any grant at all, and
 *   a fake that refused would prove a screen handles a refusal the phone never makes. A
 *   test that wants an empty pick says so with `library: []`.
 * - **Neither port ever rejects**, because neither real one does.
 *
 * Not app code — nothing under `src/` outside tests imports this, so Metro never bundles
 * it.
 */

import type {
  ImagePickingPort,
  LocationFix,
  LocationPort,
  PermissionState,
  PickedImage,
} from '@/shared/lib/platform';

/** The bits every port fake shares: what the state is, and what asking would make it. */
interface FakePermission {
  /** The current permission. Assign to start a test somewhere other than unasked. */
  state: PermissionState;
  /**
   * What the player answers the next time they are asked. Ignored while `state` is
   * `'blocked'`, exactly as the OS ignores it.
   */
  answer: PermissionState;
}

export interface FakeLocation extends LocationPort, FakePermission {
  /**
   * What the device would report. `null` is a device that cannot see the sky — a fix is
   * also withheld whenever the permission is not `'granted'`.
   */
  fix: LocationFix | null;
  /** How many times a fix was asked for, so a test can prove it was asked once. */
  readonly reads: number;
}

export interface FakeImagePicking extends ImagePickingPort, FakePermission {
  /**
   * What the player would choose, in the order they would choose it.
   *
   * A plain pick truncates it to the caller's limit, as a picker does. **A cropping pick
   * answers with one** — the next one not yet handed over — because the real port's crop
   * frame is attached to a single choice, so successive presses walk this list the way a
   * player pressing *Add a photo* three times walks their own library. Assigning to it
   * starts the walk again, which is how a test says *and then they chose that one instead*.
   *
   * Handed over whatever the permission says — see the note above.
   */
  library: readonly PickedImage[];
  /**
   * Whether the picker respects the limit it was opened with. True by default.
   *
   * A caller may **not** assume it does. The limit is handed to a native module and
   * honoured on the far side of a boundary this app does not own, and design-system 6.9
   * requires the step to refuse a surplus in words precisely because the row of three
   * cannot say anything about one on its own. Set this false to be the picker that hands
   * back more than it was asked for, and prove the step survives it.
   *
   * It covers the single-answer rule too: a picker that ignores its limit is a picker that
   * ignores the crop frame's, so `false` hands back the whole list from a cropping pick as
   * well. Both are one boundary this app does not own, and a test that wants a surplus wants
   * it whichever call produced it.
   */
  honoursLimit: boolean;
  /** Every limit the picker was opened with, in order. */
  readonly limits: readonly number[];
  /**
   * The crop ratio each pick asked for, in order — `undefined` where it asked for none.
   *
   * Recorded because *the player is offered a crop frame* is a claim about the step that is
   * otherwise invisible: the pictures come back looking the same either way, so nothing a
   * screen renders could prove the frame was ever opened.
   */
  readonly crops: readonly (readonly [number, number] | undefined)[];
}

/** A permission answer, with the one rule the OS applies itself. */
function settle(fake: FakePermission): PermissionState {
  // A permanently refused permission is not re-asked: the OS resolves it without showing
  // anything, and the state cannot change from inside the app.
  if (fake.state !== 'blocked') fake.state = fake.answer;
  return fake.state;
}

/**
 * A device whose position a test decides.
 *
 * Defaults to the ordinary path — never asked, says yes, knows where it is — so a test
 * that cares about one refusal states only that refusal.
 */
export function fakeLocation(
  initial: Partial<Pick<FakeLocation, 'state' | 'answer' | 'fix'>> = {},
): FakeLocation {
  let reads = 0;

  const fake: FakeLocation = {
    state: initial.state ?? 'undetermined',
    answer: initial.answer ?? 'granted',
    fix:
      initial.fix === undefined
        ? { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 }
        : initial.fix,

    get reads() {
      return reads;
    },

    getPermission: async () => fake.state,
    requestPermission: async () => settle(fake),

    readFix: async () => {
      reads += 1;
      return fake.state === 'granted' ? fake.fix : null;
    },
  };

  return fake;
}

/**
 * A photo library a test decides the contents of.
 *
 * Defaults to a player who has not been asked, would say yes, and has no pictures —
 * because "the player picked nothing" is the case a photos screen must survive, and a
 * default that handed one over would hide it.
 */
export function fakeImagePicking(
  initial: Partial<Pick<FakeImagePicking, 'state' | 'answer' | 'library' | 'honoursLimit'>> = {},
): FakeImagePicking {
  const limits: number[] = [];
  const crops: (readonly [number, number] | undefined)[] = [];

  let held: readonly PickedImage[] = initial.library ?? [];
  /** How far a run of cropping picks has walked `held`. Reset whenever it is reassigned. */
  let taken = 0;

  const fake: FakeImagePicking = {
    state: initial.state ?? 'undetermined',
    answer: initial.answer ?? 'granted',
    honoursLimit: initial.honoursLimit ?? true,

    get library() {
      return held;
    },
    set library(pictures: readonly PickedImage[]) {
      held = pictures;
      taken = 0;
    },

    get limits() {
      return limits;
    },
    get crops() {
      return crops;
    },

    getPermission: async () => fake.state,
    requestPermission: async () => settle(fake),

    pickImages: async ({ limit, cropTo }) => {
      limits.push(limit);
      crops.push(cropTo);

      // A picker that does not honour its limit does not honour the crop frame's either:
      // one boundary, one way of being wrong about it.
      if (!fake.honoursLimit) return held;

      // A cropping pick is single-select on both platforms, so it answers with the one
      // picture this run of presses has got to and nothing after it.
      if (cropTo !== undefined) {
        const next = held[taken];
        if (next === undefined) return [];
        taken += 1;
        return [next];
      }

      return held.slice(0, limit);
    },
  };

  return fake;
}

/** One picked image, for a test that needs a picture and does not care which. */
export function pickedImage(overrides: Partial<PickedImage> = {}): PickedImage {
  return {
    uri: 'file:///photos/one.jpg',
    width: 1200,
    height: 1600,
    mimeType: 'image/jpeg',
    fileName: 'one.jpg',
    ...overrides,
  };
}
