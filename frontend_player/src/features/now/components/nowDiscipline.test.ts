/**
 * The seven rules on this feature that nothing else can catch, walked over its own
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
 * 2. **Nothing refreshes on a timer** (`ADR-0054`). Four asks, no interval, and —
 *    since `ADR-0088` — two `setTimeout`s that do two different jobs, only one of
 *    which may reach a fetch. The rule was **narrowed** rather than exempted when
 *    the repaint clock landed, which is the only way a walk survives a second
 *    legitimate caller.
 * 3. **Neither of the prototype's two action-row icons comes back** (`ADR-0088`).
 * 4. **The screen never admits staleness** (`ADR-0038` Rule IV). No marker, no
 *    banner, no *"can't reach Raketa"*.
 * 5. **The door is never inferred** (`ADR-0084`). It is drawn exactly when the
 *    server sent one, and one place in the feature can make one at all.
 * 6. **Order is the composed screen's** (`ADR-0032`). Nothing here sorts, and a
 *    shelf can only be *made* where the wire is read — so an update cannot grow one.
 * 7. **Emphasis is never computed** (`ADR-0037`). The flag is read; the score beside
 *    it is never compared against anything.
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

/**
 * Which files contain `needle`, so a failure names the file rather than a count.
 *
 * **Comments are stripped first, for every matcher.** Each rule below is stated in
 * a docblock somewhere in the feature — often in the module the rule is about — and
 * a walk that fired on the sentence explaining it would be unmaintainable, and
 * would teach the next person to delete the explanation rather than the defect. A
 * real call is still a real call: stripping comments cannot hide one.
 */
function filesContaining(needle: RegExp): readonly string[] {
  return featureSources()
    .filter((file) => needle.test(withoutComments(file.text)))
    .map((file) => file.path);
}

/** One module's source, comments removed, for a rule that is about one file. */
function sourceOf(path: string): string {
  const found = featureSources().find((file) => file.path === path);
  if (found === undefined) throw new Error(`the walk cannot find ${path}`);
  return withoutComments(found.text);
}

describe('the feature is walkable at all', () => {
  it('finds the modules it is about to police', () => {
    const paths = featureSources().map((file) => file.path);

    // A glob that matches nothing passes every assertion below in silence.
    expect(paths).toContain('domain/countdown.ts');
    expect(paths).toContain('components/NowScreen.tsx');
    expect(paths).toContain('components/ActionRow.tsx');
    expect(paths).toContain('hooks/useRepaintClock.ts');
    expect(paths).toContain('mappers/nowMappers.ts');
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

  it('arms a timer in exactly two modules, and names what each one is for', () => {
    // **The rule is narrowed rather than exempted**, because `ADR-0088` added a
    // second timer and `ADR-0054` did not stop being true. A countdown reaching
    // zero is one of the four asks and is a single wake at a moment the *server*
    // named; a countdown *repainting* is drawing, and `ADR-0088` states the
    // distinction and states that it is stated nowhere else. Two modules, two
    // jobs, and the next matcher is what keeps them from becoming one.
    expect(filesContaining(/setTimeout\(/)).toEqual([
      'hooks/useDeadlineAsk.ts',
      'hooks/useRepaintClock.ts',
    ]);
  });

  it('keeps the repaint out of reach of a fetch', () => {
    // The failure this exists for is the one `ADR-0088` names in its own
    // consequences: *"a build agent who conflates them will put Now on a
    // 60-second poll."* The repaint clock holds a number and hands it out; it
    // cannot see Query, the use-case or the transport, so a poll cannot be added
    // to it by editing it — only by moving it somewhere else, in a diff.
    const asking = /useQuery|queryClient|invalidate|refetch|composeNow|fetch\(/;

    expect(asking.test(sourceOf('hooks/useRepaintClock.ts'))).toBe(false);
  });

  it('has a control that would fire', () => {
    expect(filesContaining(/useEffect\(/).length).toBeGreaterThan(0);
    expect(/useQuery|refetch/.test('const q = useQuery({})')).toBe(true);
  });
});

describe('the two prototype icons stay dropped', () => {
  /**
   * `ADR-0088` removed `✉` and `⌘` from the action row, and recorded the removal
   * as a **genuine override of a UI authority** rather than as a forced
   * consequence — the first on this map. Both are duplicates: `✉` is a tab-bar
   * button drawn once per card, and `⌘` opens a sheet showing four dots on every
   * card where it survives, because on the one card whose sheet has content
   * (`ready`) its primary button already goes there.
   *
   * The reason this is a walk and not an assertion about a rendered card is that
   * the defect returns by somebody reading `UI` §B6.3 — which still draws both —
   * and adding them back to a component no test renders with an act.
   */
  const DROPPED = /✉|⌘|['"](mail|inbox|command)['"]/;

  it('draws neither, in any module', () => {
    expect(filesContaining(DROPPED)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(DROPPED.test("<Feather name='mail' />")).toBe(true);
    expect(DROPPED.test("const glyph = '⌘';")).toBe(true);
    // The exit glyph the row does draw is not one of them.
    expect(DROPPED.test("<Feather name='log-out' />")).toBe(false);
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
    expect(filesContaining(STALENESS)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(STALENESS.test("we couldn't reach Raketa")).toBe(true);
    expect(STALENESS.test('const isStale = true')).toBe(true);
    // And the one word that is legitimate domain vocabulary passes.
    expect(STALENESS.test('the club caps how long a court may sit held')).toBe(false);
    expect(withoutComments('/* a stale card */ const x = 1;')).not.toContain('stale');
  });
});

describe('the door is never inferred', () => {
  /**
   * `ADR-0084` puts the door **in the shelves list, in order**, precisely so that
   * the phone is not asked to conclude one: *"an inference would fire wrongly on
   * any day the city genuinely has no matches in a sport the player **is** rated
   * at"*, and `ADR-0053` leaves the phone no rules to draw one with.
   *
   * A behavioural test can show that today's screen does not infer it. It cannot
   * show that next week's does not, and the inference is one line — a length check
   * on a list a component already iterates. So the constructor is pinned instead:
   * a door can only be *made* where the wire's block is read, and everywhere else
   * a door is a value that arrived.
   */
  it('makes a door in exactly one module, and it is the wire boundary', () => {
    // A **construction**, not the discriminant's declaration: `domain/` names the
    // literal type and building one there would be impossible anyway.
    expect(filesContaining(/\{\s*kind: 'door'/)).toEqual(['mappers/nowMappers.ts']);
  });

  it('reads the door’s copy table only where a code is resolved', () => {
    // The other half: a component that reached the table could word a door it had
    // decided to draw on its own.
    expect(filesContaining(/DOOR_COPY|doorCopy\(/)).toEqual([
      'mappers/doors.ts',
      'mappers/nowMappers.ts',
      'types.ts',
    ]);
  });

  it('has a control that would fire', () => {
    const made = /\{\s*kind: 'door'/;

    expect(made.test("return { kind: 'door', code };")).toBe(true);
    expect(/DOOR_COPY|doorCopy\(/.test('const copy = doorCopy(code, { sport });')).toBe(true);
    // The type's own declaration is not a construction, and the shelf beside it is
    // neither — a matcher that fired on either would be policing the wrong thing.
    expect(made.test("  readonly kind: 'door';")).toBe(false);
    expect(made.test("return { kind: 'shelf', code };")).toBe(false);
  });
});

describe('order is the composed screen’s, and a shelf arrives whole', () => {
  /**
   * `ADR-0032`: order is a property of the composed screen, decided once by the
   * server. Two edits would take it back, and each has its own matcher.
   *
   * The first is a **sort** — one line in a region component, and the screen quietly
   * disagrees with the shelf's own claim about why a card is third.
   *
   * The second is subtler and is what `Raketa02/Raketa#88` is actually about: *an
   * update is never allowed to carry shelves*. Every act on this screen returns Now's
   * update in its own response, and a session wiring one is one `map` away from
   * rebuilding a shelf out of it — at which point a match she just joined moves under
   * her thumb. A shelf can only be **constructed** where the wire's block is read, so
   * an update path that wanted to replace one would have to say so in a diff.
   */
  it('sorts nothing, anywhere', () => {
    expect(filesContaining(/\.sort\(|\.reverse\(/)).toEqual([]);
  });

  it('makes a shelf in exactly one module, and it is the wire boundary', () => {
    expect(filesContaining(/\{\s*kind: 'shelf'/)).toEqual(['mappers/nowMappers.ts']);
  });

  it('has a control that would fire', () => {
    expect(/\.sort\(|\.reverse\(/.test('blocks.sort((a, b) => a.code < b.code)')).toBe(true);
    expect(/\{\s*kind: 'shelf'/.test("return { kind: 'shelf', code, cards };")).toBe(true);
    // The type's own declaration is not a construction, and the door beside it is
    // neither — a matcher that fired on either would be policing the wrong thing.
    expect(/\{\s*kind: 'shelf'/.test("  readonly kind: 'shelf';")).toBe(false);
    expect(/\{\s*kind: 'shelf'/.test("return { kind: 'door', code };")).toBe(false);
  });
});

describe('emphasis is read and never computed', () => {
  /**
   * `ADR-0037` gates the loud card on three facts — fit ≥ 90, coverage ≥ 80 %, a seat
   * open — and caps it at one per screen. Every clause is about the **other** cards,
   * and the phone cannot see coverage at all.
   *
   * The edit that brings it back is one comparison in one component, and it looks
   * like tidying: the badge already holds a score, `UI` §B9 still writes
   * `emphatic ⇔ score >= 90`, and design-system 7.1 says the threshold lives *"in the
   * domain layer"*. A client that wrote it would light up the top of most screens,
   * since 4,3 % of realistic scores reach 90 and a list selects for the maximum.
   *
   * A behavioural test shows today's screen does not compare. It cannot show that
   * next week's does not, which is why the comparison itself is what is banned.
   */
  const COMPARED = /(score|coverage)\s*[<>]/;

  it('compares a score against nothing, in any module', () => {
    expect(filesContaining(COMPARED)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(COMPARED.test('emphatic={card.fit.score >= 90}')).toBe(true);
    expect(COMPARED.test('const loud = score > EMPHASIS_FLOOR;')).toBe(true);
    // Reading the flag is not comparing, and neither is printing the number.
    expect(COMPARED.test('emphatic={card.emphasis}')).toBe(false);
    expect(COMPARED.test('{`${MARK} ${score}`}')).toBe(false);
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
