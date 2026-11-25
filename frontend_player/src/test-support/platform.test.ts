/**
 * The fakes, tested — because a fake that lies is worse than no fake at all.
 *
 * A screen tested against a fake that always grants, or that hands back a picture the
 * player never chose, passes while the app is broken in exactly the cases the fake exists
 * to reach. So the two rules these fakes model on the OS's behalf are asserted here, once,
 * rather than re-discovered by whichever feature trips over them first.
 */

import { fakeImagePicking, fakeKeyboard, fakeLocation, pickedImage } from './platform';

describe('the location fake', () => {
  it('starts unasked and grants when asked', async () => {
    const location = fakeLocation();

    await expect(location.getPermission()).resolves.toBe('undetermined');
    await expect(location.requestPermission()).resolves.toBe('granted');
    await expect(location.getPermission()).resolves.toBe('granted');
  });

  it('reports the refusal a test set', async () => {
    const location = fakeLocation({ answer: 'denied' });

    await expect(location.requestPermission()).resolves.toBe('denied');
  });

  /**
   * The rule the fake exists to enforce. A blocked permission is settled outside the app:
   * asking again resolves instantly and negatively, so a screen looping on "ask again"
   * loops forever. A fake that let `answer` win would never show that.
   */
  it('stays blocked however the test says the player would answer', async () => {
    const location = fakeLocation({ state: 'blocked', answer: 'granted' });

    await expect(location.requestPermission()).resolves.toBe('blocked');
    await expect(location.getPermission()).resolves.toBe('blocked');
  });

  it('produces the fix it was given, and counts the reads', async () => {
    const location = fakeLocation({ state: 'granted' });

    await expect(location.readFix()).resolves.toEqual({
      latitude: 41.3874,
      longitude: 2.1686,
      accuracyMetres: 12,
    });
    expect(location.reads).toBe(1);
  });

  it('withholds a fix while the permission is not granted', async () => {
    const location = fakeLocation({ state: 'denied' });

    await expect(location.readFix()).resolves.toBeNull();
  });

  it('models a device that cannot find itself', async () => {
    const location = fakeLocation({ state: 'granted', fix: null });

    await expect(location.readFix()).resolves.toBeNull();
  });
});

describe('the image-picking fake', () => {
  it('starts unasked and grants when asked', async () => {
    const picking = fakeImagePicking();

    await expect(picking.getPermission()).resolves.toBe('undetermined');
    await expect(picking.requestPermission()).resolves.toBe('granted');
  });

  it('stays blocked however the test says the player would answer', async () => {
    const picking = fakeImagePicking({ state: 'blocked', answer: 'granted' });

    await expect(picking.requestPermission()).resolves.toBe('blocked');
  });

  /**
   * A player who opens the picker and chooses nothing is the ordinary case a photos
   * screen must survive, so it is what an unconfigured fake does.
   */
  it('produces nothing by default', async () => {
    const picking = fakeImagePicking({ state: 'granted' });

    await expect(picking.pickImages({ limit: 3 })).resolves.toEqual([]);
  });

  it('truncates to the limit the caller opened the picker with, the way a picker does', async () => {
    const picking = fakeImagePicking({
      state: 'granted',
      library: [
        pickedImage({ uri: 'file:///one.jpg' }),
        pickedImage({ uri: 'file:///two.jpg' }),
        pickedImage({ uri: 'file:///three.jpg' }),
      ],
    });

    const picked = await picking.pickImages({ limit: 2 });

    expect(picked.map((image) => image.uri)).toEqual(['file:///one.jpg', 'file:///two.jpg']);
    expect(picking.limits).toEqual([2]);
  });

  /**
   * The real port does not consult the permission before opening the picker, and on iOS
   * the system picker opens without any grant at all. A fake that refused here would
   * prove a screen handles a refusal the phone never makes — so a test that wants an
   * empty pick says so by emptying the library.
   */
  it('hands the library over without consulting the permission, as the port does', async () => {
    const picking = fakeImagePicking({ state: 'denied', library: [pickedImage()] });

    await expect(picking.pickImages({ limit: 3 })).resolves.toHaveLength(1);
  });
});

describe('the keyboard fake', () => {
  it('starts down, and tells a follower as it comes up and goes down', () => {
    const keyboard = fakeKeyboard();
    const told: boolean[] = [];
    keyboard.follow(() => told.push(keyboard.isUp()));

    expect(keyboard.isUp()).toBe(false);
    keyboard.raise();
    keyboard.drop();

    expect(told).toEqual([true, false]);
  });

  /** As the device's: a keyboard already up does not come up again. */
  it('tells nobody when nothing changed, and nobody who stopped following', () => {
    const keyboard = fakeKeyboard();
    const told: boolean[] = [];
    const stop = keyboard.follow(() => told.push(keyboard.isUp()));

    keyboard.drop();
    keyboard.raise();
    keyboard.raise();
    stop();
    keyboard.drop();

    expect(told).toEqual([true]);
    expect(keyboard.isUp()).toBe(false);
  });
});
