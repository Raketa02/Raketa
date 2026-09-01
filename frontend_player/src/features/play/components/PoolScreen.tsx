/**
 * **The pool** — the full ranked list, and the one screen the relaxation ladder is on.
 *
 * It is [#272](https://github.com/Raketa02/Raketa/issues/272)'s, and what stands here until
 * then is an **honest placeholder**: one sentence naming what belongs on this screen, and that
 * it is not built. That is the shell's own pattern for the three unbuilt tabs, taken for the
 * same reason — *"so that I can tell a placeholder from a bug"*.
 *
 * **It exists now because the builder routes its remedy here.** Every seat the court states a
 * shortfall on sends the player to this screen, which is where widening is offered and where
 * the ranked list can be read; a court that named a remedy with nowhere to go would be worse
 * than one that said nothing. The two params it will read are already sent — the origin search
 * and the seat being filled — and it draws neither yet, because nothing here decides anything.
 *
 * **#272 replaces this file's body.** The route above it is final: `play/pool.tsx` names this
 * component and nothing else, so the pool arrives as one edit rather than as a route, a
 * registration and a screen.
 */

import { StyleSheet, Text } from 'react-native';

import { ShellScreen } from '@/features/shell/types';
import { Note, theme } from '@/shared/ui';

import { POOL_NOT_BUILT, POOL_TITLE } from './builderPresentation';

export function PoolScreen() {
  return (
    <ShellScreen title={POOL_TITLE}>
      <Note>
        <Text style={s.body}>{POOL_NOT_BUILT}</Text>
      </Note>
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.ink },
});
