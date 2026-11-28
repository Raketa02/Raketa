/**
 * **One of the reader's groups' tiles, by its id** — the Add friends sheet's
 * ([#754](https://github.com/Rakieta02/Rakieta/issues/754); the friends screens §5; friends 4).
 *
 * The sheet's read (`friends`' `GET /friends/groups`) names each group and counts who is left to add,
 * and carries no tile: **the letters are cut once, by the server** (ADR-0183 §5), and the player's
 * own Groups list already holds them. So this draws the tile off that list — `useMyGroups`, one
 * key, usually already read by Play — and `friends` is handed it by the shell, since `groups` draws
 * `friends`' pills on Members and the other way round would be a dependency both ways.
 *
 * **Until the list is in, or for a group it no longer holds, the tile's box is held empty**, so the
 * name beside it never moves when the letters arrive. Decoration either way: the name is drawn and
 * spoken beside it (`GroupMonogram`'s note).
 */

import { View } from 'react-native';

import { theme } from '@/shared/ui';

import { useMyGroups } from '../hooks/useGroups';

import { GroupMonogram, type MonogramSize } from './GroupMonogram';

export interface MyGroupMonogramProps {
  readonly groupId: string;
  readonly size: MonogramSize;
}

export function MyGroupMonogram({ groupId, size }: MyGroupMonogramProps) {
  const group = useMyGroups().data?.find((one) => one.id === groupId);
  if (group !== undefined) return <GroupMonogram monogram={group.monogram} size={size} />;
  const side = theme.size.monogram[size];
  return <View style={{ width: side, height: side }} />;
}
