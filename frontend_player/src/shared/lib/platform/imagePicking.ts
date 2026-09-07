/**
 * The photo library, behind a port. **The only module that imports `expo-image-picker`.**
 *
 * The argument is the location port's, unchanged: a native module has no JS
 * implementation to fall back on, so a screen that imports one cannot be exercised by a
 * test, and a capability reached through exactly one file is a capability whose behaviour
 * can be read in one sitting. The linter enforces the boundary.
 *
 * It is a *second* port rather than a device module holding both, because a capability is
 * one directory and one file, and "device" is the utils bucket this app bans — the two
 * have nothing in common but the word native.
 *
 * **The crop frame is the platform's own and there is no other.** Cropping an image that is
 * already on the phone needs pixel work, which needs a second native module — so what this
 * port offers is the frame the OS puts between choosing a picture and handing it over, and
 * nothing here can re-crop a file it has already answered with. A caller that wants a photo
 * cropped differently opens the picker again. That is a real limit and it is stated here
 * rather than discovered at the call site.
 */

import * as ImagePicker from 'expo-image-picker';

import { permissionStateOf, type PermissionState } from './permission';

/** One picture the player chose, as this app names it. */
export interface PickedImage {
  /** A local `file://` URI. Valid for this process; not a durable identifier. */
  readonly uri: string;
  readonly width: number;
  readonly height: number;
  /** `null` where the platform did not say — never guessed from the extension. */
  readonly mimeType: string | null;
  readonly fileName: string | null;
}

export interface PickImagesOptions {
  /**
   * How many the player may choose. The port has no opinion on the number — how many
   * pictures a profile holds is the profile's rule — so it is passed in and handed to the
   * picker, which enforces it while the player is still choosing.
   */
  readonly limit: number;
  /**
   * Put the platform's own crop frame between the choice and the answer, locked to this
   * `[width, height]` ratio.
   *
   * The port has no opinion on the shape either — what a profile photo is cropped to is the
   * profile's rule — so it is passed in, exactly as the limit is.
   *
   * **Two platform facts ride on this and neither is negotiable from here.** A cropping pick
   * is **single-select** on both platforms, so it answers with at most one picture whatever
   * `limit` says: the OS crop UI is attached to one choice, and asking for both is asking the
   * picker to ignore one of them. And **iOS ignores the ratio**, offering its own square
   * frame; only Android honours it. That is why the option is a ratio rather than a boolean —
   * the caller can state the shape it wants without this file pretending both platforms
   * deliver it — and why nothing downstream may assume a picked image has the shape asked
   * for.
   */
  readonly cropTo?: readonly [number, number];
}

/**
 * What the app may ask the device about the player's pictures.
 *
 * Screens depend on this interface; `deviceImagePicking` is the one implementation that
 * talks to the OS, and a test substitutes `fakeImagePicking()` from
 * `src/test-support/platform.ts`.
 */
export interface ImagePickingPort {
  /** The current permission, without opening anything. */
  readonly getPermission: () => Promise<PermissionState>;
  /**
   * Ask the player. On iOS this is where they may hand over a chosen subset of their
   * library rather than all of it — which is a `granted`, because the picker opens.
   */
  readonly requestPermission: () => Promise<PermissionState>;
  /**
   * Open the picker and resolve with what was chosen.
   *
   * Empty when nothing was — the player backed out, the library could not be opened, or
   * another picker was already up. **Backing out of the crop frame is backing out**, which
   * is the same answer and needs no second one. Cancelling is an ordinary answer rather than a
   * failure, and the two arrive as one answer for the reason `readFix` gives: what a
   * screen does next is identical, so making every caller catch a native error class buys
   * nothing and is forgotten once.
   *
   * **At most one picture comes back from a cropping pick.** See `PickImagesOptions.cropTo`.
   *
   * Never rejects. That is a promise the fake in `src/test-support/platform.ts` keeps
   * too — a fake that cannot throw, standing in for a port that can, is how a refusal
   * path passes green here and crashes on a phone.
   */
  readonly pickImages: (options: PickImagesOptions) => Promise<readonly PickedImage[]>;
}

export const deviceImagePicking: ImagePickingPort = {
  async getPermission() {
    return permissionStateOf(await ImagePicker.getMediaLibraryPermissionsAsync());
  },

  async requestPermission() {
    return permissionStateOf(await ImagePicker.requestMediaLibraryPermissionsAsync());
  },

  async pickImages({ limit, cropTo }) {
    let result;
    try {
      result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        // The player was told a profile photo shows them on a court, not where they were
        // standing when it was taken. The coordinates are never read into this process, so
        // there is nothing to strip later and nothing to leak in between.
        exif: false,
        // Cropping and multi-select are mutually exclusive on both platforms: `allowsEditing`
        // is ignored the moment `allowsMultipleSelection` is set, so a call asking for both
        // would silently be a call asking for neither. The two shapes are written out rather
        // than merged for that reason — the branch is a platform constraint, not a
        // preference.
        ...(cropTo === undefined
          ? { allowsMultipleSelection: true, selectionLimit: limit }
          : { allowsEditing: true, aspect: [cropTo[0], cropTo[1]] as [number, number] }),
      });
    } catch {
      // A refused library, a picker already on screen, a platform that would not open
      // one: nothing was chosen, which is the same answer as backing out.
      return [];
    }

    if (result.canceled) return [];

    return result.assets.map((asset) => ({
      uri: asset.uri,
      width: asset.width,
      height: asset.height,
      mimeType: asset.mimeType ?? null,
      fileName: asset.fileName ?? null,
    }));
  },
};
