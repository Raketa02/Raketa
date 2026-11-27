# ADR-0200 — A level is asked where play begins

- **Status:** Accepted
- **Date:** 2026-11-03
- **§7's Home card amended 2026-11-07 by
  [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)'s
  amendment of that day** (the mechanics Q129): while a friend's ask for a level is a card on Home,
  that card is drawn instead of *Get your level*, which comes back if the ask is set aside and the
  player is still rated in nothing. A dated note marks the passage.
- **§7's Home card restored 2026-11-16 by
  [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)**
  §4 (PRD [#810](https://github.com/Raketa02/Raketa/issues/810)): a friend's ask waits in *Needs your
  answer*, the sheet behind Home's envelope, and is never drawn instead of *Get your level*. The card
  shows whenever §7 says, asked or not. The same dated note marks it.
- **One more door, 2026-11-07, from [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)**
  §5 (the mechanics Q130): the Rankings page offers ***Get your {sport} level*** in a sport the reader
  has no level in. It starts that sport's questionnaire, and the pass returns to Rankings, as every
  pass ends where it began. Nothing else here moves.
- **Amends [ADR-0090](0090-onboarding-per-player-checkpoint.md)'s entry gate.** The questionnaire
  leaves onboarding, and with it two destinations: *unfinished run → resume* and *no ratings →
  welcome*. The gate reads the account's profiles (ADR-0185 §3), then *no nickname* (ADR-0199
  §3), then *no Player profile*, then the app (§1). The profile's checkpoint and its one commit
  stand.
- **Amends [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §3.** A rating pass (the player app's onboarding pass, which ADR-0179 §3 first let begin outside
  onboarding) has three origins: a group's tab, Home and the Skill passport. It ends where it began,
  so a pass from a group ends on the group. **An unfinished run is never forced** (§5).
- **Amends ADR-0179 §1's group title**: *Finding players* is ***Your games*** (§10).
- **Amends ADR-0179's *cannot finish without an area* lines**: §2's *Where you play* row and §8's
  *Not `has_location`*. Both still hold: an area is still required, and a club the player picks
  stands in for a reading (§10).
- **Amends [ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s ordering
  argument**, its Context's *a profile does not exist until every rating already does*. A profile
  now exists before any rating. The decision the argument was for, intent in its own aggregate,
  stands and needs it less. Its stale *declared at the tail of every rating run* is corrected: intent
  is declared on the group deck's declaration step and on the You tab.
- **Amends [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md) §1 and
  §2's length**: an intro is up to **250** characters (§9). Everything else in it stands.
- **Adds a dated note to [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
  §6.** The cold-start refresh still runs, but no deck deals around the cell any more. Once the
  phone has permission, its reading replaces a club-picked area (§10).
- **Is the new record [ADR-0188](0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
  §5 asks for**: the phone-preferences store gains a fourth value, *the guide was shown*, **per
  phone rather than per account, and kept at sign-out** (§8).
- **Leaves standing** `CONTEXT.md`'s invariant *There is no onboarded player*, which is now true of
  the screens as well as the data; and the reason the questionnaire sat at sign-up, *no first game
  unrated*, which the door now keeps (§6).
- **Does not decide** the questionnaire itself (its questions, its engine, the 30% ceiling, the
  review), a privacy policy and its link at sign-up
  ([#735](https://github.com/Raketa02/Raketa/issues/735)), making location optional or a map, the
  tags, photos, week and gender steps beyond their counter, screen-reader support
  ([ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md)), Explore, or the
  Friends tab beyond its door.
- Settles the rest of PRD [#722](https://github.com/Raketa02/Raketa/issues/722), decided in the
  onboarding grilling on 2026-11-03 (Q1–Q12, Q14–Q22, Q25–Q29) and written by
  [#723](https://github.com/Raketa02/Raketa/issues/723). Built by
  [#726](https://github.com/Raketa02/Raketa/issues/726) (the intro and an area from a club),
  [#727](https://github.com/Raketa02/Raketa/issues/727) (the notice),
  [#729](https://github.com/Raketa02/Raketa/issues/729) (a pass returns to its origin),
  [#730](https://github.com/Raketa02/Raketa/issues/730) (onboarding and the door),
  [#731](https://github.com/Raketa02/Raketa/issues/731) (*+ Another sport*, the Home card, the
  notice on the phone), [#732](https://github.com/Raketa02/Raketa/issues/732) (the guide) and
  [#733](https://github.com/Raketa02/Raketa/issues/733) (the intro and location steps).

## Context

**Signing up takes 20–24 screens before Home.** Kuba sends Ania a link to *Wednesday padel*. To get
there she taps through sign-up; *How should people see you?*; *Let's set you up* (a card about the
questions ahead, then three cards headed **Value**, **Mission** and **Vision**); *Which sports do
you play?*; between 6 and 9 questions for padel, two taps each; *Check your answers* and a
calculating screen; *Your rating*; *Your starting ratings*, the same numbers again; six profile
steps; and *What Raketa keeps*, eight cards about data. With tennis as well, it is 28–36 screens.

**Most of it isn't needed when she signs up:**

- **A rating is read only where play happens**: a group's Games, Fill in and Friends tabs, Post a
  game, and Members. Joining a group, the chat and You read none.
- ***Let's set you up* and *What Raketa keeps* record nothing.** *Start playing* calls nothing, and
  no document says the data screen is legally required.
- ***Your starting ratings*** repeats *Your rating*. *Your rating* itself shows three numbers
  (**2,71**, **1,87–3,55**, **30%**), each with an ⓘ she has to find and press herself.
- **The location step contradicts itself.** It says *"to show you nearby players"* (there is no
  players search any more) and *"You can finish setting up without an area"*, and yet *Finish*,
  two screens later, stays blocked until an area is set. The area today only measures how far a
  club is.
- **The intro is cut at 100 characters**, under a paragraph of rules.

**Why the questionnaire sat at sign-up.** So that nobody plays a first game unrated: a lopsided
first game drives newcomers away. ADR-0094 built on that order, and ADR-0090's gate enforced it.

**Moving it, as the app works today, would strand people.** A player rated in nothing who opens a
player group sees all three tabs blank, with no sport chip. She is never dealt a game, so Raketa
never tells her anything. She is missing from Kuba's Members list. And an unfinished questionnaire
takes over every launch until she finishes it, because the gate's first branch resumes it.

**The market.** Playtomic asks for a level only *"if you want to join open matches or
competitions"* ([Help: How to create your account](https://playerhelp.playtomic.com/hc/en-gb/articles/19831938095633),
read 2026-10-08). Apple's [App Review Guideline 5.1.1(iv)](https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage)
says apps must not *"force people to consent to unnecessary data access"*, and gives the example
*"if a user declines to share Location, offer the ability to manually enter an address"*.

**The alternatives:**

- **Keep the questionnaire at sign-up and shorten it.** Its questions are the engine's, out of
  scope, and 6–9 per sport is what an Initial estimate costs.
- **Ask on the first yes.** The deck would deal cards to somebody it cannot place: the level window
  needs a level before a card is made.
- **A door on Games only.** Fill in, Friends, Post a game and Members would stay blank. Every way of
  playing should ask the same thing (Q14).
- **Make location optional** (Q11). The area measures every distance to a club and orders every
  club search. Apple asks for another way to give it, not for no area at all.

## Decision

### 1. Onboarding is a nickname and a profile

Onboarding is **sign-up, the naming (ADR-0199) and the six profile steps**, and it ends on Home:

> Sign-up → *How should people see you?* → *What kind of player are you?* → *Say it in your own
> words* → *Your court photos* → *When do you usually play?* → *Where do you play?* → *Who do you
> want to play with?* → Home.

The steps count *Step N of 6*, and *Finish* on the last lands on Home. ***Let's set you up***,
***Your starting ratings*** and ***What Raketa keeps*** go, with their routes and their words. The
questionnaire's own screens stay, and are reached from where play begins (§2–§7).

**The entry gate** reads the account's profiles first (ADR-0185 §3), then *no nickname* → the
naming, then *no Player profile* → the profile steps from step 1 (ADR-0090), then the app. **Zero
ratings and an unfinished run route nowhere.**

### 2. In a player group, a player rated in nothing meets one door

**Games, Fill in, Friends, Post a game and Members** each show one door: ***Get your level — pick
the sports you play, a few questions each***.

1. It opens *Which sports do you play?* over every sport, with **nothing pre-ticked**.
2. The questions run for each sport she picked. After each sport, *Your rating* offers ***Rate
   {next sport}*** and ***Done for now***.
3. The last *Your rating* offers ***Back to {group name}***, which returns her to the tab she began
   on. On Games, the one-time intent question (*Your usual game at padel*) comes next, then the
   deck, as for any sport without an intent.

A sport she rates needn't be one the group plays already. If she rates only tennis while in
*Wednesday padel*, the chip says *Tennis* and the tabs show tennis: a player group holds any sport.

### 3. An official group keeps its own card

While she is rated in none of an official group's sports, every tab keeps today's card: ***This
group plays padel · Add padel to your Skill passport to see its games. · [Rate padel]***. It offers
only that group's sports, one button each. **The pass now returns to the group**, with the chip on
the sport just rated, not to the Skill passport. Post a game's ***Get rated in padel to post
here*** begins a group pass the same way.

### 4. The sport chip appears only once there is a rating, and ends with *+ Another sport*

The group page's sport chip is drawn **only when the player holds a rating to list**, and it lists
only sports she is rated in. While a sport is left to offer, it ends with ***+ Another sport***,
which opens the same picker:

- in a player group, over **every sport she is unrated in**;
- in an official group, over **that group's sports she is unrated in**.

A player rated in everything there is to offer sees no *+ Another sport*. The pass returns to the
group.

### 5. A pass has an origin, and an unfinished run is never forced

**A pass records where it began, and ends there:**

| Origin | Where it ends |
| --- | --- |
| A group's tab (the door, the official group's card, Post a game's card, *+ Another sport*) | that group, on that tab, with the chip on the sport just rated |
| Home (the card, §7) | Home |
| The Skill passport (*Add a sport*) | the Skill passport, as ADR-0179 §3 decided |

*Done for now* ends the pass at its origin too.

**Leaving halfway never takes over the app.** The gate has no resume branch. Where a door or the
Home card stands and a run is in progress, it reads ***Carry on with your padel questions — you're
on question 5*** and opens that run. The run itself is unchanged: its transcript is on the server,
and it resumes at its outstanding question as ADR-0019 and ADR-0020 provide.

### 6. Every way to play stands behind the door, so nobody plays a first game unrated

**The reason the questionnaire sat at sign-up still holds, and is kept here instead.** An unrated
player cannot say yes, post or take a seat: the backend's refusals are unchanged. Each of those
stands behind the door, and the deck deals her nothing until she has a level.

**Members still lists only members rated in the sport**, so an unrated member is absent until she
rates. In a player group, her own Members screen shows the door instead of a blank list. *(A call
made in the spec, not grilled.)*

### 7. Two nudges, for a player who never opens a group

- **The Home card.** ***Get your level — your groups can't deal you games until you have one.*** It
  shows while she is a member of at least one group and holds no rating. With a run in progress it
  offers to carry on. It opens the picker, and the pass returns to Home. *(Amended 2026-11-07 by
  [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)'s
  amendment of that day, Q129: while a friend's ask for a level is a card on her Home, that card is
  drawn instead of this one, in its own row, and this one comes back if she sets the ask aside still
  rated in nothing.)* *(Restored 2026-11-16 by
  [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
  §4: the ask waits in *Needs your answer*, behind Home's envelope, and this card shows whenever the
  sentence above says, whether or not anybody asked.)*
- **The *Get your level* notice.** ***Get your level so your groups can deal you games.*** It goes
  **once per account, ever**, to an account that is a member of at least one group (player or
  official), whose first group join was at least 24 hours ago, and which holds no Skill rating. It
  names no group and no sport. It is **always on**, opens **Home** and is never emailed. A timed job
  tells it, on the same pattern as *How did it go?*, under a per-account key, so no process ever
  tells it twice. The groups context answers *when did this account first join a group* through a
  port.

A player who holds any rating sees neither.

### 8. The guide on *Your rating*

**The first *Your rating* a phone ever shows** carries a guide to its three numbers:

1. The screen dims, and a spotlight picks out **the level**, with a bubble holding today's ⓘ text,
   ***1 of 3***, ***Next*** and ***Skip***.
2. *Next* moves the spotlight to **the likely range** (*2 of 3*).
3. Then to **the confidence** (*3 of 3*, ***Got it***). Its bubble keeps *"The questionnaire can
   provide up to 30% confidence"*, so a 30% does not read as Raketa doubting her (Q7).

A tap on the dimmed area counts as *Next*, and nothing underneath can be pressed while the guide is
open. The device's back button counts as *Skip* *(a call made in the spec, not grilled)*. It shows
whatever the pass's origin. **It never shows again on that phone**, finished or skipped. The ⓘ
marks and their popovers stay, and the Skill passport's cards never run the guide.

**Where it is remembered.** It is a fourth value of ADR-0188's phone-preferences store, the one
module that may touch device storage. Unlike the other three, it is **per phone, not per account,
and kept at sign-out**: the ruling was once per phone (Q1–Q4).

### 9. The intro is up to 250 characters

The intro's cap moves from 100 to **250 characters**, and the counter reads *n / 250*. It is still
one line with no line breaks, still optional, and still refused for a phone number, an email, a link
or a handle. The paragraph of rules on *Say it in your own words* goes: the contact rule is said
only when broken, as *Leave out phone numbers, emails, links and handles — people reach you in the
chat.* The request schema and the column stay uncapped, as today.

ADR-0170 §4 argued that 100 characters fitted the deck card's two lines. That card went with
Classic play. The record draws the intro whole, in quotation marks under the nickname, and still
never truncates it.

### 10. Location stays required, and a refusal can pick a club

**The step tells the truth**: *"Raketa shows how far each club is and lists the nearest first. Your
area is rounded to about a kilometre and never shown to other players."* Its button is ***Use my
location***, and *Continue* appears only once an area is set. Every line about *nearby players* or
*matching* goes.

**A player who refuses** (permission denied, blocked, or no fix) is offered ***Pick a club near
where you play***. It searches Raketa's clubs by name or district, A–Z because she has no area yet.
**The pick becomes her area**: that club's point on the map, rounded to the cell like any reading.

- **Both writes take either a reading or a club**: the profile commit and the location change
  carry `latitude` and `longitude`, or a `club_id`. An unknown club is refused. The phone never
  needs a club's coordinates.
- **You › Where you play offers both ways.**
- **The cold-start refresh is unchanged** (ADR-0174 §6). It reads the phone only when permission
  exists, so once she allows location, the phone's reading replaces the club she picked.

**This reverses one practice and keeps one rule.** The practice since 2026-08-25 was *refusing
degrades, never blocks*: the step said a player could finish without an area. It never could, since
the commit requires one. The rule stays: **a Player profile cannot exist without a Location area.**
A club picked by hand now stands in for the reading, which is the alternative Apple's 5.1.1(iv)
asks for.

**The You tab's group *Finding players* is renamed *Your games***, on the tab and as its screens'
eyebrow. Nothing on it finds players any more.

## Consequences

**Easier**

- **Eight screens to Home.** Ania can join Kuba's group and chat before she answers a question.
- **A level is asked where it unlocks something**, in every place it does, and each pass ends where
  she was.
- **A player who refuses location can still finish**, honestly, and the step no longer promises
  what *Finish* refuses.
- ***There is no onboarded player*** is now true of the screens: onboarding rates nobody.

**Harder**

- **A player can stay in groups unrated, indefinitely.** One card on Home and one notice ever are
  the only nudges. After that Raketa says nothing. *N members* counts her, and Members doesn't list
  her.
- **A Player profile with no rating is now the common shape.** ADR-0090 called it representable and
  never produced. Every surface that assumed a rating now meets the empty case: the chip, the You
  header's sport pills, the passport, and ADR-0188's *last sport* default (*the first sport the
  player is rated in*), which has no value to give.
- **"No first game unrated" is now kept by the door and the backend's refusals**, not by the order
  of the screens. A new way to play added later must stand behind the door, or it reopens the gap.
- **A pass now has three endings, plus *Done for now*, plus a mid-pass button.** Every
  combination of origin and position has to be routed, or a pass strands somebody in the
  questionnaire.
- **A club-picked area is a coarser truth.** Distances are measured from the club she picked, not
  from where she is, until she allows location.
- **The guide is per phone.** A new phone shows it again, and a second account on the same phone
  never sees it.
- **An intro of 250 characters is two and a half times the text to moderate**, fenced for contact
  only, with no report.
- **One more timed job and one more port.** Notifications learns from groups when an account first
  joined one, and a per-account key has to hold across every process.

**Neutral**

- The questionnaire, its engine, the 30% ceiling, the review and the assessment routes are
  unchanged, and so is every refusal an unrated player meets.
- *What Raketa keeps* goes, and nothing said it was legally required. A privacy policy is a
  lawyer's to-do, #735.
- ADR-0094's decision stands without its ordering argument. Intent lives in its own aggregate, and
  is asked on the deck for a sport without one, as it already was.
