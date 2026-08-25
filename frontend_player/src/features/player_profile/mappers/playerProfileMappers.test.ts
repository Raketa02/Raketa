/**
 * The wire boundary for what the profile steps are rendered from.
 *
 * Fixtures are typed from the generated schema on purpose: a backend shape change then
 * fails `pnpm typecheck` rather than failing here with a confusing assertion.
 */

import type { Wire } from '@/test-support/transport';

import { toProfileOptions } from './playerProfileMappers';

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
