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
   * another picker was already up. Cancelling is an ordinary answer rather than a
   * failure, and the two arrive as one answer for the reason `readFix` gives: what a
   * screen does next is identical, so making every caller catch a native error class buys
   * nothing and is forgotten once.
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

  async pickImages({ limit }) {
    let result;
    try {
      result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsMultipleSelection: true,
        selectionLimit: limit,
        // The player was told a profile photo shows them on a court, not where they were
        // standing when it was taken. The coordinates are never read into this process, so
        // there is nothing to strip later and nothing to leak in between.
        exif: false,
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
