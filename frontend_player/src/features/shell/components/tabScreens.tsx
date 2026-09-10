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
import { PlayIntentsSection } from '@/features/player_profile/types';

import { PlaceholderScreen } from './PlaceholderScreen';
import { PLACEHOLDER_COPY } from './shellCopy';

/**
 * The landing, after onboarding and after a send. Never says nothing is happening.
 *
 * **It carries nothing but its own line, and that is current rather than permanent.** A games
 * list was composed here while the result conversation had no other door
 * ([#314](https://github.com/Raketa02/Raketa/issues/314)), and the card asking how the other
 * players were sat above it ([#386](https://github.com/Raketa02/Raketa/issues/386)). Both are
 * off the tab now: **Now is not built**, and the two sections were standing in for a screen
 * whose shape has not been decided — *what is happening today and next* is a different thing
 * from a list of every game you have ever played.
 *
 * **Neither is deleted, and that is the point of taking them off rather than out.**
 * `GamesSection`, `ResultScreen` and the card at the foot of it are built, tested and
 * unreferenced, waiting for the flow that will own them. What that costs today is that the
 * result conversation has **no door in the app at all** — its route still resolves, so the
 * suites that walk it push it directly, and nothing a player can tap reaches it.
 */
export function NowScreen() {
  return <PlaceholderScreen copy={PLACEHOLDER_COPY.now} />;
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
