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
  toPlayerProfileSurface,
  toProfileOptions,
  toUploadedPhoto,
  toWeekCells,
  toWeekFromCodes,
  toWireSlots,
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
  search_radius: { minimum_km: 1, maximum_km: 50, step_km: 1, default_km: 10 },
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

describe('the served radius bounds', () => {
  /**
   * The unit stays on every field, unlike the tag counts above. A bare `minimum` beside a
   * distance is one refactor away from being read as metres — which is the same reason the
   * backend spells it on the wire.
   */
  it('reads the range, the step and where the control opens', () => {
    expect(toProfileOptions(SERVED).searchRadius).toEqual({
      minimumKm: 1,
      maximumKm: 50,
      stepKm: 1,
      defaultKm: 10,
    });
  });
});

describe('the body that ends the part', () => {
  /**
   * A whole part's worth of answers: two tags, two photos, two cells, an area, an answer
   * about the player and a yes.
   */
  const COMMIT: ProfileCommit = {
    socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
    photoIds: ['photo-a', 'photo-b'],
    availability: [
      { day: 1, part: 'morning' },
      { day: 7, part: 'evening' },
    ],
    location: { latitude: 41.39, longitude: 2.16 },
    searchRadiusKm: 12,
    proposalsOptIn: { accepted: true, copyVersion: 'proposals-opt-in.v1' },
    gender: 'woman',
    genderPreference: 'any',
  };

  it('carries every answer the seven steps collected, in one body', () => {
    expect(toCommitRequest(COMMIT)).toEqual({
      social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
      photo_ids: ['photo-a', 'photo-b'],
      availability: [
        { day: 1, part: 'MORNING' },
        { day: 7, part: 'EVENING' },
      ],
      location: { latitude: 41.39, longitude: 2.16 },
      search_radius_km: 12,
      proposals_opt_in: { accepted: true, copy_version: 'proposals-opt-in.v1' },
      gender: 'WOMAN',
      gender_preference: 'ANY',
    });
  });

  it('keeps the photo order the player arranged, because the first one leads', () => {
    const reversed = toCommitRequest({ ...COMMIT, photoIds: ['photo-b', 'photo-a'] });

    expect(reversed.photo_ids).toEqual(['photo-b', 'photo-a']);
  });

  it('sends an empty week and no photos as themselves, never as an omission', () => {
    // Both are answers. A body that dropped either field would let the server default it,
    // which is the same value arrived at by two routes — and one of them a guess.
    const blank = toCommitRequest({ ...COMMIT, photoIds: [], availability: [] });

    expect(blank.photo_ids).toEqual([]);
    expect(blank.availability).toEqual([]);
  });

  it('sends a declined opt-in as a recorded no, with its copy version', () => {
    // `false` here is a refusal the player gave. It is never what an unanswered question
    // becomes — that one cannot reach this function at all.
    const declined = toCommitRequest({
      ...COMMIT,
      proposalsOptIn: { accepted: false, copyVersion: 'proposals-opt-in.v1' },
    });

    expect(declined.proposals_opt_in).toEqual({
      accepted: false,
      copy_version: 'proposals-opt-in.v1',
    });
  });

  it('spells each gender answer the way the contract does', () => {
    // A table and not a cast, for the day parts' reason: `prefer-not-to-say` would not
    // survive one, and a fourth value on either side must stop the mapper compiling rather
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

  it('spells each part of the day the way the contract does', () => {
    const afternoon = toCommitRequest({
      ...COMMIT,
      availability: [{ day: 3, part: 'afternoon' }],
    });

    expect(afternoon.availability).toEqual([{ day: 3, part: 'AFTERNOON' }]);
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

  it('warns about nothing when the response carried no verdict at all', () => {
    // `GET /photos/{id}` carries none, and so does any backend older than the one that
    // added the field. `null` is explicitly not `allowed` on the wire so that this
    // decision is made here — and *nobody said anything* is not a reason to tell a player
    // their photograph looks wrong.
    expect(toUploadedPhoto(answered(null)).review).toBe('allowed');
    expect(toUploadedPhoto(answered(undefined)).review).toBe('allowed');
  });

  it('warns about nothing on a verdict this build has no sentence for', () => {
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

    expect(toUploadedPhoto(fromTheFuture).review).toBe('allowed');
  });
});

describe('the week, in the two spellings that exist', () => {
  it('sends the whole grid, in the order it is held', () => {
    // The list *is* the week and what is absent from it is unticked, so nothing here sorts
    // and nothing deduplicates — the write path collapses repeats itself.
    expect(
      toWireSlots([
        { day: 6, part: 'morning' },
        { day: 2, part: 'evening' },
      ]),
    ).toEqual([
      { day: 6, part: 'MORNING' },
      { day: 2, part: 'EVENING' },
    ]);
  });

  it('reads one back', () => {
    expect(toWeekCells([{ day: 2, part: 'AFTERNOON' }])).toEqual([{ day: 2, part: 'afternoon' }]);
  });

  it('drops a cell naming a day that is not one of the seven', () => {
    // The wire types `day` as a bare integer, so seven is a promise rather than a
    // compiler's guarantee — and there is no honest eighth day to draw.
    const eighth = [{ day: 8, part: 'MORNING' }] as unknown as Wire['AvailabilitySlotResource'][];

    expect(toWeekCells(eighth)).toEqual([]);
  });
});

/**
 * The third spelling: the joined code the event stream stores, which one route sends anyway.
 *
 * A raised `KEEP_THESE_TIMES` carries the week the search ran on as `"3:EVENING"` strings —
 * the shape `AvailabilitySlotResource` exists to spare a client — so the split lives here,
 * beside the two spellings this feature already owns.
 */
describe('a week as the stream stores it', () => {
  it('splits a code into the cell it names', () => {
    expect(toWeekFromCodes(['2:EVENING', '6:MORNING'])).toEqual([
      { day: 2, part: 'evening' },
      { day: 6, part: 'morning' },
    ]);
  });

  it('carries the order it was given, and sorts nothing', () => {
    expect(toWeekFromCodes(['7:AFTERNOON', '1:MORNING'])).toEqual([
      { day: 7, part: 'afternoon' },
      { day: 1, part: 'morning' },
    ]);
  });

  it('reads a cleared week as a week with nothing in it', () => {
    // `[]` is a cleared week and is a legal thing to be offered; *not this prompt* is an
    // absence one layer up, and never an empty list.
    expect(toWeekFromCodes([])).toEqual([]);
  });

  it('drops a code it cannot read rather than guessing at the cell', () => {
    // The same answer an eighth day gets on the read above: an unreadable code is a cell
    // with nothing to draw, and a fourth part of the day is a build that shipped before it.
    expect(
      toWeekFromCodes(['8:MORNING', '3:SIESTA', 'MONDAY:MORNING', '2', ':', '2:EVENING']),
    ).toEqual([{ day: 2, part: 'evening' }]);
  });
});

describe('the profile surface Play reads', () => {
  const SERVED_SURFACE: Wire['PlayerProfileReadResponse'] = {
    availability: [{ day: 2, part: 'EVENING' }],
    search_radius_km: 12,
    play_intents: { PADEL: 'FOR_FUN', TENNIS: 'NO_PREFERENCE' },
  };

  it('carries the three facts and nothing else', () => {
    expect(toPlayerProfileSurface(SERVED_SURFACE)).toEqual({
      week: [{ day: 2, part: 'evening' }],
      searchRadiusKm: 12,
      playIntents: { padel: 'FOR_FUN', tennis: 'NO_PREFERENCE' },
    });
  });

  it('reads a cleared week as an answer rather than as a missing one', () => {
    // A player may clear their week. It means *we do not know when they play*, never
    // *never*, and it is what the search screen seeds a blank working copy from.
    expect(toPlayerProfileSurface({ ...SERVED_SURFACE, availability: [] }).week).toEqual([]);
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
