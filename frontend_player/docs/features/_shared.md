# shared — the ports, the HTTP client and the primitives

> The design record for `src/shared/` — the platform ports, the HTTP client and the design-system
> primitives built so far, one paragraph per decision. Moved out of `CLAUDE.md` on 2026-09-11 so
> it loads when a shared module is being changed rather than on every turn. **Append here** when
> a ticket adds or changes a shared port, verb or primitive. Index: [`README.md`](README.md).

`src/shared/lib/platform/` owns everything the app knows about the device: the Query
focus and online wirings, and four **platform ports** — `LocationPort` over `expo-location`,
`ImagePickingPort` over `expo-image-picker`, `LiveStreamPort` over `react-native-sse` and
`HapticsPort` over `expo-haptics`. Each
is the only importer of its module, for the reason `shared/lib/auth` is the only importer of
the keychain, plus one more: a native module has no JS implementation underneath it, so a
feature that imports one cannot be tested at all — and **the third one is here on that second
argument alone**, because its far side is a socket rather than a native module and a screen
that opened one is a screen no suite can put in front of a severed stream. **The fourth is one
verb wide** — `success()`, the yes screen's one buzz as its word lands
([ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§2), the first haptic in the app — and it is a port rather than a line in a component on the
first argument: _exactly one, and none under reduced motion_ is a count a fake can hold where a
mock could only record. Hand-written fakes
live in `src/test-support/platform.ts`, and a screen reaches each through `useLocation()` /
`useImagePicking()` / `useLiveStream()` / `useHaptics()` — contexts whose
default is the device, so only a test ever supplies anything else. Beside them sit the two
lifecycle wirings and `useOnForeground`, the app's one answer to _did we just come back_ — and
`useOnReturn`, the same question asked of a **screen**: the navigator's focus after a blur, which
is what a pop is, and which neither `AppState` nor a mount reports — and `useAppInBackground`
(#787), _can the app still be seen_: `AppState`'s `background` alone, so iOS's `inactive` (Face ID
behind the keychain's autofill) is not away there, as it is for `focusManager`; sign-in's hero
loop reads it.
**Location is foreground only** — nothing asks for, checks or starts a background one — and
it has **two uses, which the permission prompt names**: the area's fix is **coarsened to about a
kilometre the moment it is read**, and an attendance tap's precise fix (`readPreciseFix`, bounded
at `PRECISE_FIX_WITHIN_MS`) is read at that tap and handed straight to its request
([#658](https://github.com/Raketa02/Raketa/issues/658)) — so neither precise reading ever reaches
a store, a screen or a crash report.

`shared/lib/http` has **three verbs**: `httpRequest` for JSON, `httpUpload` for one file, and
`httpGetFromFeaturesHost` for the feature-flag datafile (below).
They share the correlation id, the `Authorization` header, the timeout policy, the error
mapping and the single-flight 401 rotation — a second copy of any of those is the second
networking path the module exists to prevent. `httpUpload` also reads the local `file://`
URI a picker hands back, because `fetch` is what this module is allowed to touch, and it
reports **stages rather than bytes**: React Native's `fetch` cannot say how much of a body
has gone out, and buying that would mean a second transport. It also **authorises the one read
that is not a `fetch`**: `streamAttempt` mints the URL, the correlation id and the
`Authorization` header for one attempt at the live channel and `rotateStreamCredential` puts it
through the same single-flight rotation, so the third port forwards a bag it never reads rather
than becoming the second place a bearer header is built. A **fresh bag per attempt** is the
load-bearing half — the server closes that stream at the token's `exp`, so a channel that
captured its headers would reconnect for ever with the credential that had just expired.

`src/shared/ui/` holds the design-system primitives built so far — the cards, note, row,
hairline, button, tag, chip, bar, header, the overlays and drawn objects the result screen
needed (bottom sheet, popover, level bar, confidence ring), the photo tile with its
generated court poster, the availability grid and the radius slider, the tick box with
the tick both it and the grid draw, and the **tab bar** — five columns with ⚡Play raised at
the centre, drawn from one Feather family
([ADR-0135](../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)), which is
why `@expo/vector-icons` is **declared** in `package.json` rather than inherited through
`expo`: the app's primary navigation renders through it, and an SDK bump could move or drop
it with no signal in this app's own manifest. Play's five arrivals join them — the **switch**
(6.12), the **fit pill** (7.10), the **balance bar** (7.11), the **court** (7.12) and the
availability grid's **diff variant** — plus Now's one, the **rail's dots** (7.18), which are what a
paging rail has **instead** of a peek rather than decoration hanging off one: they track the
scroll, they are not pressable on 7.9's own `hitSlop` arithmetic, they carry the state in **width**
as well as tone, and they say nothing at all, because the rail's count is on the heading above
them. **None of them reclaims a deleted section number**,
because a number in `docs/design-system.md` never moves: the fit badge and the balance bar
went with their engines in the reset and come back at 7.10 and 7.11, leaving 7.1 and 7.2
empty. With them, 9.2's **toast** is built: the queue, the live region and the dismiss,
mounted **once** at 9.3's overlay host in `src/app/_layout.tsx`, over
`src/shared/store/toast.store.ts`. Part 13's announcement requirement gains its **queued**
variant there, with the send confirmation as the one message that still interrupts. 7.3's
**meter** joins them with the accessibility contract, and it is `Bar`'s opposite: a bar states
a fraction and reports one through `accessibilityValue`, where a meter visualises a number the
row beside it already printed — so it takes **no label and no value at all**, and
`progressbar` appears nowhere in Play. The **text field** (6.13) closes the oldest gap of the
lot: the app shipped four boxes on the two auth screens with no primitive under them, and
`AuthField` — geometry, focus border, error rendering and a reveal — lived in `features/auth/`
until the chat map needed a field twice more. It is **one control in two shapes**, a single line
capped by `maxLength` and one that grows an `rlValue` line at a time to a **cap the caller sets**,
because neither growing surface has been drawn on a phone and a number here is written only for
what a device drew — five lines for the composer, which is the first caller to have needed one.
**Auth moved onto it in the same commit and `AuthField` is gone** — a
primitive introduced without moving its existing caller is a second implementation, not a shared
one. Its `labelHidden` arrived with the composer exactly as 6.13 said it would: a box under a
header naming the people and the sport, with `Send` beside it, wants **the name without the
drawing**, and the name stays required either way because a listener has none of that around them.
Beside it, 10.3 gained a **lead** slot for the conversation header's faces — `right`'s counterpart
at the other end, and a slot rather than a `faces` prop because a header that knew what a face was
would be the design system owning an avatar, which #338 §5 refused by name. **Two more arrived by promotion rather than by being
built there** — the **Social tag row** and 7.13's **run of form**, both the competitive card's
until the player record sheet turned out to draw both
([#375](https://github.com/Raketa02/Raketa/issues/375)). A copy of either would be a second
thing to keep in step with a **pinned** geometry test, and importing them out of the old loop's
Play feature would have pointed the arrow the wrong way. **The drawing came down and the rule
stayed**: Play read the row's four answers off a _candidate_, which was a search result and Play's
alone, and handed the value down — so the union and the two words it draws (`socialTagChip`,
`NO_TAGS_IN_COMMON`) sit in `shared/vocabulary` beside the nineteen labels, and `GameResult` went with the squares for `PLAY_INTENTS`' reason. **6.13's star row is
the newest of them and the first control since the switch** — five 44pt targets, flush, with a
drawn 24pt pentagram inside each, because there was nothing to type: **Archivo ships no
U+2605**, exactly as it ships no U+2713, and
[ADR-0135](../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md) fixed the icon
family as Feather, which has _no filled counterparts_ — and a five-star row is precisely the
case that limitation binds. Its fill pair is the run of form's, taken deliberately so that
_tell two states of one mark apart_ has one answer in this system rather than two, and its
three ratios on `surface` are derived in `starRow.test.ts` off the component's own table. It
takes no rule of its own: it **reports every press with the value pressed**, exactly as 6.8's
cell fires whether or not it is ticked, so whether a second press clears the row is the
caller's. **6.15's swipe row is the first control that moves a row**
([#427](https://github.com/Raketa02/Raketa/issues/427),
ADR-0165
§6): a list row that slides left on React Native's own `PanResponder` — as the radius slider
already drags, and with neither `react-native-gesture-handler` nor `reanimated` added _(both are
in the app since ADR-0176, for the radar's field, and gesture-handler since #551 for 6.8's paint
too; the row stays where it is)_ — to
reveal **one** control at its full height, and nothing else. The control is 6.1 `dark`'s fill,
`night`, and **not coral**: §1.2's list is closed, and the act a swipe reveals is the one the
screens draw `secondary`. #231 §3's argument against a swipe on the deck is kept by construction,
because the swipe only reveals: the act is the control's, and every caller puts a confirmation
behind it. What it must never take is the list's scroll, so it **never claims the press** — the
card under the finger is a door — and claims a move only once the finger has travelled
`size.swipeRow.intent` across and further across than down; once claimed it refuses to hand the
gesture back, on the slider's own line. The arithmetic — which move is a swipe, where the card
sits, where it settles — is `swipeRowGeometry.ts` and is pinned as numbers; the settle is
`motion.settle`, the system's seventh motion, skipped under collapsed presentation. A swipe is
never the only path: the control behind a closed card is hidden from assistive technology, and
`PressableCard` gained `accessibilityActions` so the caller offers the same act in the rotor. A row
handed nothing to reveal attaches no responder and draws nothing behind the card — which is the
contract [#428](https://github.com/Raketa02/Raketa/issues/428)'s challenge row reuses, revealing
_Remove the challenge_ only while nobody has joined. `test-support/swipe.ts` is the finger a test
moves, and it says why the handlers are called directly and in the responder system's own order
rather than through `fireEvent`. **The button gained a `shape`, and the face two additions, for one
screen** ([#433](https://github.com/Raketa02/Raketa/issues/433),
[ADR-0167](../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§2–§3): `Button`'s `shape` is `rounded` by default and `pill` for the yes screen's two doors — a
radius option on the one primitive rather than a second one, changing the corner and nothing else,
which is 4.2's _the chip — the only true pill_ with one fenced exception — and the yes screen's tile
is `PlayerPhoto`'s `face` box at two measured sizes with initials drawn over a **poster** and an
outlined empty seat drawn beside it, both in `features/proposals/components/YesTile.tsx` rather
than here, because the poster's initials are that screen's one licensed drawing and a face
elsewhere is still a photograph or a poster and nothing over it. `handleInitials` sits beside
`handleStem` in `shared/formatting/playerName.ts`, with the four-sided fence on it. The rest arrive
with the features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.

**The bar's second column is Players, and a header may have no heading**
([#443](https://github.com/Raketa02/Raketa/issues/443),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §1;
the decision is [`shell.md`](shell.md)'s, and this is what the primitives changed to carry it).
`TabBar`'s inventory is still five and still Feather: the second key is `players`, its label
_Players_ and its glyph `users` — `user` is You's, and `radar` is still not drawn, because the
Radar is a pane and not a tab. _Players_ is the longest of the five words, so
`theme.size.tabBar.labelMaxScale` moved from 1.7 to **1.6** — derived, as ever, by
`tabBarLabelCap.test.ts` from the real Archivo advances, the one step the seventh letter costs —
and 10.2's glyph table and Part 16 moved with it in the same commit. **`ScreenHeader` draws no
heading element where it has neither a title nor an eyebrow.** With a title the eyebrow sits
above; without one the eyebrow is the heading (#414); without either the slots are the header —
the Players tab's is its _Deck | Radar_ toggle in `lead` and, when the count arrives, a chip in
`right` — and an element carrying a role and no words would be a stop a listener lands on and
hears nothing from. `ShellScreen` forwards `lead` and `right` for it, _forwarded, not designed_,
as it already forwards the way back; 10.3 carries the callout.

**The deck's drag reached four primitives and one port, and only the tick is not fenced**
([#444](https://github.com/Raketa02/Raketa/issues/444),
[ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §3,
§7; the decisions were the old loop's Play's, whose record left with it in #576, and this is what
the shared layer changed to carry them). **`HapticsPort` is two verbs wide**: `light()` — the OS's own _impact: light_ — joins
`success()`, for one tick as a drag first crosses the deck's threshold, off under reduced motion
with the motion; the fake counts both kinds, and the router harness gained `stubHaptics` /
`resetHaptics` as a fourth port alongside the three it already wraps. **`OnCourtMark` draws a
tick before its words, everywhere it is drawn** — the photo panel at both sizes, the record
header, and the deck card — because one mark has one drawing: `Tick`'s own path (now exported as
`TICK_PATH` in its 12-unit `TICK_SPACE`) in a box that is a share of the words' font size
(`theme.size.onCourtTick`, 0,72 with a 1,5 stroke), in the words' colour. It did not fit at the
panel's own `space.xs` — 7.15's arithmetic was right about 6.8's 12 × 12 and about the corner —
so the mark's top edge is `MARK_TOP` (`space.md`, 12pt down rather than 6) on both panels and
the caps re-derive to 1,1 and 1,6 in `onCourtMarkFit.test.ts`; the component takes a placement (`on`: `card` · `record` ·
`deck`) rather than a panel size, and the deck's placement is `surface` + `textOnMedia` at
`inlineTitle`, lower-cased, uncapped. **`SocialTagRow` gained `onDark`**: over the deck card's wash
the pair is `volt` and `onDark` rather than `ok` and `base`, and nothing else about the four
answers changes. **`ShellScreen` gained `fill`** — forwarded, not designed — so a page's content
may grow to fill the scroller and a `flex: 1` child takes what the header and the pinned action
leave; the deck's stage is the one screen whose content is a stage rather than a column.
**`test-support/swipe.ts` gained `dragTo` and `release`**: a finger that has not let go, for
asserting a stamp that follows the drag, since a whole `swipe` has released before anything can be
looked at. And the deck reuses the swipe row's `intent` — `SWIPE_INTENT`, one number for the one
finger deciding between a tap, a scroll and a drag — beside its own `deckSwipe.commit` of 95.

**The one formatter reads the name, its word break already cut at a space, and `@nickname` is
spelled beside it** ([#451](https://github.com/Raketa02/Raketa/issues/451),
[ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
`playerName()`'s `NamedPlayer` carries a **name** where it carried the nickname, and ADR-0107 §4's
rule reads on it unchanged — the whole name or nobody, and nothing invents a familiar form.
`handleStem` and `handleInitials` **keep their names and their break** — a space or a dot — and
the space half is exercised for the first time: _Diego Fabregat_ stems to `Diego` in a box and
initials to `DF` over a poster, and each is still a prefix or a cut of what the owner typed, which
is what §4 admitted. The two functions keep _handle_ in their names for the reason the specs keep
_the whole handle_ in their prose and read through the ADR rather than being rewritten; what they
cut is the name, and a handle — the nickname — is never stemmed because it is never drawn where a
stem is. `atNickname` joins them: the one spelling of `@nickname`, the form a handle takes on the
two screens that draw one — the record and the reader's own You tab — and on no row, card,
sentence, sheet, toast, seat label or spoken name. It sits in the formatter's file because the
fence is a fact about how a person is named, and nothing else in that file takes a nickname, which
is how every other surface keeps it: by never being handed one.

**The one formatter reads the nickname again, the stem cuts at the first dot, and the initials
break at all three separators** ([#728](https://github.com/Raketa02/Raketa/issues/728),
[ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1–§2, superseding the
paragraph above). `NamedPlayer`'s `name` is what a player is called — **their nickname**, whole and
never with an @ — and the field keeps the word for the reason `playerName()` does (ADR-0199,
_Neutral_). **`handleStem` cuts at the first dot only** (`STEM_BREAK`), ADR-0157's cut as it stood
before ADR-0171: a nickname holds no space, and `-` and `_` stay inside a word, so `dorota_w` is
drawn whole in a box. **`handleInitials` takes the first character, then the first character after
the first `.`, `_` or `-`, else the second** (`INITIAL_BREAK`): _ania.k_ → `AK`, _kuba_ → `KU`,
`dorota_w` → `DW`, a separator with nothing after it giving the second character. The two rules no
longer break alike — ADR-0199 names the split, and whoever next touches either decides whether
they meet again. **`atNickname` is gone**: its two callers, the record header and the You header
card, draw the nickname alone now. `handleList`'s _handle_ is a nickname again, and the word is
right. **One sentence capitalised a nickname**: the deck's `sidesSpoken` upper-cased the first
letter of whatever opened it, which said _Karol.t_ for _karol.t_; it now capitalises only our own
words, _You_ and _Somebody_.

**The HTTP client has two verbs again, and the env one URL** ([#576](https://github.com/Raketa02/Raketa/issues/576)).
The third verb, `httpGetFromFeaturesHost` — the feature-flag datafile's unauthenticated read from
`EXPO_PUBLIC_FEATURES_URL` (#479, ADR-0180 §4, §6) — left with the flags, and so did the variable,
its startup check and `platform/appBuild.ts`, the reading a flag's rules targeted. The env's scheme
rule still runs as one loop over `SCHEMED_URLS`, which now names the API URL alone, so a second URL
joins it by being named there.

**The phone-preferences store, the clipboard port, and three primitives that grew a form each**
([#512](https://github.com/Raketa02/Raketa/issues/512)). `shared/lib/preferences` is the second
and last AsyncStorage importer (ADR-0188): **one key per account per value**, a read that fails is
_nothing saved_, and `forgetPhonePreferences` is step 4 of `endSession`, awaited after the status
change because it waits on no query — whichever way the session ended. It judges no value; the
owning feature turns a stale one into its default, and `phonePreferenceKeys` spells the Query key
every owner holds its value under, so the three owners share one root. **A per-phone flag joined
it with [#732](https://github.com/Raketa02/Raketa/issues/732)** (ADR-0200 §8): `readPhoneFlag` /
`raisePhoneFlag` keep _the guide on Your rating was shown_ under `raketa.phone-flags.`, a prefix
`forgetPhonePreferences` never lists, so it outlives the session — `phonePreferenceKeys.flag` is
its Query key, with no account in it. `shared/lib/platform/clipboard.ts` is the fifth
port, **read-only and one verb wide** at #512 (`readText`, never rejecting — #513 gave it a second), for Join a group's **Paste**;
`fakeClipboard()` and `stubClipboard` drive it. Both fences are lint rules proved by
`pnpm test:boundaries`. The primitives: `Segment` gained **`prominent`** (the tab's own view
switch, 6.3), `TextField` gained a **`trailing`** slot, a **`recessed`** ground for a field inside
a card and a **`focusRing`** of `ink` or `coral` (6.13), and `ScreenHeader` gained **`compact`** —
an `h2` title and a sub-line each ending in an ellipsis, for a header that names a thing rather
than a screen (10.3). `theme.ts` gained `MONOGRAM_HUES` beside `POSTER_HUES` and
`size.monogram` (7.20). All recorded in design-system Part 16.

**A header can be the door to what it names, and the segment's badge is a primitive**
([#721](https://github.com/Raketa02/Raketa/issues/721), Q125). `ScreenHeader` gained **`onPress`**,
which takes a `title` and a **`pressHint`** with it, so a pressable header is never unnamed: the
whole row is the button but for the back control and the right slot, which keep their own taps as
the deeper responders, and the named element is a `button` rather than a `header`. The row is
pressed rather than a box round the lead because the group page's sport filter measures the lead
against the row's left edge. **`CornerBadge`** is `Segment`'s private badge lifted out — the Chats
badge at `size.segmentBadge` over a box's top-right corner — so a group's tile can carry the Owner's
count of waiting requests that the Info tab carried, in the same mark (10.3, 7.21, Part 16).

**The sixth port is the share sheet, the clipboard writes, and a group page's pieces**
([#513](https://github.com/Raketa02/Raketa/issues/513)). `shared/lib/platform/share.ts` wraps
**React Native's own `Share`** — one verb, `shareText`, never rejecting, because closing the sheet
is an answer and a sheet that did not open has nothing to say — behind `ShareProvider`/`useShare`,
with `fakeShare()` recording every text it was handed and `stubShare` wiring it into the router
harness. It is fenced like the native ports, but as a **path ban with `importNames`**: `Share` is
one name out of a module every screen imports, so the ban is that name and every other one stays
free; the port file subtracts the one path ban it owns, the two AsyncStorage files keep it, and
`pnpm test:boundaries` drives a named import at all of them. **The clipboard gained `writeText`**,
answering whether the OS took the text — so a screen confirms only a copy that happened — and
`fakeClipboard()` gained `writable` to be the phone that refuses. **The store's second value,
`lastSport`**, is groups', judged there against the ratings on every read. The primitives:
`PlusOnMedia` in `Tick.tsx`, the plus in `surface` for a court's ground — a third bed for one
drawing — and `theme.ts` gained `size.groupPage` (the Games card's seat, 34, and the fast
filter's bar inset, 9) and **`motion.unfold`**, 280 ms, the eighth motion (7.21). All recorded in
design-system Part 16.

**The share port opens WhatsApp** ([#516](https://github.com/Raketa02/Raketa/issues/516)).
`SharePort` gains `openWhatsApp(message)` — `Linking.openURL('whatsapp://send?text=…')` — which
answers **whether WhatsApp took the message**: `openURL` rejects on iOS when no app claims the scheme
and on Android when no activity resolves it, so opening it is the test of whether it is installed and
no native setting is needed (`canOpenURL` is what would need `LSApplicationQueriesSchemes` and
`<queries>`). It never rejects. **The fallback to the sheet is the caller's**, so a suite can see it:
`fakeShare()` has `whatsAppInstalled` and records `whatsApped` beside `shared`. Still one file, still
the only importer of `Share`; no new port. **Gone since #529**: the official group's door became
_Share link_, the sheet, so `openWhatsApp`, `whatsAppUrl` and the fake's two WhatsApp fields went
with their only caller; the port is `shareText` alone again.

**`theme.ts` gained `size.arrivedRing`** (#529): the administrator area's players card draws how much
of an official group has arrived as a ring on `surface` — 48 across, a 4pt stroke, a `line2` track and
a `mint` arc round the percentage. The drawing stays the administrator feature's (`ArrivedRing`), one
caller; the tokens are here because every value comes from the theme. Recorded in design-system
Part 16.

**`shared/ui` has a second tab bar, the administrator area's** (`AdministratorTabBar`, club 17): **Groups
· You**, a second fixed inventory beside the five, drawn from the same columns — Feather, one weight,
selection in tone alone — with no disc and no badge. `TabBarTab` and the columns are generic over the
key so the two inventories share one drawing. Recorded in design-system Part 16.

**The phone keeps its third and last value, and a sheet can put a mark over its title**
([#518](https://github.com/Raketa02/Raketa/issues/518)). `PhonePreference` gains `lastProfile` — the
profile an account with two wore last, owned by `auth` ([`auth.md`](auth.md)) — and ADR-0188 §2's table
is full: a fourth value is a new record. `BottomSheet` takes an optional **`mark`**: the close alone on
the top row, then the mark and the title under it, centred, the title still the heading focus lands on
(9.1 as amended, for the invitation sheet's club tile). `theme.size.switcher` holds the switcher chip's
drawn ⇅ — a 16pt box and a 1,5pt stroke — because Feather ships no up-and-down pair.

**6.8's grid is a week of hours, and a drag across it paints**
([#551](https://github.com/Raketa02/Raketa/issues/551),
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5, mock 36).
`AvailabilityGrid` is transposed — the days across, the hours down — and every caller builds its
rows from `HOURS` and its cells from `WEEKDAYS`; `weeklyHoursAt` in `shared/vocabulary/week` turns
the places the grid reports back into hours, so the orientation is read one way, once. **A tap is
the cell's `Pressable`; a drag is `react-native-gesture-handler`'s pan** over the cells alone, the
second use of the library after the radar's field: the grid sits in a page that scrolls, and a
recogniser that claims the touch at a 4pt intent — under both platforms' scroll slop — is what
keeps a drag down a column a paint, while its claiming cancels the press the cell under the finger
had begun. The hour labels and the heads are outside the paint field, so a thumb there still
scrolls. **The pan is built once and reads the rows and `onPaint` through a ref** — the radius
slider's rule — and reports **the run so far, whole**, which `paintCells` lands idempotently, so a
caller a render behind the finger drops nothing. What is decided is `availabilityGridGeometry`'s,
tested as numbers: which cell a point is over (a gap belongs to the cell before it, a finger off
the grid is over the edge cell), which cells a fast drag jumped (`cellsCrossed`, one step at a
time along the longer axis), and what a run holds (`extendRun`: each cell once, in the order
crossed). **The cell is 20pt tall and under the 44pt minimum on purpose**, granted half the gap on
every side (`hit.availabilityCell`), and the tick stays on a ticked hour although mock 36 draws the
fill alone — both recorded in design-system Part 16 and flagged. The router suites drag it through
`test-support/weekGridTouch`. **Not seen on a device**: the paint against the page's scroll on
either platform, and the press the pan is meant to cancel.

**The seventh port is the payment provider's phone half, and it carries a component**
([#552](https://github.com/Raketa02/Raketa/issues/552)). `shared/lib/platform/payments.tsx` is the only
importer of `@stripe/stripe-react-native` — fenced in `CORE_PATTERNS` like the native ports, one file
wide, and probed by `pnpm test:boundaries`. Stripe's card fields are a native **view** whose entry
stays inside it, so `PaymentsPort` carries `CardFields` beside `phoneWallet`, `takeCard` (turn what
the fields hold into a reference, while they are mounted) and `confirmSetup` (the bank's check, or the
wallet's sheet — four answers, never a rejection). `PaymentsProvider`/`usePayments` as the other
ports; `fakePayments()` behaves as Stripe's test cards do, and **the router harness always provides
one** (`NO_PAYMENTS`, `stubPayments`), the live channel's rule: the device's port would reach an SDK
jest has mocked into answering _no error_ to everything. `jest.setup.js` uses the SDK's own jest mock
for that far side. `app.config.ts` adds Stripe's config plugin with Google Pay declared and **no
Apple Pay merchant** — an entitlement a personal team cannot sign (O6); the one value both the
plugin and the port read is `shared/config/applePay.ts`, which imports nothing, for
`appIdentity.ts`'s reason. `theme.size.payments` holds
the step mark, the method card's badge and the fields' row. The record is
[`payments.md`](payments.md).

**The eighth port is the phone's push notifications** ([#559](https://github.com/Raketa02/Raketa/issues/559)).
`shared/lib/platform/push.ts` is the only importer of `expo-notifications` — fenced in
`CORE_PATTERNS` like the native ports, one file wide, and probed by `pnpm test:boundaries`. Six verbs:
the permission in the platform's vocabulary (asked through a notification channel on Android, made
first), `readToken` (this phone's Expo push token, kept for the process until the system replaces it
— or `null` for a build that cannot be pushed, and for an answer Expo has not given within the app's
request timeout; it never rejects, since the sign-out waits on it), `onTokenChange`,
`onNotice` (a push while the app is open, handed up as it came — the payload is untrusted and the
feature checks it) and `onOpen` (a push tapped, the cold start's tap read once when the first
listener subscribes, every tap handed over once). `PushProvider`/`usePush` as the other ports;
`fakePush()` is a phone whose permission, token, arriving pushes and taps a suite decides, and **the
router harness always provides one** — `NO_PUSH`, inert, so no suite's _Allow notifications_ carries
into the next — with `stubPush` for the suites about it. `jest.setup.js` mocks the library's far
side. `shared/config/push.ts` holds the Expo project (none yet, #533) and whether an iPhone build may
carry the push entitlement (not yet, O6); `plugins/push.ts` takes the entitlement back out of the
iPhone build, which `expo-notifications`' own plugin adds unasked — **the removal is applied to the
returned config, before the plugin list, because a plugin registered earlier runs its change
later**, and `npx expo config --type introspect` shows no `aps-environment`. `theme.motion.hold.notice`
holds the banner's six seconds. The record is [`notifications.md`](notifications.md).

**A layer under a newer layer is hidden from a screen reader**
([#587](https://github.com/Raketa02/Raketa/issues/587)). The record's _Block_ opens its confirm
sheet from inside the record sheet — the first sheet over a sheet. On iOS that is a native window
presented from a native window, which hides the one beneath on its own; on Android it is the
host's next layer, and the layer beneath stayed a listener's. So `OverlayHost` keeps the layers'
order and tells each stage whether a newer layer covers it (`useCoveredLayer`), and a covered stage
spreads `behindOverlay` on its own layer, as the app beneath every layer already took. **The order
is a context of its own, apart from `set` and `remove`**: a stage takes its layer down when the API
it holds changes, so an API that moved with the order had every stage take its layer down and put
it back at the end — a new order, a new API, and again, a render loop the full suite found as a
worker out of memory. The back answers the newer stage first, being the newer subscription.
`ModalStage.test.tsx` walks it.

**A segment can be a door** ([#740](https://github.com/Raketa02/Raketa/issues/740), ADR-0201 §2,
6.3 as amended). `Segment`'s `door` dims the option's label to `size.segDoorOpacity` and changes
nothing else: the box, the slop, the press state and `selected: false` stay the unselected
segment's, and it never carries `disabled`, because a door that reads as shut is one nobody opens.
Its press is reported like any other, and the caller decides what a door opens — the Games switch's
other kind, recorded in `proposals.md`. The dim stops at 3,17:1 on `line2`, under 1.4.3 and past
3:1, and the words say the state as well: a door carries no number. `Segment.test.tsx` holds all three.

**Every row on Home sits on one frame** ([#798](https://github.com/Raketa02/Raketa/issues/798), the
Home rows screens §2, Part 16 2026-11-14). `HomeRow` is the section — `space.lg` under the row above,
the eyebrow heading, and on its line an optional **control** (Top 10's sport pill, #805) and an
optional **link** (_See all ›_, _Rankings ›_) — with whatever the row draws under it. `HomeRowRail` is
the rail, in 7.7's two geometries over Part 8's Strip: **peeking** (a lone card at the content width,
more at `railCardRatio`, free scroll unless the row asks to `snap`) and **paging** (the content
width, snapping, 7.18's dots tracking the scroll). **They are two parts, not one**, because a row
says something in place of a rail — _Your games_' empty sentences and failure, Top 10's _Nobody
ranked in squash yet_ — and a frame that owned its rail would grow a slot per sentence. FRIENDS
GAME, FRIEND REQUESTS, ASKED FOR A LEVEL and _Your games_ moved onto it with nothing on screen
changing; _TO CONFIRM_ stays as it is, a list in one card and not a rail. **The rail is never
remounted** — one `ScrollView` at one place in the tree whatever its count, width or heading — so it
keeps its scroll position across a re-render, as Part 8 asks. **Its first frame draws only the
cards that can be seen** (2026-11-15): `cardsDrawnFirst` — every card the screen can hold and the
one past its edge — with a same-width stand-in for each of the rest, and a second pass right after
draws them. Home's six rails of up to ten cards, a generated poster or four per card, were most of
the seconds a device spent drawing Home; the content is its full width from the first frame, so the
step, the snap, the dots and #804's on-screen sums are untouched, and every row test that counts its
cards still finds them all. **The poster dropped its group** in the same change: each mark carries
its own ink and the two arms are one path, nine native views where there were eleven, drawn the
same (`CourtPoster`; ADR-0134's composition untouched). **The link is the row's words and
name**, nothing the frame's own: the words drawn with a hidden chevron, the name naming what it
opens, a `link` role, ink `rlValue` like sign-in's link, its 16pt line overhanging the heading's
12 so a row with a link stands where one without does, reached by `hit.rowLink` — 36 tall, under 44
on purpose, and 3 to the left so a control beside it keeps its own target (6.5). **The rail takes the
row's cards**, not their count, and hands each back with its width, so the lone-card width and the
dots can never disagree with what is drawn. `HomeRow.test.tsx` walks the link, the slot, both geometries and the rail's
identity across re-renders.

**`PhotoCarousel`: all of a player's photos, sideways** ([#799](https://github.com/Raketa02/Raketa/issues/799);
the Home rows screens §6.3, §9.3; home rows 23; design-system Part 16, 2026-11-14). Every photo in the
order handed in, each a card at `size.photoCarouselRatio` (half) of the content width and 4:5
(`PHOTO_PANEL`'s shape, read off it rather than restated), on `radius.card`, over Part 8's Strip — gap 9, bleeding past the
gutter, snapping a card at a time. **Nothing with no photo**, and **a lone photo keeps the card's
size**, since a 4:5 card the content's width would stand taller than the sheet's first screen. It
announces nothing, as `PlayerPhoto` does, and imports no feature. The record draws it first, and the
vibe sheet (#803) is to draw the same one. `PhotoCarousel.test.tsx` holds the order, the size, the
corner, the Strip and the absence.

**`Switch` lost `onDark` and `accessibilityLabel`** (#799): both were for the Rankings card of a player
hidden from General, which went with _Show me in General_ (ADR-0204 §2). 6.12 keeps them specified,
as it kept the switch itself while it was unbuilt; the dark-card tests and the two contrast figures
they derived went with the code.

**`PortraitTile`, a third rail geometry, the sport pill's _All_, and two `Button` additions**
([#801](https://github.com/Raketa02/Raketa/issues/801); design-system 7.31, 7.32, Part 16 2026-11-14).
**`PortraitTile`** is a face edge to edge with the wash rising over its foot (`portraitWash`, the deck
card's value moved whole since that card is gone), a tag top-left that lets touches through, a control
top-right beside the tile's own press, and the words over the wash; its width and aspect are the
caller's (`size.portraitTile`). Top 10's portrait (#805) is to draw it too. **`HomeRowRail`'s `tiles`**
draws each at 0,355 of the content width, a lone one too. **The sport pill is generic over its
choices** (`SportPillFrame<S>`, `SportPillWords<S>`) and may offer **`ALL_SPORTS`**, drawn with a
two-toned dot; existing callers infer `Sport` and changed nothing. **`Button`** gained **`lead`**, a
Feather plus or check before the words, never spoken, and **`settledSoft`**, mint's soft bed in its
ink. `PlusOnSurface` is exported. **`shared/lib/query-client`'s `LISTS_PEOPLE`** is a query `meta`
a read declares when it lists people with the reader's relation to them (Home's people rows, Hottest
groups), and **`rereadPeopleLists`** re-reads every such read — what every friend write and every block
calls, so a write made anywhere moves the person on every row without naming a feature's keys
(architecture Part 7). Each has its suite: `HomeRow.test.tsx`, `SportPillFrame.test.tsx`,
`Button.test.tsx`; the tile is walked through New in Raketa.

**`RowSportPill`, `HomeRow`'s `over`, and a `numbered` rail** ([#805](https://github.com/Raketa02/Raketa/issues/805);
the Home rows screens §7; home rows 25–27; design-system 7.36, Part 16 2026-11-15). Top 10 puts the
deck's sport pill on a row's heading line, beside _Rankings ›_, and its bar slides over the heading
while the link stays put (home rows 27) — so the bar must end where **the pill** ends, which
`SportPillFrame`, a page's, does not know: its bar ends at the page's edge. **`RowSportPill`** measures
the pill where it stands on the heading's line and hands the row two things: the pill, for `HomeRow`'s
`control`, and — while open — a layer for **`HomeRow`'s new `over`**, which the frame draws last over
the whole section: a backdrop that folds the bar, and the bar on the pill's own line, from the row's
left edge to the pill's right end and the bar's inset past it. What folds it is the frame's —
`FoldAway`, now exported from `SportPillFrame.tsx` for this: the current sport, the backdrop,
Android's back and the screen losing focus. **The backdrop is the row's**, so a tap elsewhere on Home
leaves the bar open (a call: a backdrop over Home would need a layer above the page). **`HomeRowRail`'s
`numbered`** hands each card `size.topTen.railRatio` of the content width — the card's width; the
numeral beside it is the row's own, so its items are wider than the width it hands. Each has its
suite: `RowSportPill.test.tsx`, `HomeRow.test.tsx`; the row is walked in `rankings`' `topTen.test.tsx`.

**`FoldingLine`, `FoldingLines` and `FoldingLineFooter` — FOR YOU's quiet lines**
([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5, §8, §9; home refactor 3–13;
design-system 7.37, 4.3, Part 16 2026-11-18). `FoldingLines` is the section — the eyebrow and the
lines `space.sm` apart — and `FoldingLine` is one line: a white card, its header the title in `h2`
and a turning chevron, **a button named by its title that says whether it is expanded**. **The page
says which line is open** (`open`) and a press on the header is all the line reports (`onHeader`):
closed, the header is the whole line; open, only the header closes it, because the content's taps
are its own. **The content is drawn only while open**, and for the fold back — hidden from a
listener, untouchable, and on no page (`PageOnScreen` withheld) while it folds — and **on the page
only once it has unfolded** (`lineUnfold` after it opens), so a card fading in at no height is never
counted as seen and a closed line never reports one. **Opening is one change to a fold's height** — nought, then the
content's measured height — and a Reanimated layout transition moves the frames, the line's and those
of every line below it (`FoldingLines` hands them one beat, `lineUnfold` or `lineFold`), while one
shared value fades the content in and turns the chevron: `RecordDetails`' mechanics, for the reason
`CLAUDE.md` gives. Under Reduce motion nothing moves. **As it unfolds it asks the page to show it**
(`PageReveal`, `onScreen.ts`'s `scrollToReveal`), once per opening, and **only when it was pressed
open** (`reveals`): the line a page opens by itself never scrolls the page. **The fold's top is
measured inside the line's 1pt border**, since the fold stands in the clip within it. **A line let go
draws its rail anew at its first card when it opens again** — `HomeRow`'s _never remounted_ holds
while a line stays open. `FoldingLines` is `HomeRow`'s section holding lines, not a copy of it. **The open line has an `ink`
border and `shadow.openLine`**, the seventh shadow. **`FoldingLineFooter`** is the open content's
foot: a control, then a link 44 tall — the row frame's link, moved here and grown to the minimum —
and a layer over the footer for Top 10's open bar (`RowSportPill` now hands its pill and bar to the
footer). **`HomeRow` lost `control`, `link` and `over`**, which only the five rows used, and
`hit.rowLink` went with them; **`HomeRowRail` reads `RailBounds`** from a line, so its shares are of
the line's content and it bleeds to the line's inner edge and snaps, and takes **`itemWidth`** for
Top 10, whose numeral stands beside its card. **Where a section stands on the page now composes**
(`useTopOnPage`, `useTopWithin`): a rail in a line in FOR YOU is measured through each, as a device
lays them out — a fold's section is its line's, which is why the line names it rather than reading
the context it stands in. Suites: `FoldingLine.test.tsx`, `HomeRow.test.tsx`, `RowSportPill.test.tsx`,
`onScreen.test.ts`; the lines are walked in the shell's `forYou.test.tsx` and each feature's own.
