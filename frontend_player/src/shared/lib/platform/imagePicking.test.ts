/**
 * The image-picking port, over a faked `expo-image-picker`.
 *
 * Same seam as the location port: the native module is stubbed and everything this app
 * owns runs — the permission reading, the ceiling handed to the picker, the shape a
 * picked image leaves in, and what cancelling means.
 */

import { deviceImagePicking } from './imagePicking';

const native = jest.requireMock('expo-image-picker') as {
  getMediaLibraryPermissionsAsync: jest.Mock;
  requestMediaLibraryPermissionsAsync: jest.Mock;
  launchImageLibraryAsync: jest.Mock;
};

// The defaults are restated rather than inherited from jest.setup.js. `clearAllMocks`
// forgets calls but keeps implementations, so a `mockResolvedValue` set by one case would
// otherwise still be in force in the next one — which is the kind of order-dependence that
// passes locally and fails on a machine that shards differently.
beforeEach(() => {
  jest.clearAllMocks();
  native.getMediaLibraryPermissionsAsync.mockResolvedValue({
    granted: false,
    canAskAgain: true,
    status: 'undetermined',
  });
  native.requestMediaLibraryPermissionsAsync.mockResolvedValue({
    granted: true,
    canAskAgain: false,
    status: 'granted',
  });
  native.launchImageLibraryAsync.mockResolvedValue({ canceled: true, assets: null });
});

describe('the photo-library permission', () => {
  it('reports the state without opening anything', async () => {
    await expect(deviceImagePicking.getPermission()).resolves.toBe('undetermined');
    expect(native.requestMediaLibraryPermissionsAsync).not.toHaveBeenCalled();
    expect(native.launchImageLibraryAsync).not.toHaveBeenCalled();
  });

  it('reports what the player answered when it does ask', async () => {
    await expect(deviceImagePicking.requestPermission()).resolves.toBe('granted');
  });

  /**
   * iOS lets a player hand over a chosen subset of their library instead of all of it.
   * That is a yes — the picker opens and shows exactly those pictures — so it must not
   * read as a refusal that sends the screen down the denied path.
   */
  it('treats a limited library selection as granted', async () => {
    native.getMediaLibraryPermissionsAsync.mockResolvedValue({
      granted: true,
      canAskAgain: false,
      status: 'granted',
      accessPrivileges: 'limited',
    });
    await expect(deviceImagePicking.getPermission()).resolves.toBe('granted');
  });
});

describe('picking images', () => {
  const asset = {
    uri: 'file:///photos/one.jpg',
    width: 1200,
    height: 1600,
    mimeType: 'image/jpeg',
    fileName: 'one.jpg',
  };

  it('produces a shape this app owns rather than the picker asset', async () => {
    native.launchImageLibraryAsync.mockResolvedValue({ canceled: false, assets: [asset] });

    await expect(deviceImagePicking.pickImages({ limit: 3 })).resolves.toEqual([
      {
        uri: 'file:///photos/one.jpg',
        width: 1200,
        height: 1600,
        mimeType: 'image/jpeg',
        fileName: 'one.jpg',
      },
    ]);
  });

  it('carries the fields the picker leaves out through as null', async () => {
    native.launchImageLibraryAsync.mockResolvedValue({
      canceled: false,
      assets: [{ uri: 'file:///photos/two.heic', width: 10, height: 10 }],
    });

    await expect(deviceImagePicking.pickImages({ limit: 3 })).resolves.toEqual([
      { uri: 'file:///photos/two.heic', width: 10, height: 10, mimeType: null, fileName: null },
    ]);
  });

  /**
   * The ceiling is the caller's — the port does not know that a profile holds three
   * photos — so it is passed to the picker rather than applied after the fact. A picker
   * that enforces it is a player who is told before they choose; a slice afterwards is a
   * player whose choices are silently dropped.
   */
  it('hands the ceiling it was given to the picker', async () => {
    await deviceImagePicking.pickImages({ limit: 3 });

    const options = native.launchImageLibraryAsync.mock.calls[0]?.[0] as {
      selectionLimit: number;
      allowsMultipleSelection: boolean;
    };
    expect(options.selectionLimit).toBe(3);
    expect(options.allowsMultipleSelection).toBe(true);
  });

  /**
   * Never read the EXIF block. The player was told their photo shows them on a court, not
   * where they were standing when it was taken — so the coordinates are not carried into
   * this process at all, rather than carried in and stripped later.
   */
  it('asks the picker for no EXIF and for images only', async () => {
    await deviceImagePicking.pickImages({ limit: 3 });

    const options = native.launchImageLibraryAsync.mock.calls[0]?.[0] as {
      exif: boolean;
      mediaTypes: readonly string[];
    };
    expect(options.exif).toBe(false);
    expect(options.mediaTypes).toEqual(['images']);
  });

  it('produces nothing when the player backs out of the picker', async () => {
    await expect(deviceImagePicking.pickImages({ limit: 3 })).resolves.toEqual([]);
  });
});

/**
 * The port promises never to reject, and the fake in `src/test-support/platform.ts`
 * cannot. If the real one could, every screen tested against that fake would pass on the
 * refusal path and crash on a phone — so the promise is asserted rather than described.
 */
describe('when the picker cannot open at all', () => {
  it('answers with nothing chosen rather than throwing', async () => {
    native.launchImageLibraryAsync.mockRejectedValue(
      new Error('Different image picker is already in progress'),
    );

    await expect(deviceImagePicking.pickImages({ limit: 3 })).resolves.toEqual([]);
  });
});
