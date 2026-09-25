import { spawn, type ChildProcess } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';

import { SUITE_ENV } from './suite';

/**
 * **The website refuses to start without its configuration** (docs/environments.md): `next start`
 * exits before it takes a request, naming each variable and why, and never echoing a value.
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
      ['start', '--hostname', '127.0.0.1', '--port', '3101'],
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
      API_URL: 'http://desk:hunter2-in-the-url@127.0.0.1:4010',
      SESSION_SECRET: '',
      MAP_START: '',
    });

    expect(code).toBe(1);
    expect(output).toContain('SESSION_SECRET: is required');
    expect(output).toContain('MAP_START: is required');
    expect(output).not.toContain('hunter2');
  });

  test('an environment name that is not one of the four is refused, without echoing it', async () => {
    const { code, output } = await start({ ...SUITE_ENV, APP_ENV: 'prd-typo' });

    expect(code).toBe(1);
    expect(output).toContain('APP_ENV: must be one of local, development, staging, production');
    expect(output).not.toContain('prd-typo');
  });

  test('a short session secret, a tile URL without its placeholders and a bad start point are each refused', async () => {
    const { code, output } = await start({
      ...SUITE_ENV,
      SESSION_SECRET: 'too-short',
      MAP_TILE_URL: 'http://127.0.0.1:4010/tiles.png',
      MAP_START: '50.06;19.93',
    });

    expect(code).toBe(1);
    expect(output).toContain('SESSION_SECRET: must be at least 32 characters');
    expect(output).toContain('MAP_TILE_URL: must contain {z}, {x} and {y}');
    expect(output).toContain('MAP_START: must be "latitude,longitude" in decimal degrees');
    expect(output).not.toContain('too-short');
  });

  test('a deployed environment takes its map tiles over https only, said beside any missing variable', async () => {
    const { code, output } = await start({ ...SUITE_ENV, APP_ENV: 'staging', SESSION_SECRET: '' });

    expect(code).toBe(1);
    expect(output).toContain('SESSION_SECRET: is required');
    expect(output).toContain('MAP_TILE_URL: must start with https:// when APP_ENV is staging');
  });
});
