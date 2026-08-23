/**
 * The departure feature's only public surface.
 *
 * `src/app/` may import from here and from nowhere else inside this folder —
 * ESLint blocks the deep paths. Anything not re-exported below is an internal
 * detail this feature is free to change.
 *
 * It is deliberately two things: the screen, and the parser for the one param its
 * route carries. There is no hook here and no query key, because nothing else
 * reaches this screen's data — an action that needed to correct it would be an
 * action on the same match, and the only one is this screen's own write.
 *
 * **Now is imported, never the other way round.** This feature reads Now's
 * vocabulary — the spine, the situation table, the countdown — and hands Now the
 * update the write returns. Now knows nothing about departures beyond a boolean on
 * a card and a route to push, which is what keeps the coupling one-directional and
 * a URL wide.
 */

export { DepartureScreen, type DepartureScreenProps } from './components/DepartureScreen';
export { parseDepartureRouteParams, type DepartureRouteParams } from './schemas/routeParams';
