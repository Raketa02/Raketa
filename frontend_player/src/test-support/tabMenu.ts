/**
 * **A group page's tab menu, as a suite opens it** — *open a tab's menu, then pick a kind*, said one
 * way by every suite ([#861](https://github.com/Rakieta02/Rakieta/issues/861); PRD #859). Where a row
 * of *Competitive | For fun* once stood, the selected tab draws a chevron and a press on it opens
 * `TabMenu`; a suite that picked a kind on the row picks it here.
 *
 * **Everything is found by what a listener hears**: the selected tab by its name — the tab's word,
 * then the kind it holds, *Friends, Competitive* or *Games, For fun* — with `selected` and
 * `expanded`, and a line by the kind its name begins with: Games' live lines say their count after
 * it, *For fun, 1 game*, and its door that it is one, *For fun, not a kind you play* (#862). Nothing
 * reads a component's internals.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { act, fireEvent, screen, within } from 'expo-router/testing-library';

import { theme } from '@/shared/ui/theme';

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

/**
 * **The Games deck's swap, run to its end** (#863): a kind picked from the Games tab's menu sends the
 * stack out and brings the other kind's in, and the stack coming in answers once it has landed — so
 * a suite that answers it, or touches it, lands it first. Each beat is its own advance: the second
 * is set going by the first one's end.
 */
export function landTheSwap(): void {
  act(() => jest.advanceTimersByTime(theme.motion.kindSwap.out));
  act(() => jest.advanceTimersByTime(theme.motion.kindSwap.in));
}

/** **Shut the tab's menu open now** — a second press on its tab, which changes nothing else. */
export async function shutTabMenu(tab: string): Promise<void> {
  fireEvent.press(await menuTab(tab, true));
}

/**
 * **What the menu says, read and put away**: the tab's menu opened, the line with this whole spoken
 * name found — *Competitive, 7 games*, selected or not where `selected` says — and the menu shut
 * again, so a suite that only reads leaves the page as it found it.
 */
export async function menuSays(
  tab: string,
  name: string,
  selected?: boolean,
): ReturnType<typeof screen.findByRole> {
  const open = await openTabMenu(tab);
  const line = await within(open).findByRole('button', {
    name,
    ...(selected === undefined ? {} : { selected }),
  });
  await shutTabMenu(tab);
  return line;
}
