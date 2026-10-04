/**
 * **The way in, as a page draws it**: Raketa's two store listings, and the app itself at one of
 * its own routes. All three come from settings (ADR-0187 §7), and reach a page as addresses.
 */
export interface AppLinks {
  readonly appStore: string;
  readonly googlePlay: string;
  /** `<APP_SCHEME>://<route>`, which the app opens at that route (#520). */
  readonly openInRaketa: string;
}

/**
 * **The routes the app and this site both answer**, `<segment>/<code or token>`: this site serves
 * each as a page, the app opens each after its scheme (#520), and Apple's association file claims
 * them for the app. Written once, here; `src/app/` spells the same segments as folders.
 */
export const APP_ROUTES = { group: 'join', invitation: 'invite', reset: 'reset' } as const;

export type AppRoute = keyof typeof APP_ROUTES;

/**
 * `join/<code>`, `invite/<token>`, `reset/<token>`. **The id is the caller's to make safe**: only
 * one already known to be a code or a token is put into a route.
 */
export function appRoute(route: AppRoute, id: string): string {
  return `${APP_ROUTES[route]}/${id}`;
}
