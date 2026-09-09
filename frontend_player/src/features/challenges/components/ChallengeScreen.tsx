/**
 * One challenge, opened from its row in the Chats inbox.
 *
 * **What this screen becomes is [#361](https://github.com/Raketa02/Raketa/issues/361)'s** — the
 * card recomputed for the reader, the standing sentence, `I'm in` and `Not this time`, and the
 * route param validated before anything trusts it. What is here is the landing the inbox row
 * needs in order to be a door at all: a row whose tap resolves to nothing is not *fully
 * clickable, opening the challenge route*, it is a row that fails silently.
 *
 * It reads **no route param**, which is why there is no schema beside it yet: nothing untrusted
 * reaches this file, and a validator with nothing to validate is a shape somebody would have to
 * keep true of a screen that had not been written.
 *
 * The path carries a static `challenge` above the id, and that is a decision rather than a style
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §0.2): a
 * challenge id and a conversation id are different ids of different things, and `/chats/[id]`
 * for both is one segment a router cannot resolve and a reader cannot read. Being under
 * `/chats` is what lights the Chats column, for free and with no change to `INSIDE_A_TAB`.
 *
 * The line wears [10.1](../../../../docs/design-system.md#101-screen-structure)'s empty-state
 * shape — one line of `tiny` in `muted`, present-tense, naming what belongs here — and it is
 * pinned in `challengePresentation.test.ts` under the same two refusals every other line in this
 * app is: it never promises a date and it never says nothing is happening.
 */

import { StyleSheet, Text } from 'react-native';

import { ShellScreen } from '@/features/shell/types';
import { theme } from '@/shared/ui';

import { CHALLENGE_SCREEN_NOT_BUILT, CHALLENGE_SCREEN_TITLE } from './challengePresentation';

export function ChallengeScreen() {
  return (
    <ShellScreen title={CHALLENGE_SCREEN_TITLE}>
      <Text style={s.line}>{CHALLENGE_SCREEN_NOT_BUILT}</Text>
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  line: { ...theme.type.tiny, color: theme.color.muted },
});
