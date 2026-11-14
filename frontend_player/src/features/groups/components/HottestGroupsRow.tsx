/**
 * **HOTTEST GROUPS** — the first of Home's five rows, just below *Your games*
 * ([#800](https://github.com/Raketa02/Raketa/issues/800); ADR-0204 §3; the Home rows screens §3; the
 * mechanics §5; home rows 1, 21).
 *
 * Up to six cards on Home's row frame (`HomeRow`, `HomeRowRail`, #798), **peeking**, in the read's
 * order — HOTTEST, then GROWING, then untagged — and **no See all**. **Hidden with its heading** while
 * the read holds nothing, is in flight, or failed (the screens §1: a row that fails is left out, and
 * the rest of Home stands).
 *
 * ## The taps
 *
 * | | |
 * | --- | --- |
 * | the card | the group sheet |
 * | **Join** | a member at once — the chip reads *You're in* |
 * | **Ask to join** | a request at once — *Asked* |
 * | **Asked** | the withdraw sheet |
 * | **You're in** | the group's page |
 *
 * The sheet's one button does the same, and *Open group* closes the sheet as it opens the page.
 * **The writes are the feature's** (`useJoinGroup`, `useWithdrawJoinRequest`): each draws the card at
 * once, lands the server's answer over it, and reads again every row and read that could show the
 * group. A tap on a card whose write is still in flight is let go: the chip already says what it did.
 *
 * ## One sheet
 *
 * The group sheet and the withdraw sheet are one `BottomSheet` whose title, button and body swap
 * (`HottestGroupSheet`'s note). It draws the card **as the read now has it**, so a write or a re-read
 * moves the sheet with the card; a card the re-read dropped closes it.
 */

import { router } from 'expo-router';
import { useState } from 'react';

import { BottomSheet, HomeRow, HomeRowRail } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import type { GroupAction } from '../domain/groupRules';
import { isJoinTap, sheetButton, type SheetButton } from '../domain/hottest';
import {
  useJoinGroup,
  useRelationWritesInFlight,
  useWithdrawJoinRequest,
} from '../hooks/useGroupWrites';
import { useHottestGroups } from '../hooks/useHottestGroups';

import { groupRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { closeGroupLabel, waitingFor } from './groupsPresentation';
import { HottestGroupCard } from './HottestGroupCard';
import { GroupSheetBody, SheetAct, WithdrawBody } from './HottestGroupSheet';

const HOT = GROUPS_COPY.hottest;

export function HottestGroupsRow() {
  const groups = useHottestGroups().data;
  if (groups === undefined || groups.length === 0) return null;
  return <HottestGroups groups={groups} />;
}

/** Which face the one sheet shows, and for which card. */
interface SheetShown {
  readonly face: 'group' | 'withdraw';
  readonly groupId: string;
}

function HottestGroups({ groups }: { readonly groups: readonly HottestGroup[] }) {
  const join = useJoinGroup();
  const withdraw = useWithdrawJoinRequest();
  const [shown, setShown] = useState<SheetShown>();
  const [open, setOpen] = useState(false);

  // The cards whose write is in flight — their chips are let go until each lands.
  const writing = useRelationWritesInFlight();
  const onSheet = groups.find((group) => group.id === shown?.groupId);

  function show(face: SheetShown['face'], groupId: string) {
    setShown({ face, groupId });
    setOpen(true);
  }

  function act(group: HottestGroup, action: GroupAction | SheetButton) {
    if (writing.includes(group.id)) return;
    if (isJoinTap(action)) {
      join.mutate(group.id);
      return;
    }
    switch (action) {
      case 'requested':
        show('withdraw', group.id);
        return;
      case 'in':
      case 'open':
        setOpen(false);
        router.push(groupRoute(group.id));
        return;
    }
  }

  function withdrawRequest(groupId: string) {
    setOpen(false);
    withdraw.mutate(groupId);
  }

  return (
    <HomeRow heading={HOT.heading} testID="hottest-groups">
      <HomeRowRail cards={groups}>
        {(group, width) => (
          <HottestGroupCard
            key={group.id}
            group={group}
            width={width}
            onOpen={() => show('group', group.id)}
            onChip={(action) => act(group, action)}
          />
        )}
      </HomeRowRail>

      {onSheet === undefined || shown === undefined ? null : (
        // One element for both faces: swapping two would close one native window as the next opens.
        <BottomSheet
          visible={open}
          onClose={() => setOpen(false)}
          {...(shown.face === 'group'
            ? {
                title: onSheet.name,
                closeLabel: closeGroupLabel(onSheet.name),
                action: (
                  <SheetAct
                    button={sheetButton(onSheet)}
                    groupName={onSheet.name}
                    onPress={(button) => act(onSheet, button)}
                  />
                ),
              }
            : { title: waitingFor(onSheet.runBy), closeLabel: HOT.keepRequest })}
        >
          {shown.face === 'group' ? (
            <GroupSheetBody group={onSheet} />
          ) : (
            <WithdrawBody onWithdraw={() => withdrawRequest(onSheet.id)} />
          )}
        </BottomSheet>
      )}
    </HomeRow>
  );
}
