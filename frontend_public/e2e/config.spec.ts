import { spawn, type ChildProcess } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';

import { SUITE_ENV } from './suite';

/**
 * **The site refuses to start without its configuration** (docs/environments.md, ADR-0187 §7):
 * `next start` exits before it takes a request, naming each variable and why, and never echoing a
 * value.
 *
 * A missing variable is passed as `""`, which Next's own `.env*` loading never overrides, so a
 * developer's `.env.local` cannot fill the gap this test leaves.
 */

const ROOT = path.resolve(__dirname, '..');
const NEXT = path.join(ROOT, 'node_modules', '.bin', 'next');

function start(env: Record<string, string>): Promise<{ code: number | null; output: string }> {
  return new Promise((resolve) => {
    const child: ChildProcess = spawn(
      NEXT,
      ['start', '--hostname', '127.0.0.1', '--port', '3201'],
      {
        cwd: ROOT,
        env: {
          PATH: process.env.PATH ?? '',
          HOME: process.env.HOME ?? '',
          NODE_ENV: 'production',
          ...env,
        },
      },
    );
    let output = '';
    child.stdout?.on('data', (chunk: Buffer) => (output += chunk.toString()));
    child.stderr?.on('data', (chunk: Buffer) => (output += chunk.toString()));
    const deadline = setTimeout(() => child.kill('SIGKILL'), 20_000);
    child.on('exit', (code: number | null) => {
      clearTimeout(deadline);
      resolve({ code, output });
    });
  });
}

test.describe('Configuration', () => {
  test('a missing variable stops the server at start, named, with no value repeated', async () => {
    const { code, output } = await start({
      ...SUITE_ENV,
      API_URL: 'http://site:hunter2-in-the-url@127.0.0.1:4020',
      APP_STORE_URL: '',
      GOOGLE_PLAY_URL: '',
      APP_SCHEME: '',
    });

    expect(code).toBe(1);
    expect(output).toContain('APP_STORE_URL: is required');
    expect(output).toContain('GOOGLE_PLAY_URL: is required');
    expect(output).toContain('APP_SCHEME: is required');
    expect(output).not.toContain('hunter2');
  });

  test('the backend and the site’s own address are required too', async () => {
    const { code, output } = await start({ ...SUITE_ENV, API_URL: '', PUBLIC_SITE_URL: '' });

    expect(code).toBe(1);
    expect(output).toContain('API_URL: is required');
    expect(output).toContain('PUBLIC_SITE_URL: is required');
  });

  test('an environment name that is not one of the four is refused, without echoing it', async () => {
    const { code, output } = await start({ ...SUITE_ENV, APP_ENV: 'prd-typo' });

    expect(code).toBe(1);
    expect(output).toContain('APP_ENV: must be one of local, development, staging, production');
    expect(output).not.toContain('prd-typo');
  });

  test('an address that is not a URL, and a scheme that is not an app’s, are each refused', async () => {
    const { code, output } = await start({
      ...SUITE_ENV,
      API_URL: 'localhost:8000',
      PUBLIC_SITE_URL: 'raketa.example',
      // Starts like one, and is none: the Android button's link is built from it.
      GOOGLE_PLAY_URL: 'https://[play.google.com/store',
      APP_SCHEME: 'rakieta://',
    });

    expect(code).toBe(1);
    expect(output).toContain('API_URL: must be an absolute http:// or https:// URL');
    expect(output).toContain('PUBLIC_SITE_URL: must be an absolute http:// or https:// URL');
    expect(output).toContain('GOOGLE_PLAY_URL: must be an absolute http:// or https:// URL');
    expect(output).toContain('APP_SCHEME: must be a URL scheme such as rakieta, without ://');
  });

  test('Open in Rakieta never opens a web page or runs a script', async () => {
    for (const scheme of ['https', 'javascript']) {
      const { code, output } = await start({ ...SUITE_ENV, APP_SCHEME: scheme });

      expect(code, scheme).toBe(1);
      expect(output).toContain(
        "APP_SCHEME: must be the app's own scheme, not a web or script scheme",
      );
    }
  });

  test('a deployed environment is reached over https only, said beside any missing variable', async () => {
    const { code, output } = await start({
      ...SUITE_ENV,
      APP_ENV: 'staging',
      PUBLIC_SITE_URL: 'http://raketa.example',
      APP_STORE_URL: 'http://apps.apple.com/app/id1',
      APP_SCHEME: '',
    });

    expect(code).toBe(1);
    expect(output).toContain('APP_SCHEME: is required');
    expect(output).toContain('PUBLIC_SITE_URL: must start with https:// when APP_ENV is staging');
    expect(output).toContain('APP_STORE_URL: must start with https:// when APP_ENV is staging');
    expect(output).not.toContain('GOOGLE_PLAY_URL');
  });
});

test.describe('The app-link files’ settings', () => {
  test('each is required, and a malformed one is refused, without echoing it', async () => {
    const { code, output } = await start({
      ...SUITE_ENV,
      APPLE_TEAM_ID: 'r4ket4',
      IOS_BUNDLE_ID: 'raketa',
      ANDROID_PACKAGE: '',
      ANDROID_CERT_FINGERPRINTS: 'FA:C6:17:45, not-a-key',
    });

    expect(code).toBe(1);
    expect(output).toContain(
      'APPLE_TEAM_ID: must be the 10-character Apple team id, capitals and digits',
    );
    expect(output).toContain('IOS_BUNDLE_ID: must be a bundle id such as com.raketa.player');
    expect(output).toContain('ANDROID_PACKAGE: is required');
    expect(output).toContain(
      'ANDROID_CERT_FINGERPRINTS: must be SHA-256 fingerprints (32 hex pairs, AA:BB:…), separated by commas',
    );
    expect(output).not.toContain('not-a-key');
  });

  test('the files are made from the running server’s settings, not the build’s', async () => {
    const served = await serve({ ...SUITE_ENV, APPLE_TEAM_ID: 'DEPL0YTEAM' }, async (site) => {
      const response = await fetch(`${site}/.well-known/apple-app-site-association`);
      return (await response.json()) as { applinks: { details: { appIDs: string[] }[] } };
    });

    expect(served.applinks.details[0]?.appIDs).toEqual(['DEPL0YTEAM.com.raketa.player']);
  });
});

/**
 * Start the built site on its own port with `env`, run `use` against it once it answers, and stop
 * it whatever happens.
 */
async function serve<T>(env: Record<string, string>, use: (site: string) => Promise<T>) {
  const site = 'http://127.0.0.1:3202';
  const child = spawn(NEXT, ['start', '--hostname', '127.0.0.1', '--port', '3202'], {
    cwd: ROOT,
    env: {
      PATH: process.env.PATH ?? '',
      HOME: process.env.HOME ?? '',
      NODE_ENV: 'production',
      ...env,
    },
  });
  try {
    for (let tries = 0; ; tries += 1) {
      try {
        if ((await fetch(`${site}/icon.svg`)).ok) break;
      } catch {
        if (tries > 100) throw new Error('The site never answered');
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    return await use(site);
  } finally {
    child.kill('SIGKILL');
  }
}
