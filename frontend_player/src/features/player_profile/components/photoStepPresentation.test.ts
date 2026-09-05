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
  ACCESS_BODY,
  ADD_CONTROL_WORD,
  CEILING_TITLE,
  PHOTO_RULE_BODY,
  PHOTO_RULE_TITLE,
  POSTER_LABEL,
  PROMOTE_HINT,
  FLAGGED_BODY,
  addControlLabel,
  flaggedNoticeTitle,
  photoFailureMessage,
  photoTileHint,
  photoTileLabel,
  photosEyebrow,
  removeControlLabel,
} from './photoStepPresentation';

function photo(upload: ProfilePhoto['upload']): ProfilePhoto {
  return { uri: 'file:///photos/one.jpg', mimeType: 'image/jpeg', upload };
}

const uploaded = photo({ kind: 'uploaded', photoId: 'photo-1', review: 'allowed' });

describe('the rule the step states', () => {
  it('says what a photo must show, and what it must not', () => {
    expect(PHOTO_RULE_TITLE).toBe('Rackets mandatory, faces optional');
    expect(PHOTO_RULE_BODY).toContain('Show yourself on court or in a racket-sport setting');
    expect(PHOTO_RULE_BODY).toContain('no casual selfies, party photos, or gym mirrors');
    // The half the title makes a promise about, and the half the flagged warning is
    // measured against: the sport is the rule and the face is not.
    expect(PHOTO_RULE_BODY).toContain('Showing your face is optional');
    expect(PHOTO_RULE_BODY).toContain("The sport context isn't");
  });

  it('claims no check, because none is running', () => {
    // The content review is out of scope, and a screen that said we look would be telling
    // the player something untrue about how the product works.
    for (const claim of [/we check/i, /review/i, /moderat/i, /approv/i, /verif/i, /scan/i]) {
      expect(PHOTO_RULE_BODY).not.toMatch(claim);
      for (const body of Object.values(ACCESS_BODY)) expect(body).not.toMatch(claim);
    }
  });

  it('says what carrying on without a photo gets you, where the player is deciding it', () => {
    // The step no longer promises this in advance to somebody who has not asked. It is said
    // in the two notes a player actually meets when the pictures are not going to happen.
    for (const body of Object.values(ACCESS_BODY)) {
      expect(body).toContain('court poster of your own');
    }
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
    expect(photosEyebrow()).toBe('Setting up · Step 2 of 7 · On-court only — up to three');
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

describe('what a flagged photo is told', () => {
  it('names which photo it is about, and what was not seen in it', () => {
    // The position is how the sentence points at a tile — the same thing a failure does,
    // because the row is three pictures and a warning that named none would be a warning
    // about the step.
    expect(flaggedNoticeTitle(1, 3)).toBe('Photo 2 of 3 — we could not see a court');
  });

  it('is written as our failure to see rather than the player’s failure to comply', () => {
    // The reader may be somebody the check is wrong about. *We could not see a court* is
    // the honest report of what happened; *this is not an on-court photo* is a verdict
    // about a picture the machine may simply have got wrong.
    expect(flaggedNoticeTitle(0, 1)).toContain('we could not see');
    for (const accusation of [/you did not/i, /your photo does not/i, /not allowed/i]) {
      expect(flaggedNoticeTitle(0, 1)).not.toMatch(accusation);
      expect(FLAGGED_BODY).not.toMatch(accusation);
    }
  });

  it('says nobody has looked, because nobody has', () => {
    // Nothing reviews a flagged photo a second time. A sentence that let a player believe
    // a person would get to it would be inventing a process to reassure them with.
    expect(FLAGGED_BODY).toContain('nobody has looked');
    expect(FLAGGED_BODY).toContain('automatic');
  });

  it('says the check gets it wrong, before it says what to do', () => {
    expect(FLAGGED_BODY).toContain('gets it wrong');
    expect(FLAGGED_BODY.indexOf('gets it wrong')).toBeLessThan(FLAGGED_BODY.indexOf('swap it'));
  });

  it('says nothing is blocked, and offers keeping it first', () => {
    // A false positive costs a sentence, not a signup: the photo is stored, it keeps its
    // id and it is committed. The player who is on a court is answered first, because
    // they are the one the sentence risks insulting.
    expect(FLAGGED_BODY).toContain('Nothing is blocked');
    expect(FLAGGED_BODY.indexOf('keep it')).toBeLessThan(FLAGGED_BODY.indexOf('swap it'));
  });

  it('promises no review, no appeal and no removal', () => {
    for (const invention of [/review/i, /appeal/i, /remov/i, /delet/i, /reject/i, /violat/i]) {
      expect(FLAGGED_BODY).not.toMatch(invention);
    }
  });
});
