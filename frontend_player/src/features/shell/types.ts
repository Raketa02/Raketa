/**
 * The shell feature's only public surface.
 *
 * The shell is the app's five tabs and the one stack under them. `src/app/` mounts it and
 * names each route; nothing else outside this folder has needed anything yet.
 *
 * **What is exported is what has a caller**, and `enterPlay` is now one of them: the *Find a
 * game* segment re-enters the tab from inside it, which is **arriving rather than going
 * back**, and the deck is where that segment ships
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)). It is the reset's second entry
 * point rather than a navigation Play could write itself — laying the Play stack down is what
 * *ends a Play session*, and a `router.replace` in another feature would be that definition
 * with one caller quietly outside it. The route table, the reset itself and the placeholder
 * component stay internal; they re-export the day something outside asks for one.
 *
 * `ShellScreen` is the one that has stopped being internal: Play's *Find a game* is the second
 * screen to wear 10.1's arrangement, and it is a real screen rather than a placeholder, so the
 * chrome it wears is the shell's rather than something a feature draws again a little
 * differently ([#268](https://github.com/Raketa02/Raketa/issues/268)).
 *
 * **Five of the layers are empty, and stay present.** The shell reads nothing from the backend
 * and writes nothing to it, so `api/`, `mappers/`, `schemas/`, `use-cases/` and `hooks/` have
 * nothing to hold — and the uniform-strict rule is *keep the folders, do not invent invariants
 * to fill them* (`_template/README.md`, docs/architecture.md Part 1). What the shell owns is a
 * table of five routes, the rule that reads a tab off a path, the sentences four unbuilt tabs
 * say, and the one function that lays a stack down.
 */

export { TabShell } from './components/TabShell';
export { ShellScreen, type ShellScreenProps } from './components/ShellScreen';

/**
 * The four lines, read outside this feature by one thing: the test harness, which asserts
 * *the player is in the app* and needs to know what that looks like now that the landing is
 * the Now tab.
 */
export { PLACEHOLDER_COPY } from './components/shellCopy';

export { AroundScreen, ChatsScreen, NowScreen, YouScreen } from './components/tabScreens';

/**
 * ⚡Play's own door, from inside Play.
 *
 * Called by the *Find a game* half of Play's segment and by nothing else outside this feature.
 * It lays down `[Now, Find a game]` and **ends the Play session on the way**, which is the
 * whole point of routing it through here: a player who was building on the deck's sport and
 * taps back to the search screen has arrived, and arriving is what clears a working copy.
 */
export { enterPlay } from './components/shellNavigation';

/**
 * Where a sent challenge lands.
 *
 * Called by the court's send and by nothing else. It lays down `[Now]` and **ends the Play
 * session on the way**, which is the fourth and last caller `resetShellStack`'s own docblock
 * has been naming: *a sent game is gone for good*, so there is no court to go back to and no
 * line-up left to hold ([#274](https://github.com/Raketa02/Raketa/issues/274)).
 */
export { landOnNow } from './components/shellNavigation';
