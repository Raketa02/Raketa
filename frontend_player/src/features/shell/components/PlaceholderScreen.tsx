/**
 * A tab that names what belongs to it and admits it is not built.
 *
 * The whole test a placeholder has to pass is *can a player tell this from a bug* — so it
 * carries the tab's own title in the header and one sentence under it, and nothing else.
 *
 * **The shape of that sentence is
 * [10.1](../../../../docs/design-system.md#101-screen-structure)'s empty-state rule**: one
 * line of `tiny` in `muted`, present-tense, naming the act — no spinner, no illustration, no
 * *coming soon*, and never an assertion that nothing is happening. The argument used to live
 * here and it was promoted, because three built tabs are now writing the thing it argues
 * about while this component loses half its callers to them
 * ([#338](https://github.com/Raketa02/Raketa/issues/338) §9): an argument reachable only from
 * a component two of its readers no longer import is one that gets re-invented. This file is
 * a caller of the rule now rather than its home.
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
