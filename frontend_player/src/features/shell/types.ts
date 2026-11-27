/**
 * The shell feature's only public surface.
 *
 * The shell is the app's three tabs and the one stack under them. `src/app/` mounts it and
 * names each route.
 *
 * **What is exported is what has a caller.** The route table and the reset itself stay
 * internal; they re-export the day something outside asks for one.
 *
 * `ShellScreen` is exported because a tab's screen wears 10.1's arrangement, and the chrome it
 * wears is the shell's rather than something a feature draws again a little differently
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)).
 *
 * **Three of the layers are empty, and stay present.** The shell reads nothing from the backend
 * and writes nothing to it, so `api/`, `mappers/` and `schemas/` have nothing to hold — and the
 * uniform-strict rule is *keep the folders, do not invent invariants to fill them*
 * (`_template/README.md`, docs/architecture.md Part 1). What the shell owns is a table of three
 * routes, the rule that reads a tab off a path, the sentences the tabs it composes say, Play's
 * remembered segment, and the one function that lays a stack down.
 */

export { TabShell } from './components/TabShell';
export { ShellScreen, type ShellScreenProps } from './components/ShellScreen';

/**
 * The tabs' own sentences, read outside this feature by the test harness — which asserts *the
 * player is in the app* and needs to know what that looks like now that the landing is the Home
 * tab ([#367](https://github.com/Raketa02/Raketa/issues/367), renamed from Now by
 * [#550](https://github.com/Raketa02/Raketa/issues/550)) — and by each tab's own suite, which
 * asserts the tab's sentences rather than string literals, because the wording is this file's to
 * change and the rules the sentences carry are not.
 */
export { HOME_COPY, PLAY_COPY } from './components/shellCopy';
/**
 * **Needs your answer's words** (#816) — read by the suites that open the sheet the envelope opens
 * to reach what waits in it, for the reason above.
 */
export { NEEDS_YOUR_ANSWER_COPY } from './components/shellCopy';

/**
 * **Play** — the groups under a *Groups* title, or, with the `explore` feature flag on, the
 * *Groups | Explore* segment and the page under it ([#512](https://github.com/Raketa02/Raketa/issues/512),
 * [#826](https://github.com/Raketa02/Raketa/issues/826)).
 */
export { PlayScreen } from './components/PlayScreen';

/**
 * **The You tab's own sentences** — read outside this feature by the screens behind its rows,
 * which wear the group title they were opened from as their eyebrow
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1), and by the suites that hold the tab to its words.
 */
export { YOU_COPY } from './components/youCopy';

/** **Home** — the booked games and the ones waiting for a club (#576). */
export { HomeScreen } from './components/tabScreens';
/** **What a level got changes on Home** (#765) — the entry gate's, as a rating pass ends. */
export { useRereadAfterALevel } from './hooks/useRereadAfterALevel';
/**
 * **Home's reads, set out while the splash plays** (#874; ADR-0209 §2, amended 2026-11-24) — the
 * launch step the root layout starts after session restore and never awaits, composed here from each
 * feature's Home prefetch; the router harness's warmed launch runs the same one.
 */
export { warmHome } from './hooks/warmHome';

/**
 * The You tab — **a screen rather than a placeholder**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 *
 * The shell's for the reason Home is: a tab owns its own sentences and composes other features'
 * rows under them. In a file of its own because it is not thin.
 */
export { YouScreen } from './components/YouScreen';

/** **You › Friends** (#754) — `friends`' page, composed with the record and `groups`' doors. */
export { YouFriendsScreen } from './components/YouFriendsScreen';

/**
 * ***Invite a friend*** **into an empty seat** (#760) — `friends`' picker with one seat over a booked
 * friends game, composed with `proposals`' game and order and `groups`' doors.
 */
export { InviteAFriendScreen } from './components/InviteAFriendScreen';

/**
 * Open a tab from a screen inside another one — the tab bar's own move rather than a second one,
 * so a player sent here lands where pressing the column would have put them.
 *
 * Two callers: a group link answered once the account is in, laying Play down under Join a group
 * (#520), and *Get your level*'s notice laying Home down (#731).
 */
export { openTab } from './components/shellNavigation';

/**
 * **Open Home with Needs your answer up** (#817, ADR-0205 §1; Q25) — where a link or a notice that
 * pointed at one of the sheet's cards lands: the friend link (`links`), a friend request's and a
 * friends game invitation's notice (`notifications`). Home is laid down as `openTab` lays it, and the
 * sheet opens once the reads they re-read land, if anything waits by then.
 */
export { openNeedsYourAnswer } from './components/needsYourAnswerAsked';

/**
 * **Arrive in the app on a screen inside a tab**, its start beneath it, in one reset made before the
 * shell draws — so nothing is drawn on the way. The entry gate's, for a rating pass that ends where
 * it began: a group's page with Play beneath (ADR-0200 §5), the passport with You beneath
 * (ADR-0179 §3).
 */
export { useShellLanding, type ShellPlace } from './components/shellLanding';
