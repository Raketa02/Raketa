/**
 * Where this feature's rows on the You tab lead — each a screen pushed over the tab, under
 * the tab's own first segment so the You column stays lit (`tabForPathname`).
 *
 * Spelled here, once, for the reason `yesRoute` is spelled in `challenges`: every `/you/…`
 * screen that draws one of this feature's controls is this feature's, and the row that opens
 * it and the route file that mounts it must agree on the address. The tab's root is the
 * shell's (`SHELL_TAB_ROOT.you`); these are what hangs under it.
 */

export const YOU_KIND_OF_GAME_ROUTE = '/you/kind-of-game';
export const YOU_WEEK_ROUTE = '/you/week';
export const YOU_RADIUS_ROUTE = '/you/radius';
export const YOU_AREA_ROUTE = '/you/area';
export const YOU_WHO_YOU_PLAY_WITH_ROUTE = '/you/who-you-play-with';
export const YOU_GAME_SUGGESTIONS_ROUTE = '/you/game-suggestions';
export const YOU_PHOTOS_ROUTE = '/you/photos';
export const YOU_TAGS_ROUTE = '/you/tags';
export const YOU_INTRO_ROUTE = '/you/intro';
