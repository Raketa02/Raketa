/**
 * The five rules on this feature that nothing else can catch, walked over its own
 * source.
 *
 * Each is a rule about what the code **does not** do, and a rule of that shape has
 * no positive test: a suite full of green assertions says nothing about the line
 * somebody adds next week. Now's `nowDiscipline.test.ts` is the precedent and so is
 * its discipline — every allowance is named with its reason, never granted for
 * looking harmless, and every matcher carries a **negative control**, so a guard
 * nobody has seen fire is not one nobody should watch.
 *
 * 1. **Nothing here can say *no*** (`ADR-0048`). A counter carries a score, and the
 *    way that is made true is by there being nowhere to send a bare rejection —
 *    not by a validator turning one away.
 * 2. **The phone holds one derivation and this feature does not add a second**
 *    (`ADR-0053`). It subtracts through Now's `countdown` and its clock, or it does
 *    not subtract.
 * 3. **This feature has no second situation table.** The wire embeds the match's
 *    spine and situation half verbatim, so both screens read one table.
 * 4. **A situation is named in exactly one module.** `ADR-0060` renders *by
 *    situation*, and the only block that is keyed on one is the ending — so a
 *    screen that started switching on a name would be the screen identifier that
 *    ADR refused, arriving as an `if`.
 * 5. **Neither write is retried on the app's own initiative.** Both are writes into
 *    an argument between four people, and a retry the client makes on its own is a
 *    request the player did not authorise.
 * 6. **The screen holds no stale time**, which is the one rule here that a rendered
 *    test cannot reach at all — see the block for why.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const FEATURE = join(__dirname, '..');

interface SourceFile {
  /** Path relative to `src/features/result/`, which is how allowances are written. */
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
 * a docblock somewhere in the feature — usually in the module the rule is about —
 * and a walk that fired on the sentence explaining it would teach the next person
 * to delete the explanation rather than the defect. A real call is still a real
 * call: stripping comments cannot hide one.
 */
function filesContaining(needle: RegExp): readonly string[] {
  return featureSources()
    .filter((file) => needle.test(withoutComments(file.text)))
    .map((file) => file.path);
}

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');
}

describe('the feature is walkable at all', () => {
  it('finds the modules it is about to police', () => {
    // A glob that matches nothing passes every assertion below in silence.
    const paths = featureSources().map((file) => file.path);

    expect(paths).toContain('components/ResultScreen.tsx');
    expect(paths).toContain('components/ScorePadView.tsx');
    expect(paths).toContain('domain/scorePad.ts');
    expect(paths).toContain('mappers/endings.ts');
    expect(paths).toContain('hooks/useResultWrites.ts');
    expect(paths.length).toBeGreaterThan(10);
  });

  it('does not police its own tests', () => {
    expect(featureSources().map((file) => file.path)).not.toContain(
      'components/resultDiscipline.test.ts',
    );
  });
});

describe('there is no way to say no', () => {
  /**
   * The vocabulary of a bare rejection.
   *
   * `ADR-0048` refused it twice over: a rejection carrying no score is *"free and
   * always optimal for the loser"*, and the chat it would have been resolved in
   * does not exist. Requiring a score makes the objection specific, falsifiable,
   * and — because a counter is itself a proposal — settled by the other side's
   * silence in turn.
   *
   * It is a walk rather than a rendered assertion because the defect returns by
   * somebody adding a control to a component no test renders with a live proposal
   * on it, and because the **word** is where it starts: the product's word is
   * *propose a modification*, and `dispute` is the one the delta names and refuses.
   */
  const SAYING_NO = /reject|decline|dispute|refuse/i;

  it('holds none of the words, in any module', () => {
    expect(filesContaining(SAYING_NO)).toEqual([]);
  });

  it('is a guard that can fire', () => {
    expect(SAYING_NO.test("<Button label='Dispute this score' />")).toBe(true);
    expect(SAYING_NO.test("const REJECTED = 'no';")).toBe(true);
    // The word the product does use is not one of them.
    expect(SAYING_NO.test("const COUNTER_LABEL = 'Propose a modification';")).toBe(false);
  });
});

describe('the phone holds one derivation, and this is not where a second lives', () => {
  it('never turns a moment into a number for itself', () => {
    // `ADR-0053` allows exactly one derivation — subtracting the current time from a
    // moment the server handed over — and `now/domain/countdown.ts` is the whole of
    // it. A second `Date.parse` here would be a second place it lives, and in time a
    // second format: `4:37` on one screen and `4 min 37 s` on the other, about the
    // same deadline.
    expect(filesContaining(/Date\.parse\(/)).toEqual([]);
  });

  it('never reads the device clock at all', () => {
    // `Date.now()` is what a countdown subtracts *from*, and it belongs to the
    // timer. The timer is **Now's** `useMomentClock`, shared by all three screens
    // that count down, so a module here that read one would be a second reading of
    // *now* on one screen and two countdowns disagreeing by a render.
    expect(filesContaining(/Date\.now\(/)).toEqual([]);
  });

  it('arms no timer of its own', () => {
    // A cadence added here would be a second loop rather than a modified one, and
    // Now's own walk is what keeps the shared loop out of reach of a fetch.
    expect(filesContaining(/setTimeout|setInterval/)).toEqual([]);
  });

  it('is a guard that can fire', () => {
    // Without this, a renamed file or a moved directory would read as a rule kept.
    expect(filesContaining(/useMomentClock/).length).toBeGreaterThan(0);
  });
});

describe('there is one situation table in this app', () => {
  it('resolves the match’s sentence through Now and never through a table here', () => {
    // The wire embeds the spine and the situation half **verbatim**, so the screen
    // she arrives on cannot describe the match differently from the card she tapped.
    // A second table here would be the two disagreeing in whichever one shipped
    // last.
    expect(filesContaining(/situationCopy/)).toEqual(['mappers/resultMappers.ts']);
    expect(filesContaining(/SITUATION_COPY/)).toEqual([]);
  });

  it('names a situation in exactly one module', () => {
    // `ADR-0060`: the route *"renders by situation, not by a screen identifier"*,
    // and the only thing keyed on a name is the ending — resolved in `mappers/`,
    // where a wire code may be named at all. Every other block is composed from a
    // server boolean, a score or a clock, so a `situation === 'confirmResult'`
    // anywhere else would be the screen identifier that ADR refused, arriving as an
    // `if` in a component.
    expect(filesContaining(/playedNoScore|confirmResult|needsResult|completed/)).toEqual([
      'mappers/endings.ts',
    ]);
  });

  it('reads the wire only where this app says it may', () => {
    // `@/generated` is raw transport and belongs in `api/` and `mappers/` alone.
    // ESLint enforces it too; this states which files are expected to have it, so a
    // fourth is a decision rather than a diff nobody reads.
    expect(filesContaining(/@\/generated/)).toEqual([
      'api/resultApi.ts',
      'mappers/codes.ts',
      'mappers/resultMappers.ts',
    ]);
  });
});

describe('the conversation is never served from a cache', () => {
  /**
   * **A source-level guard, and the reason is the harness rather than the rule.**
   *
   * `staleTime: 0` is what makes a screen opened twice in half a minute ask twice,
   * against the app's 30-second default — and a cached conversation is the one thing
   * this screen must not show, because between two visits a proposal can land,
   * settle or be countered, and *accept* against a replaced score asks her to agree
   * with a number that is no longer on the table.
   *
   * Two behavioural cases assert the second request happens, and **neither can
   * fail**: under the test renderer this query is dropped from the cache when the
   * route is popped, so a reopen refetches whatever the stale time says. That is an
   * artifact of tearing the tree down rather than of the app — in a shipped build
   * `gcTime` keeps it for five minutes — so the rule is guarded where it is written
   * instead. The departure screen's identical claim has the same blind spot.
   */
  it('overrides the app default to zero, in the hook where the query is declared', () => {
    expect(filesContaining(/staleTime: 0/)).toEqual(['hooks/useResult.ts']);
    expect(filesContaining(/staleTime: [1-9]/)).toEqual([]);
  });

  it('is a guard that can fire', () => {
    expect(/staleTime: [1-9]/.test('staleTime: 60_000,')).toBe(true);
    expect(/staleTime: 0/.test('staleTime: 60_000,')).toBe(false);
  });
});

describe('nothing retries a write for her', () => {
  it('turns retry off where the two mutations are declared', () => {
    // Neither write carries an idempotency key, because the contract needs none: a
    // second identical score from one side is a **correction**, and a second
    // acceptance comes back as the situation with `mayAccept` false. That is what
    // makes a retry *she* makes safe — and it is not a licence to make one for her.
    expect(filesContaining(/retry:\s*false/)).toEqual(['hooks/useResultWrites.ts']);
    expect(filesContaining(/retry:\s*(true|\d)/)).toEqual([]);
  });

  it('reaches Query in exactly two modules', () => {
    expect(filesContaining(/useQueryClient|@tanstack\/react-query/)).toEqual([
      'hooks/useResult.ts',
      'hooks/useResultWrites.ts',
    ]);
  });
});
