/**
 * The auth feature's only public surface.
 *
 * `src/app/` and other features may import from here and from nowhere else inside this
 * folder — ESLint blocks the deep paths. Anything not re-exported below is an internal
 * detail this feature is free to change.
 */

export { AccountScreen } from "./components/AccountScreen";
export { SignInScreen } from "./components/SignInScreen";
export { SignUpScreen } from "./components/SignUpScreen";

export type {
  AuthenticatedUser,
  Registration,
  SignInCredentials,
} from "./domain/AuthenticatedUser";

export { authKeys } from "./hooks/authKeys";
export { useCurrentUser } from "./hooks/useCurrentUser";

/**
 * The launch step. Exported because the bootstrap sequence needs it and
 * `shared/lib/bootstrap` may not import a feature — so the root layout, whose job is
 * composition, wires the two together.
 */
export { restoreSession, type RestoredSession } from "./use-cases/restoreSession";
