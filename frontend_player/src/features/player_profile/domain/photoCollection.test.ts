/**
 * The photo rules, with no renderer, no store and no socket — which is the point of their
 * living in a function of a list rather than inside the step that draws three tiles.
 */

import { AppError } from '@/shared/errors';
import { theme } from '@/shared/ui';

import {
  ASSUMED_MEDIA_TYPE,
  PHOTO_CEILING,
  PROFILE_PHOTO_ASPECT,
  addPhotos,
  mediaTypeOf,
  promoteToProfile,
  flaggedPositions,
  heldPhotos,
  photoIds,
  recordUpload,
  removePhoto,
  replacePhoto,
  samePhotoIds,
  slotsLeft,
  standingPhotos,
  uploadedPhotoIds,
  uploadedPhotos,
  type ProfilePhoto,
} from './photoCollection';

/** A photo that has arrived, so a list of them reads as a settled collection. */
function uploaded(name: string): ProfilePhoto {
  return {
    uri: `file:///photos/${name}.jpg`,
    mimeType: 'image/jpeg',
    upload: { kind: 'uploaded', photoId: `id-${name}`, review: 'allowed' },
  };
}

function arrival(name: string, mimeType: string | null = 'image/jpeg') {
  return { uri: `file:///photos/${name}.jpg`, mimeType };
}

/** The same shape as `uploaded`, with the verdict the check came back with. */
function flagged(name: string): ProfilePhoto {
  return {
    uri: `file:///photos/${name}.jpg`,
    mimeType: 'image/jpeg',
    upload: { kind: 'uploaded', photoId: `id-${name}`, review: 'flagged' },
  };
}

const failure = new AppError('unknown', 'retryable-by-user', 'nope');

describe('the ceiling', () => {
  it('is three, which is what the row of tiles is three of', () => {
    expect(PHOTO_CEILING).toBe(3);
  });

  it('counts down as photos are added, and never below zero', () => {
    expect(slotsLeft([])).toBe(3);
    expect(slotsLeft([uploaded('one'), uploaded('two')])).toBe(1);
    expect(slotsLeft([uploaded('one'), uploaded('two'), uploaded('three')])).toBe(0);
  });

  it('takes what fits and refuses the rest, counting the refusal', () => {
    // A picker can hand back more than the row has room for, and the layout cannot say so.
    const addition = addPhotos(
      [uploaded('one')],
      [arrival('two'), arrival('three'), arrival('four')],
    );

    expect(addition.photos).toHaveLength(3);
    expect(addition.refused).toBe(1);
  });

  it('changes nothing at all when there is no room, and says how many it turned away', () => {
    const full = [uploaded('one'), uploaded('two'), uploaded('three')];

    const addition = addPhotos(full, [arrival('four')]);

    expect(addition.photos).toEqual(full);
    expect(addition.refused).toBe(1);
  });
});

describe('adding what the picker handed back', () => {
  it('appends in the order they were picked, uploading and at nothing', () => {
    const addition = addPhotos([], [arrival('one'), arrival('two')]);

    expect(addition.photos.map((photo) => photo.uri)).toEqual([
      'file:///photos/one.jpg',
      'file:///photos/two.jpg',
    ]);
    expect(addition.photos.map((photo) => photo.upload)).toEqual([
      { kind: 'uploading', progress: 0 },
      { kind: 'uploading', progress: 0 },
    ]);
    expect(addition.refused).toBe(0);
  });

  it('keeps what the platform said the bytes are, including having said nothing', () => {
    const addition = addPhotos([], [arrival('one', null)]);

    expect(addition.photos[0]?.mimeType).toBeNull();
  });

  it('drops a picture already held rather than showing it twice', () => {
    const addition = addPhotos([uploaded('one')], [arrival('one'), arrival('two')]);

    expect(addition.photos.map((photo) => photo.uri)).toEqual([
      'file:///photos/one.jpg',
      'file:///photos/two.jpg',
    ]);
    // Not a refusal: the ceiling had room, and nothing the player asked for is missing.
    expect(addition.refused).toBe(0);
  });
});

describe('the shape a photo is cropped to', () => {
  /**
   * The whole reason the constant exists rather than being written at the picker: the crop
   * frame and the tile have to be the same rectangle, or a player frames a photograph and
   * the row crops it again on the way in.
   */
  it('is the shape of the tile it will be drawn in', () => {
    const [width, height] = PROFILE_PHOTO_ASPECT;

    expect(width / height).toBe(theme.size.photoTile.aspectRatio);
  });

  /** Whole numbers, because that is what a native crop frame takes. */
  it('is a pair of whole numbers', () => {
    for (const side of PROFILE_PHOTO_ASPECT) {
      expect(Number.isInteger(side)).toBe(true);
      expect(side).toBeGreaterThan(0);
    }
  });
});

describe('swapping one photo for another', () => {
  /**
   * The whole point of `replacePhoto` being a rule rather than a remove and an add: the
   * player put that picture in that slot, and swapping which photograph it is does not
   * un-put it. Remove-then-add would send a replaced profile photo to the back of a queue
   * it was at the front of.
   */
  it('keeps the position the replaced photo held', () => {
    const held = [uploaded('one'), uploaded('two'), uploaded('three')];

    const after = replacePhoto(held, held[1]!.uri, arrival('new'));

    expect(after.map((photo) => photo.uri)).toEqual([
      held[0]!.uri,
      'file:///photos/new.jpg',
      held[2]!.uri,
    ]);
    // Replacing the one that leads leaves the replacement leading, which is the same
    // sentence read from position one.
    expect(replacePhoto(held, held[0]!.uri, arrival('new'))[0]!.uri).toBe('file:///photos/new.jpg');
  });

  /** A replacement is a new picture, so it starts where every new picture starts. */
  it('begins uploading at zero, and carries the media type it arrived with', () => {
    const held = [uploaded('one')];

    const [replaced] = replacePhoto(held, held[0]!.uri, arrival('new', 'image/heic'));

    expect(replaced?.upload).toEqual({ kind: 'uploading', progress: 0 });
    expect(replaced?.mimeType).toBe('image/heic');
  });

  it('leaves the collection alone when the photo it would replace is not held', () => {
    const held = [uploaded('one')];

    expect(replacePhoto(held, 'file:///photos/gone.jpg', arrival('new'))).toBe(held);
  });

  /**
   * The same dedupe `addPhotos` applies, for the same reason: one photograph in two slots is
   * a collection the row cannot draw honestly. Replacing something with itself is therefore
   * a no-op rather than a re-upload of a picture that is already there.
   */
  /**
   * **A replacement stands in for the photo it replaced until it has arrived.** The profile
   * on the You tab holds the old photo, and a write sent while the new one is on its way — or
   * after it failed — must keep holding it in that slot, not drop it: the player asked for a
   * swap, not a removal (ADR-0179 §2's write is on *an upload that landed*).
   */
  it('remembers the arrived photo it replaced, until it has arrived itself', () => {
    const held = [uploaded('one'), flagged('two')];

    const swapped = replacePhoto(held, held[1]!.uri, arrival('new'));

    expect(swapped[1]?.replacing).toEqual({ photoId: 'id-two', review: 'flagged' });
    expect(standingPhotos(swapped)).toEqual([
      { photoId: 'id-one', review: 'allowed' },
      { photoId: 'id-two', review: 'flagged' },
    ]);
    // Failing leaves the old one standing; arriving is what replaces it.
    const failed = recordUpload(swapped, 'file:///photos/new.jpg', {
      kind: 'failed',
      error: failure,
    });
    expect(photoIds(standingPhotos(failed))).toEqual(['id-one', 'id-two']);
    const landed = recordUpload(swapped, 'file:///photos/new.jpg', {
      kind: 'uploaded',
      photoId: 'id-new',
      review: 'allowed',
    });
    expect(photoIds(standingPhotos(landed))).toEqual(['id-one', 'id-new']);
    expect(landed[1]?.replacing).toBeUndefined();
  });

  it('carries the stood-for photo forward through a second replacement before the first arrived', () => {
    const held = [uploaded('one')];
    const once = replacePhoto(held, held[0]!.uri, arrival('new'));

    const twice = replacePhoto(once, 'file:///photos/new.jpg', arrival('newer'));

    expect(twice[0]?.replacing).toEqual({ photoId: 'id-one', review: 'allowed' });
    expect(photoIds(standingPhotos(twice))).toEqual(['id-one']);
  });

  it('stands for nothing when the photo it replaced had not arrived either', () => {
    const [picked] = addPhotos([], [arrival('picked')]).photos;

    const swapped = replacePhoto([picked!], picked!.uri, arrival('new'));

    expect(swapped[0]?.replacing).toBeUndefined();
    expect(standingPhotos(swapped)).toEqual([]);
  });

  it('leaves the collection alone when the arrival is already in it', () => {
    const held = [uploaded('one'), uploaded('two')];

    expect(replacePhoto(held, held[0]!.uri, arrival('two'))).toBe(held);
    expect(replacePhoto(held, held[0]!.uri, arrival('one'))).toBe(held);
  });
});

describe('which photo is the profile photo', () => {
  it('is the first one, without anything being flagged', () => {
    const photos = addPhotos([], [arrival('one'), arrival('two')]).photos;

    expect(photos[0]?.uri).toBe('file:///photos/one.jpg');
  });

  it('moves to the front when a photo is promoted, and the others keep their order', () => {
    const photos = [uploaded('one'), uploaded('two'), uploaded('three')];

    const promoted = promoteToProfile(photos, 'file:///photos/three.jpg');

    expect(promoted.map((photo) => photo.uri)).toEqual([
      'file:///photos/three.jpg',
      'file:///photos/one.jpg',
      'file:///photos/two.jpg',
    ]);
  });

  it('is unchanged by promoting the photo that already leads', () => {
    const photos = [uploaded('one'), uploaded('two')];

    expect(promoteToProfile(photos, 'file:///photos/one.jpg')).toEqual(photos);
  });

  it('is unchanged by promoting a photo that is not held', () => {
    const photos = [uploaded('one')];

    expect(promoteToProfile(photos, 'file:///photos/gone.jpg')).toEqual(photos);
  });

  it('becomes the next photo when the profile photo is removed', () => {
    // The whole of "removing the profile photo promotes another": there is no promotion,
    // there is a removal, and position one is still position one.
    const photos = [uploaded('one'), uploaded('two'), uploaded('three')];

    const left = removePhoto(photos, 'file:///photos/one.jpg');

    expect(left[0]?.uri).toBe('file:///photos/two.jpg');
  });

  it('is nobody when the last photo is removed', () => {
    expect(removePhoto([uploaded('one')], 'file:///photos/one.jpg')).toEqual([]);
  });
});

describe('one photo failing', () => {
  it('costs that photo and leaves the others exactly where they were', () => {
    const photos = addPhotos([], [arrival('one'), arrival('two'), arrival('three')]).photos;

    const after = recordUpload(photos, 'file:///photos/two.jpg', {
      kind: 'failed',
      error: failure,
    });

    expect(after.map((photo) => photo.upload.kind)).toEqual(['uploading', 'failed', 'uploading']);
    expect(after.map((photo) => photo.uri)).toEqual(photos.map((photo) => photo.uri));
  });

  it('writes nothing at all for a photo that is no longer held', () => {
    const photos = [uploaded('one')];

    expect(
      recordUpload(photos, 'file:///photos/gone.jpg', { kind: 'uploading', progress: 0.5 }),
    ).toEqual(photos);
  });
});

describe('what the draft ends up carrying', () => {
  it('is the ids of the photos that arrived, in the player order', () => {
    const photos = [uploaded('two'), uploaded('one')];

    expect(uploadedPhotoIds(photos)).toEqual(['id-two', 'id-one']);
  });

  it('leaves out a photo still uploading and one that failed — neither has an id to name', () => {
    const photos = [
      uploaded('one'),
      { ...uploaded('two'), upload: { kind: 'uploading', progress: 0.5 } } as ProfilePhoto,
      { ...uploaded('three'), upload: { kind: 'failed', error: failure } } as ProfilePhoto,
    ];

    expect(uploadedPhotoIds(photos)).toEqual(['id-one']);
  });

  it('follows a promotion, because the order is the answer', () => {
    const photos = promoteToProfile([uploaded('one'), uploaded('two')], 'file:///photos/two.jpg');

    expect(uploadedPhotoIds(photos)).toEqual(['id-two', 'id-one']);
  });

  /**
   * **The You tab's photos write carries the same list with the verdicts beside it**, so the
   * cache can be written from the route's answer — ids only — without losing what the check
   * said about each: the pair is what the workbench holds, and the ids are read off it.
   */
  it('is also the pairs, id and verdict, for the write that keeps the verdicts', () => {
    const photos = [
      uploaded('one'),
      { ...uploaded('two'), upload: { kind: 'uploading', progress: 0.5 } } as ProfilePhoto,
      { ...uploaded('three'), upload: { kind: 'uploaded', photoId: 'id-three' } } as ProfilePhoto,
    ];

    expect(uploadedPhotos(photos)).toEqual([
      { photoId: 'id-one', review: 'allowed' },
      { photoId: 'id-three' },
    ]);
    expect(uploadedPhotoIds(photos)).toEqual(photoIds(uploadedPhotos(photos)));
  });
});

describe('whether two lists of ids are the same answer', () => {
  it('is by id and by position — the order is the answer', () => {
    expect(samePhotoIds(['a', 'b'], ['a', 'b'])).toBe(true);
    expect(samePhotoIds(['a', 'b'], ['b', 'a'])).toBe(false);
    expect(samePhotoIds(['a'], ['a', 'b'])).toBe(false);
    expect(samePhotoIds([], [])).toBe(true);
  });
});

/**
 * **The workbench's second caller seeds it from the read** (ADR-0179 §2): the photos a profile
 * already holds, each drawn from the signed address `GET /photos/{id}` answered, arrive as
 * `uploaded` — an id, a verdict where the check concluded one — exactly as an upload's answer
 * would have left them, so every rule above reads a restored tile and a fresh one alike.
 */
describe('a workbench seeded from the profile', () => {
  it('holds each photo as uploaded, keyed by its signed address, in the profile’s order', () => {
    const seeded = heldPhotos(
      [{ photoId: 'id-two', review: 'flagged' }, { photoId: 'id-one' }],
      (photoId) => `https://store.test/${photoId}?signature=whatever`,
    );

    expect(seeded).toEqual([
      {
        uri: 'https://store.test/id-two?signature=whatever',
        mimeType: null,
        upload: { kind: 'uploaded', photoId: 'id-two', review: 'flagged' },
      },
      {
        uri: 'https://store.test/id-one?signature=whatever',
        mimeType: null,
        upload: { kind: 'uploaded', photoId: 'id-one' },
      },
    ]);
    expect(uploadedPhotoIds(seeded)).toEqual(['id-two', 'id-one']);
    expect(flaggedPositions(seeded)).toEqual([0]);
  });
});

describe('what a photo is sent as', () => {
  it('is what the platform said it is', () => {
    expect(mediaTypeOf('image/heic')).toBe('image/heic');
  });

  it('is a JPEG when the platform said nothing, because a type has to be named', () => {
    expect(mediaTypeOf(null)).toBe(ASSUMED_MEDIA_TYPE);
    expect(ASSUMED_MEDIA_TYPE).toBe('image/jpeg');
  });
});

describe('what the on-court check made of a photo', () => {
  it('names the flagged photos by their position in the row', () => {
    // Positions rather than photos: the sentence the step puts on one says which tile it
    // is about, exactly as a failure's does.
    expect(flaggedPositions([uploaded('one'), flagged('two'), flagged('three')])).toEqual([1, 2]);
  });

  it('is nothing at all when every photo came back allowed', () => {
    expect(flaggedPositions([uploaded('one'), uploaded('two')])).toEqual([]);
  });

  it('is nothing for a photo nobody looked at — an absent verdict is not a flag', () => {
    // Three answers and two values (ADR-0138): checked and passed, checked and flagged, and
    // *nobody looked* — a photo that arrived while the reviewer could not be reached. The
    // warning is for a conclusion, and the absence of one is not a conclusion.
    const unlooked = {
      ...uploaded('one'),
      upload: { kind: 'uploaded', photoId: 'id-one' },
    } as ProfilePhoto;

    expect(flaggedPositions([unlooked, flagged('two')])).toEqual([1]);
  });

  it('says nothing about a photo that has not arrived, or did not', () => {
    // Neither has a verdict, because neither has an answer from the platform. A tile that
    // is still going up must not be warned about, and one that failed has nothing stored
    // for a check to have looked at.
    const inFlight = recordUpload([uploaded('one')], 'file:///photos/one.jpg', {
      kind: 'uploading',
      progress: 0.5,
    });
    const failed = recordUpload([uploaded('two')], 'file:///photos/two.jpg', {
      kind: 'failed',
      error: failure,
    });

    expect(flaggedPositions(inFlight)).toEqual([]);
    expect(flaggedPositions(failed)).toEqual([]);
  });

  it('does not keep a flagged photo out of the commit', () => {
    // The whole of the rule: it warns, it never refuses. A flagged photo is stored, keeps
    // its id and is committed with the rest — the cost of the check being wrong is a
    // sentence, not a photograph the player loses.
    expect(uploadedPhotoIds([uploaded('one'), flagged('two')])).toEqual(['id-one', 'id-two']);
  });

  it('does not move a flagged photo out of the lead', () => {
    // Position one is the profile photo and nothing else decides it. A collection that
    // demoted a flagged photo would be the check enforcing something it is not allowed to.
    const held = [flagged('one'), uploaded('two')];

    expect(uploadedPhotoIds(held)).toEqual(['id-one', 'id-two']);
    expect(flaggedPositions(held)).toEqual([0]);
  });
});
