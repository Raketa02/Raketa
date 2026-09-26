/**
 * **The invitation sheet** — a club offering an account that already exists its administrator
 * profile, on launch ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories
 * 117–119; club mocks 5–6; ADR-0184 §2, ADR-0185 §3).
 *
 * **It is offered whenever the signed-in account's own read lists an invitation this launch has not
 * set aside.** `/users/me` carries the invitations addressed to the account's email, soonest to
 * expire first, and the server stops listing one once it is accepted, removed or past its 72 hours —
 * so *it stops appearing once the invitation expires* is the read's, and the sheet never judges an
 * expiry by the phone's clock. It is mounted over each profile's home, the player's app and the
 * administrator area, and nowhere in onboarding: an invitation waits until the account is in.
 *
 * **Club 5, then club 6.** The club's tile over *Ogrody 33 wants to make you an administrator*, what
 * accepting does, **Accept** and **Not now**. Accept adds the profile (`auth`'s `useAcceptInvitation`,
 * whose answer is the account's profiles) and **the same sheet becomes the profile list**, the one
 * worn ticked — one modal changing its content, never a second presented as the first leaves. A row
 * switches there and then; the close keeps what is worn.
 *
 * **Not now, and the close, set it aside until the next launch** (`useInvitationsSetAside`, memory
 * only). An invitation that ran out while the sheet was up says so, naming the club to ask, and
 * leaves nothing to accept; a failure to reach the server keeps Accept to press again.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  useAcceptInvitation,
  useCurrentUser,
  useKeepProfile,
  type PendingInvitation,
  type ProfileChoice,
} from '@/features/auth/types';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import { profileOptions, type ProfileOption } from '../domain/profiles';
import { useInvitationsSetAside } from '../store/invitationsSetAside.store';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import {
  invitationBody,
  invitationEnded,
  invitationRefusal,
  invitationTitle,
} from './administratorPresentation';
import { useChooseProfile } from './areaNavigation';
import { ClubTile } from './ClubTile';
import { ProfileRows } from './ProfileRows';

const COPY = ADMINISTRATOR_COPY.invitation;

export interface InvitationSheetProps {
  /** The profile the screen under the sheet belongs to — the one the list ticks after Accept. */
  readonly worn: ProfileChoice;
}

export function InvitationSheet({ worn }: InvitationSheetProps) {
  const user = useCurrentUser();
  const setAside = useInvitationsSetAside((state) => state.setAside);
  const setAsideOne = useInvitationsSetAside((state) => state.setAsideOne);
  const accept = useAcceptInvitation();
  const keep = useKeepProfile();
  const chooseProfile = useChooseProfile(worn);
  // Once accepted, the sheet is the profile list — kept up though the read no longer lists the
  // invitation it began as.
  const [listing, setListing] = useState(false);

  const offered = user.data?.profiles.pendingInvitations.find(
    (invitation) => !setAside.includes(invitation.administratorId),
  );
  // **Pinned** while it is being answered: Accept's own answer drops it from the read, and the sheet
  // must go on being about it. Otherwise the sheet is about whatever the read offers.
  const [pinned, setPinned] = useState<PendingInvitation | undefined>(undefined);
  const invitation = pinned ?? offered;

  if (user.data === undefined) return null;
  const visible = listing || invitation !== undefined;

  const decideLater = () => {
    if (invitation !== undefined) setAsideOne(invitation.administratorId);
    setPinned(undefined);
    accept.reset();
  };

  const closeList = () => {
    setListing(false);
    setPinned(undefined);
  };

  const choose = (option: ProfileOption) => {
    closeList();
    chooseProfile(option);
  };

  const acceptIt = (offer: PendingInvitation) => {
    setPinned(offer);
    accept.mutate(offer.administratorId, {
      onSuccess: () => {
        // **Accepting is not switching.** The profile worn stays the one the phone remembers, so a
        // gate re-reading the account — which now holds the new club — cannot move anybody on a
        // choice left on the phone from a time the account held that club before.
        keep(worn);
        setListing(true);
      },
    });
  };

  if (listing) {
    return (
      <BottomSheet
        visible={visible}
        onClose={closeList}
        title={ADMINISTRATOR_COPY.switcher.title}
        closeLabel={ADMINISTRATOR_COPY.switcher.close}
      >
        <ProfileRows options={profileOptions(user.data)} worn={worn} onChoose={choose} />
      </BottomSheet>
    );
  }

  const ended = invitationEnded(accept.error);

  return (
    <BottomSheet
      visible={visible}
      onClose={decideLater}
      title={invitation === undefined ? '' : invitationTitle(invitation.clubName)}
      closeLabel={COPY.close}
      mark={
        invitation === undefined ? undefined : (
          <ClubTile clubName={invitation.clubName} size="card" />
        )
      }
    >
      {invitation === undefined ? null : (
        <>
          <Text style={s.body}>{invitationBody(user.data.profiles)}</Text>

          {/* Said on the sheet because nothing under it can. `alert`: it appeared unasked. */}
          {accept.error === null ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {invitationRefusal(invitation.clubName, accept.error)}
            </Note>
          )}

          <View style={s.actions}>
            {ended ? null : (
              <Button
                label={COPY.accept}
                variant="dark"
                size="lg"
                busy={accept.isPending}
                busyLabel={COPY.accepting}
                onPress={() => acceptIt(invitation)}
              />
            )}
            <Button
              label={ended ? COPY.done : COPY.notNow}
              variant="secondary"
              size="lg"
              onPress={decideLater}
            />
          </View>
        </>
      )}
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
