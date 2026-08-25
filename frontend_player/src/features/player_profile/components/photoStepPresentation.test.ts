/**
 * The words on the photos step, held against the two things copy on this screen must do:
 * state the on-court rule, and claim no check that is not running.
 *
 * Written out rather than derived from the tables — a test that asked the code for the
 * words would agree with any words at all, including none.
 */

import { AppError } from '@/shared/errors';

import type { ProfilePhoto } from '../domain/photoCollection';

import {
  ADD_CONTROL_WORD,
  CEILING_TITLE,
  NO_PHOTO_IS_FINE,
  PHOTO_RULE_BODY,
  PHOTO_RULE_TITLE,
  POSTER_LABEL,
  PROMOTE_HINT,
  addControlLabel,
  photoFailureMessage,
  photoTileHint,
  photoTileLabel,
  photosEyebrow,
  removeControlLabel,
} from './photoStepPresentation';

function photo(upload: ProfilePhoto['upload']): ProfilePhoto {
  return { uri: 'file:///photos/one.jpg', mimeType: 'image/jpeg', upload };
}

const uploaded = photo({ kind: 'uploaded', photoId: 'photo-1' });

describe('the rule the step states', () => {
  it('says what a photo must show, and what it must not', () => {
    expect(PHOTO_RULE_TITLE).toBe('Rackets mandatory, faces optional');
    expect(PHOTO_RULE_BODY).toContain('Photos show you on a court');
    expect(PHOTO_RULE_BODY).toContain('Not a selfie, not the beach, not the gym mirror');
    expect(PHOTO_RULE_BODY).toContain('Faces are optional; the sport is not');
  });

  it('claims no check, because none is running', () => {
    // The content review is out of scope, and a screen that said we look would be telling
    // the player something untrue about how the product works.
    for (const claim of [/we check/i, /review/i, /moderat/i, /approv/i, /verif/i, /scan/i]) {
      expect(PHOTO_RULE_BODY).not.toMatch(claim);
      expect(NO_PHOTO_IS_FINE).not.toMatch(claim);
    }
  });

  it('says adding none is fine, and what a player gets instead', () => {
    expect(NO_PHOTO_IS_FINE).toContain('No photo is fine');
    expect(NO_PHOTO_IS_FINE).toContain('court poster of your own');
  });
});

describe('the ceiling', () => {
  it('is a fact, stated the way the tags step states its own', () => {
    // The two are one decision — a refusal as a fact, no apology and no "you can only".
    // Do not reword either independently of the other.
    expect(CEILING_TITLE).toBe('Three is the ceiling');
  });
});

describe('the eyebrow', () => {
  it('carries the rule beside the position', () => {
    expect(photosEyebrow()).toBe('Setting up · Step 2 of 6 · On-court only — up to three');
  });
});

describe('what the add control announces', () => {
  it('says how many slots remain, because the row cannot say it', () => {
    expect(addControlLabel(3)).toBe('Add a photo, 3 slots left');
    expect(addControlLabel(1)).toBe('Add a photo, 1 slot left');
  });

  it('is the same words a player reads on it', () => {
    expect(addControlLabel(2)).toContain(ADD_CONTROL_WORD);
  });
});

describe('what a tile is called', () => {
  it('names its position, and says which one leads', () => {
    expect(photoTileLabel(uploaded, 0, 3)).toBe('Photo 1 of 3, profile photo');
    expect(photoTileLabel(uploaded, 1, 3)).toBe('Photo 2 of 3');
  });

  it('counts the photos held rather than the tiles drawn', () => {
    expect(photoTileLabel(uploaded, 0, 1)).toBe('Photo 1 of 1, profile photo');
  });

  it('says what the strip says, because the strip is not legible to a screen reader', () => {
    expect(photoTileLabel(photo({ kind: 'uploading', progress: 0.5 }), 1, 3)).toBe(
      'Photo 2 of 3, uploading',
    );
    expect(
      photoTileLabel(
        photo({ kind: 'failed', error: new AppError('server', 'terminal', 'x') }),
        1,
        3,
      ),
    ).toBe('Photo 2 of 3, upload failed');
  });

  it('lets an upload in flight outrank the profile marker, as the strip does', () => {
    expect(photoTileLabel(photo({ kind: 'uploading', progress: 0 }), 0, 2)).toBe(
      'Photo 1 of 2, uploading',
    );
  });
});

describe('what pressing a tile would do', () => {
  it('is a promotion on any settled photo that is not already leading', () => {
    expect(photoTileHint(uploaded, 1)).toBe(PROMOTE_HINT);
  });

  it('is nothing on the photo that already leads', () => {
    expect(photoTileHint(uploaded, 0)).toBeUndefined();
  });

  it('is a promotion on one still uploading, because the press does the same thing', () => {
    expect(photoTileHint(photo({ kind: 'uploading', progress: 0.5 }), 2)).toBe(PROMOTE_HINT);
  });

  it('is a retry on a failed one, whatever its position', () => {
    const failed = photo({ kind: 'failed', error: new AppError('server', 'terminal', 'x') });

    expect(photoTileHint(failed, 0)).toBe('Try this upload again');
    expect(photoTileHint(failed, 2)).toBe('Try this upload again');
  });
});

describe('the remove control', () => {
  it('names which photo it removes — "Remove" alone says nothing out of context', () => {
    expect(removeControlLabel(1, 3)).toBe('Remove photo 2 of 3');
  });
});

describe('the poster', () => {
  it('says it is generated, so nobody has to see it to know it is not the player', () => {
    expect(POSTER_LABEL).toContain('generated court poster');
    expect(POSTER_LABEL).toContain('not a photograph');
  });
});

describe('why an upload failed', () => {
  it('names what the player can do about the codes their own choice produces', () => {
    const unsupported = new AppError('validation', 'requires-user-correction', 'diagnostic', {
      code: 'unsupported_image_format',
    });

    expect(photoFailureMessage(unsupported)).toContain('That format is not one we can take');
    // Never the backend's own message: it is written for a log and ships English into
    // every locale.
    expect(photoFailureMessage(unsupported)).not.toContain('diagnostic');
  });

  it('falls back to the recovery category for a failure this build has never seen', () => {
    const unknown = new AppError('server', 'retryable-automatically', 'diagnostic', {
      code: 'something_new',
    });

    expect(photoFailureMessage(unknown)).toBe(
      "We couldn't reach Raketa. Check your connection and try again.",
    );
  });

  it('does the same for a failure that carries no code at all', () => {
    expect(photoFailureMessage(new AppError('unknown', 'terminal', 'x'))).toBe(
      'Something went wrong at our end. Try again later.',
    );
  });
});
