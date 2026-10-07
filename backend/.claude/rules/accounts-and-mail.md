---
paths:
  - "app/modules/administrators/**"
  - "app/modules/users/**"
  - "app/modules/auth/**"
  - "app/application/mail/**"
  - "app/infrastructure/mail/**"
---

# Email, administrators and signing out everywhere

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A use case never sends email; it writes the mail queue**
  ([ADR-0186](../../../docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md)). The
  message is rendered whole — the copy lives with its templates in the backend
  (`app/application/mail/layout.py`, and each flow's own words beside its use case), since an
  email has no client to choose a sentence from a code — and written through `MailQueue` in
  the act's own transaction; the mail worker sends it through the `Mailer` port and purges
  the body. **An email's Message-ID is its queue row's id** (`<mail_id@sender domain>`,
  #594): every attempt at one email is one message to a mailbox, and the dev console's
  *Sent* pane links to it in the mail catcher by it. `.importlinter` keeps `smtplib` out of
  every domain and application layer. **A secret never enters the event store or the
  outbox** (ADR-0184 §4): a one-time credential is a row in `one_time_credentials`, hashed,
  and `OneTimeCredentials` is the one mechanism every flow that issues one goes through —
  *Forgot password?* on both surfaces and the administrators' invitations.
  `tests/api/test_forgot_password.py` and `tests/api/test_invitations.py` assert that no
  link, code or ticket ever reaches an event, at every step.
- **An Administrator is a club naming a person, and every administrator request asks
  again** ([ADR-0184](../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md),
  [ADR-0185](../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md),
  #508). `app/modules/administrators/` holds **one event-sourced aggregate per (club,
  email)** — *invited*, *active*, *removed*, and *expired* **derived** from a window that is
  the invitation credential's own 72 hours, so an existing account's invitation, which carries
  no credential, lapses at the same instant — and its `save` writes the `administrators` row in
  the caller's transaction. Five things are load-bearing. **Which email is decided at sending
  and recorded nowhere** (`application/sending.py`): an account that can sign in is asked to
  accept in the app with no code; anybody else gets a link to `<PUBLIC_SITE_URL>/invite/<token>`
  and a code — the club reset's while one is pending — and each credential **retires every live
  one of both kinds**, as acceptance and removal do. **A removal is emailed**
  (`application/removal_emails.py`, ADR-0191 §4–§5): *removed* to somebody whose
  administratorship reached an account, *invitation withdrawn* to somebody still invited —
  notices, so no button and no code. **Everything done to a User is done by
  `users`** (`InvitationAccounts`, behind the `AccountHolders` port): an account an invitation
  opens is `AccountOpenedByInvitation` — the club-typed Name, no Nickname, no attestation —
  the club's reset is `PasswordCleared` (`users.password_hash` became nullable, and a cleared
  account signs in as a stranger would), and the attestation given later is `AdultAttested`.
  **The club's reset is refused for an account that acts as a player** — attested, or holding
  a Player profile — which is the same predicate `/users/me`'s `profiles.acts_as_player`
  reports and the gate reads first. **The guard is `AdministratorAtClubDep`**: every
  administrator operation takes the club from its own path under
  `/api/v1/administrator/clubs/{club_id}` and meets `403 not_an_administrator` the request after
  a removal; it is also the only writer of *last used*, at most once an hour. And **playing
  requires the attestation**: `AttestedPlayerDep` refuses an assessment's start and a Player
  profile's commit with `403 adult_attestation_missing`, because sign-up no longer guarantees
  every account one. The club's five routes are under `/api/v1/club/administrators`; the
  player's are `/api/v1/invitations/{claim,password,by-token,{id}/acceptance}` and
  `POST /api/v1/users/me/adult-attestation`. `APP_SCHEME` is where the existing account's
  button opens the app. Seeded by `app/seeds/administrators.py`: at Ogrody 33, the
  administrator-only `administrator-only@raketa.example`, `rated-in-every-sport` who also plays,
  and `the-one-sport-player`'s pending invitation, resent by a run that finds it expired.
- **Signing out everywhere is one instant per account**
  ([ADR-0185](../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §7). A password change is an event on the account's own stream — `PasswordChanged` on a
  User's, `ClubAccountPasswordChanged` on a Club account's — projected onto the row as
  `credentials_changed_at`, which both surfaces' token resolution already reads; an access
  token issued **strictly before** it is refused as `access_token_revoked`, and
  `SignOutEverywhere` revokes the account's refresh tokens on that surface. The comparison
  reads the token's `iat_us` — microseconds **on the injected clock**, which is why
  `get_token_service` takes `ClockDep` — never the whole-second `iat`, which would sign a reset
  out of the session it opens.
