/**
 * One screen per tab, each as thin as the tab behind it is empty.
 *
 * Five named components rather than one taking a `tab` prop: a route file's whole job is to
 * say which screen a path is, and `<AroundScreen />` says it where `<TabScreen tab="around"
 * />` makes the route file hold the answer as data. One of the five is not a placeholder in
 * the same way, and that is the other reason — You still carries the account panel.
 */

import { AccountPanel } from '@/features/auth/types';

import { PlaceholderScreen } from './PlaceholderScreen';
import { FIND_A_GAME_COPY, PLACEHOLDER_COPY } from './shellCopy';

/** The landing, after onboarding and after a send. Never says nothing is happening. */
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
 * shell arriving is what gives it a home rather than a reason to disappear. The line above it
 * is still the citation — the profile, the radius and the week are what this tab becomes, and
 * none of the three is editable here yet.
 */
export function YouScreen() {
  return (
    <PlaceholderScreen copy={PLACEHOLDER_COPY.you}>
      <AccountPanel />
    </PlaceholderScreen>
  );
}

/**
 * Play's entry, stubbed until [#268](https://github.com/Raketa02/Raketa/issues/268).
 *
 * **No back control of its own**, and that is the ticket's rule rather than an omission: *back
 * from Find a game leaves Play entirely* is a fact about the **stack** — Now is underneath,
 * put there by the reset — so the platform's own back already lands where it should, and the
 * bar is on screen either way. Whether the built screen wants a chevron beside that is #268's
 * to decide with the real header in front of it.
 */
export function FindAGameScreen() {
  return <PlaceholderScreen copy={FIND_A_GAME_COPY} />;
}
