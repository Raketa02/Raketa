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
that did not fill — in its group (`gameRoute`), `DECK` the group's deck **with the card on top**
(`groups`' `groupDeckRoute`), and `RESULT` the booked game's result screen (`bookedResultRoute`,
since [#664](https://github.com/Raketa02/Raketa/issues/664)) — every step at the court. **A Fill in alert is the one notice whose kind decides**: the backend
sends it as `BOOKING` to a reader who is **not in the game**, so it opens the open seat seen from
outside, in its group (`rescueRoute`, A4.3) — the booked game's own details would tell that reader the
game is not theirs any more. **One function opens all five** (`useOpenNotice`'s `destinationOf`: the
route, and the reads behind it), whichever way the
tap came — a row of the list, the banner, the phone's own notification — and it **pushes over
wherever the player is**: a notice is not a tab press, so nothing is laid down and _back_ goes where
the player was. The reads behind the screen are marked stale first, so a deck read twenty seconds ago
does not open without the card the notice is about — and the result screen, which draws two (the
booking, which names its Game, and `games`' list, which holds it), does not open on a score from
before the one _Is that right?_ asks about. A notice whose sport or kind this build cannot
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

**The always on are words and a tag, never controls** — sixteen since #677. Mock 52 drew seven; the rows are
A7.2's as [#620](https://github.com/Raketa02/Raketa/issues/620) amends it, a row a line of the
mechanics §17.2's table, in its order ([#628](https://github.com/Raketa02/Raketa/issues/628)): _It's a
game! · you paid_ (_· held_ since #642) · _Waiting for one payment_ · _Fix your card
by … to keep your seat_ (since #643) · _Confirm your payment by … to keep your seat_ · _Game called off · with the refund_ (_· nothing was taken, or with the refund_ since #642) · _Someone left your game · or
it's filling again_ · _You've been refunded_ · _Your new game_ · _A game moved to another court_ (#677) · _A game you left_ · _Your post didn't fill_ · and since #664 the five steps at the court: _… is at the club and you're not there yet_ · _… is at the club · who you said isn't here yet_ · _How did it go? · your game's hour has ended_ · _Is that right? · … put a score up, or changed it_ · _Was … at the club? · they say they were_. One row can be several notices — _A game you left_ is two — and a row names a
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
keys are checked — ids that are ids, one of four places; the kinds narrowed where the wire is read —
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
19. **_It's a game! · waiting for one payment_ opens the game's details in its group, under Play**,
    as the backend sends it (`PROPOSAL`), while Home's card for the same game opens the booked details
    over Home. Both draw it waiting for one payment with _Leave the game_. The phone could open the
    booking for this kind as it does a Fill in alert, but the backend's call is kept (#628, #630).
20. **The always-on rows name notices the backend does not give yet** (_Waiting for one payment_,
    _A game you left_, _or it's filling again_): A7.2 lists the amended table, and #623 and #625 bring
    them.
21. **The five steps at the court are worded on the settings by the phone** (#664): no table lists
    them yet — the mechanics §17.2 and the screens A7.2 are the root's to amend — so each row is its
    notice's title with the name, the club and the time left out, as the rows above it are, and a
    title that would not say on its own what it is about gains a line after the dot — whom _… is at
    the club_ is told to, when _How did it go?_ comes, that the player _Was … at the club?_ asks about
    says they were. _Is that right?_ is one row for its three variants — a score put up, a different
    one put up, a score changed — which its line names as _put a score up, or changed it_.
22. **A step at the court opens the result screen over wherever the player is**, as call 3 has every
    notice do — so _back_ from it is the list, Home or You, never the booked details beneath it.
23. **A step at the court whose sport or kind this build cannot name opens nothing**, as every notice
    does, although the result screen needs only the booking's id: one rule for every notice, and an
    old build cannot draw that game's sport anyway.

**Owed**: the root's §17.2 table, A7.2's always-on list and A9's destinations for #664's five, and
`CONTEXT.md`'s _Notice_ entries for them (#663's handover). #533's Expo project id into `shared/config/push.ts` (and Android's FCM credentials), and
O6 before `IPHONE_PUSH` turns true — both then need a development build rebuilt. **A development
build is owed now**: `expo-notifications` is a native module. The root owes ADR-0189 §5's amendment
and `CONTEXT.md`'s _Notice_ and _Notification preferences_ (#549's handover). Agent config, left for
the user: `frontend_player/CLAUDE.md` still says six platform ports, and
`.claude/rules/auth-and-http.md`'s sign-out sequence does not name the phone's removal (Part 5 does). **Nothing here has been seen on a device**, and no push has
been delivered to one.

**A new card first is told as Your new game, which opens the deck with it on top** (#628; the
mechanics Q107, Q123). If a club's cancel calls the game off, the four are told when the card they
were promised arrives:
_Your new game · Fri 19:00 at Bonarka Arena_ / _The same players · 40 zł a share — say yes to book
it._ **Why**: a notice that promises _you'll get a new card first_ is answered when the card comes,
rather than by a card dealt without a word. The notice is `NEW_GAME`, sent as `DECK`: the group's deck
in the card's sport and kind, the card on top, as _You complete it_ arrives. **It opens the same way
from the banner, a row behind the bell and a tapped push** (`useOpenNotice`). The phone adds only the
code (`domain/vocabulary.ts`, held to the wire by `wireVocabulary.ts`); the words and where it opens
are the backend's, read by the one `targetOf`. Before #628 a build listed it and opened nothing, and a
code this build cannot name still opens nothing.

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

**Decided, and built since #642 and #643 (below): twelve always on — ten since #676 — and the take is quiet**
(the mechanics Q113 and §17.2;
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-10-10 amendment; root [#635](https://github.com/Raketa02/Raketa/issues/635)). **Why**: a share is now held when its game fills and
taken at the club's cut-off, and a card refused before the cut-off is fixed, not paid. The first row
reads _It's a game! · held_, the called-off row _Game called off · nothing was taken, or with the
refund_, and _Fix your card by … to keep your seat_ joins before _Confirm your payment_
([#642](https://github.com/Raketa02/Raketa/issues/642), [#643](https://github.com/Raketa02/Raketa/issues/643)). The take at the cut-off is a quiet row in the list, never pushed, so it is
not a row here.

**Held, not paid** ([#642](https://github.com/Raketa02/Raketa/issues/642); the mechanics Q113,
§17.2). The first always-on row reads _It's a game! · held_ and the called-off row _Game called off ·
nothing was taken, or with the refund_; the words a notice says are still the backend's. The phone
spells the two kinds #638 added, `FIX_YOUR_CARD` and `TIME_TO_FIX_RAN_OUT`, so a tap on one opens
where the backend says; their row in the settings is #643's.

**Fix your card is always on** ([#643](https://github.com/Raketa02/Raketa/issues/643); the mechanics
Q113, §17.2; the screens A7.2). The settings listed twelve (ten since #676): _Fix your card by … to keep your seat_ sits
after _Waiting for one payment_ and before _Confirm your payment by … to keep your seat_, as A7.2
orders them. **Why**: a card refused before the cut-off is told to its player every way there is, as
a time to pay is. The notice's words, and _Your time to fix your card ran out_, are the backend's; an
arrival re-reads _TO CONFIRM_ as any does, so a row loses its time when the time-ran-out notice lands.

**Each step at the court is told, and a tap lands where it is acted on**
([#664](https://github.com/Raketa02/Raketa/issues/664); the backend's
[#663](https://github.com/Raketa02/Raketa/issues/663); the spec #649, F-RESULT-10.1 and 35.1;
[ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
§7). At
16:10 Ivan taps _Oscar isn't here yet_ at Ogrody 33: Oscar is told _Ivan is at Ogrody 33 and you're
not there yet_, and the banner — or the phone's own notification — opens the game's result screen on
_Are you here?_ with **I'm here** ready. When Oscar arrives, Ivan is told _Oscar is at Ogrody 33_. At
the hour's end all four of a Competitive game are asked _How did it go?_; when Marta puts 6–4 6–3 up,
Oscar and Paula are asked _Is that right?_, which opens on her score with _That's right_; and when
Oscar says _I was there_ the next morning, his courtmates are asked _Was Oscar at Ogrody 33?_. **Why**:
each step waits on one person, and a notice that opens anywhere else leaves them to find the screen.
The phone spells the five kinds — `NOT_HERE_YET`, `AT_THE_CLUB`, `HOW_DID_IT_GO`, `IS_THAT_RIGHT`,
`WERE_THEY_THERE` — and the new destination `RESULT` (`domain/vocabulary.ts`, held to the wire by
`wireVocabulary.ts`), which `targetOf` reads as the result screen by the notice's `game_id`, the
booking's. The words are the backend's, a For fun game is told none of these, and all five are
always on, because each decides somebody's record or result. Push itself is still off: switching it
on is the set-up ticket's.
**No notice is about a club's answer — no club confirms a game**
([#676](https://github.com/Raketa02/Raketa/issues/676); the backend's #669;
[ADR-0196](../../../docs/adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
§1, the mechanics Q121; the screens A7.2). Paula's yes completes Marta's Thursday game at Kazimierz
Padel and it is booked at once, so the four are told _It's a game! · 25 zł held_ like at any club.
`WAITING_FOR_THE_CLUB` (_It's a game! · Kazimierz Padel answers by 21:15_), `CLUB_CONFIRMED` and
`CLUB_COULD_NOT_TAKE_IT` (_said no_, _didn't answer in time_) left the wire and `domain/vocabulary.ts`,
and their two rows left the settings, which list ten (eleven since #677). **Why**: every full game books the moment its
last yes lands, at every club, so there is no answer to wait for or to be told.

**_Game moved_ is always on, and it opens the booked game** (#677; ADR-0196 §2, §4; the backend's
#671 and #672). A club's cancel that a free court absorbs, or the club's own Move, tells every player
on the booking: _Bonarka Arena moved your game to Court 3 · Thu 19:00_, with _Court 2 can't be played
· Padel · indoor · nothing else changes_ for an automatic move, and _Padel · indoor · nothing else
changes_ for the club's own. It is not emailed. `targetOf` opens it where the backend sends it
(`BOOKING`), so a row behind the bell, the banner and a push all land on the booked game, with the
court and its kind on it (_Court 3 · indoor_).

**A notice about no game is listed, and opens nowhere yet**
([#728](https://github.com/Raketa02/Raketa/issues/728), carrying
[#727](https://github.com/Raketa02/Raketa/issues/727)'s contract). Regenerating the player types for
the nickname brought #727's _Get your level_ with it: the wire's `NoticeKind` gained
`GET_YOUR_LEVEL`, `Opens` gained `HOME`, and a listed notice's game facts (`game_id`, `pool_id`,
`sport`, `game_kind`) may be `null` — the first notice about no game. The vocabulary spells both codes,
because `wireVocabulary.ts`'s assertion fails the build otherwise, and **nothing more**: `toTarget`
answers `undefined` for a notice that opens Home or names no game, so it is listed in the backend's
words with nowhere to open, as a code this build cannot name already was. `targetOf` takes
`GameOpens`, every place but Home. **The push is untouched**: its schema still asks for a game, so a
_Get your level_ push is not read. Drawing it, opening Home and reading its push are
[#731](https://github.com/Raketa02/Raketa/issues/731)'s. `notificationMappers.test.ts` holds both
_nowhere_ answers.

**_Get your level_ opens Home** ([#731](https://github.com/Raketa02/Raketa/issues/731),
ADR-0200 §7), which rules the paragraph above's _nowhere yet_. `NoticeTarget` gained `{ opens:
'home' }`, and `toTarget` answers it for **any notice that says it opens Home**, whatever its kind,
since it names nothing a later release could have meant differently. **The push is read now**: the
schema is a union — a game's seven keys, checked against `GAME_OPENS` (the four places a game is),
or a notice about no game's three, `notice_id`, `kind` and `HOME` — and a game's push with no game
in it is still no notice. **Home is laid down, not pushed**: every other destination is pushed over
wherever the player is, so _back_ returns there, but Home is a tab's root, and a second Home over
the list would put Home behind Home — so `useOpenNotice` calls the shell's `openTab('home', …)`,
the tab bar's own move, from the list, the banner or a tapped push, and does nothing where Home is
already on screen. The ratings, the groups list and the run left halfway — what the card is drawn
from — are marked stale first. The walk is `notifications.test.tsx`'s _Get your level_ block, with Home's card on the
landing.

**A friend's two notices** ([#753](https://github.com/Raketa02/Raketa/issues/753), on #745's;
the friends mechanics §12). `FRIEND_REQUEST` opens **Home**, where its card is — the _Get your level_
landing, with Home's own read now among the reads marked stale. `FRIENDS_MADE` opens **the new
friend's record**: `Opens` gained `RECORD`, and the notice names its person as `player_id` (on the list
and in the push, which is read as an id or not at all). **A record is a sheet, not a screen**, so
there is no route to push: a tap — a list row, the banner, a push — names the person in
`recordOpened.store` (feature-scoped, process-scoped), and `NoticesHost`, which is up as long as the
tabs are, draws `player_record`'s sheet over wherever the player is, and forgets them when it closes.
**Answering a request clears its row in the bell on the server**, and the bell reads again at
once: `rereadNotices` crosses to the shell, which hands it to `friends`' request row — `friends`
naming this feature's keys would loop back through the record.

**#749's two notices are spelled, and land nowhere yet** ([#757](https://github.com/Raketa02/Raketa/issues/757)
regenerated the types). `LEVEL_ASKED` and `LEVEL_GOT` join the kinds, and `QUESTIONNAIRE` and
`PICKER` join `Opens`, held to the wire as every code here is. Both are told and listed, and a tap
opens nothing — `toTarget` answers `undefined`, as for a code this build cannot place — and a push
that opens either is not read as a notice. Their landings, the sport's questionnaire and the group's
picker, are [#758](https://github.com/Raketa02/Raketa/issues/758)'s.

**An ask for a Level lands: _Level asked_ on the sport's questionnaire, _Level got_ on the asker's
picker** ([#758](https://github.com/Raketa02/Raketa/issues/758), on #749's; the friends mechanics
§5, §12; the words §29.5). `NoticeTarget` gained `questionnaire` (a sport) and `picker` (a group and
a sport), and the push is read for both: `LEVEL_ASKED` by the sport it names, `LEVEL_GOT` by the
group it names as `pool_id` and the sport — each nothing to open without them, the person each names
left on the wire. **_Level asked_ walks in through the level pass**, as the Skill passport's chip
does: `useOpenNotice` holds `onboarding`'s `useAddASport(FROM_HOME)`, so the sport's run is started
— or its unfinished run handed back — a pass of that one sport begun, and the question route
replaced to. **Its usual return is Home's**: a notice names no group to go back to, and every way out
of the pass lands on Home ([`onboarding.md`](onboarding.md)). A start that fails says why as a toast
where the player is — **_You have a padel level already._**, neutral and held to be read, when they
got one since the ask (`sport_already_rated`); the failure's recovery sentence otherwise — and opens
nothing. **The words are handed in** (`OpenNoticeWords`, from `components/openNoticeWords.ts`), since
a hook names no copy — `administrator`'s `refusal`, the same seam — and `notificationsCopy` stays
import-light for the shell. **_Level got_ lays the group's page under its picker** (`groups`'
`groupPickerRoutes`): the page on its Friends tab, standing on the sport, and the picker pushed over
it — pushed alone, **Done** would seat the picks on a court nobody was looking at and go back to the
list, and the court's line-ups are forgotten only when the page goes. So Done and _back_ land on the
court, as from _+ Friends_, and _back_ again is wherever the notice was opened. **Your friends'
lists are marked stale first** — the friend's Level is what arrived, and a picker drawn from a read
from before it would still grey them; a push arriving re-reads them too, so a picker already open
turns the row pickable. **Calls made here**: _You have a padel level already._ (§29.5 gives no
refusal); the page under the picker. **Not seen on a device**: the two screens pushed at once, and
the questionnaire replacing the list.

**A friends game's three new notices land where every notice of their kind does**
([#759](https://github.com/Raketa02/Raketa/issues/759), on #751's; the friends mechanics §12):
`FRIENDS_GAME_INVITATION` opens Home, where its card is at the very top (_FRIENDS GAME · n_, and
Home's read is marked stale first, as a friend request's is); `CANT_MAKE_IT` and `DIDNT_ANSWER` open
the game, where the seat reads _can't make it_ or _didn't answer_; and _called off · nobody paid_ is
the existing `GAME_CALLED_OFF`, its reason `BY_THE_SENDER`, opening the game. Nothing here needed
more than the kinds spelled: Home and the booking are targets the mapping already reads off `opens`.
**Answering an invitation on Home re-reads the bell** (the shell hands `FriendsGamesRow` the re-read,
as it does the friend requests row); whether the server takes its row off is #751's gap.
