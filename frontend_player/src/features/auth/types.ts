/**
 * The auth feature's only public surface.
 *
 * `src/app/` and other features may import from here and from nowhere else inside this
 * folder — ESLint blocks the deep paths. Anything not re-exported below is an internal
 * detail this feature is free to change.
 */

export { AccountPanel } from './components/AccountPanel';
/**
 * The naming step — *How should people see you?* — onboarding's first screen, and this
 * feature's on the second part's own precedent: the values it asks for are the users
 * context's, and the follow-up that edits them will drive the same rules. See the screen.
 */
export { NamingScreen } from './components/NamingScreen';
/**
 * ***Start playing*'s first step, the Adult attestation** (ADR-0185 §4–§5,
 * [#517](https://github.com/Raketa02/Raketa/issues/517)) — this feature's on the naming's precedent:
 * the act is the users context's, on the account, and the tick box and its sentence are sign-up's.
 */
export { StartPlayingScreen } from './components/StartPlayingScreen';

/**
 * **The naming, from the You tab**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7): the *Nickname* row the shell composes, the screen behind it the route file mounts, and
 * the row's words for the suites that hold the tab to them (ADR-0199 §3).
 */
export { NicknameRow, YOU_NICKNAME_ROUTE, type NicknameRowProps } from './components/NicknameRow';
export { NicknameScreen } from './components/NicknameScreen';
export { NICKNAME_ROW_TITLE, SAVE_NICKNAME } from './components/nicknamePresentation';
export { SignInScreen } from './components/SignInScreen';
/**
 * **Whether a route is the screen in view** (#784) — read in the route file and handed to the
 * stage, whose status bar is light only while it is. The navigator's hooks throw outside a
 * navigator, so the screen takes the answer as a prop and the suites draw it on its own.
 */
export { useScreenInView } from './hooks/useScreenInView';
export { SignUpScreen } from './components/SignUpScreen';

/**
 * ***Forgot password?*** ([#515](https://github.com/Raketa02/Raketa/issues/515)) — the email form,
 * the neutral confirmation, the code, and *Set a new password* by a claimed code or by the email's
 * link. Each route file reads its params through the parser beside it and mounts the screen.
 */
export { ForgotPasswordScreen } from './components/ForgotPasswordScreen';
export { ResetCodeScreen } from './components/ResetCodeScreen';
export { ResetSentScreen } from './components/ResetSentScreen';
export { RESET_ROUTES } from './components/resetRoutes';
export { SetNewPasswordScreen } from './components/SetNewPasswordScreen';
export {
  parseEmailParam,
  parseInvitationLinkParams,
  parseInvitationTicketParams,
  parseResetLinkParams,
  parseResetTicketParams,
} from './schemas/credentialRouteParams';

/**
 * ***Have an invitation code?*** and ***Set your password*** ([#518](https://github.com/Raketa02/Raketa/issues/518))
 * — the email and the code, and the password by a claimed code or by the invitation email's link,
 * validated before the form is drawn. `INVITATION_ROUTES.link` is what the links ticket (#520) opens.
 */
export { InvitationCodeScreen } from './components/InvitationCodeScreen';
export { InvitationLinkScreen } from './components/InvitationLinkScreen';
export { SetYourPasswordScreen } from './components/SetYourPasswordScreen';
export { INVITATION_ROUTES } from './components/invitationRoutes';

/**
 * **An invitation's link, read — and its words** ([#520](https://github.com/Raketa02/Raketa/issues/520)):
 * a link opened on a phone that is signed in is read here too, before the sheet it opens is drawn,
 * and a spent one is said in the sentence *Set your password* would have said it in.
 */
export type { InvitationLink, InvitationLinkState } from './domain/invitation';
export { useInvitationLink } from './hooks/useInvitationLink';
export { LINK_STATE_MESSAGE, invitationErrorMessage } from './components/invitationPresentation';

/**
 * **Named** — holding a nickname (ADR-0199 §3) — for the entry gate's first destination.
 */
export { named } from './domain/naming';

/**
 * **Which profile the account wears, and the one the phone remembers** (ADR-0188 §2, #518) — the
 * value, its reading back, and the hooks that read and keep it per account. The entry gate opens an
 * account with two profiles in the one it wore last; the switcher keeps what is chosen.
 */
export { PLAYER_PROFILE, type ProfileChoice } from './domain/lastProfile';
export { useKeepProfile, useLastProfile } from './hooks/useLastProfile';

export type {
  AccountProfiles,
  AdministeredClub,
  AuthenticatedUser,
  Handover,
  HeldProfiles,
  PendingInvitation,
  Naming,
  Registration,
  SignInCredentials,
} from './domain/AuthenticatedUser';

/**
 * Where an account with no nickname is sent. The entry gate reaches for it, and one file spelling the
 * route is one place to change it — `SOCIAL_STEPS_ENTRY`'s own argument.
 */
export const NAMING_STEP = '/name';

/**
 * Where *Start playing* begins — the Adult attestation. The administrator's You tab pushes it, and
 * the entry gate sends an account that holds no profile at all to it; one spelling for both.
 */
export const START_PLAYING_STEP = '/start-playing';

export { authKeys } from './hooks/authKeys';
/**
 * The signed-in player's read — its key and its fetch as one thing — for the one reader that must
 * look it up without observing it: a feature-flag gate, which reads the player once when its
 * screen mounts (ADR-0180 §7). Its key carries the mapped type, so that lookup needs no cast and
 * cannot disagree with this feature about what the entry holds.
 */
export {
  ACCOUNT_FOLLOWED_MS,
  currentUserQuery,
  useCurrentUser,
  useFollowedAccount,
} from './hooks/useCurrentUser';
/** **Who is reading the screen** — the cached player's id, read once and never observed. */
export { useReaderId } from './hooks/useReaderId';
/**
 * The one write another feature may make to the authenticated player.
 *
 * Onboarding's second part ends in a commit that creates a Player profile, and the entry
 * gate reads whether one exists off this player. The *fact* is auth's, so the cache effect
 * is auth's too — see the hook.
 */
export { useMarkPlayerProfileCommitted } from './hooks/useMarkPlayerProfileCommitted';

/**
 * **The one way out of a session**, for the one caller outside this feature that must take it
 * without a button: the administrator area, when the club has removed an account that holds
 * nothing else (PRD #500 story 136). The sequence is this feature's — revoke, then `endSession` —
 * so the caller gets the hook and never the steps.
 */
export { useSignOut } from './hooks/useAuthActions';
/**
 * Its button's words and its refusal's, for the one other place that offers it: a link's sheet
 * (#520).
 */
export { SIGN_OUT } from './components/accountPresentation';
export { authErrorMessage } from './components/authErrorMessage';

/**
 * **Accepting a club's invitation** (#518) — for the invitation sheet, which the administrator
 * feature draws. The act and its cache effect are this feature's: what it changes is the account's
 * profiles, which this feature carries.
 */
export { useAcceptInvitation } from './hooks/useAuthActions';

/**
 * The launch steps. Exported because the bootstrap sequence needs them and
 * `shared/lib/bootstrap` may not import a feature — so the root layout, whose job is
 * composition, wires them together: `restoreSession` asks with `fetchCurrentUserAtLaunch`,
 * so the answer — or the failure — is left in the cache the entry gate reads.
 *
 * `refreshTokens` is the wire call the rotation is built on, not the rotation itself:
 * that lives in `shared/lib/http` and `shared/lib/auth`, and nothing here may re-implement
 * it.
 */
export { refreshTokens } from './use-cases/refreshTokens';
export { restoreSession, type RestoredSession } from './use-cases/restoreSession';
export { fetchCurrentUserAtLaunch } from './hooks/useCurrentUser';
/**
 * **The launch's offline rule, and the remembered profile read before any screen** (#874) — for the
 * step after session restore, which warms Home only for an account the entry gate will send to the
 * tabs (`shell`'s warm-up, through `onboarding`'s rule over the account) and never on a phone that
 * already knows it is offline.
 */
export { phoneKnowsItIsOffline } from './use-cases/restoreSession';
export { fetchLastProfile } from './hooks/useLastProfile';
