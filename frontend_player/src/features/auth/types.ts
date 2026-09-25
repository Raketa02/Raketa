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
 * **The naming, from the You tab**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7): the *Name* row the shell composes, the screen behind it the route file mounts, and
 * the row's words for the suites that hold the tab to them.
 */
export { NameRow, YOU_NAME_ROUTE, type NameRowProps } from './components/NameRow';
export { NameScreen } from './components/NameScreen';
export { NAME_ROW_TITLE, SAVE_NAME, nameLine } from './components/namePresentation';
export { SignInScreen } from './components/SignInScreen';
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
  parseResetLinkParams,
  parseResetTicketParams,
} from './schemas/resetRouteParams';

export type {
  AuthenticatedUser,
  Naming,
  Registration,
  SignInCredentials,
} from './domain/AuthenticatedUser';

/**
 * Where an unnamed account is sent. The entry gate reaches for it, and one file spelling the
 * route is one place to change it — `SOCIAL_STEPS_ENTRY`'s own argument.
 */
export const NAMING_STEP = '/name';

export { authKeys } from './hooks/authKeys';
/**
 * The signed-in player's read — its key and its fetch as one thing — for the one reader that must
 * look it up without observing it: a feature-flag gate, which reads the player once when its
 * screen mounts (ADR-0180 §7). Its key carries the mapped type, so that lookup needs no cast and
 * cannot disagree with this feature about what the entry holds.
 */
export { currentUserQuery, useCurrentUser } from './hooks/useCurrentUser';
/**
 * The one write another feature may make to the authenticated player.
 *
 * Onboarding's second part ends in a commit that creates a Player profile, and the entry
 * gate reads whether one exists off this player. The *fact* is auth's, so the cache effect
 * is auth's too — see the hook.
 */
export { useMarkPlayerProfileCommitted } from './hooks/useMarkPlayerProfileCommitted';

/**
 * The two launch steps. Exported because the bootstrap sequence needs them and
 * `shared/lib/bootstrap` may not import a feature — so the root layout, whose job is
 * composition, wires the two together.
 *
 * `refreshTokens` is the wire call the rotation is built on, not the rotation itself:
 * that lives in `shared/lib/http` and `shared/lib/auth`, and nothing here may re-implement
 * it.
 */
export { refreshTokens } from './use-cases/refreshTokens';
export { restoreSession, type RestoredSession } from './use-cases/restoreSession';
