/**
 * One screen per tab — **two of them**, and only one is a placeholder.
 *
 * Named components rather than one taking a `tab` prop: a route file's whole job is to say
 * which screen a path is, and `<YouScreen />` says it where `<TabScreen tab="you" />` makes
 * the route file hold the answer as data. One of the two is not a placeholder in the same
 * way, and that is the other reason — You still carries the account panel.
 *
 * **Play and Players are not here; Chats and Now have both left the placeholder table.** Play's
 * stub was an entry until [#268](https://github.com/Raketa02/Raketa/issues/268) built the screen,
 * Chats' until [#360](https://github.com/Raketa02/Raketa/issues/360) built the inbox, and Now's
 * until [#367](https://github.com/Raketa02/Raketa/issues/367) built the rail. All three are still
 * the shell's, because each is a composition of other features' surfaces under the tab's own
 * words — which is what this file's remaining entries are too. **Around's entry retired with the
 * tab**: the deck moved in as Players
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1), and that screen is `features/play`'s own, named by its route file exactly as Find a game
 * is — the tab has no words of its own for the shell to compose anything under.
 */

import { AccountPanel } from '@/features/auth/types';
import { GamesRail } from '@/features/plans/types';
import { PlayIntentsSection } from '@/features/player_profile/types';

import { PlaceholderScreen } from './PlaceholderScreen';
import { ShellScreen } from './ShellScreen';
import { NOW_COPY, PLACEHOLDER_COPY } from './shellCopy';

/**
 * **The landing, after onboarding and after a send — and it stops being a placeholder here**
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)).
 *
 * The games list arrived under a citation first ([#314](https://github.com/Raketa02/Raketa/issues/314));
 * what replaces both is `GamesRail`, which is *what is happening today and next* drawn rather than
 * described. The tab keeps the shape it has always had — it owns its own words and nothing that is
 * drawn under them — so the empty sentences are handed down and the heading over the rail is the
 * rail's.
 *
 * **It still never says nothing is happening.** The line says what the tab **is** and the one under
 * it names the act, which is true whether or not a game is on screen.
 */
export function NowScreen() {
  return (
    <ShellScreen title={NOW_COPY.title}>
      <GamesRail empty={NOW_COPY.empty} />
    </ShellScreen>
  );
}

/**
 * The one tab that is not only a placeholder.
 *
 * Signing out is the account's own surface and has existed since the walking skeleton; the
 * shell arriving is what gives it a home rather than a reason to disappear.
 *
 * **The per-sport declaration is the first of the three citations to arrive**
 * ([#296](https://github.com/Raketa02/Raketa/issues/296)): `PlayIntentsSection` lists what a
 * player has declared in each sport they are rated in, and writes on the `PROFILE_SCREEN`
 * surface the contract has been holding open for it. The radius and the week are still
 * unbuilt, so the line above stays exactly as it is — it names what this tab becomes, and two
 * thirds of that is still owed.
 *
 * Both children are other features' sections composed by the shell, which is what this tab has
 * always been: it owns the citation and nothing that is drawn under it.
 */
export function YouScreen() {
  return (
    <PlaceholderScreen copy={PLACEHOLDER_COPY.you}>
      <PlayIntentsSection />
      <AccountPanel />
    </PlaceholderScreen>
  );
}
