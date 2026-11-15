/**
 * **Every screen pushed over a tab takes the push transition** — held against the file tree, since
 * nothing else notices a route left off the list. It still opens, swapped in with no transition,
 * and a screen whose header matches the page under it reads as a blink: Info over a group's page
 * shipped that way, beside Post a game, a game's details and a rescue.
 *
 * The tree is read from disk rather than from the harness's route table, which is written by hand
 * and could leave out the same route the list does.
 */

import { readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { PUSHED_SCREENS } from './pushedScreens';

const TAB_TREE = join(__dirname, '..', '..', '..', 'app', '(app)', '(tabs)');

/**
 * The two roots a tab press **lands** on, which take the shell's `none`: Home, kept at the bottom,
 * and You's root, laid over it by the press (`TAB_STACK`). ⚡Play's root is not one of them: it takes
 * the push, so back from it reads as leaving Play.
 */
const TAB_ROOTS = ['index', 'you/index'];

/** Every route in the tab tree as `Stack.Screen` names it: the path, no extension, no layout. */
function routesUnder(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return routesUnder(path);
    if (!entry.name.endsWith('.tsx') || entry.name.startsWith('_')) return [];
    return [relative(TAB_TREE, path).slice(0, -'.tsx'.length).split(sep).join('/')];
  });
}

const routes = routesUnder(TAB_TREE);
const pushed: readonly string[] = PUSHED_SCREENS;

it('reads the tab tree, roots and pushed screens both', () => {
  // A path that resolved to nothing would pass both checks below on an empty list.
  expect(routes).toEqual(expect.arrayContaining([...TAB_ROOTS, 'play/group/[groupId]/info']));
});

it('gives every route but the two tab roots the push transition', () => {
  const missing = routes.filter((r) => !TAB_ROOTS.includes(r) && !pushed.includes(r));
  expect(missing).toEqual([]);
});

it('names no screen the tree does not have, and neither root', () => {
  const stray = pushed.filter((name) => !routes.includes(name) || TAB_ROOTS.includes(name));
  expect(stray).toEqual([]);
});
