/**
 * The wire boundary for what the profile steps are rendered from, and for the one body
 * that ends the part.
 *
 * Fixtures are typed from the generated schema on purpose: a backend shape change then
 * fails `pnpm typecheck` rather than failing here with a confusing assertion.
 */

import type { Wire } from '@/test-support/transport';

import type { ProfileCommit } from '../domain/profileCommit';

import {
  toCommitRequest,
  toDeckCounts,
  toPhotoAddress,
  toPlayerProfileSurface,
  toProfileOptions,
  toUploadedPhoto,
  toWeeklyHours,
  toWireLocation,
  toWireWeeklyHours,
} from './playerProfileMappers';

const SERVED: Wire['PlayerProfileOptionsResponse'] = {
  social_tag_groups: [
    {
      group: 'AFTER_THE_MATCH',
      tags: [{ id: 'STAYS_FOR_A_DRINK' }, { id: 'SHARES_A_LIFT' }],
    },
    { group: 'ON_THE_COURT', tags: [{ id: 'PLAYS_TO_WIN' }] },
  ],
  social_tag_selection: { minimum_tags: 2, maximum_tags: 6 },
};

describe('the served tag vocabulary', () => {
  it('keeps the groups and the tags inside them in the order they were sent', () => {
    // Both orders are part of the contract — the picker renders what it is given rather
    // than sorting, so a client that sorted would show a different screen from the one
    // product arranged.
    expect(toProfileOptions(SERVED).socialTagGroups).toEqual([
      { group: 'AFTER_THE_MATCH', tagIds: ['STAYS_FOR_A_DRINK', 'SHARES_A_LIFT'] },
      { group: 'ON_THE_COURT', tagIds: ['PLAYS_TO_WIN'] },
    ]);
  });

  it('drops a tag this build has no words for, and keeps the rest of its group', () => {
    // The generated union says this cannot arrive. A phone that has not been updated in
    // eight months says otherwise, and an id with no label is a chip with no words on it.
    const withANewTag: Wire['PlayerProfileOptionsResponse'] = {
      ...SERVED,
      social_tag_groups: [
        {
          group: 'ON_THE_COURT',
          // A tag added after this build shipped.
          tags: [{ id: 'PLAYS_TO_WIN' }, { id: 'CALLS_THE_SCORE_OUT_LOUD' as any }],
        },
      ],
    };

    expect(toProfileOptions(withANewTag).socialTagGroups).toEqual([
      { group: 'ON_THE_COURT', tagIds: ['PLAYS_TO_WIN'] },
    ]);
  });

  it('drops a group this build has no heading for, rather than rendering it unlabelled', () => {
    const withANewGroup: Wire['PlayerProfileOptionsResponse'] = {
      ...SERVED,
      social_tag_groups: [
        ...SERVED.social_tag_groups,
        // A group added after this build shipped.
        { group: 'HOW_YOU_TRAVEL' as any, tags: [{ id: 'SHARES_A_LIFT' }] },
      ],
    };

    expect(toProfileOptions(withANewGroup).socialTagGroups.map((group) => group.group)).toEqual([
      'AFTER_THE_MATCH',
      'ON_THE_COURT',
    ]);
  });

  it('drops a group left with nothing this build can draw', () => {
    // A heading over no chips is a group a player cannot answer — worse than the group's
    // absence, because it reads as something failing to load.
    const allNew: Wire['PlayerProfileOptionsResponse'] = {
      ...SERVED,
      social_tag_groups: [
        // Tags added after this build shipped.
        { group: 'ON_THE_COURT', tags: [{ id: 'CALLS_THE_SCORE_OUT_LOUD' as any }] },
      ],
    };

    expect(toProfileOptions(allNew).socialTagGroups).toEqual([]);
  });
});

describe('the served selection bounds', () => {
  it('reads how many tags a profile must hold, in the app’s own words', () => {
    // `minimum_tags` carries its unit because a bare `minimum` beside a list of eighteen
    // reads as a count of something. Inside the app the type says which, so the field does
    // not have to.
    expect(toProfileOptions(SERVED).socialTagSelection).toEqual({ minimum: 2, maximum: 6 });
  });
});

describe('the body that ends the part', () => {
  /**
   * A whole part's worth of answers: two tags, two photos, two cells, an area and an answer
   * about the player — and no intro, which is what most parts will carry.
   */
  const COMMIT: ProfileCommit = {
    socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
    photoIds: ['photo-a', 'photo-b'],
    weeklyHours: [
      { day: 1, hour: 7 },
      { day: 7, hour: 22 },
    ],
    location: { kind: 'reading', area: { latitude: 41.39, longitude: 2.16 } },
    gender: 'woman',
    genderPreference: 'any',
  };

  it('carries every answer the six steps collected, in one body', () => {
    expect(toCommitRequest(COMMIT)).toEqual({
      social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
      photo_ids: ['photo-a', 'photo-b'],
      weekly_hours: [
        { day: 1, hour: 7 },
        { day: 7, hour: 22 },
      ],
      location: { latitude: 41.39, longitude: 2.16 },
      gender: 'WOMAN',
      gender_preference: 'ANY',
    });
  });

  it('carries a picked club as its id, and nothing of a reading beside it', () => {
    // ADR-0200 §10: the server rounds the club's point to the cell; the phone never needs it.
    const picked = toCommitRequest({
      ...COMMIT,
      location: {
        kind: 'club',
        club: { id: 'club-1', name: 'Bonarka Arena', district: 'Podgórze' },
      },
    });

    expect(picked.location).toEqual({ club_id: 'club-1' });
  });

  it('carries the intro where there is one, and leaves the field out where there is none', () => {
    // Out, not empty: the wire reads `null`, whitespace and an absence as the same answer,
    // and the body sends the one that cannot be read as a line somebody wrote.
    const written = toCommitRequest({ ...COMMIT, intro: 'Will travel for a hard game.' });

    expect(written.intro).toBe('Will travel for a hard game.');
    expect(toCommitRequest(COMMIT)).not.toHaveProperty('intro');
  });

  it('keeps the photo order the player arranged, because the first one leads', () => {
    const reversed = toCommitRequest({ ...COMMIT, photoIds: ['photo-b', 'photo-a'] });

    expect(reversed.photo_ids).toEqual(['photo-b', 'photo-a']);
  });

  it('sends an empty week and no photos as themselves, never as an omission', () => {
    // Both are answers. A body that dropped either field would let the server default it,
    // which is the same value arrived at by two routes — and one of them a guess.
    const blank = toCommitRequest({ ...COMMIT, photoIds: [], weeklyHours: [] });

    expect(blank.photo_ids).toEqual([]);
    expect(blank.weekly_hours).toEqual([]);
  });

  it('spells each gender answer the way the contract does', () => {
    // A table and not a cast: `prefer-not-to-say` would not survive one, and a fourth value on either side must stop the mapper compiling rather
    // than produce a string the other end has never heard of.
    expect(toCommitRequest({ ...COMMIT, gender: 'man' }).gender).toBe('MAN');
    expect(toCommitRequest({ ...COMMIT, gender: 'prefer-not-to-say' }).gender).toBe(
      'PREFER_NOT_TO_SAY',
    );
  });

  it('sends the widest preference as itself rather than leaving the field out', () => {
    // The field has a default on the wire, so an omission would land the same value — by a
    // second route, decided on the other side. What an unconstrained player sends is one
    // decision, made here.
    expect(toCommitRequest({ ...COMMIT, genderPreference: 'any' }).gender_preference).toBe('ANY');
  });

  it('spells a narrowed preference the way the contract does', () => {
    expect(toCommitRequest({ ...COMMIT, genderPreference: 'women-only' }).gender_preference).toBe(
      'WOMEN_ONLY',
    );
    expect(toCommitRequest({ ...COMMIT, genderPreference: 'men-only' }).gender_preference).toBe(
      'MEN_ONLY',
    );
  });
});

describe('what an upload answered', () => {
  function answered(review: Wire['PhotoResponse']['review']): Wire['PhotoResponse'] {
    return {
      photo_id: 'photo-1',
      url: 'https://store.test/photo-1?signature=whatever',
      expires_at: '2026-08-25T12:00:00Z',
      review,
    };
  }

  it('carries the id and the verdict, and neither the URL nor the expiry', () => {
    // The URL is not an identifier and must not be stored as one: the tile is drawing the
    // device's own copy, so a second, expiring address for the same picture is a round
    // trip to see what is already on screen — and a mapper that carried one would invite
    // somebody to keep it.
    expect(toUploadedPhoto(answered('flagged'))).toEqual({
      photoId: 'photo-1',
      review: 'flagged',
    });
  });

  it('reads a verdict that says nothing was wrong as exactly that', () => {
    expect(toUploadedPhoto(answered('allowed')).review).toBe('allowed');
  });

  it('carries no verdict at all when the response carried none — nobody looked', () => {
    // The reviewer could not be asked, or a backend older than the one that added the
    // field. `null` is explicitly not `allowed` on the wire so that this decision is made
    // here: *nobody said anything* is not a reason to tell a player their photograph looks
    // wrong, and it is not a reason to say it passed either (ADR-0138) — the You tab's row
    // says *on court* only of a photo the check passed. So the pair is the id alone.
    expect(toUploadedPhoto(answered(null))).toEqual({ photoId: 'photo-1' });
    expect(toUploadedPhoto(answered(undefined))).toEqual({ photoId: 'photo-1' });
  });

  it('carries no verdict on one this build has no sentence for', () => {
    // The phone that has not been updated in eight months, meeting a decision minted
    // after it shipped. A warning the app cannot phrase is one it must not invent — the
    // same answer a tag with no label gets, arrived at the same way.
    // Through `unknown`, because the generated union is exactly the set of verdicts this
    // build knows and a body carrying a fourth is by definition one it cannot be given a
    // type for. That is the case under test, not a hole in it.
    const fromTheFuture = {
      ...answered('allowed'),
      review: 'quarantined',
    } as unknown as Wire['PhotoResponse'];

    expect(toUploadedPhoto(fromTheFuture)).toEqual({ photoId: 'photo-1' });
  });
});

describe('where a held photo is read from', () => {
  it('is the signed address, and nothing else out of the answer', () => {
    // `GET /photos/{id}` answers the same shape as the upload; what the You tab wants of it
    // is the one thing the upload's mapping refuses to carry — the address a tile draws —
    // because a restored photo has no device copy. The expiry stays behind: nothing stores
    // the address past the screen.
    expect(
      toPhotoAddress({
        photo_id: 'photo-1',
        url: 'https://store.test/photo-1?signature=whatever',
        expires_at: '2026-08-25T12:00:00Z',
        review: null,
      }),
    ).toBe('https://store.test/photo-1?signature=whatever');
  });
});

describe('the week, in the two spellings that exist', () => {
  it('sends the whole grid, in the order it is held', () => {
    // The list *is* the week and what is absent from it is unticked, so nothing here sorts
    // and nothing deduplicates — the write path collapses repeats itself.
    expect(
      toWireWeeklyHours([
        { day: 6, hour: 9 },
        { day: 2, hour: 19 },
      ]),
    ).toEqual([
      { day: 6, hour: 9 },
      { day: 2, hour: 19 },
    ]);
  });

  it('reads one back', () => {
    expect(toWeeklyHours([{ day: 2, hour: 14 }])).toEqual([{ day: 2, hour: 14 }]);
  });

  it('drops a cell naming a day that is not one of the seven', () => {
    // The wire types `day` as a bare integer, so seven is a promise rather than a
    // compiler's guarantee — and there is no honest eighth day to draw.
    expect(toWeeklyHours([{ day: 8, hour: 9 }])).toEqual([]);
  });

  it('drops an hour the grid does not draw, keeping the ones either side of it', () => {
    // The same promise about `hour`: the week runs 07:00 to 23:00, so its first cell starts
    // at 7 and its last at 22, and a 23 or a 6 is a cell there is no row for.
    expect(
      toWeeklyHours([
        { day: 3, hour: 6 },
        { day: 3, hour: 7 },
        { day: 3, hour: 22 },
        { day: 3, hour: 23 },
        { day: 3, hour: 19.5 },
      ]),
    ).toEqual([
      { day: 3, hour: 7 },
      { day: 3, hour: 22 },
    ]);
  });
});

describe('the profile surface You reads', () => {
  const SERVED_SURFACE: Wire['PlayerProfileReadResponse'] = {
    weekly_hours: [{ day: 2, hour: 19 }],
    play_intents: { PADEL: 'FOR_FUN', TENNIS: 'NO_PREFERENCE' },
    social_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'],
    photos: [{ photo_id: 'photo-1', review: 'allowed' }, { photo_id: 'photo-2' }],
    intro: 'Will travel for a hard game.',
    gender: 'MAN',
    gender_preference: 'ANY',
    ranking_visibility: 'SHOWN',
  };

  it('carries every fact the tab draws — the week and the declarations, the three social ones, and the two that gate the matcher', () => {
    expect(toPlayerProfileSurface(SERVED_SURFACE)).toEqual({
      week: [{ day: 2, hour: 19 }],
      playIntents: { padel: 'FOR_FUN', tennis: 'NO_PREFERENCE' },
      socialTagIds: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'],
      photos: [{ photoId: 'photo-1', review: 'allowed' }, { photoId: 'photo-2' }],
      intro: 'Will travel for a hard game.',
      gender: 'man',
      genderPreference: 'any',
    });
  });

  it('reads the owner’s own gender and preference in the app’s spellings — the one shape that carries them', () => {
    // ADR-0179 §4: the owner reads their own answer on the route scoped to `me`, so the screen
    // that asks *who should we match you with* can open on the answer already given.
    const narrowed = toPlayerProfileSurface({
      ...SERVED_SURFACE,
      gender: 'PREFER_NOT_TO_SAY',
      gender_preference: 'WOMEN_ONLY',
    });

    expect(narrowed.gender).toBe('prefer-not-to-say');
    expect(narrowed.genderPreference).toBe('women-only');
  });

  it('leaves the gender absent on a profile committed before the question existed — never prefer not to say', () => {
    const { gender: _served, ...neverAsked } = SERVED_SURFACE;

    expect(toPlayerProfileSurface(neverAsked)).not.toHaveProperty('gender');
  });

  it('leaves the intro absent where none was written, never an empty string', () => {
    const { intro: _served, ...noIntro } = SERVED_SURFACE;

    expect(toPlayerProfileSurface(noIntro)).not.toHaveProperty('intro');
  });

  it('reads no photos as a real answer — the poster stands in', () => {
    expect(toPlayerProfileSurface({ ...SERVED_SURFACE, photos: [] }).photos).toEqual([]);
  });

  it('drops a tag this build has no words for, keeping the rest in the served order', () => {
    // The same answer the options mapping gives: a chip with no words on it is dropped
    // rather than drawn, and the picker on You still opens on the tags it can name.
    const fromTheFuture = {
      ...SERVED_SURFACE,
      social_tags: ['STAYS_FOR_A_DRINK', 'BRINGS_THE_BALLS', 'PLAYS_TO_WIN'],
    } as unknown as Wire['PlayerProfileReadResponse'];

    expect(toPlayerProfileSurface(fromTheFuture).socialTagIds).toEqual([
      'STAYS_FOR_A_DRINK',
      'PLAYS_TO_WIN',
    ]);
  });

  it('reads a cleared week as an answer rather than as a missing one', () => {
    // A player may clear their week. It means *we do not know when they play*, never
    // *never*, and it is what the search screen seeds a blank working copy from.
    expect(toPlayerProfileSurface({ ...SERVED_SURFACE, weekly_hours: [] }).week).toEqual([]);
  });

  it('leaves an undeclared sport absent, which is what the interstitial reads', () => {
    const declared = toPlayerProfileSurface(SERVED_SURFACE).playIntents;

    expect(declared.squash).toBeUndefined();
  });

  it('drops a declaration this build cannot read, sport and all', () => {
    // Two shapes of the same phone-that-was-not-updated case: a fifth sport, and a fourth
    // intent. Neither can open a chip or seed a mode, and guessing at a weight vector is
    // the one answer worse than opening on the declared default.
    const fromTheFuture = {
      ...SERVED_SURFACE,
      play_intents: { PADEL: 'FOR_FUN', PICKLEBALL: 'FOR_FUN', TENNIS: 'RANKED' },
    } as unknown as Wire['PlayerProfileReadResponse'];

    expect(toPlayerProfileSurface(fromTheFuture).playIntents).toEqual({ padel: 'FOR_FUN' });
  });
});

describe('toWireLocation', () => {
  it('sends a reading as its cell — the two numbers and nothing else', () => {
    // `extra="forbid"` on the server: a third key on a reading is a 422.
    expect(
      toWireLocation({ kind: 'reading', area: { latitude: 50.06, longitude: 19.94 } }),
    ).toEqual({ latitude: 50.06, longitude: 19.94 });
  });

  it('sends a picked club as its id alone — never its name or its district', () => {
    expect(
      toWireLocation({
        kind: 'club',
        club: { id: 'club-1', name: 'Bonarka Arena', district: 'Podgórze' },
      }),
    ).toEqual({ club_id: 'club-1' });
  });
});

describe('the cards each kind deals, across the groups', () => {
  /** The wire's two numbers, keyed by the deck's own kinds (ADR-0201 §6). */
  it('reads the two counts by the kind they count', () => {
    const served: Wire['DeckCountsResponse'] = { sport: 'PADEL', competitive: 7, for_fun: 0 };

    expect(toDeckCounts(served)).toEqual({ competitive: 7, forFun: 0 });
  });
});
