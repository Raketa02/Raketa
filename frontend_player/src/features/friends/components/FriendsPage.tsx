/**
 * **The Friends page** — one page, two modes ([#754](https://github.com/Raketa02/Raketa/issues/754),
 * PRD #743 stories 34–41; the friends screens §4; friends 3).
 *
 * ```
 * ‹  Friends                       [+ Add friends]     friends 3's header, both modes
 * ──────────────────────────────────────────────
 *    the body: the three tabs from You (FriendsTabs),
 *    or the picker from a group's Friends tab (#757)
 * ──────────────────────────────────────────────
 *    the foot: nothing from You; the picker's Done (#757)
 * ```
 *
 * ## The frame is the page; the mode is its body
 *
 * **From You** it holds three tabs (`FriendsTabs`); **from a group's Friends tab** it is a picker
 * with no tabs and **Done** at its foot (§4.2, #757). What the two share is this: the header — back,
 * *Friends*, and **+ Add friends** top right, the black pill friends 3 draws — and the **Add friends**
 * sheet the pill opens. So the page is a frame that takes its body (`children`) and its foot
 * (`action`), and #757 hands it the picker and *Done* without touching either.
 *
 * **No eyebrow**: the header is friends 3's in both modes (§4.1), so a page shared with a group's
 * court does not wear the You tab's group title. **A pull re-reads every list on it** — this
 * feature's own keys, which every friends write re-reads too.
 *
 * ## What the composer hands in
 *
 * The record a row opens (`player_record`'s, which draws this feature's button), the groups' tiles
 * and the way into Members (`groups'`, which draws this feature's pills): the shell composes them,
 * as it composes Home's request cards, so this feature imports neither. `behind` hides the page from
 * a screen reader while the composer's record is up; the sheet's own is this frame's.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { ShellScreen } from '@/features/shell/types';
import { Button, behindOverlay } from '@/shared/ui';

import { friendKeys } from '../hooks/friendKeys';

import { AddFriendsSheet, type GroupDoors } from './AddFriendsSheet';
import { FRIENDS_COPY } from './friendsCopy';

const COPY = FRIENDS_COPY.page;

export interface FriendsPageProps {
  readonly onBack: () => void;
  /** The Add friends sheet's tiles and its door into Members — `groups'`, handed in. */
  readonly groups: GroupDoors;
  /** The mode: the three tabs from You, or the picker (#757). */
  readonly children: ReactNode;
  /** Pinned under the page — the picker's *Done* (#757). Nothing from You. */
  readonly action?: ReactNode;
  /** The composer's overlay (the record) is up over the page. */
  readonly behind?: boolean;
}

export function FriendsPage({
  onBack,
  groups,
  children,
  action,
  behind = false,
}: FriendsPageProps) {
  const client = useQueryClient();
  const [adding, setAdding] = useState(false);

  return (
    <>
      <View style={s.root} {...behindOverlay(adding || behind)}>
        <ShellScreen
          title={COPY.title}
          onBack={onBack}
          right={
            <Button
              label={COPY.add}
              accessibilityLabel={COPY.addLabel}
              variant="dark"
              size="sm"
              shape="pill"
              onPress={() => setAdding(true)}
            />
          }
          {...(action === undefined ? {} : { action })}
          onRefresh={() => client.invalidateQueries({ queryKey: friendKeys.all })}
        >
          {children}
        </ShellScreen>
      </View>

      <AddFriendsSheet visible={adding} onClose={() => setAdding(false)} groups={groups} />
    </>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
});
