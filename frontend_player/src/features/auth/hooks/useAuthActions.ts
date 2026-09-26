/**
 * The auth mutations, as semantic hooks.
 *
 * Each one declares its own retry decision at the call site, because the global default
 * is `retry: false` and overriding it silently is how a mutation gets repeated.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';

import type {
  AuthenticatedUser,
  Naming,
  Registration,
  SignInCredentials,
} from '../domain/AuthenticatedUser';
import type { NewPassword, ResetCodeClaim } from '../domain/passwordReset';
import { askForPasswordReset } from '../use-cases/askForPasswordReset';
import { attestAdult } from '../use-cases/attestAdult';
import { claimResetCode } from '../use-cases/claimResetCode';
import { namePlayer } from '../use-cases/namePlayer';
import { setNewPassword } from '../use-cases/setNewPassword';
import { signIn } from '../use-cases/signIn';
import { signOut } from '../use-cases/signOut';
import { signUp } from '../use-cases/signUp';

import { authKeys } from './authKeys';
import { currentUserQuery } from './useCurrentUser';

/** What the toast says once a new password is set — the copy module's, handed in by the screen. */
export interface SetNewPasswordOptions {
  readonly done: string;
}

/**
 * **Not retried.** A failed sign-in is almost always a wrong password, and repeating it
 * walks the account toward whatever lockout policy the backend has. The player retries
 * by tapping the button.
 *
 * No cache write on success: the session status change is what moves the app, and the
 * profile is fetched by `useCurrentUser` once the authenticated tree renders.
 */
export function useSignIn() {
  return useMutation<void, AppError, SignInCredentials>({
    mutationFn: signIn,
    retry: false,
  });
}

/**
 * **Not retried, and this one matters.** Registration creates a record. A silent retry
 * of a request that actually succeeded but whose response was lost would ask the backend
 * to create the same account twice — and the second attempt fails as
 * `email_already_registered`, which the player would read as "that didn't work" about an
 * account that now exists.
 */
export function useSignUp() {
  return useMutation<void, AppError, Registration>({
    mutationFn: signUp,
    retry: false,
  });
}

/**
 * **Not retried.** The use-case already treats the server revoke as best-effort and
 * always tears the local session down, so there is nothing a retry could improve.
 */
export function useSignOut() {
  return useMutation<void, AppError, void>({
    mutationFn: signOut,
    retry: false,
  });
}

/**
 * **The naming** — *How should people see you?* — and the cache effect it declares.
 *
 * **Not retried.** The act is repeatable on the server, so a retry would be safe; it is still
 * not automatic, because the one refusal this ever meets is a taken handle, and the identical
 * body fails identically. The player retries by changing the box.
 *
 * **Written, and then re-read, in that order** — the same shape as `useMarkPlayerProfileCommitted`
 * and for the same reasons, with one difference the ADR asks for:
 *
 * - The **write** is not a guess. The server answered with the name *as recorded* — trimmed,
 *   collapsed — so what goes into the cached player is what the server holds, and a gate
 *   reading the cache in the next instant already finds a named player. A cache still saying
 *   *no name* would route the player straight back to the step they just finished.
 * - The **re-read** is the server staying the authority, and it is **awaited**
 *   ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 *   §3: *it submits the naming, re-reads `/me`, and only then moves on*).
 *
 * **`fetchQuery`, and not an invalidation, because the entry may be gone.** Nothing on the
 * naming step observes the player, and an unobserved query is garbage-collected after its
 * `gcTime` — five minutes, which is a slow typist away. An invalidation of an entry that is not
 * there refetches nothing and resolves at once, and the write above has nothing to write into;
 * the "re-read" then happens on whichever screen mounts next, which is the gate's — correct, but
 * not the promise. `fetchQuery` on the one query definition creates the entry where it has to,
 * fetches it regardless of freshness, and **throws where the read failed**: the mutation then
 * fails, the screen says the platform could not be reached and stays, and a second *Continue*
 * repeats an act the server admits twice. That is the honest shape — a naming the app could not
 * confirm is not one it should move on from.
 *
 * The mutation resolves after both, so a caller's own `onSuccess` navigates on a cache that is
 * already right and a server that has already confirmed it.
 */
export function useNamePlayer() {
  const queryClient = useQueryClient();

  return useMutation<Naming, AppError, Naming>({
    mutationFn: namePlayer,
    retry: false,
    onSuccess: async (recorded) => {
      queryClient.setQueryData<AuthenticatedUser>(authKeys.currentUser(), (player) =>
        // Nothing cached to update — the re-read below creates the entry. Returning
        // `undefined` leaves the cache untouched rather than inventing a player out of two
        // strings.
        player === undefined
          ? undefined
          : { ...player, name: recorded.name, nickname: recorded.nickname },
      );
      // `staleTime: 0` is the point: the write above just made the entry fresh, and a fetch that
      // honoured that would hand the write back as the server's answer.
      await queryClient.fetchQuery({ ...currentUserQuery(), staleTime: 0 });
    },
  });
}

/**
 * ***Start playing*'s first step, the Adult attestation** — and the cache effect it declares
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §4–§5).
 *
 * **Not retried.** The act is safe to repeat — giving it twice records nothing — but a failure is
 * the player's to see and press again, every mutation's rule.
 *
 * **Written, and then re-read, in that order** — the naming's shape, for its reasons. The account
 * **acts as a player** from the moment it attests (ADR-0185 §2), and that is what the entry gate
 * reads first: the write puts it in the cached player at once, so a gate reading the cache in the
 * next instant already sends the account on to the naming rather than back to its administrator
 * area, and the awaited `fetchQuery` is the server staying the authority. The caller's own
 * `onSuccess` navigates on a cache that is already right.
 */
export function useAttestAdult() {
  const queryClient = useQueryClient();

  return useMutation<void, AppError, void>({
    mutationFn: attestAdult,
    retry: false,
    onSuccess: async () => {
      queryClient.setQueryData<AuthenticatedUser>(authKeys.currentUser(), (player) =>
        player === undefined
          ? undefined
          : { ...player, profiles: { ...player.profiles, actsAsPlayer: true } },
      );
      await queryClient.fetchQuery({ ...currentUserQuery(), staleTime: 0 });
    },
  });
}

/**
 * ***Forgot password?*** — ask for the email.
 *
 * **Not retried.** The server throttles per address and says so to nobody, so a silent retry
 * spends one of the person's three emails an hour on a request they cannot see; the answer is
 * identical either way, and a person who got nothing asks again with the button.
 */
export function useAskForPasswordReset() {
  return useMutation<void, AppError, string>({
    mutationFn: askForPasswordReset,
    retry: false,
  });
}

/**
 * The code, exchanged for a ticket. **Not retried**: five wrong codes lock the credential, and a
 * retry of a wrong one is a second wrong one the person never typed.
 */
export function useClaimResetCode() {
  return useMutation<string, AppError, ResetCodeClaim>({
    mutationFn: claimResetCode,
    retry: false,
  });
}

/**
 * *Set a new password*, signed in at the end.
 *
 * **Not retried.** Setting it spends the link, the code and the ticket together, so a retry of a
 * request that landed but whose answer was lost meets `credential_used` — a refusal about a
 * password that is, in fact, set. The person presses again, and is told so in words.
 *
 * **The toast is the "done"**: the `(auth)` guard sees the session begin and hands it to the entry
 * gate, so there is no screen of this flow left to say it on. It says what else happened, because
 * a person whose other phone goes quiet should know why.
 */
export function useSetNewPassword({ done }: SetNewPasswordOptions) {
  return useMutation<void, AppError, NewPassword>({
    mutationFn: setNewPassword,
    retry: false,
    onSuccess: () => showToast({ message: done, tone: 'ok' }),
  });
}
