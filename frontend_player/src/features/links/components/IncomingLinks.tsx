/**
 * **Where a held link is answered** — mounted over each home a signed-in account can be in: the
 * player's app, and an administrator area ([#520](https://github.com/Rakieta02/Rakieta/issues/520),
 * PRD #500 stories 46–48, 113, 117–119).
 *
 * A link is held from the moment it arrives (`redirectSystemPath`) until a place that can answer it
 * is reached, and these are those places: nothing here is drawn during sign-in or onboarding, because
 * nothing here is mounted there. What each link gets is `linkRules`'; this draws it:
 *
 * - **A group link** opens **Join a group** with the link in its field and its group found under it,
 *   over Play › Groups so *back* is the list — or, in an administrator area, switches an account that
 *   plays to Player first (`playersLinkMove`).
 * - **A friend link** (#756) is opened as the account (`friends`' opening), and lands on **Home with
 *   Needs your answer up** (#817), where its owner's request now waits — nowhere for the account's
 *   own link or a friend's; a dead link, or one whose owner the account blocked, is a toast. In an
 *   administrator area it moves as a group link does.
 * - **An invitation's link** is read (`by-token`) and weighed against the account signed in
 *   (`invitationLinkOutcome`): the account's own invitation has the invitation sheet offer that club's
 *   again; another address's gets a sheet naming it, with **Sign out**; a spent link says why.
 * - **A reset link** gets a sheet asking to sign out first — its link names no account, so the app
 *   cannot tell whether it is this one's.
 * - **The app's bare address** — the club's email to an existing account — has the invitation sheet
 *   offer every invitation set aside this launch again.
 *
 * **Sign out** on either sheet leads to the link's own screen, signed out — *Set your password* for
 * the invited address, *Set a new password* — by the token in its path. **Stay signed in** lets the
 * link go.
 */

import { useQueryClient } from '@tanstack/react-query';
import { router, usePathname } from 'expo-router';
import { useEffect, useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useOfferInvitationsAgain, useSwitchProfile } from '@/features/administrator/types';
import {
  LINK_STATE_MESSAGE,
  PLAYER_PROFILE,
  SIGN_OUT,
  authErrorMessage,
  invitationErrorMessage,
  useCurrentUser,
  useInvitationLink,
  useSignOut,
} from '@/features/auth/types';
import { linkOpeningMessage, useOpenFriendLink } from '@/features/friends/types';
import { joinGroupRouteFor } from '@/features/groups/types';
import { rereadNotices } from '@/features/notifications/types';
import { openNeedsYourAnswer, openTab } from '@/features/shell/types';
import type { AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import type { CredentialLink, IncomingLink } from '../domain/incomingLink';
import {
  friendLinkLanding,
  invitationLinkOutcome,
  letsTheLinkGo,
  playersLinkMove,
  type LinkHome,
} from '../domain/linkRules';
import { letGoOf, useHeldLink } from '../hooks/heldLink';

import { linkScreenHref } from './linkRoutes';
import {
  LINKS_COPY,
  RESET_WHILE_SIGNED_IN,
  someoneElsesInvitationBody,
  someoneElsesInvitationTitle,
} from './linksPresentation';

type LinkOf<K extends IncomingLink['kind']> = Extract<IncomingLink, { readonly kind: K }>;

export interface IncomingLinksProps {
  /** The home this is mounted over — the player's app, or an administrator area. */
  readonly over: LinkHome;
}

export function IncomingLinks({ over }: IncomingLinksProps) {
  const link = useHeldLink();

  if (link === null) return null;

  // Keyed by the link, so a newer one arriving while an older is being answered starts afresh.
  switch (link.kind) {
    case 'join':
      return <GroupLink key={link.code} link={link} over={over} />;
    case 'friend':
      return <FriendLink key={link.code} link={link} over={over} />;
    case 'invite':
      return <InvitationLink key={link.token} link={link} />;
    case 'reset':
      return <ResetLink key={link.token} link={link} />;
    case 'open':
      return <OpenLink link={link} />;
  }
}

/**
 * **A group link: Join a group, over Play › Groups** — `shell`'s own move to Play, then the screen
 * pushed on it, so *back* is the Groups list. In an administrator area, a switch to Player first, and
 * the player's app answers it.
 */
function GroupLink({ link, over }: { readonly link: LinkOf<'join'>; readonly over: LinkHome }) {
  const pathname = usePathname();
  const user = useCurrentUser();
  const switchTo = useSwitchProfile();
  const move = playersLinkMove(over, user.data?.profiles.actsAsPlayer === true);
  // Where the person is at the moment the link is opened, read then rather than closed over: the
  // effect's job is to fire when the link arrives, not whenever the path changes.
  const where = useRef(pathname);
  where.current = pathname;

  useEffect(() => {
    switch (move) {
      case 'answer':
        letGoOf(link);
        openTab('play', where.current);
        router.push(joinGroupRouteFor(link.code));
        return;
      case 'switch-to-player':
        switchTo(PLAYER_PROFILE);
        return;
      case 'wait':
        return;
    }
  }, [link, move, switchTo]);

  return null;
}

/**
 * **A friend link: opened as the account, then Home with Needs your answer up** (#756, #817; the
 * friends mechanics §4.2–§4.3; ADR-0205 §1). The opening puts the owner's request in the sheet —
 * *{nickname} wants to be your friend* — and the player lands on it; Home and the bell are read
 * again by the opening, the bell's re-read handed in, so the sheet opens on what Home says then: a
 * request the owner's block swallowed lands on Home as it is, with no sheet. **The account's own
 * link, or a friend's, moves nobody**: there is nothing to answer. **A link that cannot be opened is
 * said, as a toast, wherever the player is** — a dead one *Nothing at that link*, one whose owner
 * they blocked how to see it, a failed one why — and let go: it is never tried again.
 *
 * **Opened once**, whatever renders this again while it is on its way, and answered through
 * `mutateAsync` so the landing is heard even if this is unmounted first. In an administrator area
 * the account that plays is switched to Player, and the player's app opens it.
 */
function FriendLink({ link, over }: { readonly link: LinkOf<'friend'>; readonly over: LinkHome }) {
  const pathname = usePathname();
  const user = useCurrentUser();
  const switchTo = useSwitchProfile();
  const client = useQueryClient();
  const { mutateAsync: open } = useOpenFriendLink(() => rereadNotices(client));
  const move = playersLinkMove(over, user.data?.profiles.actsAsPlayer === true);
  // Where the person is when the answer comes, read then — `GroupLink`'s reason.
  const where = useRef(pathname);
  where.current = pathname;
  const asked = useRef(false);

  useEffect(() => {
    switch (move) {
      case 'answer':
        if (asked.current) return;
        asked.current = true;
        open(link.code).then(
          (relation) => {
            letGoOf(link);
            if (friendLinkLanding(relation) === 'home') openNeedsYourAnswer(where.current);
          },
          (error: AppError) => {
            showToast({ message: linkOpeningMessage(error), hold: 'read' });
            letGoOf(link);
          },
        );
        return;
      case 'switch-to-player':
        switchTo(PLAYER_PROFILE);
        return;
      case 'wait':
        return;
    }
  }, [link, move, switchTo, open]);

  return null;
}

/** **The app's bare address** — the invitation sheet offers what was set aside this launch again. */
function OpenLink({ link }: { readonly link: LinkOf<'open'> }) {
  const offerAgain = useOfferInvitationsAgain();

  useEffect(() => {
    offerAgain();
    letGoOf(link);
  }, [link, offerAgain]);

  return null;
}

/** **An invitation's link, on a signed-in phone** — read, weighed, and answered once. */
function InvitationLink({ link }: { readonly link: LinkOf<'invite'> }) {
  const read = useInvitationLink(link.token);
  const user = useCurrentUser();
  const offerAgain = useOfferInvitationsAgain();

  const outcome =
    read.data === undefined || user.data === undefined
      ? undefined
      : invitationLinkOutcome(read.data, user.data.email);
  const failure = read.error;
  // What the outcome says, as values: it is a fresh object each render, and the effect is keyed on
  // what it says rather than on which object said it.
  const offeredClub = outcome?.kind === 'offer' ? outcome.clubName : undefined;
  const spent = outcome?.kind === 'spent' ? outcome.state : undefined;
  const answered = outcome !== undefined && letsTheLinkGo(outcome);

  useEffect(() => {
    if (failure !== null) {
      showToast({ message: invitationErrorMessage('link')(failure), hold: 'read' });
      letGoOf(link);
      return;
    }
    if (offeredClub !== undefined) offerAgain(offeredClub);
    if (spent !== undefined) showToast({ message: LINK_STATE_MESSAGE[spent], hold: 'read' });
    if (answered) letGoOf(link);
  }, [failure, offeredClub, spent, answered, link, offerAgain]);

  if (outcome?.kind !== 'someone-else' || user.data === undefined) return null;

  return (
    <SignOutForLink
      link={link}
      title={someoneElsesInvitationTitle(outcome.invited)}
      body={someoneElsesInvitationBody(user.data.email, outcome.invited)}
    />
  );
}

/** **A reset link, on a signed-in phone** — sign out first, or let it go. */
function ResetLink({ link }: { readonly link: LinkOf<'reset'> }) {
  const user = useCurrentUser();

  if (user.data === undefined) return null;

  return (
    <SignOutForLink
      link={link}
      title={RESET_WHILE_SIGNED_IN.title}
      body={RESET_WHILE_SIGNED_IN.body(user.data.email)}
    />
  );
}

/**
 * **The sheet both ask with** — who is signed in, and **Sign out** or **Stay signed in**.
 *
 * Signing out is `auth`'s sequence, and then the link's own screen: the session's end hands the
 * person to sign-in first, and the screen is laid over it. `mutateAsync` rather than `mutate`'s
 * callbacks, which a component unmounted by the session ending would never hear. A sign-out that
 * failed leaves the session and the sheet as they were, and says why, as the You tab's does.
 */
function SignOutForLink({
  link,
  title,
  body,
}: {
  readonly link: CredentialLink;
  readonly title: string;
  readonly body: string;
}) {
  const signOut = useSignOut();

  const leave = () => {
    signOut.mutateAsync().then(
      () => router.replace(linkScreenHref(link)),
      () => undefined,
    );
  };
  const stay = () => letGoOf(link);

  return (
    <BottomSheet visible onClose={stay} title={title} closeLabel={LINKS_COPY.close}>
      <Text style={s.body}>{body}</Text>

      {/* Said on the sheet because nothing under it can. `alert`: it appeared unasked. */}
      {signOut.error === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {authErrorMessage(signOut.error)}
        </Note>
      )}

      <View style={s.actions}>
        <Button
          label={SIGN_OUT.label}
          variant="dark"
          size="lg"
          busy={signOut.isPending}
          busyLabel={SIGN_OUT.busyLabel}
          onPress={leave}
        />
        <Button label={LINKS_COPY.stay} variant="secondary" size="lg" onPress={stay} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.muted },
  actions: { gap: theme.space.sm, paddingTop: theme.space.xs },
});
