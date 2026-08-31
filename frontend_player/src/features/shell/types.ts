/**
 * The shell feature's only public surface.
 *
 * The shell is the app's five tabs and the one stack under them. `src/app/` mounts it and
 * names each route; nothing else outside this folder has needed anything yet.
 *
 * **What is exported is what has a caller.** The route table, the reset and its two entry
 * points and the placeholder component are all internal today, and they re-export the day
 * something outside asks for one — `enterPlay` when the *Find a game* segment re-enters the
 * tab from inside it, which arrives with the deck
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)). Exporting them now would be a
 * surface sized for tickets that do not exist.
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
