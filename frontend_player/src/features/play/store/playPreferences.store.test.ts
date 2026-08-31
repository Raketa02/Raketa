import { usePlayPreferences } from './playPreferences.store';

const read = () => usePlayPreferences.getState();

beforeEach(() => {
  read().reset();
});

describe('what Play opens on', () => {
  it('holds nothing until Play has been entered once', () => {
    expect(read().sport).toBeUndefined();
  });

  it('seeds the sport from the ratings and the mode from the declaration', () => {
    read().seedIfAbsent('tennis', 'COMPETITIVE');

    expect(read().sport).toBe('tennis');
    expect(read().mode).toBe('COMPETITIVE');
  });

  it('opens for fun for a player who declared no preference, and for one who declared nothing', () => {
    read().seedIfAbsent('padel', 'NO_PREFERENCE');
    expect(read().mode).toBe('FOR_FUN');

    read().reset();
    read().seedIfAbsent('padel', undefined);
    expect(read().mode).toBe('FOR_FUN');
  });

  it('does not re-seed a player who has already chosen', () => {
    // Both doors into Play lay the stack down, so the seed runs on every entry. An
    // unconditional one would put a player who switched to tennis back on padel each time
    // they came in from ⚡.
    read().seedIfAbsent('padel', 'COMPETITIVE');
    read().chooseSport('tennis');
    read().chooseMode('FOR_FUN');

    read().seedIfAbsent('padel', 'COMPETITIVE');

    expect(read().sport).toBe('tennis');
    expect(read().mode).toBe('FOR_FUN');
  });

  it('is never written back: the declaration seeds the toggle and the toggle changes nothing', () => {
    // ADR-0094's drift backstop is written for the sticky-tab case — switch once, decline
    // once, then search in the new mode for a month. A toggle that wrote itself back into the
    // declaration would agree with it always and the backstop would catch nothing. Nothing in
    // this store's surface can write to the profile, which is the whole of the guarantee.
    read().seedIfAbsent('padel', 'COMPETITIVE');
    read().chooseMode('FOR_FUN');

    expect(Object.keys(read()).sort()).toEqual([
      'chooseMode',
      'chooseSport',
      'mode',
      'reset',
      'seedIfAbsent',
      'sport',
    ]);
  });
});
