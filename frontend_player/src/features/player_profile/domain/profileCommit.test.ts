import { networkUnavailable } from '@/shared/errors';

import type { ProfilePhoto } from './photoCollection';
import { emptyDraft, recordAnswer, type ProfileDraft } from './ProfileDraft';
import {
  commitStanding,
  commitToSend,
  mayFinish,
  readyToCommit,
  STEP_THAT_ASKS,
} from './profileCommit';

/** Everything the six steps collect, all of it answered. The ordinary end of the part. */
function answeredDraft(): ProfileDraft {
  return recordAnswer(emptyDraft(), {
    socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
    intro: 'Moved from Wrocław in May. Needs opponents.',
    photoIds: ['photo-1'],
    weeklyHours: [{ day: 3, hour: 19 }],
    location: { latitude: 41.39, longitude: 2.16 },
    gender: 'woman',
    // Not written by `answeredDraft` because a player never has to: `emptyDraft` already
    // holds `any`. It is named here anyway, so a test that narrows it is visibly changing
    // something the part carries rather than filling something it was short of.
    genderPreference: 'any',
  });
}

describe('a draft with every answer given', () => {
  it('is ready, and yields exactly what the part collected', () => {
    const standing = readyToCommit(answeredDraft());

    expect(standing).toEqual({
      kind: 'ready',
      commit: {
        socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
        intro: 'Moved from Wrocław in May. Needs opponents.',
        photoIds: ['photo-1'],
        weeklyHours: [{ day: 3, hour: 19 }],
        location: { latitude: 41.39, longitude: 2.16 },
        gender: 'woman',
        genderPreference: 'any',
      },
    });
  });

  it('is ready with no intro, and then carries none', () => {
    // The intro is optional and a player who skipped has no line rather than an empty one —
    // so the commit does not hold the field at all, rather than holding an empty string
    // the server would read as the same answer by a second route.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { intro: '' }));

    expect(standing.kind).toBe('ready');
    expect(standing.kind === 'ready' && standing.commit).not.toHaveProperty('intro');
  });

  it('carries the intro trimmed, and a blank one as none', () => {
    const written = readyToCommit(recordAnswer(answeredDraft(), { intro: '  Needs opponents. ' }));
    const blank = readyToCommit(recordAnswer(answeredDraft(), { intro: '   ' }));

    expect(written.kind === 'ready' && written.commit.intro).toBe('Needs opponents.');
    expect(blank.kind === 'ready' && blank.commit).not.toHaveProperty('intro');
  });

  it('is ready with no photos', () => {
    // Photos are a genuinely empty answer — a player may hold none — so reading an empty
    // list as *unanswered* would block them on a question they already answered.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { photoIds: [] }));

    expect(standing.kind).toBe('ready');
  });

  it('is ready on one ticked hour of the week', () => {
    // The floor is exactly one. One tick is a real answer, and the near-total absence of
    // overlap that follows is a *measured* near-zero (ADR-0102).
    const standing = readyToCommit(
      recordAnswer(answeredDraft(), { weeklyHours: [{ day: 6, hour: 9 }] }),
    );

    expect(standing.kind).toBe('ready');
  });
});

describe('a draft still missing an answer', () => {
  it('names the area a player continued past', () => {
    // The location step can be left without one, at the cost the step names. The commit
    // is where that cost is collected: a profile takes part in search and matchmaking
    // through one spatial input, and there is nothing to send in its place.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { location: undefined }));

    expect(standing).toEqual({ kind: 'incomplete', missing: ['location'] });
  });

  it('names a week with nothing ticked', () => {
    // The week stopped being a genuinely empty answer when ADR-0102 gave it a floor:
    // silence about when a player usually plays is never scored, so it is asked for.
    // Photos keep the exemption — none is still an answer to *add some photos*.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { weeklyHours: [] }));

    expect(standing).toEqual({ kind: 'incomplete', missing: ['availability'] });
  });

  it('names all of them, in the order the steps asked', () => {
    const standing = readyToCommit(emptyDraft());

    expect(standing).toEqual({
      kind: 'incomplete',
      missing: ['availability', 'location', 'gender'],
    });
  });

  it('names an unanswered question about the player, and never the preference beside it', () => {
    // The two are asked on one screen and are not the same kind of thing: the answer about
    // the player is required, and the preference over others is `any` until somebody
    // narrows it. A report that listed both would send a player back to fix something they
    // already hold.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { gender: undefined }));

    expect(standing).toEqual({ kind: 'incomplete', missing: ['gender'] });
  });

  it('is ready on a narrowed preference exactly as on the widest one', () => {
    // Narrowing is an answer, not a problem to be resolved before finishing. What it costs
    // the player is said on the step that takes it, not here.
    const narrowed = readyToCommit(
      recordAnswer(answeredDraft(), { genderPreference: 'women-only' }),
    );

    expect(narrowed.kind).toBe('ready');
  });
});

describe('no part running at all', () => {
  it('is incomplete rather than an empty commit', () => {
    // The absence of a draft is not an absence of answers: it is a player who is not in
    // the part. Committing one would create a profile nobody was asked for.
    expect(readyToCommit(undefined)).toEqual({
      kind: 'incomplete',
      missing: ['availability', 'location', 'gender'],
    });
  });
});

describe('where a missing answer is fixed', () => {
  it('names the step that asked for it, never the one that noticed', () => {
    // The commit is only ever attempted from the last step, and the last step can fix
    // exactly one of the three. The other two are somewhere behind it.
    expect(STEP_THAT_ASKS.availability).toBe('availability');
    expect(STEP_THAT_ASKS.location).toBe('location');
    expect(STEP_THAT_ASKS.gender).toBe('gender');
  });
});

// ---------------------------------------------------------------------------
// Where the part stands, and when the finish opens
// ---------------------------------------------------------------------------

const NO_PHOTOS: readonly ProfilePhoto[] = [];

function photoThatIs(upload: ProfilePhoto['upload']): ProfilePhoto {
  return { uri: 'file:///one.jpg', mimeType: 'image/jpeg', upload };
}

const IDLE = { kind: 'idle' } as const;

describe('the standing the last step renders from', () => {
  it('is ready, and carries the body, when everything is in', () => {
    const standing = commitStanding(answeredDraft(), NO_PHOTOS, IDLE);

    expect(standing.kind).toBe('ready');
    expect(mayFinish(standing)).toBe(true);
  });

  it('names what is missing before it looks at anything else', () => {
    const standing = commitStanding(
      recordAnswer(answeredDraft(), { location: undefined }),
      [photoThatIs({ kind: 'uploading', progress: 0.4 })],
      IDLE,
    );

    // Only one of the two is the player's to do something about. Waiting quietly on the
    // photo would say nothing about the answer that actually needs them.
    expect(standing).toEqual({ kind: 'incomplete', missing: ['location'] });
    expect(mayFinish(standing)).toBe(false);
  });

  it('waits for a photo that is still arriving, and asks for nothing', () => {
    // The body names photos by the ids the server gave back, so a commit sent now would
    // quietly leave out a picture the player watched upload.
    const standing = commitStanding(
      answeredDraft(),
      [photoThatIs({ kind: 'uploading', progress: 0.4 })],
      IDLE,
    );

    expect(standing).toEqual({ kind: 'uploading', photos: 1 });
    expect(mayFinish(standing)).toBe(false);
  });

  it('does not wait for a photo that failed', () => {
    // That one is not on its way anywhere — the tile says so and offers the retry. Holding
    // the whole part shut on it would make one failure cost the setup rather than the
    // picture.
    const standing = commitStanding(
      answeredDraft(),
      [photoThatIs({ kind: 'failed', error: networkUnavailable() })],
      IDLE,
    );

    expect(standing.kind).toBe('ready');
    expect(mayFinish(standing)).toBe(true);
  });

  it('reads a request in flight as busy rather than as an unanswered part', () => {
    // A busy control is not a disabled one. A request going out is not a part that is short
    // of something, and saying so would ask a player for an answer they just gave.
    const standing = commitStanding(answeredDraft(), NO_PHOTOS, { kind: 'sending' });

    expect(standing).toEqual({ kind: 'committing' });
    expect(mayFinish(standing)).toBe(true);
  });

  it('keeps the finish open after a failure, because the finish is the retry', () => {
    const error = networkUnavailable();
    const standing = commitStanding(answeredDraft(), NO_PHOTOS, { kind: 'failed', error });

    expect(standing).toMatchObject({ kind: 'failed', error });
    expect(mayFinish(standing)).toBe(true);
    // **The same answers**, so the retry is a replay of the request that failed rather than
    // a second one. The draft was never touched by the failure.
    expect(commitToSend(standing)).toEqual(
      commitToSend(commitStanding(answeredDraft(), NO_PHOTOS, IDLE)),
    );
  });

  it('reports what is outstanding rather than a failure the player has moved past', () => {
    // A failure over a part that is no longer complete is a failure about answers that have
    // since been taken back. There is nothing to retry with, and what is outstanding now is
    // the truthful thing to say.
    const standing = commitStanding(
      recordAnswer(answeredDraft(), { location: undefined }),
      NO_PHOTOS,
      { kind: 'failed', error: networkUnavailable() },
    );

    expect(standing).toEqual({ kind: 'incomplete', missing: ['location'] });
    expect(commitToSend(standing)).toBeUndefined();
  });

  it('sends nothing at all while one is in flight, or once one has landed', () => {
    // The disabled control is a courtesy and the key is the defence — but a rule that let a
    // press start a second request while the first was still going would be relying on the
    // server to sort out something the client never had to create.
    expect(
      commitToSend(commitStanding(answeredDraft(), NO_PHOTOS, { kind: 'sending' })),
    ).toBeUndefined();
    expect(commitToSend(commitStanding(undefined, NO_PHOTOS, { kind: 'landed' }))).toBeUndefined();
  });

  it('reads a commit that landed before the draft it cleared', () => {
    // **The order is the rule.** Committing clears the draft, so asking the draft first
    // would report a part that has just succeeded as *incomplete* — and the last step would
    // flash a demand for an answer the player gave a moment ago.
    const standing = commitStanding(undefined, NO_PHOTOS, { kind: 'landed' });

    expect(standing).toEqual({ kind: 'committed' });
    expect(mayFinish(standing)).toBe(true);
  });

  it('holds it shut while the player has not answered about themselves', () => {
    // The question on the last step itself. `prefer not to say` is an answer; nothing is.
    const unanswered = recordAnswer(answeredDraft(), { gender: undefined });

    expect(mayFinish(commitStanding(unanswered, NO_PHOTOS, IDLE))).toBe(false);
  });

  it('opens it on a narrowed preference exactly as on the widest one', () => {
    const narrowed = recordAnswer(answeredDraft(), { genderPreference: 'men-only' });

    expect(mayFinish(commitStanding(narrowed, NO_PHOTOS, IDLE))).toBe(true);
  });
});
