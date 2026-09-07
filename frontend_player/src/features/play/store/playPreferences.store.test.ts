import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayIntent } from '../domain/vocabulary';

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
      'forgetAwaitedDeclaration',
      'mode',
      'reset',
      'seedIfAbsent',
      'seedModeOnFirstDeclaration',
      'sport',
      'sportAwaitingDeclaration',
    ]);
  });
});

describe('the declaration the player just made', () => {
  /**
   * What the screen does on every render of Find a game: it hands the store the sport it is on
   * and whatever the profile says about it. The two actions are called together because the
   * screen has one effect, and every walk below is written the way that effect runs.
   */
  const observed = (sport: Sport, intent: PlayIntent | undefined) => {
    read().seedIfAbsent(sport, intent);
    read().seedModeOnFirstDeclaration(sport, intent);
  };

  it('moves the segment when the sport on screen gains its first declaration', () => {
    observed('padel', undefined);
    expect(read().mode).toBe('FOR_FUN');

    observed('padel', 'COMPETITIVE');

    expect(read().mode).toBe('COMPETITIVE');
  });

  it('takes for fun from the mapping when the answer is no preference', () => {
    observed('padel', undefined);
    read().chooseMode('COMPETITIVE');

    observed('padel', 'NO_PREFERENCE');

    expect(read().mode).toBe('FOR_FUN');
  });

  it('does nothing for a declaration that already existed when the screen opened', () => {
    observed('padel', 'COMPETITIVE');
    read().chooseMode('FOR_FUN');

    // The refetch: the same declaration, read a second time.
    observed('padel', 'COMPETITIVE');

    expect(read().mode).toBe('FOR_FUN');
  });

  it('does nothing on a switch to a sport that was declared in already', () => {
    observed('padel', undefined);
    read().chooseSport('tennis');

    observed('tennis', 'COMPETITIVE');

    expect(read().mode).toBe('FOR_FUN');
  });

  it('does not re-seed a player who moved the segment, switched sport and came back', () => {
    observed('padel', undefined);
    read().chooseMode('COMPETITIVE');

    read().chooseSport('tennis');
    observed('tennis', undefined);
    read().chooseSport('padel');
    observed('padel', undefined);

    expect(read().mode).toBe('COMPETITIVE');
  });

  it('still answers the sport the screen came back to, once that sport is declared', () => {
    observed('padel', undefined);
    read().chooseSport('tennis');
    observed('tennis', undefined);
    read().chooseSport('padel');
    observed('padel', undefined);

    observed('padel', 'COMPETITIVE');

    expect(read().mode).toBe('COMPETITIVE');
  });

  /**
   * The other end of *already existed when the screen opened*: the store outlives the screen,
   * so a declaration made after the player left Play is one they come back to rather than one
   * they have just made — and the segment they moved is theirs to keep.
   */
  it('does not answer a declaration made while the screen was closed', () => {
    observed('padel', undefined);

    // Leaving Play, and a declaration arriving from somewhere that is not this screen.
    read().forgetAwaitedDeclaration();
    observed('padel', 'COMPETITIVE');

    expect(read().mode).toBe('FOR_FUN');
  });

  it('is forgotten when the process ends', () => {
    observed('padel', undefined);
    read().reset();

    // Nothing was seen without a declaration since, so there is no transition to answer.
    read().seedModeOnFirstDeclaration('padel', 'COMPETITIVE');

    expect(read().mode).toBe('FOR_FUN');
  });
});
