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
      APP_SCHEME: 'raketa://',
    });

    expect(code).toBe(1);
    expect(output).toContain('API_URL: must be an absolute http:// or https:// URL');
    expect(output).toContain('PUBLIC_SITE_URL: must be an absolute http:// or https:// URL');
    expect(output).toContain('APP_SCHEME: must be a URL scheme such as raketa, without ://');
  });

  test('Open in Raketa never opens a web page or runs a script', async () => {
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
