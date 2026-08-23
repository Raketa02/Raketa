/**
 * The four rules on this feature that nothing else can catch, walked over its own
 * source.
 *
 * Each is a rule about what the code **does not** do, and a rule of that shape has
 * no positive test: a suite full of green assertions says nothing about the line
 * somebody adds next week. Now's `nowDiscipline.test.ts` is the precedent and so
 * is its discipline — every allowance is named with its reason, never granted for
 * looking harmless, and every matcher carries a **negative control**, so a guard
 * nobody has seen fire is not one nobody should watch.
 *
 * 1. **Nothing here mentions transferring a seat** (`ADR-0086`). It is the
 *    leaver's best outcome and it belongs to a flow that does not exist.
 * 2. **The phone holds one derivation and this feature does not add a second**
 *    (`ADR-0053`). It subtracts through Now's `countdown` or it does not subtract.
 * 3. **This feature has no second situation table.** The wire embeds the match's
 *    spine and situation half verbatim, so both screens read one table or they
 *    eventually disagree.
 * 4. **The write is never retried on the app's own initiative.** The idempotency
 *    key makes a retry *she* makes safe; it is not a licence to make one for her.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const FEATURE = join(__dirname, '..');

interface SourceFile {
  /** Path relative to `src/features/departure/`, which is how allowances are written. */
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

    expect(paths).toContain('components/DepartureScreen.tsx');
    expect(paths).toContain('mappers/outcomes.ts');
    expect(paths).toContain('hooks/useLeaveMatch.ts');
    expect(paths).toContain('domain/requestKey.ts');
    expect(paths.length).toBeGreaterThan(8);
  });

  it('does not police its own tests', () => {
    expect(featureSources().map((file) => file.path)).not.toContain(
      'components/departureDiscipline.test.ts',
    );
  });

  it('sees through a comment to the code under it', () => {
    // The negative control for the stripper itself: every matcher below depends on
    // it, and a stripper that ate code would make all four vacuous.
    expect(withoutComments('/* transfer */ const x = 1;')).toContain('const x = 1');
    expect(withoutComments('// transfer\nconst y = 2;')).toContain('const y = 2');
    expect(withoutComments('/* transfer */')).not.toContain('transfer');
  });
});

describe('nothing offers to hand a seat to somebody', () => {
  it('says nothing about a transfer anywhere in the feature', () => {
    // `ADR-0086`: transferring a seat is the leaver's **best** outcome — a named
    // person always pays full price — and it is the invite flow, which this map
    // rules out. *"Advertising a door that is not there is worse than the gap."*
    // A rendered test can only prove today's screen is silent; this proves the
    // words are not in the build at all.
    expect(filesContaining(/transfer/i)).toEqual([]);
  });

  it('is a guard that can fire', () => {
    // The negative control. Without it, a matcher that quietly stopped matching —
    // a renamed file, a moved directory — would read as a rule being kept.
    expect(filesContaining(/outcome/i).length).toBeGreaterThan(0);
  });
});

describe('the phone holds one derivation, and this is not where a second lives', () => {
  it('never turns a moment into a number for itself', () => {
    // `ADR-0053` allows exactly one derivation — subtracting the current time from
    // a moment the server handed over — and `now/domain/countdown.ts` is the whole
    // of it. A second `Date.parse` here would be a second place it lives, and in
    // time a second format: `4:37` on one screen and `4 min 37 s` on the other,
    // about the same deadline.
    expect(filesContaining(/Date\.parse\(/)).toEqual([]);
  });

  it('reads the device clock only where a repaint needs an instant', () => {
    // `Date.now()` is not a derivation from server data — it is what a countdown
    // subtracts *from*. It belongs to the timer and to nothing else: a component
    // reading it would be a second reading of *now* on one screen, and two
    // countdowns disagreeing by a render.
    expect(filesContaining(/Date\.now\(/)).toEqual(['hooks/useDepartureClock.ts']);
  });

  it('computes nothing about money', () => {
    // The quote is a label and never an amount (`ADR-0033`), and half of what she
    // paid is a figure the server sends or nobody does. Arithmetic on a `Money`
    // here would be the phone inventing what a departure is worth.
    expect(filesContaining(/amount\s*[*/]|\/\s*2\b/)).toEqual([]);
  });
});

describe('there is one situation table in this app', () => {
  it('resolves the match’s sentence through Now and never through a table here', () => {
    // The wire embeds the spine and the situation half **verbatim**, so the screen
    // she arrives on cannot describe the match differently from the card she
    // tapped. A second table here would be the two disagreeing in whichever
    // language shipped last.
    expect(filesContaining(/situationCopy/)).toEqual(['mappers/departureMappers.ts']);
    expect(filesContaining(/SITUATION_COPY/)).toEqual([]);
  });

  it('reads the wire only where this app says it may', () => {
    // `@/generated` is raw transport and belongs in `api/` and `mappers/` alone.
    // ESLint enforces it too; this states which files are expected to have it, so
    // a third one is a decision rather than a diff nobody reads.
    expect(filesContaining(/@\/generated/)).toEqual([
      'api/departureApi.ts',
      'mappers/codes.ts',
      'mappers/departureMappers.ts',
    ]);
  });
});

describe('nothing retries the write for her', () => {
  it('turns the mutation’s retry off where the mutation is declared', () => {
    // A retry the client makes on its own is a request the player did not
    // authorise, on an act that ends her participation in a match. The key makes a
    // retry **she** makes safe; it is not a licence to make one for her.
    expect(filesContaining(/retry:\s*false/)).toEqual(['hooks/useLeaveMatch.ts']);
    expect(filesContaining(/retry:\s*(true|\d)/)).toEqual([]);
  });

  it('arms exactly one timer, and it cannot reach Query', () => {
    // The repaint is a repaint and never an occasion to ask. A module that both
    // held a cadence and could fetch is how a screen quietly starts polling.
    expect(filesContaining(/setTimeout|setInterval/)).toEqual(['hooks/useDepartureClock.ts']);
    expect(filesContaining(/useQueryClient|@tanstack\/react-query/)).toEqual([
      'hooks/useDeparture.ts',
      'hooks/useLeaveMatch.ts',
    ]);
  });
});
