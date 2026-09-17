# ADR-0178 — An overlay on Android is a layer in the tree, not a native window

- **Status:** Accepted
- **Date:** 2026-09-17
- **Narrows** the player app's `BottomSheet` note's *"9.3's single root-level overlay host is
  not needed for this one … it becomes necessary for the first overlay that has to stay inside
  the React tree"* — it is necessary now, on one platform, for every overlay. Design-system 9.3
  — *overlays render from a single root-level overlay host* — is what the app does on Android
  from here; on iOS it still does not, and this record says why the two differ.
- **Consequence of** [ADR-0176](0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md)
  §2, which put the first animated style in the app.
- **A client change only.** Nothing on the wire changes. Grilled 2026-09-17 in the app, from
  the phone in hand.

## Context

The radar's record sheet on the Android phone slid in transparent: a sliver of white at the
top-left of the screen, the sheet's close control sitting over the *Deck* toggle, a window that
took every touch and showed nothing. The deck's own sheet — the same `BottomSheet`, the same
`PlayerRecordSheet` — was whole. Bisected on the device, the difference was not the radar's
geometry but its **animated styles**: with every `useAnimatedStyle` and `useAnimatedProps` in
the field neutralised the sheet was whole again, and a 1 × 1 `useAnimatedStyle` view placed on
the *deck* pane collapsed the deck's sheet the same way. So: **on Android under the New
Architecture, any mounted Reanimated style makes every React Native `Modal` lay its content
out at 0 × 0.** The measurement behind that sentence: a modal's content is laid out at
`0 × 0` first and again at `360 × 702` a frame later when the dialog reports its size as native
state, and Reanimated 3.16 loses the second pass — on the first open, and on every open after,
a rebuilt dialog included.

Sizing the stage from the window ourselves drew the sheet, and then showed the rest. Nothing
in it could be pressed: the scrim, the close control and the foot's two buttons all received
their press-in and never their press. Android's native dispatch finds no child under the
finger inside a 0 × 0 view, so the dialog's root re-dispatches every touch's *start* from its
own `onTouchEvent`, and the second start re-runs the responder negotiation, which React
Native's `Modal` host wins — it always claims the responder — terminating the pressable on its
way to the release. The sheet's scroll view, a native view, never saw a touch at all. The
native window is not mis-sized on Android while Reanimated 3.16 is in the app; it is
**unusable**, and the version that fixes it is not the SDK's.

## Decision

### 1. `ModalStage`: one contract, two platforms

`BottomSheet`, `Popover` and `SearchingLatch` draw on a **`ModalStage`** — visible, a request
to close, an arrival, a layer — and nothing else in the app touches `Modal`. **On iOS the
stage is React Native's `Modal`**, the separate native window it always was, unaffected and
carrying its own exit animation. **On Android the stage is a layer in the tree**, hosted at the
root: `ModalStage.android.tsx`, a file Metro picks and no caller chooses.

### 2. The host: design-system 9.3's root-level layer, done

`OverlayHost` wraps the route tree in the root layout and renders every stage's layer as a
sibling of the app, after it, beside the toast host — so a layer paints over every screen and
the tab bar, and `theme.layer` orders it against a toast as 9.3 wrote it: a sheet beneath, a
popover over. While any layer is up the whole app beneath takes `behindOverlay`, because a
native window hid the tab bar and the other screens from a screen reader on its own and a layer
in the tree has to say so itself. The stage keeps the two things the window gave: the
hardware back is subscribed while the stage is up and always answered *handled*, and the
arrival is the window's — a slide over `motion.sheet`, a fade over `motion.popover`, nothing
under reduced motion — on the native driver.

### 3. What a stage's children keep, and what they do not

A layer is rendered by the host, not by the overlay that asked for it, so its children keep
every context the root provides and lose any a screen would have given them. Every provider in
this app is at the root, and no sheet's content reads the navigation; a sheet that grows either
is a sheet that moves the provider up or stops reading the route, never a sheet that goes back
to the window. A stage re-states its layer on every render, as a portal does, and the host
reconciles the same position so the layer's state — a scroll position, a pressed control —
survives it. With no host at all, a unit test rendering an overlay alone, the layer draws in
place.

## Consequences

- **Two platforms, one mechanism each, and a reader has to know which.** The contract is one
  file and the rule is one sentence: *iOS is the window, Android is the host*. The harness runs
  as iOS, so the Android stage is tested by importing its file and asserting what the window
  gave — the layer at the root, the app hidden beneath, the back gesture answered — and the
  three surfaces are tested against the window as before.
- **Android loses the window's slide-out.** Every caller unmounts an overlay the moment it
  closes, which the window animated and a layer cannot; the arrival is kept, the departure is a
  cut. A host that kept a leaving layer for one beat would re-render a snapshot of a component
  that has gone — a sheet reading the record again for its own exit — and is not worth it.
- **The keyboard is not handled, on either platform, and now it is a decision.** No overlay
  holds a text input; the first that does takes on `KeyboardAvoidingView` in its stage.
- **The measurement is written where the next reader will trip on it**: the host's note,
  `docs/architecture.md` Part 13 and the app's `CLAUDE.md`. The root cause is the library's,
  and when a Reanimated the SDK pins no longer loses the state pass, the Android stage can
  go back to the window by deleting one file — this record stands until somebody has measured
  that.
