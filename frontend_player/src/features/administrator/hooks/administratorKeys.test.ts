import { administratorKeys } from './administratorKeys';

describe('the administrator query keys', () => {
  // A sign-out's clear and the removal watch both find everything this feature reads by its root.
  it('puts every key under one root, then the club', () => {
    const club = administratorKeys.club('c');

    for (const key of [
      administratorKeys.groups('c'),
      administratorKeys.group('c', 'g'),
      administratorKeys.create('c'),
      administratorKeys.settings('c', 'g'),
      administratorKeys.answers('c', 'g'),
    ]) {
      expect(key.slice(0, club.length)).toEqual(club);
    }
    expect(club[0]).toBe(administratorKeys.all[0]);
  });

  it('keys one Administrator’s two clubs apart', () => {
    expect(administratorKeys.groups('a')).not.toEqual(administratorKeys.groups('b'));
    expect(administratorKeys.group('a', 'g')).not.toEqual(administratorKeys.group('b', 'g'));
  });

  // Re-reading the Groups tab must not re-read every page with it.
  it('keeps a group’s page outside the Groups tab’s key', () => {
    const list = administratorKeys.groups('c');

    expect(administratorKeys.group('c', 'g').slice(0, list.length)).not.toEqual(list);
  });

  it('keys the answers to a group’s requests under that group, apart from every other group’s', () => {
    const page = administratorKeys.group('c', 'g');

    expect(administratorKeys.answers('c', 'g').slice(0, page.length)).toEqual(page);
    expect(administratorKeys.answers('c', 'g')).not.toEqual(administratorKeys.answers('c', 'h'));
  });
});
