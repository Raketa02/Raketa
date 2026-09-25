/**
 * **The group page's dark card** — a headline, what the app is waiting for, and the link's two
 * doors under it (play 14–17, 39, 45, 54–55). Games, Fill in and the Friends screen each draw one
 * while a group is starting, because at that stage every tab has the same remedy: send the link.
 *
 * `children` stand between the headline and the line — the Games card's seats. The line is
 * optional because one state has nothing to wait for (*Nothing picked right now*).
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text } from 'react-native';

import { DarkCard, theme } from '@/shared/ui';

import type { Group } from '../domain/group';

import { GroupLinkActions } from './GroupLinkActions';

export interface LinkCardProps {
  readonly group: Pick<Group, 'name' | 'link'>;
  readonly headline: string;
  /** A headline that is a figure — *3 of 4* — is drawn in mono, as every count is (1.4). */
  readonly headlineIsCount?: boolean;
  readonly line?: string;
  readonly children?: ReactNode;
}

export function LinkCard({
  group,
  headline,
  headlineIsCount = false,
  line,
  children,
}: LinkCardProps) {
  return (
    <DarkCard style={s.card}>
      <Text style={headlineIsCount ? s.count : s.headline}>{headline}</Text>
      {children}
      {line === undefined ? null : <Text style={s.line}>{line}</Text>}
      <GroupLinkActions group={group} />
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { alignItems: 'center', gap: theme.space.md },
  // 3.3: `h2` titles a card.
  headline: { ...theme.type.h2, color: theme.color.surface, textAlign: 'center' },
  count: { ...theme.num.m, ...theme.tabular, color: theme.color.surface, textAlign: 'center' },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
});
