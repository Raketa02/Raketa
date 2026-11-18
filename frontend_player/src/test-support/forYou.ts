/**
 * **FOR YOU's lines, as a player reaches them** ([#820](https://github.com/Raketa02/Raketa/issues/820);
 * ADR-0205 §5) — every line is closed when Home opens, and a closed line draws nothing it holds, so a
 * suite about what a line holds opens it first, as a player would.
 */

import { act, fireEvent, screen, within } from 'expo-router/testing-library';

import { theme } from '@/shared/ui';

/** A line's header — the button named by its title. */
export const lineHeader = (title: string) => screen.getByRole('button', { name: title });

/** Whether a line is open, by its header's spoken state. */
export const isOpen = (title: string) =>
  screen.getByRole('button', { name: title }).props.accessibilityState?.expanded === true;

/**
 * **Opens a line**, once it is shown — a press on its header, the fold of a line open before it run,
 * and its own unfold, so the line asked for is drawn open and its cards are on the page.
 */
export async function openLine(title: string): Promise<void> {
  const closed = await screen.findByRole('button', { name: title, expanded: false });
  fireEvent.press(closed);
  // Two beats, each its own act: the unfold's clock starts only once the fold's end is drawn.
  act(() => jest.advanceTimersByTime(theme.motion.lineFold));
  act(() => jest.advanceTimersByTime(theme.motion.lineUnfold));
  await screen.findByRole('button', { name: title, expanded: true });
}

/** The lines FOR YOU shows, top to bottom, by title. */
export function lineTitles(): string[] {
  return within(screen.getByTestId('for-you'))
    .getAllByRole('button')
    .filter((node) => node.props.accessibilityState?.expanded !== undefined)
    .map((node) => node.props.accessibilityLabel as string);
}
