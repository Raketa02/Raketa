---
paths:
  - 'src/shared/lib/auth/**'
  - 'src/shared/lib/http/**'
  - 'src/shared/lib/bootstrap/**'
  - 'src/app/(auth)/**'
---

# Auth, in four rules that are easy to get wrong

1. **Single-flight refresh.** One `refreshPromise`; every concurrent 401 awaits the same one.
   Ten parallel refreshes rotate each other out and log the user out at random.
2. **Retry an authenticated request exactly once.** The retry carries a flag saying refresh
   was attempted; a second 401 terminates the session instead of looping forever. **The live
   channel is the one act that rotates without being allowed to end a session** — it is a latency
   optimisation over an authoritative read path running on the same screen, and that path is what
   may act on a refusal — so `rotateStreamCredential` rotates once per channel and then stops
   attempting rather than calling `abandon` (`shared/lib/http/httpClient.ts`, ADR-0147 §6).
3. **Rejected ≠ unreachable.** A refresh the auth server _rejects_ clears credentials and
   caches. A refresh that _times out_ preserves them — losing signal in a lift is not a
   logout.
4. **Logout is a system operation.** Revoke → clear memory → delete keychain → cancel
   in-flight requests → `queryClient.cancelQueries()` + `clear()` → reset sensitive UI state
   → set unauthenticated → navigate. Skipping the cache clear leaks user A's data to user B
   on the same device.

## The chokepoints

- `src/shared/lib/auth` is the **only** consumer of `expo-secure-store`
  (`tokenManager · refreshCoordinator · authService · authSession`). No feature, screen or
  hook imports it directly. One module owning the keychain is what makes token lifetime
  auditable.
- `src/shared/lib/http` is the **only** place `fetch` is configured, and the only place the
  401 → refresh → retry rotation lives. A second networking path defeats both.
- Timeouts live here as classes (request/upload/download/background). `fetch` has no default
  timeout, and no feature contains a millisecond literal.

## Bootstrap

Model it as a **state**, never as `user === undefined`. The ordered sequence is: error
reporting → validate config → wire focus/online managers → read SecureStore →
restore/validate session → start warming Home (never awaited, #874) → start reading the
install referrer (never awaited) → load fonts → render a tree. Nothing renders a route tree
before it resolves. **It runs behind the drawn splash and nothing hides a splash at its end**
(ADR-0209): the launch gate lets the OS launch window go on the drawn splash's first layout,
mounts the tree underneath when the sequence resolves, and fades the splash once the first
screen is ready.

iOS Keychain data can survive a reinstall, so **a token existing is not proof a session
exists** — bootstrap validates it.

Never log a token, an `Authorization` header, a password or a full payload. The logger
redacts structurally; production logging is stricter than development.
