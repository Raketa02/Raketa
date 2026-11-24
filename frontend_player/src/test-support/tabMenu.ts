/**
 * **A group page's tab menu, as a suite opens it** — *open a tab's menu, then pick a kind*, said one
 * way by every suite ([#861](https://github.com/Raketa02/Raketa/issues/861); PRD #859). Where a row
 * of *Competitive | For fun* once stood, the selected tab draws a chevron and a press on it opens
 * `TabMenu`; a suite that picked a kind on the row picks it here.
 *
 * **Everything is found by what a listener hears**: the selected tab by its name — the tab's word,
 * then the kind it holds, *Friends, Competitive* — with `selected` and `expanded`, and a line by the
 * kind its name begins with (Games' lines say their count after it from #862). Nothing reads a
 * component's internals.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { fireEvent, screen, within } from 'expo-router/testing-library';

/** `word`, with every character a pattern would read as an operator escaped. */
function literal(word: string): string {
  return word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** A name that is `word`, or `word` followed by a comma and more: *Friends* or *Friends, For fun*. */
function beginsWith(word: string): RegExp {
  return new RegExp(`^${literal(word)}(,|$)`);
}

/**
 * **The selected tab that offers its menu** — *Friends, Competitive* — shut unless `expanded` says
 * otherwise. Found once it says a kind, so a tab drawn without its menu is never it.
 */
export function menuTab(tab: string, expanded = false): ReturnType<typeof screen.findByRole> {
  return screen.findByRole('button', {
    name: new RegExp(`^${literal(tab)}, `),
    selected: true,
    expanded,
  });
}

/** **Open the selected tab's menu** — a press on the tab — and the menu it opens. */
export async function openTabMenu(tab: string): ReturnType<typeof screen.findByRole> {
  fireEvent.press(await menuTab(tab));
  return screen.findByTestId('tab-menu');
}

/** A line of the menu open now, by the kind its name begins with. */
export function menuLine(kind: string, selected?: boolean): ReturnType<typeof screen.findByRole> {
  return within(screen.getByTestId('tab-menu')).findByRole('button', {
    name: beginsWith(kind),
    ...(selected === undefined ? {} : { selected }),
  });
}

/** **Open a tab's menu, then pick a kind** — the one way every suite says it. */
export async function pickKind(tab: string, kind: string): Promise<void> {
  await openTabMenu(tab);
  fireEvent.press(await menuLine(kind));
}
