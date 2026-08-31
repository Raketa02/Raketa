/**
 * A tab that names what belongs to it and admits it is not built.
 *
 * The whole test a placeholder has to pass is *can a player tell this from a bug* — so it
 * carries the tab's own title in the header and one sentence under it, and nothing else. No
 * spinner, no empty-state illustration, no *coming soon*: the first two would be a screen
 * pretending to be loading something, and the third is a promise nobody made.
 *
 * The line is `tiny` in `muted` — the workhorse secondary text — because the sentence is
 * about the app rather than about the player, and a placeholder that shouted would be the
 * loudest thing in a tab that does nothing.
 *
 * `children` is what is *already* built on this tab, and there is exactly one today: the You
 * tab still carries the account panel, which is the only way out of a session and predates
 * the shell by every slice.
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import { ShellScreen } from './ShellScreen';
import type { PlaceholderCopy } from './shellCopy';

export interface PlaceholderScreenProps {
  readonly copy: PlaceholderCopy;
  readonly children?: ReactNode;
}

export function PlaceholderScreen({ copy, children }: PlaceholderScreenProps) {
  return (
    <ShellScreen title={copy.title}>
      <Text style={s.line}>{copy.line}</Text>
      {children}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  line: { ...theme.type.tiny, color: theme.color.muted },
});
