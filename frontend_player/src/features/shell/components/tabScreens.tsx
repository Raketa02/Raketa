/**
 * One screen per tab — **four of them**, each as thin as the tab behind it is empty.
 *
 * Four named components rather than one taking a `tab` prop: a route file's whole job is to
 * say which screen a path is, and `<AroundScreen />` says it where `<TabScreen tab="around"
 * />` makes the route file hold the answer as data. One of the four is not a placeholder in
 * the same way, and that is the other reason — You still carries the account panel.
 *
 * **Play is not here at all any more.** Its stub was a fifth entry until
 * [#268](https://github.com/Raketa02/Raketa/issues/268) built the screen; the route now names
 * `features/play`'s own, which is what the file tree should say about a tab that exists.
 */

import { AccountPanel } from '@/features/auth/types';
import { GamesSection } from '@/features/games/types';
import { PlayIntentsSection } from '@/features/player_profile/types';

import { PlaceholderScreen } from './PlaceholderScreen';
import { PLACEHOLDER_COPY } from './shellCopy';

/**
 * The landing, after onboarding and after a send. Never says nothing is happening.
 *
 * **The games list is the first thing built on it** ([#314](https://github.com/Raketa02/Raketa/issues/314)),
 * composed under the tab's own line the way `PlayIntentsSection` is on You: a game is *what is
 * happening today and next*, and the result conversation had no door without one. The line above
 * it stays exactly as it is — what Now becomes is still mostly owed — and the section draws
 * nothing at all when there are no games, because asserting emptiness is the one thing this tab
 * has refused to do since it was built.
 */
export function NowScreen() {
  return (
    <PlaceholderScreen copy={PLACEHOLDER_COPY.now}>
      <GamesSection />
    </PlaceholderScreen>
  );
}

export function AroundScreen() {
  return <PlaceholderScreen copy={PLACEHOLDER_COPY.around} />;
}

export function ChatsScreen() {
  return <PlaceholderScreen copy={PLACEHOLDER_COPY.chats} />;
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
