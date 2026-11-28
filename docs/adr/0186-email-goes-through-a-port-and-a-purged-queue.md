# ADR-0186 — Email goes through a port and a purged queue, and nothing is sent until a domain exists

- **Status:** Accepted
- **Date:** 2026-09-25
- **§3 amended 2026-10-04 by [ADR-0191](0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)**: two removal notices join the table, and **a
  notice carries no button and no code**. Every message that leads somewhere still has a button.
- **Follows [ADR-0091](0091-photo-storage-behind-a-port.md)'s shape**, where a port has a local stand-in
  and a deployed adapter selected by configuration. Here that's a mail catcher locally, and a
  production sender that stays off.
- **Narrows [ADR-0003](0003-transactional-outbox-for-event-delivery.md)'s** *"We will deliver
  all side effects through a transactional outbox"*. An email that carries a secret is delivered
  through **a second queue**, the mail queue, whose row the use case writes in its own transaction
  (§2). Every other side effect still goes through the outbox. 0003's reasons all carry over: the
  same transaction, delivery after commit, `SKIP LOCKED`, at least once. Its rule *"a use case that
  calls an external API directly is a defect"* stands, because the use case writes a row and a
  worker does the sending.
- **Runs on [ADR-0092](0092-periodic-jobs-as-embedded-loops.md)**: the sender is an embedded loop,
  safe to run twice at once.
- **Distinguishes [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)'s *no presentation*
  rule.** An email is text the backend writes, and that's allowed, because an email has no client to
  render it (§4).
- **Follows [ADR-0028](0028-four-environment-model-and-typed-configuration.md)'s refusals** for every
  new setting.
- Settles [#501](https://github.com/Rakieta02/Rakieta/issues/501) for the PRD
  [#500](https://github.com/Rakieta02/Rakieta/issues/500). Built by
  [#507](https://github.com/Rakieta02/Rakieta/issues/507), with the invitation emails in
  [#508](https://github.com/Rakieta02/Rakieta/issues/508).

## Context

**The backend can't send email**, and PRD #500 needs it for:

- invitations to administrators, in two variants (new person, existing account)
- the club's reset of an administrator's password
- *Forgot password?* for players, administrators and clubs
- the resend of each

Every one of them but the existing-account invitation carries a **secret**: a link token and an
8-character code. ADR-0184 §4 rules that a secret never enters the event store.

**No domain exists yet.** Nothing can be sent from a real address, and only `local` runs
([ADR-0010](0010-local-first-development-aws-deferred.md)). The product owner still has to walk the
whole journey by hand, opening invitations and reading codes, without a real mailbox.

Rejected on the way:

- **Sending inside the use case.** The request would wait on an SMTP server. An email could leave for
  a transaction that then rolls back, which is an invitation to an administrator who doesn't exist.
- **Sending from an outbox handler after commit.** The outbox stores serialised **domain events**, and
  the email needs the token and the code. Putting them in the event would write a secret to the event
  store. Having the handler mint the secret would move issuing a credential out of the use case that
  decides it.
- **A hosted email API from day one.** It brings a vendor and a key for a platform with no domain. It
  can still arrive later, behind the same port.

## Decision

### 1. A mailer port, with an SMTP adapter

A **mailer port** sends one rendered message. Its adapter speaks **SMTP**, configured by settings.

- **Locally**, the adapter points at a **mail catcher container** (Mailpit) in the dev stack. Every
  email lands in its web inbox at `localhost:8025`, and none leaves the machine.
- **The production sender** is the same adapter pointed at a real relay. It **stays off until a domain
  exists.** Selecting an environment that would send, without its sender configured, fails at start.
  It never falls back to not sending (ADR-0028).

The settings cover the **sender address**, the **SMTP connection**, the **public site URL** that links
are built from, the **club website URL** for the club's own reset page, and the **app scheme**. All of
them follow the environment refusals, and none of them is a literal in code
([ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §7).

### 2. A use case never sends. It writes a mail queue row, and a worker sends it and purges it

A use case that issues a secret **renders the whole message into a mail queue row, in its own
transaction**: recipient, subject, plain text and HTML, link and code included. The row and the act
that issued the secret commit together or not at all.

A **worker**, an embedded loop (ADR-0092), claims rows with `FOR UPDATE SKIP LOCKED`, sends each one
through the port, and then **purges the secret body**. What stays is what a person debugging delivery
needs: the kind of message, when it was sent, and whether it failed. The token and the code don't stay.

**Delivery is at least once.** A process that dies between the send and the mark will send again. A
duplicate invitation is harmless, and a lost one isn't.

**This is a second queue, not the outbox.** The outbox carries domain events to handlers and keeps
nothing secret. The mail queue carries rendered messages to one port, and it is **the one place a
secret sits, for as long as it takes to send it**.

### 3. The messages

| Message | Button | Code |
| --- | --- | --- |
| Invitation, new person | public site `/invite/<token>` | yes |
| Invitation, existing account (*"[Club] wants to make you an administrator"*) | opens the app | none: no credential, no password step |
| The club's *Reset password* of an administrator | public site `/invite/<token>` | yes |
| *Forgot password?*, player or administrator | public site `/reset/<token>` | yes |
| *Forgot password?*, club | the club website's own *Set a new password* page | yes |
| Resend of any of the above | as the original | as the original |

**The club's reset reuses the invitation's page.** It puts the person back to *invited*
([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md) §6),
and the invitation's *Set your password* already sets a password for exactly that state. A
third page would say the same thing in different words. The credential still expires at 72 hours,
the invitation's own lifetime.

Every message is **plain text and HTML**, carries **a button**, and is written by **Rakieta**. Every
message that carries a credential also carries **its code**, which is all of them except the
existing-account invitation. The brand is the same everywhere
([ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §8).

### 4. An email's words live in the backend

[ADR-0022](0022-kernel-negative-space-and-constant-homes.md) says that what crosses the API is values
and machine codes, never display text, because every client renders its own sentences. That rule
exists for text a **client** renders. **An email has no client.** It goes from the backend to a mailbox,
and nothing in between could render a code. So the email's copy lives **with its templates in the
backend**, and the backend is the renderer. The API rule is untouched. Nothing here lets the backend
send a sentence to an app.

### 5. Tests read the emails a person would read

The API tests replace the adapter with a **recording mailer**. A test **drains the queues** and then
reads the emails sent, with their links and codes, the way a person would. A **controllable clock**
checks the 72-hour and 1-hour expiries without waiting. Nothing asserts which table was written.

## Consequences

**Easier**

- The product owner opens every invitation and code in one local inbox and walks the journey by hand.
- An email and the act that caused it can't disagree: they commit together.
- No secret outlives its send, and the event store never holds one.
- Moving to a real relay, or to a hosted API later, is configuration and one adapter. No use case
  changes.

**Harder**

- **Deliverability is unhandled.** SPF, DKIM, DMARC, bounces, complaints and a suppression list are all
  absent. Turning the production sender on brings every one of them, and that work belongs to the
  domain, not to this record.
- **The copy lives in two places now.** The app's words are in the copy deck, and the emails' words are
  in backend templates. Nothing checks that the two share a voice.
- **A live secret sits in the database until the worker runs.** The purge is the control. It's tested,
  and nothing in production would notice if it stopped.
- **One more container runs in the dev stack**, and one more embedded loop runs in every API process.
- **At least once means a person may get the same email twice.** Each copy carries the same credential,
  so either works and the second is only noise.
