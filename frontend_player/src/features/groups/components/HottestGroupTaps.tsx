/**
 * **What a Groups heating up card's taps do** — on Home's line and on the Groups heating up page alike
 * ([#800](https://github.com/Raketa02/Raketa/issues/800), [#823](https://github.com/Raketa02/Raketa/issues/823);
 * ADR-0205 §7: *a tile opens the same group sheet, and the chips behave as on Home*).
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
 * once — on the line and on the page, wherever it was tapped — lands the server's answer over it, and
 * reads again every row and read that could show the group. A tap on a card whose write is still in
 * flight is let go: the chip already says what it did.
 *
 * ## One sheet
 *
 * The group sheet and the withdraw sheet are one `BottomSheet` whose title, button and body swap
 * (`HottestGroupSheet`'s note). It draws the card **as the read now has it**, so a write or a re-read
 * moves the sheet with the card; a card the re-read dropped closes it. Each surface keeps its own: the
 * page's sheet over the page, the line's over Home.
 */

import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';

import { BottomSheet } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import type { GroupAction } from '../domain/groupRules';
import { isJoinTap, sheetButton, type SheetButton } from '../domain/hottest';
import {
  useJoinGroup,
  useRelationWritesInFlight,
  useWithdrawJoinRequest,
} from '../hooks/useGroupWrites';

import { groupRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { closeGroupLabel, waitingFor } from './groupsPresentation';
import { GroupSheetBody, SheetAct, WithdrawBody } from './HottestGroupSheet';

const HOT = GROUPS_COPY.hottest;

/** Which face the one sheet shows, and for which card. */
interface SheetShown {
  readonly face: 'group' | 'withdraw';
  readonly groupId: string;
}

export interface HottestTaps {
  /** Anywhere on a card but its chip: the group sheet. */
  readonly openSheet: (groupId: string) => void;
  /** A card's chip, by what it offers. */
  readonly chip: (group: HottestGroup, action: GroupAction) => void;
  /** The one sheet, drawn beside the cards. */
  readonly sheet: ReactNode;
  /** Whether it is up — a page steps back from a screen reader while it is. */
  readonly sheetUp: boolean;
}

/** `groups` is the read as it now stands — the sheet draws its card from it. */
export function useHottestTaps(groups: readonly HottestGroup[]): HottestTaps {
  const join = useJoinGroup();
  const withdraw = useWithdrawJoinRequest();
  const [shown, setShown] = useState<SheetShown>();
  const [open, setOpen] = useState(false);

  // The cards whose write is in flight — their chips are let go until each lands.
  const writing = useRelationWritesInFlight();
  const onSheet = groups.find((group) => group.id === shown?.groupId);
  // A read that dropped the card closed its sheet — for good: a later read bringing the card back
  // must not open it again under a reader who tapped nothing (`usePersonSheet`'s rule).
  if (open && shown !== undefined && onSheet === undefined) setOpen(false);

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

  const sheet =
    onSheet === undefined || shown === undefined ? null : (
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
    );

  return {
    openSheet: (groupId) => show('group', groupId),
    chip: act,
    sheet,
    sheetUp: open && onSheet !== undefined,
  };
}
