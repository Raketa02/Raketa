# auth — sign up, sign in, session restore

> The design record for `src/features/auth/` — what the feature does and the reasons the shape
> is what it is, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so it loads
> when this feature is being changed rather than on every turn. **Append here** when a ticket
> changes what this feature does. Index: [`README.md`](README.md).

**Sign-up asks whether the player is an adult, and it is an attestation.** The platform is
adults only, and that is a precondition of _holding an account_ rather than a rule about who
is shown to whom ([ADR-0124](../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
What the form collects is **one boolean — never a date of birth**, and it is **not age
verification**: there is no date picker anywhere in this app and this is not where the first
one arrives. The box is never pre-ticked, _Create account_ is never disabled by it, and the
refusal is a sentence under the box rather than a closed control
([ADR-0089](../../../docs/adr/0089-player-profile-context-event-sourced.md)). The same sentence
renders when the server refuses by `adult_attestation_required` — an older build or a
replayed request can carry a body this form would not have sent, and _try again_ would then
be the one thing that is not true.

**Sign-up asks for credentials only, and the naming is this feature's screen inside onboarding**
([#451](https://github.com/Raketa02/Raketa/issues/451),
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
The nickname left the sign-up form: choosing credentials and saying who you are are two different
moments, and a sign-up refused for a taken handle was a sign-up refused for a reason that had
nothing to do with the account. What replaces it is **the naming** — _How should people see
you?_ — a **Name** (free text, spaces allowed, never unique, 2–64 after the trim and the
collapse) and a **Nickname** (the handle under the rule the sign-up form used to state, unique),
submitted together as one act, `PUT /users/me/name`, repeatable. The screen lives in
`features/auth/` on the second part's own precedent — the values are the users context's and the
follow-up that edits them from the You tab will drive the same schema, mutation and sentences —
and the route file under `(onboarding)/` is what makes it onboarding's first screen. The
nickname's rule is written under its box before anything is typed, so a refusal never surprises;
a taken handle comes back by code with its field and lands under that box, exactly as the
sign-up conflicts always did. **The step cannot be skipped**: the device's back is claimed and
refused, and on success the mutation writes what the server recorded into the cached player and
_awaits_ a fresh read of `/me` before the screen hands the next destination to the entry gate —
`router.replace('/')`, as the data screen leaves the second part — because where a named player
belongs is the gate's rule and not this screen's. **The re-read is a `fetchQuery` on the one
query definition, not an invalidation**: nothing on the step observes the player, an unobserved
entry is garbage-collected after five minutes, and an invalidation of an entry that is not there
refetches nothing and resolves at once — the re-read would then be the gate's, which is correct
and not the promise. `fetchQuery` creates the entry where it has to and _throws where the read
failed_, so a naming the app could not confirm keeps the player on the step under the
could-not-reach banner rather than moving on; the act is repeatable, and the next _Continue_ is
the same request with a re-read that answers. `AuthenticatedUser` carries `name` and
`nickname`, both absent until the naming, and the **You tab draws the name, `@nickname` under it
and the email** — one of the two screens that draw a handle, the other being the record.

**The naming, from the You tab** ([#469](https://github.com/Raketa02/Raketa/issues/469),
[ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
§7 — the follow-up ADR-0171 left open). **The refactor came first**: `useNamingForm` is the
form — what is typed, what the schema refuses before a round trip, the send through
`useNamePlayer`, the server's refusal with the field it names — and `NamingFields` draws the
two boxes, the handle's rule and each refusal under its box, with the banner above them; the
naming step is now that form under its own chrome (the eyebrow, the question, _Continue_, a
back that is refused), and its suite is unchanged. **`NameScreen`** is the same form under the
tab's chrome — _On your card · Name_, a way back, `avoidsKeyboard` — pre-filled from
`GET /users/me` with _Save_ where the step says _Continue_ and no sentence over the boxes: the
step's question does not need repeating on a screen that only edits the answer. A taken handle
is the server's `409 nickname_already_taken` on the press, drawn under the box in the app's own
sentence exactly as the step draws it, and never a lookup while typing (ADR-0159's
enumeration). The mutation writes what the server recorded and awaits the re-read before it
resolves, so the tab's header card and the **`NameRow`** — _Ada Lovelace · @ada_, the name and
the handle together or nothing, which makes the tab one of the two places the handle is drawn —
already say the new name on the way back. **`AccountPanel` is the button now.** The name, the
handle and the email it drew were the way to tell which player the gate let through while the
tab was a placeholder; the header card and the _Name_ row say the first two, and the email has
no row because it has no route (ADR-0179 §9) — a fact with no door under a list of facts with
doors reads as a broken row. _Sign out_ stays at the foot, `dark` and not `primary`, the only
way out of a session.
