/**
 * **FOR YOU's lines, as a player reaches them** ([#820](https://github.com/Rakieta02/Rakieta/issues/820);
 * ADR-0205 §5) — every line is closed when Home opens, and a closed line draws nothing it holds, so a
 * suite about what a line holds opens it first, as a player would.
 */

import { act, fireEvent, screen, within } from 'expo-router/testing-library';

import { theme } from '@/shared/ui';

/** A count as a line says it, after its title (#822): *, 14*, *, 99+*. */
const COUNT = String.raw`, (\d+|99\+)`;
const SAID_COUNT = new RegExp(`${COUNT}$`);

/**
 * **A line's spoken name, whatever its count** — its title, then its count as drawn (*Players at your
 * level, 14*), or the title alone on a line with none (Top 10). A suite about the count asserts the
 * whole name; every other suite finds the line by its title.
 */
export function lineNamed(title: string): RegExp {
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^${escaped}(${COUNT})?$`);
}

/** A line's header — the button named by its title. */
export const lineHeader = (title: string) => screen.getByRole('button', { name: lineNamed(title) });

/** Whether a line is open, by its header's spoken state. */
export const isOpen = (title: string) =>
  lineHeader(title).props.accessibilityState?.expanded === true;

/**
 * **Opens a line**, once it is shown — a press on its header, the fold of a line open before it run,
 * and its own unfold, so the line asked for is drawn open and its cards are on the page.
 */
export async function openLine(title: string): Promise<void> {
  const name = lineNamed(title);
  const closed = await screen.findByRole('button', { name, expanded: false });
  fireEvent.press(closed);
  // Two beats, each its own act: the unfold's clock starts only once the fold's end is drawn.
  act(() => jest.advanceTimersByTime(theme.motion.lineFold));
  act(() => jest.advanceTimersByTime(theme.motion.lineUnfold));
  await screen.findByRole('button', { name, expanded: true });
}

type Node = ReturnType<typeof screen.getByTestId>;

/**
 * **What stands in an open line's footer, left to right** (`folding-line-footer`) — *link* for the
 * part that holds its link, and `name`'s word for every other part (#821: Top 10's switcher at the
 * left, *Open the rankings ›* at the right).
 */
export function footerParts(footer: Node, name: (part: Node) => string): string[] {
  return footer.children.map((part: Node | string) => {
    if (typeof part === 'string') return part;
    return within(part).queryByRole('link') !== null ? 'link' : name(part);
  });
}

/** The lines FOR YOU shows, top to bottom, by title — their counts left off. */
export function lineTitles(): string[] {
  return lineNames().map((name) => name.replace(SAID_COUNT, ''));
}

/** The lines FOR YOU shows, top to bottom, by their whole spoken names — counts and all. */
export function lineNames(): string[] {
  return within(screen.getByTestId('for-you'))
    .getAllByRole('button')
    .filter((node) => node.props.accessibilityState?.expanded !== undefined)
    .map((node) => node.props.accessibilityLabel as string);
}
