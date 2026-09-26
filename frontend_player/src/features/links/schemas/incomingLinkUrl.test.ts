/**
 * **Reading a link the phone hands the app** — the one place an address from outside is turned into
 * something the app acts on ([#520](https://github.com/Raketa02/Raketa/issues/520), ADR-0187 §7:
 * *untrusted route input, never able to repoint the backend*).
 *
 * Three links and nothing else, each rebuilt from the parts that were checked: a link that is not
 * one of them — or is one of them malformed — is no link at all.
 */

import { readIncomingLink } from './incomingLinkUrl';

const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

const read = (url: string, domain: string | null = null) => readIncomingLink(url, domain);

describe('a group link', () => {
  it.each([
    'raketa://join/k7pq2mxa',
    'raketa:///join/k7pq2mxa',
    'raketa://join/k7pq2mxa/',
    'RAKETA://join/k7pq2mxa',
    '/join/k7pq2mxa',
  ])('reads %p', (url) => {
    expect(read(url)).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('reads the code in lower case, the case every code is minted in', () => {
    expect(read('raketa://join/K7PQ2MXA')).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('keeps nothing of a query or a fragment', () => {
    expect(read('raketa://join/k7pq2mxa?api=https://evil.example#https://evil.example')).toEqual({
      kind: 'join',
      code: 'k7pq2mxa',
    });
  });

  it.each([
    'raketa://join/k7pq',
    'raketa://join/k7pq2mxa9',
    'raketa://join/k7pq-2mx',
    'raketa://join',
  ])('is no link when the code cannot be one: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });
});

describe('the web domain', () => {
  it('is read once it is set', () => {
    expect(read('https://raketa.app/join/k7pq2mxa', 'raketa.app')).toEqual({
      kind: 'join',
      code: 'k7pq2mxa',
    });
    expect(read('https://Raketa.App/invite/' + TOKEN, 'raketa.app')).toEqual({
      kind: 'invite',
      token: TOKEN,
    });
  });

  it('is no link while no domain is set', () => {
    expect(read('https://raketa.app/join/k7pq2mxa')).toBeUndefined();
  });

  it.each([
    'https://evil.example/join/k7pq2mxa',
    'https://raketa.app.evil.example/join/k7pq2mxa',
    'https://raketa.app@evil.example/join/k7pq2mxa',
    'https://raketa.app:8443/join/k7pq2mxa',
    'http://raketa.app/join/k7pq2mxa',
  ])('is no link from anywhere else: %p', (url) => {
    expect(read(url, 'raketa.app')).toBeUndefined();
  });
});

describe('an invitation link and a reset link', () => {
  it('reads each token as it was sent', () => {
    expect(read(`raketa://invite/${TOKEN}`)).toEqual({ kind: 'invite', token: TOKEN });
    expect(read(`raketa://reset/${TOKEN}`)).toEqual({ kind: 'reset', token: TOKEN });
  });

  it.each([
    'raketa://invite/',
    'raketa://invite/a%20b',
    'raketa://reset/..%2F..',
    `raketa://reset/${'a'.repeat(257)}`,
  ])('is no link when the token cannot be one: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });
});

/**
 * **The app's bare address** — the button of the club's email to an account that already exists
 * carries no token (ADR-0184 §2), only `raketa://`: *open Raketa and accept there*.
 */
describe('the app’s bare address', () => {
  it.each(['raketa://', 'raketa:///', 'RAKETA://', 'raketa://?utm_source=email'])(
    'reads %p as opening the app',
    (url) => {
      expect(read(url)).toEqual({ kind: 'open' });
    },
  );

  it('is not a path the router holds, nor the web domain’s home', () => {
    expect(read('/')).toBeUndefined();
    expect(read('https://raketa.app/', 'raketa.app')).toBeUndefined();
  });
});

describe('everything else', () => {
  it.each([
    'raketa://sign-in',
    'raketa://play/join/k7pq2mxa',
    'raketa://JOIN/k7pq2mxa',
    'raketa://administrator/c0000000-0000-4000-8000-000000000033/you',
    '/question/1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6?sport=PADEL',
    'exp://192.168.1.5:8081/--/join/k7pq2mxa',
    'exp+raketa-player://expo-development-client/?url=http%3A%2F%2F192.168.1.5%3A8081',
    'javascript:alert(1)',
    '',
  ])('is no link: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });

  it('reads nothing out of an address far longer than any link', () => {
    expect(read(`raketa://join/k7pq2mxa?${'x'.repeat(10_000)}`)).toBeUndefined();
  });
});
