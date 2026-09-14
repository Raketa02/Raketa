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
([ADR-0166](../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§2), the first haptic in the app — and it is a port rather than a line in a component on the
first argument: _exactly one, and none under reduced motion_ is a count a fake can hold where a
mock could only record. Hand-written fakes
live in `src/test-support/platform.ts`, and a screen reaches each through `useLocation()` /
`useImagePicking()` / `useLiveStream()` / `useHaptics()` — contexts whose
default is the device, so only a test ever supplies anything else. Beside them sit the two
lifecycle wirings and `useOnForeground`, the app's one answer to _did we just come back_ — and
`useOnReturn`, the same question asked of a **screen**: the navigator's focus after a blur, which
is what a pop is, and which neither `AppState` nor a mount reports.
**Location is foreground only** — nothing asks for, checks or starts a background one — and
a fix is **coarsened to about a kilometre the moment it is read**, so the precise reading
never reaches a store, a screen or a crash report.

`shared/lib/http` has **two verbs**: `httpRequest` for JSON and `httpUpload` for one file.
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
thing to keep in step with a **pinned** geometry test, and importing them out of
`features/play/` would point the arrow the wrong way. **The drawing came down and the rule
stayed**: `play/domain/socialTagOverlap` reads the row's four answers off a _candidate_, which
is a search result and Play's alone, and hands the value down — so the union and the two words
it draws (`socialTagChip`, `NO_TAGS_IN_COMMON`) sit in `shared/vocabulary` beside the nineteen
labels, and `GameResult` went with the squares for `PLAY_INTENTS`' reason. **6.13's star row is
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
[ADR-0165](../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§6): a list row that slides left on React Native's own `PanResponder` — as the radius slider
already drags, and with neither `react-native-gesture-handler` nor `reanimated` added — to
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
[ADR-0166](../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
§2–§3): `Button`'s `shape` is `rounded` by default and `pill` for the yes screen's two doors — a
radius option on the one primitive rather than a second one, changing the corner and nothing else,
which is 4.2's _the chip — the only true pill_ with one fenced exception — and the yes screen's tile
is `PlayerPhoto`'s `face` box at two measured sizes with initials drawn over a **poster** and an
outlined empty seat drawn beside it, both in `features/challenges/components/YesTile.tsx` rather
than here, because the poster's initials are that screen's one licensed drawing and a face
elsewhere is still a photograph or a poster and nothing over it. `handleInitials` sits beside
`handleStem` in `shared/formatting/playerName.ts`, with the four-sided fence on it. The rest arrive
with the features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.
