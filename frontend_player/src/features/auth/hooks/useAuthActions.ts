/**
 * The auth mutations, as semantic hooks.
 *
 * Each one declares its own retry decision at the call site, because the global default
 * is `retry: false` and overriding it silently is how a mutation gets repeated.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { usePush } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';

import type {
  AccountProfiles,
  AuthenticatedUser,
  Naming,
  Registration,
  SignInCredentials,
} from '../domain/AuthenticatedUser';
import type { InvitationCodeClaim, InvitationPassword } from '../domain/invitation';
import { PLAYER_PROFILE } from '../domain/lastProfile';
import type { NewPassword, ResetCodeClaim } from '../domain/passwordReset';
import { acceptInvitation } from '../use-cases/acceptInvitation';
import { askForPasswordReset } from '../use-cases/askForPasswordReset';
import { attestAdult } from '../use-cases/attestAdult';
import { claimInvitationCode } from '../use-cases/claimInvitationCode';
import { claimResetCode } from '../use-cases/claimResetCode';
import { namePlayer } from '../use-cases/namePlayer';
import { setInvitationPassword } from '../use-cases/setInvitationPassword';
import { setNewPassword } from '../use-cases/setNewPassword';
import { signIn } from '../use-cases/signIn';
import { signOut } from '../use-cases/signOut';
import { signUp } from '../use-cases/signUp';

import { authKeys } from './authKeys';
import { currentUserQuery, fetchCurrentUserAtSessionStart } from './useCurrentUser';
import { useKeepProfile } from './useLastProfile';

/** What the toast says once a new password is set — the copy module's, handed in by the screen. */
export interface SetNewPasswordOptions {
  readonly done: string;
}

/**
 * **Not retried.** A failed sign-in is almost always a wrong password, and repeating it
 * walks the account toward whatever lockout policy the backend has. The player retries
 * by tapping the button.
 *
 * No cache write on success: the session status change is what moves the app. **The account
 * is read before it changes** (`fetchCurrentUserAtSessionStart`, `decisions.md` §3.1), so the
 * button stays busy until the entry gate can go straight to where the player belongs, rather
 * than the gate drawing nothing while it asks.
 */
export function useSignIn() {
  const queryClient = useQueryClient();

  return useMutation<void, AppError, SignInCredentials>({
    mutationFn: (credentials) =>
      signIn(credentials, () => fetchCurrentUserAtSessionStart(queryClient)),
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
  const queryClient = useQueryClient();

  return useMutation<void, AppError, Registration>({
    // Sign-in's read, for sign-in's reason: _Creating account…_ turns until the gate can move.
    mutationFn: (registration) =>
      signUp(registration, () => fetchCurrentUserAtSessionStart(queryClient)),
    retry: false,
  });
}

/**
 * **Not retried.** The use-case already treats the server revoke as best-effort and
 * always tears the local session down, so there is nothing a retry could improve.
 *
 * It is handed this tree's push port: the first thing a sign-out does is let the phone go (#559).
 */
export function useSignOut() {
  const phone = usePush();
  return useMutation<void, AppError, void>({
    mutationFn: () => signOut(phone),
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
 * - The **write** is not a guess. The server answered with the nickname *as recorded*, so what
 *   goes into the cached player is what the server holds, and a gate reading the cache in the
 *   next instant already finds a named player. A cache still saying *no nickname* would route the
 *   player straight back to the step they just finished.
 * - The **re-read** is the server staying the authority, and it is **awaited**
 *   ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3: *it
 *   submits the naming, re-reads `/me`, and only then moves on*).
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
        // `undefined` leaves the cache untouched rather than inventing a player out of a
        // string.
        player === undefined ? undefined : { ...player, nickname: recorded.nickname },
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
 *
 * **Starting to play is choosing Player** ([#518](https://github.com/Rakieta02/Rakieta/issues/518)):
 * the gate reads the profile the phone remembers first, and an account that wore a club's profile
 * last would be sent straight back to that club's area. So the choice is kept here, before the
 * re-read, and the gate goes on to the naming.
 */
export function useAttestAdult() {
  const queryClient = useQueryClient();
  const keepProfile = useKeepProfile();

  return useMutation<void, AppError, void>({
    mutationFn: attestAdult,
    retry: false,
    onSuccess: async () => {
      keepProfile(PLAYER_PROFILE);
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
  const queryClient = useQueryClient();

  return useMutation<void, AppError, NewPassword>({
    // Sign-in's read: the account before the session opens (`decisions.md` §3.1).
    mutationFn: (password) =>
      setNewPassword(password, () => fetchCurrentUserAtSessionStart(queryClient)),
    retry: false,
    onSuccess: () => showToast({ message: done, tone: 'ok' }),
  });
}

/**
 * ***Have an invitation code?*** — the code, exchanged for a ticket. **Not retried**, for
 * `useClaimResetCode`'s reason: five wrong codes lock the invitation, and a retry of a wrong one is
 * a second wrong one nobody typed.
 */
export function useClaimInvitationCode() {
  return useMutation<string, AppError, InvitationCodeClaim>({
    mutationFn: claimInvitationCode,
    retry: false,
  });
}

/**
 * ***Set your password***, signed in at the end. **Not retried**: setting it spends the link, the
 * code and the ticket together, so a retry of a request that landed meets `credential_used` about a
 * password that is, in fact, set.
 *
 * **No toast.** The `(auth)` guard hands the session to the entry gate, which opens the
 * administrator area — the place the invitation was for, and the *done* in itself.
 */
export function useSetInvitationPassword() {
  const queryClient = useQueryClient();

  return useMutation<void, AppError, InvitationPassword>({
    // Sign-in's read: the account before the session opens (`decisions.md` §3.1).
    mutationFn: (password) =>
      setInvitationPassword(password, () => fetchCurrentUserAtSessionStart(queryClient)),
    retry: false,
  });
}

/**
 * **Accept a club's invitation** — the administrator profile added to this account, and the cache
 * effect it declares ([#518](https://github.com/Rakieta02/Rakieta/issues/518), ADR-0184 §2).
 *
 * **Not retried**, though accepting twice is the same answer: a failure is the person's to see and
 * press again, every mutation's rule here.
 *
 * **The answer is written, not re-read.** The server answers the account's profiles exactly as
 * `/users/me` would — the new club among them, the invitation gone from those pending — so they go
 * into the cached player at once: the switcher the sheet turns into draws both profiles from it, and
 * nothing offers the invitation again.
 */
export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation<AccountProfiles, AppError, string>({
    mutationFn: acceptInvitation,
    retry: false,
    onSuccess: (profiles) => {
      queryClient.setQueryData<AuthenticatedUser>(authKeys.currentUser(), (player) =>
        player === undefined ? undefined : { ...player, profiles },
      );
    },
  });
}
