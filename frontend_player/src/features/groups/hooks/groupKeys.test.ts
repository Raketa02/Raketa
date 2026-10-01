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

  // Leaving or deleting a group reaches everything read about it through its page's key.
  it('keys a group’s Members and requests under its page', () => {
    const page = groupKeys.detail('a');

    expect(groupKeys.members('a', 'padel').slice(0, page.length)).toEqual(page);
    expect(groupKeys.requests('a').slice(0, page.length)).toEqual(page);
  });

  it('keys leaving one group apart from leaving any other', () => {
    expect(groupKeys.exit('a')).not.toEqual(groupKeys.exit('b'));
    expect(groupKeys.exit('a').slice(0, groupKeys.detail('a').length)).toEqual(
      groupKeys.detail('a'),
    );
  });

  it('keys the answers to a group’s requests apart from every other group’s', () => {
    expect(groupKeys.answers('a')).not.toEqual(groupKeys.answers('b'));
  });

  it('keys Members by the sport', () => {
    expect(groupKeys.members('a', 'padel')).not.toEqual(groupKeys.members('a', 'tennis'));
  });
});
