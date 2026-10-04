/**
 * The shell feature's only public surface.
 *
 * The shell is the app's five tabs and the one stack under them. `src/app/` mounts it and
 * names each route; nothing else outside this folder has needed anything yet.
 *
 * **What is exported is what has a caller.** `enterPlay` was one for as long as the deck lived
 * under Play: the *Find a game* segment re-entered the tab from inside it, which is **arriving
 * rather than going back** ([#270](https://github.com/Raketa02/Raketa/issues/270)). The segment
 * left with the deck's move to its own tab (ADR-0169 §1), and so did the export — the route
 * table and the reset itself stay internal too; they re-export the day something outside asks
 * for one. The placeholder component went with the last placeholder (ADR-0179).
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
 * table of five routes, the rule that reads a tab off a path, the sentences the three tabs it
 * composes say, and the one function that lays a stack down.
 */

export { TabShell } from './components/TabShell';
export { ShellScreen, type ShellScreenProps } from './components/ShellScreen';

/**
 * The two built tabs' own sentences, read outside this feature by the test harness — which
 * asserts *the player is in the app* and needs to know what that looks like now that the
 * landing is the Now tab ([#367](https://github.com/Raketa02/Raketa/issues/367)) — and by each
 * tab's own suite, which asserts the tab's sentences rather than string literals, because the
 * wording is this file's to change and the rules the sentences carry are not.
 */
export { CHATS_COPY, NOW_COPY, PLAY_COPY } from './components/shellCopy';

/**
 * **Play with `find_a_game` off** — the *Groups | Explore* segment and the page under it
 * ([#512](https://github.com/Raketa02/Raketa/issues/512)). The Play route draws it where the empty
 * placeholder used to be; the placeholder is Explore's page now.
 */
export { PlayScreen } from './components/PlayScreen';

/**
 * **The You tab's own sentences** — read outside this feature by the screens behind its rows,
 * which wear the group title they were opened from as their eyebrow
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1), and by the suites that hold the tab to its words.
 */
export { YOU_COPY } from './components/youCopy';

export { NowScreen } from './components/tabScreens';

/**
 * The You tab — **a screen rather than a placeholder**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 *
 * The shell's for the reason Now and Chats are: a tab owns its own sentences and composes other
 * features' rows under them. In a file of its own because it is not thin.
 */
export { YouScreen } from './components/YouScreen';

/**
 * The Chats tab — **a screen rather than a placeholder**
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)).
 *
 * It is the shell's for the reason the Now and You tabs are: a tab owns its own sentences and
 * composes other features' sections under them. It has a file of its own because it is no
 * longer thin.
 */
export { ChatsScreen } from './components/ChatsScreen';

/**
 * Open a flanking tab from a screen inside another one.
 *
 * Two callers. The first is a **link to where a fact lives**: Find a game's standing
 * declaration line offers *Change*, and what it changes is on the You tab beside the other
 * durable facts strangers read ([#294](https://github.com/Raketa02/Raketa/issues/294),
 * [#296](https://github.com/Raketa02/Raketa/issues/296)). The second is **the yes screen's
 * *Open the chat* after a mutual** ([#434](https://github.com/Raketa02/Raketa/issues/434),
 * ADR-0167 §1): the room has to land as `[Chats list, the room]` and the list is nowhere under
 * the deck, so the screen lays the Chats tab down and pushes the room over it — *from the deck
 * this switches the tab; Players keeps its held deck*. It is the tab bar's own move rather than
 * a second one — the shell has one navigation and every arrival replaces — so a player sent
 * here lands where pressing the column would have put them, and **the Play session ends on the
 * way**, which is what leaving Play has always meant.
 */
export { openTab } from './components/shellNavigation';

/**
 * Where a sent challenge lands.
 *
 * Called by the court's send and by nothing else. It lays down `[Now]` and **ends the Play
 * session on the way**, which is the fourth and last caller `resetShellStack`'s own docblock
 * has been naming: *a sent game is gone for good*, so there is no court to go back to and no
 * line-up left to hold ([#274](https://github.com/Raketa02/Raketa/issues/274)).
 */
export { landOnNow } from './components/shellNavigation';
