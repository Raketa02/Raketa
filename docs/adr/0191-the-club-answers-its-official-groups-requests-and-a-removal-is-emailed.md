# ADR-0191 — The club answers its official groups' requests, and a removal is emailed

- **Status:** Accepted
- **Date:** 2026-10-04
- **Narrows [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §7–§8.**
  *Approving* and *declining* an Official group's Join request are no longer only its
  Administrator's: **the club answers them too, at any time** (§1–§3). §8's *"a handover moves who
  answers"* now moves which Administrator answers; the club answers throughout. Nothing else in
  either section moves. The club still edits nothing in a group, deletes none and removes nobody.
- **Narrows [ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
  §8's** *"An Administrator … answers their join requests"*. They still do, no longer alone.
- **Amends ADR-0184 §7** by one consequence: **a removal is emailed to the person** (§4).
  *"Removal needs no push and no revocation list"* stands. The email informs, and enforces nothing.
- **Amends [ADR-0186](0186-email-goes-through-a-port-and-a-purged-queue.md) §3** by two messages,
  and narrows its *"every message … carries a button"*: **a notice carries none** (§5).
- Decided at the #529 QA walk of PRD [#500](https://github.com/Raketa02/Raketa/issues/500), at the
  product owner's ask: *evaluate whether the club can approve join requests at any time*, and
  *evaluate whether a removed administrator needs an email*. Both evaluations came out positive.

## Context

**A group could be left with requests that nobody could answer.** The club removes an
Administrator ([ADR-0184](0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
§7), and their Official groups *need an administrator* until a Handover. The club can hand a group
only to an **active** Administrator. A club between administrators, one that has invited somebody
who hasn't accepted yet, has nobody to hand it to. So the queue grew, and the player app already
said, on the group's row and in its comments, that *the club* approves while a group needs an
administrator. The club website had no way to do it. Two more states hit the same wall:

- the club's *Reset password* parks the person's groups until a new password is set (§Z4 of #529);
- an active Administrator may simply not answer: on holiday, or gone quiet in the WhatsApp group.

**A removal reached only an open app.** ADR-0184 §7 makes a removal take effect on the person's
next administrator request, and the app turns that refusal into a message. That message exists
only if the app is open in the administrator area when the next request goes out. Anybody else
finds out by their groups vanishing:

- someone signed out sees nothing when they sign back in;
- someone who has the app closed sees nothing at all;
- an administrator-only account the club removed signs in to *Start playing*, with nothing to say
  why.

An Administrator still *invited* has an email in their inbox whose link now reads *"That link has
expired. Ask the club to send a new one"*. That's misleading, because the club is who withdrew it.

Considered and rejected:

- **The club answers only while nobody runs the group.** It covers the orphan, but not the silent
  Administrator. It also makes the website's queue appear and disappear with a state the desk doesn't
  control: a reset, an acceptance or a handover elsewhere. And a desk could be refused mid-click
  because somebody became active a second earlier. One rule, *the club can always answer*, has no
  such edge.
- **The club hands the group to itself.** A Club account is not a User and can't be an
  Administrator ([ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md)).
  Making it one would put a club into the player app's profile model for one button.
- **Tell the removed person in the app only, on next sign-in.** It reaches nobody who doesn't open
  the app. It also needs a stored *you were removed* fact per account, read once, which is the
  revocation list ADR-0184 chose not to keep.

## Decision

### 1. An Official group's club answers its Join requests, at any time

The club **approves** and **declines** Join requests waiting on any of its Official groups, whoever
runs the group and while nobody does. The rules are the Administrator's own (ADR-0183 §7):

- **Approving** admits the player at once. Approving somebody already in changes nothing.
  Approving somebody with nothing waiting is `join_request_not_found`.
- **Declining** removes the request silently, and the player may ask again. Declining what isn't
  waiting changes nothing, and never removes a member.
- **Whoever answers first wins.** The other answer meets the settled state above.
- **Answering isn't running.** Who runs the group doesn't change, nor does *needs an administrator*.
- **A Player group is never its home club's.** No club answers one, even at its own courts.

The aggregate takes the answer `as_club`, and **only the two answers accept it**. Renaming, the
policy, the size and the sports stay the Administrator's. The events are the ones that already
exist: `join_request_approved` and `join_request_declined`, with `approved_by` and `declined_by` set
to **the Club account's id**, as a Handover's `assigned_by` already is. No event, field or migration
is added.

### 2. The club surface: one read and two answers

| Route (under `/api/v1/club`) | Answers |
| --- | --- |
| `GET /groups/{group_id}/requests` | everybody waiting, in the order they asked: `player_id`, the whole `name` (or `null`), and every sport they're rated in with its Level |
| `POST /groups/{group_id}/requests/{player_id}/approve` | `204`; `404 join_request_not_found` with nothing waiting |
| `POST /groups/{group_id}/requests/{player_id}/decline` | `204` |

Anything that isn't this club's Official group is `404 group_not_found`: no group, another club's,
or a Player group at this club. These are the same refusals as the Handover's.

**The club sees a name and Levels, and nothing more.** The request card is club mock 20's, without
the photograph. The website draws no photographs anywhere, so none crosses. No Player Score
crosses either, as everywhere a request is drawn. No block applies, because a club is in nobody's
block list.

### 3. The website: *Want to join · N* on the group's page

The page a Groups-table row opens is now **the group's page**: caption *Official group*, then a
**Want to join · N** card over the Hand over card. The card lists each person with their name, a
line like *Padel 2,44 · Tennis 2,60*, then **Decline** and **Approve**, a dark pill like mock 20's.

- **No confirmation for either answer**, as in the app.
- **The line under the title names who else can answer.** If someone runs the group: *"[name]
  answers them in the app, and you can answer them here too."* If nobody does: *"Nobody runs this
  group right now, so they wait for you. Answer them here, or hand the group over below."*
- **When nobody is waiting, there's no card.**
- **An answer somebody gave first** is said (*"… isn't waiting any more: somebody answered
  first."*), and the page is drawn again.

### 4. A removal is emailed, and which email depends on whether they ran its groups

`RemoveAdministrator` retires every live link (as before) and writes **one notice** to the mail
queue, in the same transaction. The test for which notice is **whether the administratorship ever
reached an account**. That is the stream's own `account_id`: the club's *Reset password* keeps it,
and a new Invitation clears it.

- **Somebody who ran its groups** gets *"[Club] removed you as an administrator"*. It says they no
  longer run its groups, that the groups stay with the club, and that their account stays, *"and so
  does anything you do on it as a player"*.
- **Somebody still invited** gets *"[Club] withdrew its invitation"*. It says *"The invitation it
  sent you no longer works"*, which also covers an existing account's in-app invitation, which had
  no code.

Both end *"If this is a surprise, ask [Club] about it."* and are signed *Raketa*. The club
website's *Remove* question now says *"Raketa emails them to say so."*

### 5. A notice carries no button and no code

ADR-0186 §3's messages each lead somewhere, and every one has a button. These two lead nowhere:
nothing is asked of the person, and nothing opens. A button to *Open Raketa* would be noise to
somebody who never installed it.

**The layout's button becomes optional, both its label and its address or neither, and a code
requires a button**, so a credential can never travel without the page it opens. The two messages
join §3's table:

| Message | Button | Code |
| --- | --- | --- |
| Removal of somebody who ran the club's groups | none | none |
| Removal of somebody still invited (*invitation withdrawn*) | none | none |

They go through the mail queue like the rest. They carry no secret, as the existing-account
invitation already doesn't, so the purge is only a cleanup for them.

## Consequences

**Easier**

- **No request ever waits on nobody.** A club between administrators lets its players in itself.
  The player app's *"[club] approves joins"* is finally true.
- **No new state**: no event, no column, no migration. The club's answers are the existing events,
  answered by an id the history already uses for the club.
- **A removed person knows**, wherever they are. The administrator-only account that lands on *Start
  playing* has an email in its inbox saying why.

**Harder**

- **Two parties can answer one queue.** A desk can decline somebody an Administrator meant to let
  in. The decline is silent and the player may ask again, so it costs a second tap. An approval
  **can't be undone**, because nobody removes a Group member (ADR-0183 §7). The club is the
  accountable party for its Official groups, and that is the trade, named.
- **The club now reads players' names and Skill Levels**, which it never did before: one read per
  group page, only of people who asked to join that club's group. Who sees what on the club surface
  now includes players, and a future data-export or erasure flow has one more reader to account
  for.
- **The history no longer says *the Administrator* when it says who answered.** `approved_by` is
  sometimes a Club account's id. Nothing reads it today but the log line; a future reader must not
  assume it names a User.
- **Two more emails** a person may not want, including one to a mistyped address the club invited
  and then withdrew. That person already got the invitation, so the second email tells them to
  ignore the first.
- **The removal email is sent at the removal, not when the app hears it.** Someone with the app
  open now gets both the in-app message and the email. Both say the same thing.
