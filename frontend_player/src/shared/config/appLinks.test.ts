/**
 * **The links into the app, as configuration** — the one setting that turns the web domain's links
 * on, and what iOS and Android are told once it does
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), ADR-0187 §7).
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
    expect(readLinkDomain('raketa.app')).toBe('raketa.app');
    expect(readLinkDomain('links.raketa.co.uk')).toBe('links.raketa.co.uk');
  });

  it.each([
    'https://raketa.app',
    'raketa.app/join',
    'raketa.app:443',
    'Raketa.app',
    'localhost',
    'raketa',
    '192.168.1.20',
    '-raketa.app',
    'raketa..app',
    'user@raketa.app',
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
    expect(nativeLinkConfig('raketa.app').ios).toEqual({
      associatedDomains: ['applinks:raketa.app'],
    });
  });

  /**
   * One verified filter for the three pages the public site serves an in-app twin of — the paths
   * `apple-app-site-association` claims on the site's side (#526), and no others.
   */
  it('claims the three pages on Android, verified, over https only', () => {
    expect(nativeLinkConfig('raketa.app').android).toEqual({
      intentFilters: [
        {
          action: 'VIEW',
          autoVerify: true,
          data: [
            { scheme: 'https', host: 'raketa.app', pathPrefix: '/join/' },
            { scheme: 'https', host: 'raketa.app', pathPrefix: '/invite/' },
            { scheme: 'https', host: 'raketa.app', pathPrefix: '/reset/' },
          ],
          category: ['BROWSABLE', 'DEFAULT'],
        },
      ],
    });
  });

  it('knows exactly three pages', () => {
    expect(LINK_PAGES).toEqual(['join', 'invite', 'reset']);
  });
});

describe('the address a link is spelled at', () => {
  it("is the app's own scheme while there is no domain", () => {
    expect(appLinkTo('join', 'k7pq2mxa', null)).toBe('raketa://join/k7pq2mxa');
  });

  it('is the web domain once there is one', () => {
    expect(appLinkTo('join', 'k7pq2mxa', 'raketa.app')).toBe('https://raketa.app/join/k7pq2mxa');
  });
});
