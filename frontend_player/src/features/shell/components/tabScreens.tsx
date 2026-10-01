/**
 * The screens the shell composes under a tab's own words — **one of them here now**, and none
 * of them a placeholder.
 *
 * Named components rather than one taking a `tab` prop: a route file's whole job is to say
 * which screen a path is, and `<HomeScreen />` says it where `<TabScreen tab="now" />` makes
 * the route file hold the answer as data.
 *
 * **Every tab has left the placeholder table.** Play's stub was an entry until
 * [#268](https://github.com/Raketa02/Raketa/issues/268) built the screen, Chats' until
 * [#360](https://github.com/Raketa02/Raketa/issues/360) built the inbox, Now's until
 * [#367](https://github.com/Raketa02/Raketa/issues/367) built the rail, and You's until
 * [ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * built the tab — the last of them, and the table went with it. Three are still the shell's,
 * because each is a composition of other features' surfaces under the tab's own words: Now
 * below, and Chats and You in files of their own because neither is thin. **Around's entry
 * retired with the tab**: the deck moved in as Players
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1), and that screen is `features/play`'s own, named by its route file exactly as Find a game
 * is — the tab has no words of its own for the shell to compose anything under.
 */

import { GamesRail } from '@/features/plans/types';
import { PaymentsToConfirm, useBookedCards } from '@/features/proposals/types';

import { ShellScreen } from './ShellScreen';
import { HOME_COPY } from './shellCopy';

/**
 * **Home — the landing, after onboarding and after a send — and it stopped being a placeholder
 * here** ([#367](https://github.com/Raketa02/Raketa/issues/367)). It was **Now** until
 * [#550](https://github.com/Raketa02/Raketa/issues/550) renamed the tab whole — key, label, copy
 * and this component — with the route staying `/`: your games from the moment they fill.
 *
 * The games list arrived under a citation first ([#314](https://github.com/Raketa02/Raketa/issues/314));
 * what replaces both is `GamesRail`, which is *what is happening today and next* drawn rather than
 * described. The tab keeps the shape it has always had — it owns its own words and nothing that is
 * drawn under them — so the empty sentences are handed down and the heading over the rail is the
 * rail's.
 *
 * **It still never says nothing is happening.** The line says what the tab **is** and the one under
 * it names the act, which is true whether or not a game is on screen.
 *
 * **The booked games ride the same rail** ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A8): `features/proposals` draws them and the rail takes them as a slot, first, so
 * Home is one rail of your games whichever loop made them. **And a payment to confirm is above it**
 * — proposals' *TO CONFIRM*, which draws nothing while there is none: the bar's Home badge counts
 * every payment the player has to confirm, and a count with nothing on the tab to answer it would
 * be a dead end.
 */
export function HomeScreen() {
  const booked = useBookedCards();
  return (
    <ShellScreen title={HOME_COPY.title}>
      <PaymentsToConfirm />
      <GamesRail empty={HOME_COPY.empty} booked={booked} />
    </ShellScreen>
  );
}
