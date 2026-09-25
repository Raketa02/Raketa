import { groupKeys } from './groupKeys';

describe('the groups query keys', () => {
  // A join rewrites every cached search through this one root.
  it('puts both searches under one root', () => {
    const root = groupKeys.searches();

    expect(groupKeys.homeClubs('ogr').slice(0, root.length)).toEqual(root);
    expect(groupKeys.toJoin('ogr').slice(0, root.length)).toEqual(root);
  });

  it('keys each search by its text, and the two searches apart', () => {
    expect(groupKeys.toJoin('ogr')).not.toEqual(groupKeys.toJoin('ogro'));
    expect(groupKeys.homeClubs('ogr')).not.toEqual(groupKeys.toJoin('ogr'));
  });

  it('keys a group’s page by its id', () => {
    expect(groupKeys.detail('a')).not.toEqual(groupKeys.detail('b'));
  });
});
