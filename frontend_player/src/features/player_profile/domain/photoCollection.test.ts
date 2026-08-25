/**
 * The photo rules, with no renderer, no store and no socket — which is the point of their
 * living in a function of a list rather than inside the step that draws three tiles.
 */

import { AppError } from '@/shared/errors';

import {
  ASSUMED_MEDIA_TYPE,
  PHOTO_CEILING,
  addPhotos,
  mediaTypeOf,
  promoteToProfile,
  recordUpload,
  removePhoto,
  slotsLeft,
  uploadedPhotoIds,
  type ProfilePhoto,
} from './photoCollection';

/** A photo that has arrived, so a list of them reads as a settled collection. */
function uploaded(name: string): ProfilePhoto {
  return {
    uri: `file:///photos/${name}.jpg`,
    mimeType: 'image/jpeg',
    upload: { kind: 'uploaded', photoId: `id-${name}` },
  };
}

function arrival(name: string, mimeType: string | null = 'image/jpeg') {
  return { uri: `file:///photos/${name}.jpg`, mimeType };
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
