/**
 * Five rules about what this app does **not** do with notifications, walked over
 * its own source.
 *
 * Each one is a rule no green assertion can carry, because each is an absence.
 * Four of the five are walked over the **whole of `src/`** rather than over this
 * feature, and deliberately: the tempting place to write the branch, install the
 * listener or persist the answer is in whichever feature happens to want it, and
 * a walk scoped to the feature that already behaves would never see it.
 *
 * 1. **Nothing branches on `timeSensitiveSetting`** (`ADR-0065`). It is reported
 *    and never acted on — the cascade does not demote a player who has revoked,
 *    and neither does the phone. This is `Raketa02/Raketa#95`'s fourth
 *    acceptance criterion, and it is the one the record itself flags as looking
 *    like an oversight to anybody who finds the field before they find the
 *    reasoning.
 * 2. **One module asks the OS.** ESLint bans `expo-notifications` everywhere
 *    else; this says *which* module, so the ban cannot be satisfied by moving
 *    the import somewhere quieter.
 * 3. **Nothing subscribes to a notification, and nothing reads one's payload**
 *    (`ADR-0062`). The notification carries no truth — the backend's own
 *    `PushMessage` has no data field at all — so a tap re-reads live state, and
 *    the strongest form of *renders nothing the payload carried* is that no code
 *    in this app ever receives one. Opening the app **is** `ADR-0054`'s first
 *    ask, and it already refetches.
 * 4. **This feature never reaches Query** (`ADR-0054`). Four things ask Now to
 *    refresh and there are only four; a notification handler that invalidated a
 *    key would be a fifth, arriving through the one feature with a reason to
 *    want one.
 * 5. **Nothing persists her answer.** The OS holds whether she was asked and
 *    what she said, and it is the only thing entitled to: a durable *she said
 *    no* on this device would be a record of a refusal that the platform can
 *    neither show her nor let her change.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

/** `src/`, because four of the five rules are about the app and not a feature. */
const SOURCE = join(__dirname, '..', '..', '..');

const FEATURE = 'features/notifications/';

interface SourceFile {
  /** Path relative to `src/`, which is how the allowances below are written. */
  readonly path: string;
  readonly text: string;
}

/**
 * Every module the app ships. Tests are not app code, and neither is
 * `test-support/`, which ships to no build.
 */
function appSources(): readonly SourceFile[] {
  const found: SourceFile[] = [];

  const walk = (dir: string, prefix: string) => {
    for (const entry of readdirSync(dir).sort()) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        if (entry === 'generated' || entry === 'test-support') continue;
        walk(full, `${prefix}${entry}/`);
        continue;
      }
      if (!/\.tsx?$/.test(entry) || /\.test\.tsx?$/.test(entry)) continue;
      found.push({ path: `${prefix}${entry}`, text: readFileSync(full, 'utf8') });
    }
  };

  walk(SOURCE, '');
  return found;
}

/**
 * Which files contain `needle`, so a failure names the file rather than a count.
 *
 * **Comments are stripped first, for every matcher**, the same way Now's walk
 * strips them: every rule below is explained in a docblock somewhere near the
 * code it governs, and a walk that fired on the explanation would teach the next
 * person to delete the explanation rather than the defect.
 */
function filesContaining(needle: RegExp, within = ''): readonly string[] {
  return appSources()
    .filter((file) => file.path.startsWith(within))
    .filter((file) => needle.test(withoutComments(file.text)))
    .map((file) => file.path);
}

describe('the app is walkable at all', () => {
  it('finds the modules it is about to police', () => {
    const paths = appSources().map((file) => file.path);

    // A glob that matches nothing passes every assertion below in silence.
    expect(paths).toContain('shared/lib/notifications/osNotifications.ts');
    expect(paths).toContain(`${FEATURE}use-cases/registerDevice.ts`);
    expect(paths).toContain(`${FEATURE}hooks/useDeviceRegistration.ts`);
    expect(paths).toContain(`${FEATURE}components/NotificationExplainer.tsx`);
    expect(paths).toContain(`${FEATURE}store/standbyAsk.store.ts`);
    // The feature this must never reach into, so the reach would be visible.
    expect(paths).toContain('features/now/components/NowScreen.tsx');
  });
});

describe('nothing branches on what Time Sensitive is set to', () => {
  /**
   * A comparison, a switch, or a truthiness test on the setting — in either
   * spelling, because it crosses the wire as `time_sensitive_setting` and lives
   * in the app as `timeSensitive`.
   */
  const BRANCHED =
    /(?:timeSensitive|time_sensitive)[\w.]*\s*(?:===|!==|==|!=|\?\?|\?)|(?:if|switch|while)\s*\(\s*[\w.]*(?:timeSensitive|time_sensitive)/i;

  it('compares it against nothing, in any module', () => {
    expect(filesContaining(BRANCHED)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(BRANCHED.test("if (address.timeSensitive === 'disabled') return;")).toBe(true);
    expect(BRANCHED.test('switch (device.timeSensitive) {')).toBe(true);
    expect(BRANCHED.test("if (body.time_sensitive_setting !== 'enabled') skip();")).toBe(true);
    expect(BRANCHED.test('const loud = timeSensitive ? 1 : 0;')).toBe(true);
    // Carrying it is the whole job, and carrying is not branching.
    expect(BRANCHED.test('time_sensitive_setting: address.timeSensitive,')).toBe(false);
    expect(BRANCHED.test('timeSensitive: await os.timeSensitive(),')).toBe(false);
  });
});

describe('one module asks the OS', () => {
  const IMPORTS_THE_SDK = /from 'expo-notifications'|require\('expo-notifications'\)/;

  it('is the adapter, and nothing else in the app', () => {
    expect(filesContaining(IMPORTS_THE_SDK)).toEqual([
      'shared/lib/notifications/osNotifications.ts',
    ]);
  });

  /**
   * `ADR-0061`'s promise in the other direction: refusing costs a player the
   * message and never a card. Now's own walk already refuses it the OS; this is
   * the same claim made from outside, so deleting either one leaves the other.
   */
  it('is not Now', () => {
    expect(filesContaining(IMPORTS_THE_SDK, 'features/now/')).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(IMPORTS_THE_SDK.test("import * as Notifications from 'expo-notifications';")).toBe(true);
    expect(
      IMPORTS_THE_SDK.test("import { osNotifications } from '@/shared/lib/notifications';"),
    ).toBe(false);
  });
});

describe('nothing receives a notification, so nothing can render one', () => {
  const RECEIVES =
    /addNotificationResponseReceivedListener|addNotificationReceivedListener|useLastNotificationResponse|getLastNotificationResponseAsync|setNotificationHandler|getPresentedNotificationsAsync/;

  it('subscribes to nothing, in any module', () => {
    expect(filesContaining(RECEIVES)).toEqual([]);
  });

  /**
   * And nothing reaches into a payload. The backend composes `PushMessage` with
   * no data field at all, so this is a rule about a thing that cannot arrive —
   * which is exactly when a walk is worth more than an assertion.
   */
  const READS_A_PAYLOAD = /request\.content|notification\.(?:data|request)|response\.notification/;

  it('reads a payload nowhere', () => {
    expect(filesContaining(READS_A_PAYLOAD)).toEqual([]);
  });

  it('has controls that would fire', () => {
    expect(RECEIVES.test('Notifications.addNotificationResponseReceivedListener(onTap);')).toBe(
      true,
    );
    expect(RECEIVES.test('const last = useLastNotificationResponse();')).toBe(true);
    expect(
      READS_A_PAYLOAD.test('const id = response.notification.request.content.data.matchId;'),
    ).toBe(true);
    // Creating the one Android channel is not receiving anything.
    expect(RECEIVES.test('await Notifications.setNotificationChannelAsync(OFFERS_CHANNEL, {')).toBe(
      false,
    );
  });
});

describe('this feature never reaches the cache', () => {
  const REACHES_QUERY = /@tanstack\/react-query|queryClient|invalidateQueries|nowKeys/;

  it('holds no Query call, in any module', () => {
    expect(filesContaining(REACHES_QUERY, FEATURE)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(
      REACHES_QUERY.test('await queryClient.invalidateQueries({ queryKey: nowKeys.all });'),
    ).toBe(true);
    expect(REACHES_QUERY.test("import { httpRequest } from '@/shared/lib/http';")).toBe(false);
  });
});

describe('nothing persists what she answered', () => {
  const PERSISTS = /SecureStore|AsyncStorage|persist\(|createJSONStorage|MMKV/;

  it('writes nothing durable, in any module of this feature', () => {
    expect(filesContaining(PERSISTS, FEATURE)).toEqual([]);
  });

  it('has a control that would fire', () => {
    expect(PERSISTS.test('export const useStandbyAskStore = create(persist(store, {')).toBe(true);
    expect(PERSISTS.test('const useStandbyAskStore = create<StandbyAskState>((set) => ({')).toBe(
      false,
    );
  });
});

/** One module's source, comments removed, for a rule that is about one file. */
function withoutComments(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
}
