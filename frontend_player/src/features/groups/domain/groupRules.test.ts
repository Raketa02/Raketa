import type { SearchedClub, ClubSearch, GroupAtClub } from './group';
import { groupAction, searchOutcome } from './groupRules';

const BONARKA: SearchedClub = {
  id: 'club-bonarka',
  name: 'Bonarka Arena',
  district: 'Bonarka',
  distanceKm: 3.1,
  sports: ['padel', 'badminton'],
  groups: [],
};

function row(
  relation: GroupAtClub['relation'],
  joinPolicy: GroupAtClub['joinPolicy'],
): Pick<GroupAtClub, 'relation' | 'joinPolicy'> {
  return { relation, joinPolicy };
}

describe('what a group row offers the reader', () => {
  it('offers Join on an Anyone group they are not in', () => {
    expect(groupAction(row('NONE', 'ANYONE'))).toBe('join');
  });

  it('offers Ask to join on a People I approve group', () => {
    expect(groupAction(row('NONE', 'PEOPLE_I_APPROVE'))).toBe('ask');
  });

  it('says the request is waiting once they asked', () => {
    expect(groupAction(row('REQUESTED', 'PEOPLE_I_APPROVE'))).toBe('requested');
  });

  it('says they are in, whatever the policy', () => {
    expect(groupAction(row('MEMBER', 'ANYONE'))).toBe('in');
    expect(groupAction(row('MEMBER', 'PEOPLE_I_APPROVE'))).toBe('in');
  });
});

function search(overrides: Partial<ClubSearch>): ClubSearch {
  return { text: 'o', clubs: [], nextPage: null, readAs: 'TEXT', ...overrides };
}

describe('which answer a search draws', () => {
  it('draws the clubs when there are any', () => {
    expect(searchOutcome(search({ clubs: [BONARKA] }))).toEqual({ kind: 'clubs' });
  });

  it('says there is no match for text that found nothing, quoting what was typed', () => {
    expect(searchOutcome(search({ text: 'perr' }))).toEqual({ kind: 'no-match', text: 'perr' });
  });

  it('says there is nothing at a link that leads nowhere', () => {
    expect(searchOutcome(search({ text: 'raketa.app/join/ZZZZZZZZ', readAs: 'LINK' }))).toEqual({
      kind: 'nothing-at-link',
    });
  });

  it('draws the club a live link found', () => {
    expect(searchOutcome(search({ readAs: 'LINK', clubs: [BONARKA] }))).toEqual({
      kind: 'clubs',
    });
  });
});
