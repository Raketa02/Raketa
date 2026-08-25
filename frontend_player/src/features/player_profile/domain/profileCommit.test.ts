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
    photoIds: ['photo-1'],
    availability: [{ day: 3, part: 'evening' }],
    location: { latitude: 41.39, longitude: 2.16 },
    searchRadiusKm: 10,
    proposalsOptIn: { accepted: true, copyVersion: 'proposals-opt-in.v1' },
  });
}

describe('a draft with every answer given', () => {
  it('is ready, and yields exactly what the part collected', () => {
    const standing = readyToCommit(answeredDraft());

    expect(standing).toEqual({
      kind: 'ready',
      commit: {
        socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
        photoIds: ['photo-1'],
        availability: [{ day: 3, part: 'evening' }],
        location: { latitude: 41.39, longitude: 2.16 },
        searchRadiusKm: 10,
        proposalsOptIn: { accepted: true, copyVersion: 'proposals-opt-in.v1' },
      },
    });
  });

  it('is ready with no photos and a blank week', () => {
    // Both are genuinely empty answers — a player may hold no photos, and a blank week
    // means *no preference* and never *leave me out*. Reading either as unanswered would
    // block a player on a question they already answered.
    const standing = readyToCommit(
      recordAnswer(answeredDraft(), { photoIds: [], availability: [] }),
    );

    expect(standing.kind).toBe('ready');
  });

  it('is ready with the opt-in declined', () => {
    // No is a whole answer. A readiness rule that opened only on yes would be the product
    // withholding the rest of itself until it got the answer it wanted.
    const standing = readyToCommit(
      recordAnswer(answeredDraft(), {
        proposalsOptIn: { accepted: false, copyVersion: 'proposals-opt-in.v1' },
      }),
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

  it('names an unanswered proposals question', () => {
    const standing = readyToCommit(recordAnswer(answeredDraft(), { proposalsOptIn: undefined }));

    expect(standing).toEqual({ kind: 'incomplete', missing: ['proposals-opt-in'] });
  });

  it('names a radius that was never seeded', () => {
    // The radius step writes the served default the moment it knows it, so this is the
    // step that was never reached rather than a player who declined to choose.
    const standing = readyToCommit(recordAnswer(answeredDraft(), { searchRadiusKm: undefined }));

    expect(standing).toEqual({ kind: 'incomplete', missing: ['search-radius'] });
  });

  it('names all of them, in the order the steps asked', () => {
    const standing = readyToCommit(emptyDraft());

    expect(standing).toEqual({
      kind: 'incomplete',
      missing: ['location', 'search-radius', 'proposals-opt-in'],
    });
  });
});

describe('no part running at all', () => {
  it('is incomplete rather than an empty commit', () => {
    // The absence of a draft is not an absence of answers: it is a player who is not in
    // the part. Committing one would create a profile nobody was asked for.
    expect(readyToCommit(undefined)).toEqual({
      kind: 'incomplete',
      missing: ['location', 'search-radius', 'proposals-opt-in'],
    });
  });
});

describe('where a missing answer is fixed', () => {
  it('names the step that asked for it, never the one that noticed', () => {
    // The commit is only ever attempted from the last step, and the last step can fix
    // exactly one of the three. The other two are somewhere behind it.
    expect(STEP_THAT_ASKS.location).toBe('location');
    expect(STEP_THAT_ASKS['search-radius']).toBe('radius');
    expect(STEP_THAT_ASKS['proposals-opt-in']).toBe('opt-in');
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

  it('opens the finish on a declined opt-in exactly as on an accepted one', () => {
    // No is a whole answer. A gate that opened only on yes would be the product withholding
    // the rest of itself until it got the answer it wanted.
    const declined = recordAnswer(answeredDraft(), {
      proposalsOptIn: { accepted: false, copyVersion: 'proposals-opt-in.v1' },
    });

    expect(mayFinish(commitStanding(declined, NO_PHOTOS, IDLE))).toBe(true);
  });

  it('holds it shut while the proposals question has no answer at all', () => {
    const unanswered = recordAnswer(answeredDraft(), { proposalsOptIn: undefined });

    expect(mayFinish(commitStanding(unanswered, NO_PHOTOS, IDLE))).toBe(false);
  });
});
