**I want to redesign the bottom menu of the player application. I will provide you mock reference of the design of the bottom menu. The design from the mock references is priority so if you have to create new adr or update then do it.**

## What it is

The player app's main navigation: three destinations — **Home**, **Play**, **You** — in a single floating dock that hovers over the bottom of every main screen instead of sitting flush against the edge. It looks like a piece of frosted glass laid on top of the page: the content runs underneath it and shows through, softened. One tab is always selected, held in a soft coral pill. Take into account that the chat screen does not have a bottom menu, and screens like the its a game splash doesn’t have it.

Do not take decisions based on mocked data and mock sizes. Any decision is based on real evidences.

## Design

**Shape and placement.** A rounded slab, 54 px tall, inset 12 px from the left and right edges and lifted 10 px off the bottom of the screen, with a 22 px corner radius. Because it never touches the edges, the page is visible all around it — the dock reads as an object resting on the screen, not as a band that ends it.

**Material.** Translucent white (about two-thirds opaque) with a strong blur behind it and a touch more colour saturation, so whatever passes beneath — a list card, the dark teal of a game card, a photo — appears as a soft wash rather than a hard shape. A bright one-pixel hairline runs along the inside of its edge, the way light catches the rim of glass, and a faint outer hairline plus a soft, low shadow lift it off the page. Over a light screen the dock looks almost white; over a dark card it darkens slightly with it. It always belongs to the screen it's on.

**The three tabs.** Equal thirds. Each tab is an icon with a small label under it:

- **Home** — a house.
- **Play** — a lightning bolt, Rakieta's mark for a game being dealt. The bolt is always drawn filled, whatever its state, because it is the brand's symbol rather than a pictogram.
- **You** — a head-and-shoulders figure.

Idle tabs are drawn in ink at reduced opacity, the icon as an outline. The **selected tab** is the only coloured thing on the dock: its icon fills in and turns coral, its label turns coral, and a soft coral pill — coral at 13 % — appears behind icon and label together, 76 × 42 px, fully rounded. The pill is the same coral family as the Yes button and the app's badges, so "selected" and "live" share one colour throughout the product.

**Content runs under it.** On scrolling screens — rows slide beneath the glass as you scroll, and every list ends with enough room that its last row can be scrolled clear of the dock and read in full. On the Games deck, which doesn't scroll, the card and its three round buttons (No · i · Yes) sit above the dock with a fixed clearance, so nothing is ever covered.

This is the mock reference of the bottom menu components for you to know the aspect and design:

`"C:\Users\rober\Desktop\rakieta_features\7.refactor_menu\1_menu component.png"`

This is how the bottom menu is lay out and displayed in a complete screen for example the home screen. Do not take anything into account from the following mock apart from the bottom menu. This mock intention is to show you the dimension on screen and how looks on an overall screen. Rest of the screen is just mock:

`"C:\Users\rober\Desktop\rakieta_features\7.refactor_menu\2_bottom_menu_home_sceen.png"`

**MOTION AND ANIMATION**

# Evaluate the times of the animation and adjust for maximal optimization and performance to avoid jittered or lagged animation.

## what happens when you tap another tab

### In one sentence

The coral pill doesn't disappear and reappear — it *travels*. It leaves the tab you were on, slides along the glass to the tab you tapped, stretching like a bubble as it moves, overshoots a hair, settles, and the new icon colours in under it as it lands. Total time: just under half a second.

### The cast

Three things move, in this order of importance:

1. The pill — the soft coral capsule (76 × 42 px, coral at 13 %) that marks the selected tab. There is only one, and it is the hero of the animation.
2. The icon and label you tapped — they switch from idle (outline, ink at reduced opacity) to selected (filled, coral).
3. The icon and label you left — they switch back from selected to idle.

The dock itself, the glass, the other tab: nothing else moves.

### Frame by frame (tap on *You* while on *Home*)

| Time | What you see |
| --- | --- |
| 0 ms | Your finger lifts off *You*. The screen behind the dock has already changed to the You page. On the dock, nothing has changed yet except that *Home*'s icon has gone back to an outline — the pill is still sitting on Home. |
| 0 → 160 ms | The pill pushes off towards the right, fast at first. As it accelerates it stretches: by about a third of the way it is roughly 30 % wider and 15 % shorter than at rest — a bubble being pulled, not a box being dragged. The pill is now a long coral smear covering the gap between *Play* and *You*. The *You* icon is still an outline underneath it. |
| 160 → 320 ms | The pill slows as it approaches *You*, and as it slows it contracts: it goes slightly narrower and taller than its resting shape (about 6 % each way), the recoil of the stretch. It passes its target by a few pixels — the overshoot — then eases back. |
| 140 → 440 ms | Starting a touch after the pill sets off, the *You* icon fills in and colours: outline to solid, grey-ink to coral, label with it, over 0.3 s. Because this starts late and runs smoothly, the icon seems to light up *because* the pill arrived, not before it. |
| 320 → 460 ms | The pill rounds back to its exact resting shape and sits centred under *You*. |
| 460 ms | Still. Coral pill, coral filled icon and label under it; *Home* and *Play* back to outlines. |

### What gives it the "bubble" feel

- Stretch-and-squash. A rigid object would keep its shape while sliding. The pill gets wider and flatter when it accelerates and narrower and taller when it brakes, the way a soft thing deforms when it's pulled and then stops. The proportions are small enough that it never looks like a cartoon — you feel it more than you see it.
- Overshoot. It travels a few pixels past the target and settles back, so the landing has weight. The easing is a spring curve, not a straight ease-out.
- One object, continuous. Because the same pill travels the whole way, your eye follows it across the dock. Nothing blinks out and blinks in; the dock is never without its selection marker, not even for a frame.
- The icon lights up after the pill. The ~140 ms delay on the icon's colour is what sells the causality: the pill arrives, the tab wakes up. If the icon changed instantly the pill would look like it was chasing a decision already made.

### Edge behaviour

- Any distance, same timing. Home → You crosses two tabs, Home → Play crosses one; both take the same 0.46 s. The far jump just moves faster, so it stretches a little more — which is exactly what you'd expect of a bubble pulled further.
- Tapping the tab you're on does nothing: the pill doesn't bounce or pulse. It only moves when the selection actually changes.
- Rapid taps. If you tap a third tab while the pill is still travelling, it changes course from wherever it is and heads for the new tab — it doesn't finish the first trip first and doesn't snap.
- Navigating inside a section (opening a game from Home, a group from Play) never moves the pill, because the selected tab doesn't change. The pill moves only when you cross from one branch of the app to another.
- Reduced motion. If the phone asks for it, the pill simply appears under the new tab and the icon switches colour at once; no slide, no stretch.

### In numbers, for whoever builds it

- Slide: 460 ms, spring easing (starts fast, slight overshoot, soft settle).
- Pill deformation during the slide: 100 % → 130 % wide / 84 % tall at 35 % of the way → 94 % wide / 106 % tall at 70 % → 100 % at the end.
- Icon and label colour-in: 300 ms, plain ease, starting 140 ms after the slide begins; outline → filled and ink-at-62 % → coral.
- The outgoing icon returns to idle immediately.
- Nothing on the dock other than the pill and the two icons changes.
