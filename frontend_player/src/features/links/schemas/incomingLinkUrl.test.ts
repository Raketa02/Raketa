/**
 * **Reading a link the phone hands the app** — the one place an address from outside is turned into
 * something the app acts on ([#520](https://github.com/Raketa02/Raketa/issues/520), ADR-0187 §7:
 * *untrusted route input, never able to repoint the backend*).
 *
 * Four links and nothing else, each rebuilt from the parts that were checked: a link that is not
 * one of them — or is one of them malformed — is no link at all. And the install referrer Google
 * Play hands an Android app on its first launch (#756), read for the two links that carry a code.
 */

import { readIncomingLink, readReferrerLink } from './incomingLinkUrl';

const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

const read = (url: string, domain: string | null = null) => readIncomingLink(url, domain);

describe('a group link', () => {
  it.each([
    'rakieta://join/k7pq2mxa',
    'rakieta:///join/k7pq2mxa',
    'rakieta://join/k7pq2mxa/',
    'RAKIETA://join/k7pq2mxa',
    '/join/k7pq2mxa',
  ])('reads %p', (url) => {
    expect(read(url)).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('reads the code in lower case, the case every code is minted in', () => {
    expect(read('rakieta://join/K7PQ2MXA')).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('keeps nothing of a query or a fragment', () => {
    expect(read('rakieta://join/k7pq2mxa?api=https://evil.example#https://evil.example')).toEqual({
      kind: 'join',
      code: 'k7pq2mxa',
    });
  });

  it.each([
    'rakieta://join/k7pq',
    'rakieta://join/k7pq2mxa9',
    'rakieta://join/k7pq-2mx',
    'rakieta://join',
  ])('is no link when the code cannot be one: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });
});

/** **A friend link** (#756) — `f/<code>`, its code a group code's shape (the friends mechanics §4.1). */
describe('a friend link', () => {
  it.each(['rakieta://f/tk4m9q2z', 'rakieta:///f/tk4m9q2z', '/f/tk4m9q2z', 'rakieta://f/TK4M9Q2Z'])(
    'reads %p, its code in lower case',
    (url) => {
      expect(read(url)).toEqual({ kind: 'friend', code: 'tk4m9q2z' });
    },
  );

  it('is read off the web domain once one is set', () => {
    expect(read('https://raketa.app/f/tk4m9q2z?utm_source=whatsapp', 'raketa.app')).toEqual({
      kind: 'friend',
      code: 'tk4m9q2z',
    });
    expect(read('https://raketa.app/f/tk4m9q2z')).toBeUndefined();
  });

  it.each(['rakieta://f/tk4m', 'rakieta://f/tk4m-9q2', 'rakieta://f', 'rakieta://F/tk4m9q2z'])(
    'is no link when it cannot be one: %p',
    (url) => {
      expect(read(url)).toBeUndefined();
    },
  );
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
    expect(read(`rakieta://invite/${TOKEN}`)).toEqual({ kind: 'invite', token: TOKEN });
    expect(read(`rakieta://reset/${TOKEN}`)).toEqual({ kind: 'reset', token: TOKEN });
  });

  it.each([
    'rakieta://invite/',
    'rakieta://invite/a%20b',
    'rakieta://reset/..%2F..',
    `rakieta://reset/${'a'.repeat(257)}`,
  ])('is no link when the token cannot be one: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });
});

/**
 * **The app's bare address** — the button of the club's email to an account that already exists
 * carries no token (ADR-0184 §2), only `rakieta://`: *open Rakieta and accept there*.
 */
describe('the app’s bare address', () => {
  it.each(['rakieta://', 'rakieta:///', 'RAKIETA://', 'rakieta://?utm_source=email'])(
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
    'rakieta://sign-in',
    'rakieta://play/join/k7pq2mxa',
    'rakieta://JOIN/k7pq2mxa',
    'rakieta://administrator/c0000000-0000-4000-8000-000000000033/you',
    '/question/1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6?sport=PADEL',
    'exp://192.168.1.5:8081/--/join/k7pq2mxa',
    'exp+rakieta-player://expo-development-client/?url=http%3A%2F%2F192.168.1.5%3A8081',
    'javascript:alert(1)',
    '',
  ])('is no link: %p', (url) => {
    expect(read(url)).toBeUndefined();
  });

  it('reads nothing out of an address far longer than any link', () => {
    expect(read(`rakieta://join/k7pq2mxa?${'x'.repeat(10_000)}`)).toBeUndefined();
  });
});

/**
 * **The install referrer** (#756, the friends mechanics §4.3) — the text Google Play keeps from the
 * store button that installed the app, which the public site sets to the page's own link,
 * `<public site>/join/<code>` or `<public site>/f/<code>`.
 *
 * Anybody can put any text there — a Play listing's address takes any `referrer` — so it is read as
 * the scheme is: **the page and its value, and nothing else**. Its host proves nothing either way,
 * so any is taken, the laptop's `http://localhost:3001` included. **Only the two pages that carry a
 * code**: a token is a credential, and no store button carries one.
 */
describe('the install referrer', () => {
  it.each([
    ['https://raketa.app/f/tk4m9q2z', { kind: 'friend', code: 'tk4m9q2z' }],
    ['https://raketa.app/join/K7PQ2MXA', { kind: 'join', code: 'k7pq2mxa' }],
    ['http://localhost:3001/f/tk4m9q2z', { kind: 'friend', code: 'tk4m9q2z' }],
    ['https://raketa.app/f/tk4m9q2z?utm_source=whatsapp', { kind: 'friend', code: 'tk4m9q2z' }],
  ])('reads %p', (referrer, link) => {
    expect(readReferrerLink(referrer)).toEqual(link);
  });

  /** Play hands it back decoded; one encoded once more is read the same. */
  it('reads a link still encoded', () => {
    expect(readReferrerLink('https%3A%2F%2Fraketa.app%2Ff%2Ftk4m9q2z')).toEqual({
      kind: 'friend',
      code: 'tk4m9q2z',
    });
  });

  it.each([
    'utm_source=google-play&utm_medium=organic',
    `https://raketa.app/invite/${TOKEN}`,
    `https://raketa.app/reset/${TOKEN}`,
    'https://raketa.app/',
    'https://raketa.app/play/join/k7pq2mxa',
    'https://raketa.app/f/tk4m',
    'rakieta://f/tk4m9q2z',
    'javascript:alert(1)',
    '%E0%A4%A',
    '',
    `https://raketa.app/f/tk4m9q2z?${'x'.repeat(10_000)}`,
  ])('is no link: %p', (referrer) => {
    expect(readReferrerLink(referrer)).toBeUndefined();
  });
});
