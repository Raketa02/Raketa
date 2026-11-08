/**
 * The rankings feature's only public surface ([#775](https://github.com/Raketa02/Raketa/issues/775);
 * [ADR-0203](../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)).
 *
 * A ranking per sport, sorted by the level: Home's trophy and the Rankings page. Every place, chip and
 * gap is the server's; what this feature owns is the page — which sport it is on, its words, and how
 * the card, the podium and the list are drawn.
 */

/** **The Rankings page** — `/rankings`, pushed over Home. */
export { RankingsScreen, type RankingsScreenProps } from './components/RankingsScreen';

/** **The trophy left of Home's bell** — the shell places it. */
export { RankingTrophy } from './components/RankingTrophy';

/**
 * **Where Rankings is** — for the trophy, and for the entry gate landing a pass that began on
 * Rankings' *Get your {sport} level* back on that sport.
 */
export { RANKINGS_PATH, rankingsRoute } from './components/rankingsRoutes';

/** The route's params, untrusted until read here. */
export { parseRankingsParams, type RankingsParams } from './schemas/routeParams';
