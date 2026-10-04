/**
 * **The links into the app, as configuration** — the app's scheme, the three pages a link opens, and
 * the one setting that turns the web domain's links on
 * ([#520](https://github.com/Raketa02/Raketa/issues/520),
 * [ADR-0187](../../../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
 * §4, §7).
 *
 * A group link in WhatsApp, the invitation email's button and the reset email's link are the public
 * site's pages `join/<code>`, `invite/<token>` and `reset/<token>`. On a phone with Raketa installed
 * the same three open the app — by its own scheme today, and by the web domain once one exists, when
 * iOS and Android are told the domain is the app's (universal links, verified app links). **Which
 * domain is a setting, `EXPO_PUBLIC_LINK_DOMAIN`, and none is set anywhere yet**, so the associated
 * domain and the intent filter are simply absent: nothing is claimed that no site could back.
 *
 * **This module imports nothing at runtime**, for `appIdentity`'s reason: `app.config.ts` loads it
 * in Node, before Metro, to tell the native project about the domain, and `env.ts` loads it inside
 * the app to validate the same variable. One reading of the variable for both runtimes, so the
 * binary and the running app cannot disagree about which links are the app's.
 */

/**
 * **One scheme, at every environment** — `app.config.ts`'s `scheme`, and the address every link
 * uses while no domain is set. Per-environment schemes wait for per-environment identifiers.
 */
export const APP_SCHEME = 'raketa';

/** **The three pages a link opens in the app**, by their first path segment on the public site. */
export const LINK_PAGES = ['join', 'invite', 'reset'] as const;

export type LinkPage = (typeof LINK_PAGES)[number];

/** The variable, named once for the refusal and the template. */
const VARIABLE = 'EXPO_PUBLIC_LINK_DOMAIN';

/** **The rule, in one wording** — said after the variable's name here and in `env.ts`'s refusal. */
export const LINK_DOMAIN_RULE =
  'must be a bare lower-case host name — no scheme, port or path — or be empty';

/**
 * A bare host name, lower case, of at least two labels ending in letters — what an Apple
 * `applinks:` entry and an Android intent filter's `host` both take. No scheme, port, path or user,
 * and no address: a universal link is a domain's, and an IP or `localhost` is nobody's.
 */
const HOST = /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;

/**
 * **The link domain, read** — `null` while nothing is set, which is every environment today.
 *
 * A value that is not a bare host name refuses, naming the variable and **never its value**, the
 * rule `env.ts` keeps for every setting: config lands in logs and CI output. A refusal rather than a
 * fallback to *off*, because a domain someone meant to set and mistyped would ship a build whose
 * links silently open the browser, and nothing would say why.
 */
export function readLinkDomain(raw: string | undefined): string | null {
  const value = raw?.trim() ?? '';
  if (value === '') return null;
  if (!HOST.test(value)) {
    throw new Error(`${VARIABLE} ${LINK_DOMAIN_RULE}. Copy .env.example to .env.local and set it.`);
  }
  return value;
}

/**
 * One of Android's intent filters, in the shape `app.config.ts`'s `android.intentFilters` takes —
 * spelled here rather than imported so this module stays free of `expo/config`. The arrays are
 * mutable because `ExpoConfig`'s are, and each call builds a fresh object.
 */
export interface LinkIntentFilter {
  readonly action: 'VIEW';
  readonly autoVerify: true;
  readonly data: { readonly scheme: 'https'; readonly host: string; readonly pathPrefix: string }[];
  readonly category: ['BROWSABLE', 'DEFAULT'];
}

export interface NativeLinkConfig {
  readonly ios: { readonly associatedDomains?: string[] };
  readonly android: { readonly intentFilters?: LinkIntentFilter[] };
}

/**
 * **What iOS and Android are told about the domain** — nothing while there is none.
 *
 * Once set: iOS associates the domain (`applinks:`), and Android gets one **verified** filter for
 * the three pages over `https`, so a tap on the site's link opens the app without a chooser. The
 * site's half is #526's: Apple's association file claims the same three paths, and Android's asset
 * links name this package. The scheme needs no filter of its own — Expo registers `raketa://` from
 * the config's `scheme` — and it opens every path, which is why the app reads every link it is
 * handed before trusting it (`+native-intent`).
 */
export function nativeLinkConfig(domain: string | null): NativeLinkConfig {
  if (domain === null) return { ios: {}, android: {} };

  return {
    ios: { associatedDomains: [`applinks:${domain}`] },
    android: {
      intentFilters: [
        {
          action: 'VIEW',
          autoVerify: true,
          data: LINK_PAGES.map((page) => ({
            scheme: 'https' as const,
            host: domain,
            pathPrefix: `/${page}/`,
          })),
          category: ['BROWSABLE', 'DEFAULT'],
        },
      ],
    },
  };
}

/**
 * **The address a link to one of the pages is spelled at** — the web domain's once there is one,
 * the app's scheme until then. It is what a link the app received reads as when the app shows it,
 * rebuilt from the parts it checked rather than echoed as it arrived.
 */
export function appLinkTo(page: LinkPage, value: string, domain: string | null): string {
  return domain === null
    ? `${APP_SCHEME}://${page}/${value}`
    : `https://${domain}/${page}/${value}`;
}
