/**
 * The feature's query keys, in one file. No string key is ever typed inline in a
 * component — a key written twice is two cache entries the first time one of them gains
 * a parameter.
 *
 * Every parameter that changes the response belongs in the key. `currentUser` takes none
 * because the access token decides the answer, and the token is not a value this app is
 * allowed to put in a cache key.
 */
export const authKeys = {
  all: ['auth'] as const,
  currentUser: () => [...authKeys.all, 'current-user'] as const,
  /** What an invitation's link opens — held for the screen it is read on, and gone with it. */
  invitationLink: (token: string) => [...authKeys.all, 'invitation-link', token] as const,
} as const;
