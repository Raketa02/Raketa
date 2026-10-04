/**
 * **The handover sheet** — a club telling this account it made it the administrator of a group
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
 * §2, #529 N5–N7), as the invitation sheet tells it a club wants it to run its groups.
 *
 * **It is offered whenever the account's own read lists a handover it has not been told about** —
 * the server's fact, recorded on the group, so a phone that showed it and a phone that did not
 * agree once either has. One club at a time, with every group that club handed (`nextHandoverNotice`).
 * Mounted where the invitation sheet is — over the player's app and over every administrator area —
 * and **it waits while an invitation is on offer**, which asks something of the person; this only
 * tells.
 *
 * **Nothing is asked, so there is nothing to decline.** The one choice is where to go: **Open the
 * group** (the page, where the queue it came with waits), or **See your groups** when several came
 * at once — switching to that club's profile first, as the switcher would — or **Got it**, the
 * close and a swipe, which stay where the person is. **Every way out says it was seen**: a sheet
 * that came back after *Got it* would be asking a question it never put.
 *
 * **It appears without the app being sent away and back**: the read it draws from is followed while
 * the account runs a club's groups (`useFollowedAccount`, every half minute in the foreground).
 */

import { useQueryClient } from '@tanstack/react-query';
import { router, usePathname } from 'expo-router';
import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useFollowedAccount, useKeepProfile, type ProfileChoice } from '@/features/auth/types';
import { ClubTile } from '@/features/groups/types';
import { BottomSheet, Button, theme } from '@/shared/ui';

import { nextHandoverNotice, type HandoverNotice } from '../domain/handovers';
import { administratorKeys } from '../hooks/administratorKeys';
import { useNoteHandoversSeen } from '../hooks/useHandovers';
import { useHandoversClosed } from '../store/handoversClosed.store';
import { useInvitationsSetAside } from '../store/invitationsSetAside.store';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { handoverBody, handoverTitle, handoverWaiting } from './administratorPresentation';
import { administratorHome, officialGroupRoute } from './administratorRoutes';
import { openAreaTab } from './areaNavigation';

const COPY = ADMINISTRATOR_COPY.handover;

export interface HandoverSheetProps {
  /** The profile the screen under the sheet belongs to — where *Open* switches from, if anywhere. */
  readonly worn: ProfileChoice;
}

export function HandoverSheet({ worn }: HandoverSheetProps) {
  const user = useFollowedAccount();
  const closed = useHandoversClosed((state) => state.closed);
  const closeThem = useHandoversClosed((state) => state.close);
  const setAside = useInvitationsSetAside((state) => state.setAside);
  const seen = useNoteHandoversSeen();
  const keep = useKeepProfile();
  const pathname = usePathname();
  const client = useQueryClient();

  const profiles = user.data?.profiles;
  // An invitation asks; this only tells — so it waits for the invitation sheet to be answered.
  const inviting =
    profiles?.pendingInvitations.some(
      (invitation) => !setAside.includes(invitation.administratorId),
    ) ?? false;
  const notice =
    profiles === undefined || inviting ? undefined : nextHandoverNotice(profiles.handovers, closed);

  // The club's Groups tab was read before the group was its: read it again, so the card is there.
  const told = notice?.groups.map((group) => group.groupId).join(',');
  const toldAt = notice?.clubId;
  useEffect(() => {
    if (toldAt === undefined) return;
    void client.invalidateQueries({ queryKey: administratorKeys.groups(toldAt) });
  }, [client, told, toldAt]);

  const close = (it: HandoverNotice) => {
    closeThem(it.groups.map((group) => group.groupId));
    seen.mutate(it);
  };

  const open = (it: HandoverNotice) => {
    close(it);
    const there = worn.kind === 'administrator' && worn.clubId === it.clubId;
    if (there) {
      openAreaTab(it.clubId, 'groups', pathname);
    } else {
      // The switcher's move: the phone keeps the club's profile, and the app goes to its Groups.
      keep({ kind: 'administrator', clubId: it.clubId });
      router.replace(administratorHome(it.clubId));
    }
    const [only] = it.groups;
    if (it.groups.length === 1 && only !== undefined) {
      router.push(officialGroupRoute(it.clubId, only.groupId));
    }
  };

  const waiting = notice === undefined ? undefined : handoverWaiting(notice.groups);

  return (
    <BottomSheet
      visible={notice !== undefined}
      onClose={() => {
        if (notice !== undefined) close(notice);
      }}
      title={notice === undefined ? '' : handoverTitle(notice.clubName, notice.groups)}
      closeLabel={COPY.close}
      mark={notice === undefined ? undefined : <ClubTile clubName={notice.clubName} size="card" />}
    >
      {notice === undefined ? null : (
        <>
          <Text style={s.body}>{handoverBody(notice.groups)}</Text>
          {waiting === undefined ? null : <Text style={s.waiting}>{waiting}</Text>}
          <View style={s.actions}>
            <Button
              label={notice.groups.length === 1 ? COPY.openGroup : COPY.openGroups}
              variant="dark"
              size="lg"
              onPress={() => open(notice)}
            />
            <Button
              label={COPY.gotIt}
              variant="secondary"
              size="lg"
              onPress={() => close(notice)}
            />
          </View>
        </>
      )}
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  waiting: { ...theme.type.tiny, color: theme.color.ink, textAlign: 'center' },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
