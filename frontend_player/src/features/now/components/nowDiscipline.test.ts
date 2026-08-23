/**
 * The three rules on this feature that nothing else can catch, walked over its own
 * source.
 *
 * Each is a rule about what the code **does not** do, and a rule of that shape has
 * no positive test: a suite full of green assertions says nothing about the line
 * somebody adds next week. The backend's `app/` walks are the precedent, and so is
 * their discipline — every allowance below is named with its reason, never granted
 * for looking harmless, and every matcher carries a **negative control** so a guard
 * nobody has seen fire is not one nobody should watch.
 *
 * 1. **The phone holds no rules** (`ADR-0053`). One derivation, in one module.
 * 2. **Nothing refreshes on a timer** (`ADR-0054`). Four asks, and no interval.
 * 3. **The screen never admits staleness** (`ADR-0038` Rule IV). No marker, no
 *    banner, no *"can't reach Raketa"*.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { dependencies, devDependencies } from '../../../../package.json';

const FEATURE = join(__dirname, '..');

interface SourceFile {
  /** Path relative to `src/features/now/`, which is how the allowances are written. */
  readonly path: string;
  readonly text: string;
}

/** Every module the app ships from this feature. Tests are not app code. */
function featureSources(): readonly SourceFile[] {
  const found: SourceFile[] = [];

  const walk = (dir: string, prefix: string) => {
    for (const entry of readdirSync(dir).sort()) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        walk(full, `${prefix}${entry}/`);
        continue;
      }
      if (!/\.tsx?$/.test(entry) || /\.test\.tsx?$/.test(entry)) continue;
      found.push({ path: `${prefix}${entry}`, text: readFileSync(full, 'utf8') });
    }
  };

  walk(FEATURE, '');
  return found;
}

/** Which files contain `needle`, so a failure names the file rather than a count. */
function filesContaining(needle: RegExp): readonly string[] {
  return featureSources()
    .filter((file) => needle.test(file.text))
    .map((file) => file.path);
}

describe('the feature is walkable at all', () => {
  it('finds the modules it is about to police', () => {
    const paths = featureSources().map((file) => file.path);

    // A glob that matches nothing passes every assertion below in silence.
    expect(paths).toContain('domain/countdown.ts');
    expect(paths).toContain('components/NowScreen.tsx');
    expect(paths.length).toBeGreaterThan(10);
  });

  it('does not police its own tests', () => {
    expect(featureSources().map((file) => file.path)).not.toContain(
      'components/nowDiscipline.test.ts',
    );
  });
});

describe('the phone holds no rules and only subtracts', () => {
  it('turns a server moment into a number in exactly one module', () => {
    // `ADR-0053`: *"a client's only derivation is subtracting the current time from
    // a moment it was handed."* Every moment on this screen arrives as a string and
    // `Date.parse` is the only way to make one arithmetic — so one file holding it
    // is the whole of the rule, mechanically.
    expect(filesContaining(/Date\.parse\(/)).toEqual(['domain/countdown.ts']);
  });

  it('reads the device’s own clock only where the line is about the player', () => {
    // `deviceClock` renders the header eyebrow — the one line on Now that says *it
    // is now 14:30 where you are* rather than naming a club's wall clock. Nothing
    // else may construct a `Date`, because a `Date` built from a card's moment is
    // one component away from a locally derived state.
    expect(filesContaining(/new Date\(/)).toEqual(['domain/deviceClock.ts']);
  });

  it('has a control that would fire', () => {
    // The matchers above pass trivially if the walk cannot see source at all.
    expect(filesContaining(/Date\.now\(\)/).length).toBeGreaterThan(0);
  });
});

describe('nothing refreshes on a timer', () => {
  it('has no interval anywhere', () => {
    // `ADR-0054` supersedes `ADR-0038`'s thirty-second poll outright: there is no
    // loop to write, no cadence to tune and no foreground gate. A phone in a pocket
    // costs nothing.
    expect(filesContaining(/setInterval|setImmediate|requestAnimationFrame/)).toEqual([]);
  });

  it('asks Query for no interval either', () => {
    // The poll this feature is most likely to grow back is not a `setInterval`: it
    // is one option on one query, and it reads like configuration rather than like
    // machinery. `refetchInterval: 30_000` restores `ADR-0038` exactly, in a line
    // nobody would call a timer — which is why the walk has to name it.
    expect(filesContaining(/refetchInterval/)).toEqual([]);
  });

  it('arms a one-shot wake in exactly one module, and that module is the fourth ask', () => {
    // A countdown reaching zero is one of the four things that count as asking. It
    // is a single wake at a moment the **server** named — never a period, and never
    // a fallback in case nothing else happens.
    expect(filesContaining(/setTimeout\(/)).toEqual(['hooks/useDeadlineAsk.ts']);
  });

  it('has a control that would fire', () => {
    expect(filesContaining(/useEffect\(/).length).toBeGreaterThan(0);
  });
});

describe('the screen never admits staleness', () => {
  /**
   * The vocabulary of a screen apologising for itself.
   *
   * `ADR-0038` Rule IV, kept by `ADR-0054`: no card carries a stale marker, no
   * banner appears, and there is no *"can't reach Raketa"*. The residual is bounded
   * by the player's own behaviour rather than by us, and the screen either shows
   * what is true or shows that it is fetching.
   *
   * **The bare word `stale` is deliberately not on this list**, and that is the
   * interesting half. A *stale hold* is real domain vocabulary — `CardHoldReason`
   * has `stale` as a member, and its sentence is about a **court** the club has
   * capped, which a card must be able to say. Banning the word would have forced an
   * exemption for the one file that legitimately holds it, and an exemption is how a
   * walk stops meaning anything. What is banned is the screen saying that *it* is
   * behind.
   */
  const STALENESS =
    /out of date|last updated|can(no|')?t reach|couldn'?t reach|no connection|\boffline\b|\breconnecting\b|stale (data|screen|card)|\bisStale\b|\bstaleness\b/i;

  it('says none of it, in any module', () => {
    // Comments are stripped first: the rule is stated in several docblocks, and a
    // walk that fired on the sentence explaining it would be unmaintainable.
    expect(
      featureSources()
        .filter((file) => STALENESS.test(withoutComments(file.text)))
        .map((file) => file.path),
    ).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(STALENESS.test("we couldn't reach Raketa")).toBe(true);
    expect(STALENESS.test('const isStale = true')).toBe(true);
    // And the one word that is legitimate domain vocabulary passes.
    expect(STALENESS.test('the club caps how long a court may sit held')).toBe(false);
    expect(withoutComments('/* a stale card */ const x = 1;')).not.toContain('stale');
  });
});

describe('nothing survives a launch', () => {
  it('installs no cache persister', () => {
    // A cold open shows a shimmer *because there is nothing to restore*. The moment
    // a persister is installed, the shimmer becomes a stale card that is tappable
    // and an offer that died overnight comes back to life — which is the failure
    // `ADR-0054` names when it chooses the shimmer over a restored screen.
    //
    // The dependency list is what is asserted, for the same reason the i18n refusal
    // asserts one: a decision of this shape is reversed by adding a package.
    const names = [
      ...Object.keys(dependencies as Record<string, string>),
      ...Object.keys(devDependencies as Record<string, string>),
    ];

    expect(names.filter((name) => /persist|async-storage/i.test(name))).toEqual([]);
  });
});

/**
 * Source with its comments removed.
 *
 * Deliberately crude — a `//` inside a string literal would be cut too. Nothing in
 * this feature contains one, and the alternative is a parser for a guard whose
 * whole value is that it is readable.
 */
function withoutComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
}
