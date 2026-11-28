/**
 * **The links into the app, as configuration** — the one setting that turns the web domain's links
 * on, and what iOS and Android are told once it does
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520), ADR-0187 §7).
 *
 * Pure, like `appIdentity`: the functions are what `app.config.ts` calls in Node and what `env.ts`
 * calls at launch, so the table is tested here without booting either.
 */

import { appLinkTo, LINK_PAGES, nativeLinkConfig, readLinkDomain } from './appLinks';

describe('the link domain setting', () => {
  it('is off while nothing is set, which is every environment today', () => {
    expect(readLinkDomain(undefined)).toBeNull();
    expect(readLinkDomain('')).toBeNull();
    expect(readLinkDomain('   ')).toBeNull();
  });

  it('takes a bare host name', () => {
    expect(readLinkDomain('rakieta.app')).toBe('rakieta.app');
    expect(readLinkDomain('links.rakieta.co.uk')).toBe('links.rakieta.co.uk');
  });

  it.each([
    'https://rakieta.app',
    'rakieta.app/join',
    'rakieta.app:443',
    'Rakieta.app',
    'localhost',
    'rakieta',
    '192.168.1.20',
    '-rakieta.app',
    'rakieta..app',
    'user@rakieta.app',
  ])('refuses %p, naming the variable and not the value', (value) => {
    expect(() => readLinkDomain(value)).toThrow(/EXPO_PUBLIC_LINK_DOMAIN/);
    try {
      readLinkDomain(value);
    } catch (error) {
      expect((error as Error).message).not.toContain(value);
    }
  });
});

describe('what the operating systems are told', () => {
  it('claims nothing while no domain is set: no associated domain, no verified intent filter', () => {
    expect(nativeLinkConfig(null)).toEqual({ ios: {}, android: {} });
  });

  it('associates the domain with the app on iOS', () => {
    expect(nativeLinkConfig('rakieta.app').ios).toEqual({
      associatedDomains: ['applinks:rakieta.app'],
    });
  });

  /**
   * One verified filter for the four pages the public site serves an in-app twin of — the paths
   * `apple-app-site-association` claims on the site's side (#526, and `/f/` since #755), and no
   * others.
   */
  it('claims the four pages on Android, verified, over https only', () => {
    expect(nativeLinkConfig('rakieta.app').android).toEqual({
      intentFilters: [
        {
          action: 'VIEW',
          autoVerify: true,
          data: [
            { scheme: 'https', host: 'rakieta.app', pathPrefix: '/join/' },
            { scheme: 'https', host: 'rakieta.app', pathPrefix: '/invite/' },
            { scheme: 'https', host: 'rakieta.app', pathPrefix: '/reset/' },
            { scheme: 'https', host: 'rakieta.app', pathPrefix: '/f/' },
          ],
          category: ['BROWSABLE', 'DEFAULT'],
        },
      ],
    });
  });

  /** A friend link's page, `f/<code>`, is the fourth (#756). */
  it('knows exactly four pages', () => {
    expect(LINK_PAGES).toEqual(['join', 'invite', 'reset', 'f']);
  });
});

describe('the address a link is spelled at', () => {
  it("is the app's own scheme while there is no domain", () => {
    expect(appLinkTo('join', 'k7pq2mxa', null)).toBe('rakieta://join/k7pq2mxa');
  });

  it('is the web domain once there is one', () => {
    expect(appLinkTo('join', 'k7pq2mxa', 'rakieta.app')).toBe('https://rakieta.app/join/k7pq2mxa');
  });

  it('spells a friend link the same way', () => {
    expect(appLinkTo('f', 'tk4m9q2z', null)).toBe('rakieta://f/tk4m9q2z');
    expect(appLinkTo('f', 'tk4m9q2z', 'rakieta.app')).toBe('https://rakieta.app/f/tk4m9q2z');
  });
});
