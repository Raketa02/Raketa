/**
 * The rankings feature's only public surface ([#775](https://github.com/Rakieta02/Rakieta/issues/775);
 * [ADR-0203](../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)).
 *
 * A ranking per sport, sorted by the level: Home's trophy, Home's Top 10 and the Rankings page. Every place, chip and
 * gap is the server's; what this feature owns is the page — which sport it is on, its words, and how
 * the card, the podium and the list are drawn.
 */

/** **The Rankings page** — `/rankings`, pushed over Home. */
export { RankingsScreen, type RankingsScreenProps } from './components/RankingsScreen';

/** **The trophy left of Home's bell** — the shell places it. */
export { RankingTrophy, type RankingTrophyProps } from './components/RankingTrophy';

/**
 * **Top 10, the last of FOR YOU's lines** (#805, #820) — the shell folds it under Players with your
 * vibe, `undefined` while hidden, and reads it again on Home's pull (`rereadTopTen`).
 */
export { useTopTenLine } from './components/TopTenLine';
export { rereadTopTen } from './hooks/useTopTen';
/** **Whether Top 10's read has finished** (#871) — behind its opening sport — for the shell's reveal. */
export { useTopTenFinished } from './hooks/useTopTen';
/** **Top 10, set out before Home is drawn, its chain included** (#874) — the shell's warm-up. */
export { prefetchTopTen } from './hooks/useTopTen';

/**
 * **Where Rankings is** — for the trophy, and for the entry gate landing a pass that began on
 * Rankings' *Get your {sport} level* back on that sport.
 */
export { RANKINGS_PATH, rankingsRoute } from './components/rankingsRoutes';

/** The route's params, untrusted until read here. */
export { parseRankingsParams, type RankingsParams } from './schemas/routeParams';
