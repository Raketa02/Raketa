# Rakieta Player App — full preview build

A deployment of `rakieta-player-app-prototype-v37.html` with **Create** and **Inbox** removed from the tab bar, and everything else — Onboarding, Now, Find, and the complete You section — present with its real seeded data.

## Onboarding

**Mandatory on open**, and the mock sign-in / account-creation card is skipped entirely — the app boots straight into sport selection, the first real onboarding step. Once in, there is no way to reach Now, Find, Create or You until the flow completes: this is enforced at the render level, not by hiding a button. The tab bar does not exist while onboarding is active, and even a background navigation attempt cannot make anything but the onboarding screen actually draw. Only completing the flow clears the lock and hands off to Now.

## Now, Find, Create, You — the complete Walkthrough section

All four are the **complete v37 sections**, present with real seeded data:

- **Now** and **Find** — unmodified, with match cards, filters, and every dependent screen (match detail, five-numbers, the cancellation timeline, leaving a seat, the live replacement search, seat resolution, the checkpoint, transferring a seat, payment).
- **Create** — restored to the tab bar. The Open Match / Private Court choice, the full creation flow with duplicate-detection, and the doubles line-up screen (choose who is playing, watch the forecast move as seats change) are all present and reachable through ordinary navigation, exactly as in the prototype's own "Walkthrough" scenario group.
- **You** — all three groups (Playing, At your clubs, Money and account), sixteen rows, every one reachable and backed by real seed data: memberships, programmes, Open Play, competitions, community groups, the club profile, the wallet, the sports card, settings, and privacy.

Only **Inbox** remains out of the tab bar — it was never part of the Walkthrough section and stays excluded.

## What was deliberately removed

- The **Inbox** tab, and the one link that would otherwise reach it from a live match card on Now.
- The internal scenario rail / demo drawer used during prototype review — hidden via CSS so the app presents as itself rather than as a QA harness.
- The **simulated clock** card at the bottom of the phone frame. The app runs frozen at its seeded moment.
- The **mock sign-in card** at the very start of onboarding (fake email/password fields, "Create my account"). The app skips straight to sport selection.

## Two real bugs found and fixed while verifying this build

**1. Every match was missing.** Rewriting the boot sequence to force onboarding first (an earlier requirement) replaced the original boot line, `runScenario('intro')`, with a direct call into onboarding. That original line's real job — seeding every match in the app via `seedMatches()` — was a side effect nobody had named, and dropping it meant `S.matches` stayed permanently empty. Every build shipped between that change and this one would have shown a genuinely empty Now and Find to a real visitor, despite passing every test that existed at the time, because those tests happened to go through `runScenario()` themselves, which silently re-seeded the data before checking it. It surfaced when this update's own verification ran the *exact* boot sequence shipped in `index.html`, with no shortcuts. Fixed by restoring the seeding call and the matching baseline wallet ledger explicitly in the boot sequence, with a permanent static check confirming `seedMatches()` is called there directly.

**2. The app overflowed a real phone's screen.** The base stylesheet was built for a desktop viewer looking at a small phone *mockup* sitting beside a scenario-review sidebar: a fixed 392×788px box, a 290px grid column reserved for that sidebar, and a `max-width:900px` breakpoint meant to make all of that fluid on a narrow screen. Hiding the sidebar with `display:none` (done several builds ago) does not free the grid track reserved for it — `#app{grid-template-columns:290px 1fr}` still allocates that first 290px whether or not anything visible occupies it, so on an actual phone the app was squeezed into whatever was left of the real viewport width. Rather than keep tuning that breakpoint's arithmetic, the fix removes the condition entirely: every mobile-style rule now applies unconditionally, at every viewport size — `#app` is always a single column, `#phone` always fills the real viewport (`100dvh`), and the vestigial desktop top bar is hidden rather than shown. On a real phone this now fills the screen; on a wider screen it centres as a single column capped at 520px.

## Verified

- 89 scenarios, 40 view functions, 35 match-state contexts all render without error.
- The mock sign-in card is confirmed absent: no email/password fields, no "Create my account" button, boot lands directly on sport selection.
- 10 onboarding-lock assertions confirm: the app boots directly into onboarding, the tab bar renders empty while it's active, a simulated tap on the Find tab mid-onboarding does not change what actually draws, and completing the flow correctly clears the lock, lands on Now, and restores the tab bar.
- The complete You section is confirmed: all three groups present, all sixteen rows reachable, and each of the ten screens (membership, programmes, Open Play, competitions, groups, the club profile, wallet, sports card, settings, privacy) independently checked to render real seeded content rather than an empty state.
- **16 Walkthrough-specific assertions**, one per screen in the prototype's own nine-scenario Walkthrough group: Start here, Find a game, Book a court, Join and pay (match detail and payment), the Open Match / Private Court choice, both paths advancing correctly, the doubles line-up self-initialising with a real forecast, and the owner-guarantee block rendering correctly for a split-pay private court.
- 1 assertion confirms the simulated-clock card carries the hidden class in the shipped markup.
- **A static check reads the shipped boot sequence itself** and confirms it calls `seedMatches()` directly — the specific regression this build's verification caught and fixed.
- **5 static layout checks read the shipped stylesheet itself** and confirm the real-device fix landed correctly: no rail column reserved, the phone frame fills the real viewport height unconditionally (not gated behind a media query), and the vestigial desktop top bar is hidden.

## Deploying

Drag this folder onto Netlify, or `netlify deploy --prod` from inside it. It's a single self-contained `index.html` — the only external dependency is the Google Fonts stylesheet, loaded at runtime.
