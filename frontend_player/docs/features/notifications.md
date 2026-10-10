# notifications — You › Account › Notifications, push, the banner and the recent list

The client side of the backend's **Notifications** context (#549): the three notices a player
chooses, the phone pushed every notice given to them, a push drawn as a banner while the app is
open, and the recent notices behind a bell on Home. Built by
[#559](https://github.com/Raketa02/Raketa/issues/559) from the Games & Fill in screens (A7.2, A9;
mocks 50, 52, 53), the mechanics (§17.2) and
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5. The shell
composes `NotificationsRow` into the You tab's **ACCOUNT** group under _Payments_, `NoticeBell` into
Home's header and `NoticesHost` beside the tabs; the screens are `/you/notifications` and
`/notices`.

**The words of a notice are the backend's.** A notice's title and body are drawn by
`notifications/application/words.py` at push time and again at every read, because the phone's
system draws a push before the app runs. The list draws the same words; the app writes none of its
own about a notice. What the app decides is **where a tap opens** (`domain/notice.ts`'s `targetOf`)
and **how _when_ is said** (`givenWhen`: the clock today, _Yesterday_, a weekday within the week, the
date past it — by the Warsaw calendar, never by the hours since).

**Where a notice opens** (A9): `BOOKING` the booked game's details over Home (`proposals`'
`bookedGameRoute` — the booking's id is the game's own), `PROPOSAL` a game still filling — or one
that did not fill — in its group (`gameRoute`), and `DECK` the group's deck **with the card on top**
(`groups`' `groupDeckRoute`). **A Fill in alert is the one notice whose kind decides**: the backend
sends it as `BOOKING` to a reader who is **not in the game**, so it opens the open seat seen from
outside, in its group (`rescueRoute`, A4.3) — the booked game's own details would tell that reader the
game is not theirs any more. **One function opens all four** (`useOpenNotice`'s `destinationOf`: the
route, and the read behind it), whichever way the
tap came — a row of the list, the banner, the phone's own notification — and it **pushes over
wherever the player is**: a notice is not a tab press, so nothing is laid down and _back_ goes where
the player was. The read behind the screen is marked stale first, so a deck read twenty seconds ago
does not open without the card the notice is about. A notice whose sport or kind this build cannot
name is listed, words and all, and opens nothing.

**The deck opens at the card** (A9: _the deck opens with the card on top for You complete it,
Challenges and Your new game_). The group page's route takes the card's sport, kind and id beside the group's
(`parseGroupRouteParams`' `arrival` — all three or none; an arrival this build cannot read opens the
page as it always opens). The page stands on the card's sport until the player picks another —
**opening is not picking**, so the phone's last sport is untouched (ADR-0188 §2) — moves the switch to
the card's kind, turns to Games, and `GamesDeck` draws the card first while it is dealt
(`proposals`' `withOnTop`). Once it is answered, filled or gone the deck is the server's order again.

**The three choices save on every tap**, Games & money's shape for its reasons
(`useSaveNotificationChoices`): the chip turns before the answer, a tap turns from the last tap, the
saves go one at a time in the order tapped each sending all three, only the last one in flight
writes its answer, a refusal says so under the cards and the three are read again, and offline the
taps are held. The row's line is the chosen ones that are on, short — _You complete it · Challenges ·
Fill in alerts_ (mock 50) — or _Only the ones always on_.

**The eleven always on are words and a tag, never controls.** Mock 52 drew seven; the rows are
A7.2's as [#620](https://github.com/Raketa02/Raketa/issues/620) amends it, a row a line of the
mechanics §17.2's table, in its order ([#628](https://github.com/Raketa02/Raketa/issues/628)): _It's a
game! · you paid_ · _It's a game! · the club answers by …_ · _Waiting for one payment_ · _Confirm your
payment by … to keep your seat_ · _Game called off · with the refund_ · _Someone left your game · or
it's filling again_ · _You've been refunded_ · _The club confirmed / said no / didn't answer in time_ ·
_Your new game_ · _A game you left_ · _Your post didn't fill_. One row can be several notices — _the
club confirmed / said no / didn't answer in time_ is three, _A game you left_ two — and a row names a
notice before the backend gives it: _Waiting for one payment_ comes with #625, _A game you left_ and
_filling again_ with #623. Each has 6.4's green **on** tag, one element to a listener (_…, always
on_). The three choices are **switches** (`OnOffChip`): 6.2's pill
drawn _On_ ink-filled and _Off_ outlined, spoken as the choice's name and line with its `checked`
state, because the word drawn is the state.

**Asking is the line at the top, and only there** (A7.2; `docs/architecture.md` Part 13: _just in
time, never a wall at launch_). While the phone may not show a notice the screen opens on a card
offering **Allow notifications**; pressed, the OS asks (`ensurePermission`), and a yes registers the
phone at once. A phone that will never ask again is offered **Open settings**, and the answer is read
again on the way back. The line is offered **every time** the screen opens while the answer is
missing — A7.2 says _the first time_ — because it is the one way back to pushes. **Nothing else asks**:
a launch only reads the permission.

**The phone is registered by `usePushRegistration`, under the tabs.** Once the permission is granted
— at launch, after a sign-in, the moment _Allow notifications_ is answered yes — it reads the token
and `POST /players/me/devices` with it in the body, **once per token per session**; again when the
system replaces the token (`onTokenChange`); and again on the next return to the app after a
registration failed. A mutation, held offline and sent on reconnect, as the location refresh's write
is; a failure is said to nobody, because nobody pressed anything. The permission is one answer the
screen and the registration share (`notificationKeys.permission()`, `networkMode: 'always'`, never
fresh, so every return to the foreground reads it again).

**The phone is let go at sign-out — the sign-out's first step, and `auth`'s.** `signOut(phone)` asks
the push port for the token **whatever the permission says now** — a phone registered while it
allowed notifications and switched off since would, switched on again with nobody signed in, show the
last player's notices — and `POST /players/me/devices/removal` with it, **beside the revoke and before
the session ends**, because it needs the access token; best-effort, as the revoke is, and side by side
with it so an offline sign-out waits for one timeout rather than two. The token read is bounded by the
app's request timeout, because minting one asks Expo's servers. **A session that ends by itself cannot let the phone
go** — the refresh was refused, so there is nothing to sign the removal with — and that phone is
still pushed the last player's notices until somebody signs in on it (the backend moves a phone to
whoever registers it last) or Expo reports it gone. See the calls below.

**A notice while the app is open is the banner** (`NoticeBanner`, chosen by `useNotices`; A9's
_in-app banner_), and **the banner has two sources**, because A9 gives it a column of its own beside
the push — a player who never allowed notifications, or on a phone that cannot be pushed yet (every
phone, until the Expo project exists), is still told while the app is open:

- **A push arriving** is the banner at once. No foreground handler is set, and a notification nobody
  handles in the foreground is not presented, so the phone draws nothing itself.
- **The list behind the bell is read for the session** — on the way in, on every return to the app,
  whenever a push marks it stale, and **every minute while this phone is not being pushed**
  (`usePushRegistration` answers whether it is) — and a notice the session has not seen before is the
  banner, the newest if a read brings several.

**Each notice is drawn once.** What the session has seen is every id in its first read — so **a
launch draws nothing**: what was told while the app was closed is in the bell's number, which is the
catch-up (Q101, [#627](https://github.com/Raketa02/Raketa/issues/627)) — and a pushed notice's id the
moment it is drawn, so the list read after it does not draw it again; a notice the day bundled another
into keeps its id, and is not new. **Coming back from the background draws the newest notice the
session has not seen, and the number counts the rest** — the bannered one too: the number is the
server's, and a banner is not a visit. **A notice of the player's own act is never
the banner** (Q102): the list marks it `your_own` — the yes that filled the game, the seat they took —
and the banner is the newest notice that is somebody else's; the server pushes no own notice either.
The banner is the notice's own title and body, a press opening its game, a close control, held
`motion.hold.notice` (6 s) and spoken once, queued; the next notice replaces it. **It re-reads, and
changes nothing**: a push marks stale the list, Home's read (the bar's badge counts what needs the
player, and every always-on notice moves it) and the read behind the screen it opens — a push never
changes state the server did not say (Part 13). **A notice the list's read brings re-reads Home too**
(Q103) — the minute's read, a return to the app, a pull — so the game it is about is on Home before
it is tapped; before #627 the minute's read left Home as it was until the app had been away for longer
than Home stays fresh. The player's own notice re-reads it as well: it is cheap, and a fill seen on
another phone has moved Home all the same. A notice the day bundled into a row already listed keeps
the row's id and re-reads nothing: the bundled kinds are deck cards and Fill in alerts, none of them
on Home.

**A push tapped on the phone opens its game** — with the app in the background, or not running at
all: the port hands over the tap that started the app once the first listener subscribes, and every
tap once however it arrives. **The payload is untrusted input** (`schemas/pushNotice.ts`): its seven
keys are checked — ids that are ids, one of three places; the kinds narrowed where the wire is read —
and anything else opens nothing. Pushes are only heard while the tabs are up, so a tap that arrives on a sign-in screen is
answered once the player is in.

**The list behind the bell** (`NoticesScreen`, `/notices` — Home's, under `shellTabs`'
`INSIDE_A_TAB`): newest first, one card of rows on the receipts' shape — the title, the body, _when_
in mono at the trailing edge and a chevron on every row that opens something. **No mock draws it.**
Empty, it says what will arrive there; a pull re-reads it, as does a push arriving — the session
holds it for the banner.

**The bell shows a number** (Q101, [#627](https://github.com/Raketa02/Raketa/issues/627)): the
notices that reached the list since the player last opened it, never their own — the server's count
(#621's `new_count`), so it is the same on every phone. Drawn up to 99, _99+_ above it, and nothing at
nought; spoken on the bell's name exactly, _Recent notifications, 120 new_. It is the session's read,
so the minute's read, a push and a return to the app all move it. **Opening the list is the visit**
(`useNoticesVisit`): the list is read again however fresh, and once that read lands
`POST /players/me/notices/visit` follows it — whatever is listed by the time it arrives is seen, so
the list is written as the server will answer next (nothing new, nought) and read again, and Home's
bell is clear the moment the player is back. **A read that fails sends no visit**, and the bell keeps
its number; so does leaving before that read lands. While the list is open, a read bringing a new
row no visit has covered sends it again — a notice reaching the open list, or one the day bundled
into a row already there (`domain/notice.ts`' `readOnTheOpenList`, keyed by the row and when it
reached the list, so a visit the server declines to move cannot loop). The visit is **never held for later** — `networkMode: 'always'`, not retried — because one
landing on a reconnect would mark seen what reached the list while nobody was looking. **The rows
that came since the last visit stand out** — a dot before _when_, which turns `ink`, and _New_ said
first — **for as long as the list is open**, held by the screen rather than read off the latest answer,
since once the visit lands the server says none is new; the next visit starts from nothing. They are
taken from the read the list opens on too, so nothing flashes in a moment later — a row a visit on
another phone has seen since that read still stands out on this one. Nothing is
marked read row by row, and there is no _mark all_.

**The eighth platform port** is the phone's push notifications — `shared/lib/platform/push.ts`, the
only importer of `expo-notifications` ([`_shared.md`](_shared.md)). **No phone has a token to give
yet**: `shared/config/push.ts` holds `EXPO_PROJECT_ID = null` until #533 creates the Expo project (and
gives Android its FCM key), and `IPHONE_PUSH = false` until the Apple Developer membership exists
(O6) — `plugins/push.ts` takes the push entitlement back out of the iPhone build, because
`expo-notifications`' plugin adds it unasked and a personal team cannot sign it. So today the
permission is asked, the choices save and the list is read, and nothing is pushed.

**Calls made here, open for the product owner** (design-system Part 16 has the drawings'):

1. **The permission line is offered every time** the screen opens while the answer is missing, not
   only the first time (A7.2's words).
2. **The list and the banner are drawn without a mock** — the receipts' rows; 9.2's toast surface at
   the top, with a close control and a 6 s hold.
3. **A notice opens over wherever the player is**, never by laying a tab down — so a deck or a game
   opened from Home lights Play, as a live yes opened from Payments does.
4. ~~**The bell carries no count**~~ — **answered** by Q101 (2026-10-09, the product owner, from
   S-01B): the bell counts the notices since the list was last opened, the server keeps it, and
   opening the list clears it ([#621](https://github.com/Raketa02/Raketa/issues/621),
   [#627](https://github.com/Raketa02/Raketa/issues/627)). See _The bell shows a number_ above.
5. **The deck opened by a notice stands on the card's sport without saving it** as the last sport
   picked, and moves the switch to the card's kind. The switch is one value for the app, held only
   while it is open (ADR-0188 §5), and Friends shares it: holding the card's kind apart for Games
   alone would draw the page's two switches on two different kinds.
6. **The always-on rows are `rlLabel`**, smaller than mock 52's: the system has no regular role at
   the titles' size.
7. **A session that ends by itself leaves the phone registered** to the last player until the next
   sign-in on it. Closing it needs a removal the backend accepts without a session — the token as
   its own proof — which is the backend's to decide.
8. **No foreground handler is set**: a push while the app is open makes no sound and draws only the
   banner.
9. **The Android channel is named _Your games_** — the one string Android's settings show for the
   app's notifications.
10. **Asking is offered on this screen and nowhere else.** A player who never opens You › Account ›
    Notifications is never asked, and so never pushed — not even _Confirm your payment to keep your
    seat_; they still see the banner and the list while the app is open. A just-in-time ask
    elsewhere — after the first _It's a game!_, say — would reach them, and is a product decision.
11. **While the phone is not pushed, the list is read every minute the app is open** — the banner's
    latency then, and one request a minute per open app until push exists. A push stops it.
12. **The bell's number is drawn in `ink`** — `shared/ui`'s `CountBadge`, the tab bar's badge, in
    its `news` tone rather than the bar's `coralInk` (design-system 7.29, Part 16 2026-10-09): 1.2
    closes coral at six, and a count of news is not a thing only the player can clear. The market's
    unread counts are red.
13. **The bannered notice stays in the number** — the spec's _the number counts the rest_ is read as
    _the rest are counted, not bannered_. Taking one off would make a phone's number differ from the
    server's, which Q101 keeps the same on every phone.
14. **Leaving the list before its first read lands sends no visit**, and the bell keeps its number:
    the visit marks seen whatever is listed when it arrives, and a cached read may be missing some.
15. **A notice that reaches the open list sends the visit again** — a read while the list is open
    that brings a row not yet drawn as new — so it stands out there and is not counted on the way
    back. Q101 says only that opening clears the number. Keyed by rows rather than the number, so a
    visit the server declines to move cannot loop.
16. **A new row stands out by a dot before _when_, which turns `ink`**, and is spoken _New_ first.
    No mock draws it; the dot is `sportDot`, the app's one small round mark.
17. **The banner still comes down over the open list** for a notice that arrives while it is open,
    as over any screen — the row stands out beneath it too.
18. **The bell is spoken with the exact number** past 99, where it draws _99+_.
19. **_It's a game! · answers by_ opens the game's details in its group, under Play**, as the backend
    sends it (`PROPOSAL`), while Home's card for the same game opens the booked details over Home.
    Both draw it waiting for the club with _Leave the game_. The phone could open the booking for
    this kind as it does a Fill in alert, but the backend's call is kept (#628).
20. **The always-on rows name notices the backend does not give yet** (_Waiting for one payment_,
    _A game you left_, _or it's filling again_): A7.2 lists the amended table, and #623 and #625 bring
    them.

**Owed**: #533's Expo project id into `shared/config/push.ts` (and Android's FCM credentials), and
O6 before `IPHONE_PUSH` turns true — both then need a development build rebuilt. **A development
build is owed now**: `expo-notifications` is a native module. The root owes ADR-0189 §5's amendment
and `CONTEXT.md`'s _Notice_ and _Notification preferences_ (#549's handover). Agent config, left for
the user: `frontend_player/CLAUDE.md` still says six platform ports, and
`.claude/rules/auth-and-http.md`'s sign-out sequence does not name the phone's removal (Part 5 does). **Nothing here has been seen on a device**, and no push has
been delivered to one.

**The four matched at a club that confirms are told It's a game!, which opens the game**
([#628](https://github.com/Raketa02/Raketa/issues/628); the backend's #622; the mechanics Q103). At
20:15 Paula's yes fills Friday's 19:00 at Kazimierz Padel. The three others are told _It's a game! ·
Kazimierz Padel answers by 21:15_ / _Padel · Fri 19:00. Nobody pays until it confirms._, and Paula
sees the screen: at a club that confirms with that line under the word, at a club that books at once
as before (`proposals.md`). Her own copy is listed already seen, never bannered or counted (Q102,
#627's `yourOwn`). **Why**: the product owner ruled that _It's a game!_ marks the four being matched,
not only booked. The notice is `WAITING_FOR_THE_CLUB`, sent as `PROPOSAL`: the game's details in its
group under Play, which draw it _Waiting for the club_ with _Leave the game_. The club's yes stays one
notice, _Kazimierz Padel confirmed your game_, which opens the booked game.

**A new card first is told as Your new game, which opens the deck with it on top** (#628; the
mechanics Q107). If the club says no, the four are told when the card they were promised arrives:
_Your new game · Fri 19:00 at Bonarka Arena_ / _The same players · 40 zł a share — say yes to book
it._ **Why**: a notice that promises _you'll get a new card first_ is answered when the card comes,
rather than by a card dealt without a word. The notice is `NEW_GAME`, sent as `DECK`: the group's deck
in the card's sport and kind, the card on top, as _You complete it_ arrives. **Both open the same way
from the banner, a row behind the bell and a tapped push** (`useOpenNotice`). The phone adds only the
two codes (`domain/vocabulary.ts`, held to the wire by `wireVocabulary.ts`); the words and where each
opens are the backend's, read by the one `targetOf`. Before #628 a build listed both and opened
neither, and a code this build cannot name still opens nothing.

**A time to pay is told by the server, and an arrival re-reads _TO CONFIRM_ too**
([#630](https://github.com/Raketa02/Raketa/issues/630); the backend's #625 and #626; the mechanics
Q109–Q111). Paula's bank wants to check her payment when Ivan's yes fills the game: she is told
_Confirm your payment by 14:40 to keep your seat_, the others _It's a game! · waiting for one payment
until 14:40_, and at 14:40 she reads _Your time to pay ran out · Tue 19:00_ while the rest read that
it is filling again. The phone adds the two new codes, `WAITING_FOR_A_PAYMENT` and
`TIME_TO_PAY_RAN_OUT`, and opens each where the backend says, as #628 did for its two. **A notice
arriving now re-reads Home's two reads** (`proposals`' `rereadHome`): the games, the badge with them,
and _TO CONFIRM_ above them. **Why**: the confirm notice puts a row there and the time-ran-out notice
takes its time off, and before this only the games were read again — a row could be missing, or keep a
time that had run out, until the app came back to the foreground.
