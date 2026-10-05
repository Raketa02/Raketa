'use client';

import { useRef, useState, type KeyboardEvent } from 'react';

import { clock } from '@/ui/format';

import { DAYS } from '../copy';
import { END_HOUR, FIRST_HOUR, type WeekHour } from '../mappers';
import { cellKey } from '../schemas';

import styles from './HoursGrid.module.css';

const HOURS = Array.from({ length: END_HOUR - FIRST_HOUR }, (_, index) => FIRST_HOUR + index);
const DAY_NUMBERS = DAYS.map((_, index) => index + 1);

/** The cell a pointer is over, or `null` off the grid. */
function cellAt(target: EventTarget | Element | null): WeekHour | null {
  if (!(target instanceof Element)) return null;
  const cell = target.closest<HTMLElement>('[data-cell]')?.dataset;
  if (cell?.day === undefined || cell.hour === undefined) return null;
  return { day: Number(cell.day), hour: Number(cell.hour) };
}

/**
 * Every cell on the straight line from `from` to `to`, `to` included and `from` not. The browser
 * sends a fast drag's moves a frame apart, so a pointer can cross a cell it is never seen over.
 */
function cellsBetween(from: WeekHour, to: WeekHour): WeekHour[] {
  const steps = Math.max(Math.abs(to.day - from.day), Math.abs(to.hour - from.hour));
  return Array.from({ length: steps }, (_, index) => {
    const along = (index + 1) / steps;
    return {
      day: Math.round(from.day + (to.day - from.day) * along),
      hour: Math.round(from.hour + (to.hour - from.hour) * along),
    };
  });
}

const STEPS: Readonly<Record<string, readonly [number, number]>> = {
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
};

/**
 * **The week, seven days by sixteen hours** (the player's own grid, mock 36): each cell a
 * checkbox named by its day and hour, offered in green. A press paints: it turns the cell it
 * lands on to the other state, and every cell the pointer passes over while held to that same
 * state, so a drag that begins on an offered hour clears. The keyboard walks the grid with the
 * arrows, one stop in the tab order for the whole of it, and Space ticks. `onPaint` says which
 * cell to turn which way; the owner keeps the week.
 */
export function HoursGrid({
  label,
  cells,
  onPaint,
}: {
  /** What a screen reader calls the grid: whose week it is. */
  label: string;
  cells: ReadonlySet<string>;
  onPaint: (key: string, on: boolean) => void;
}) {
  const grid = useRef<HTMLDivElement>(null);
  /** The state a press is painting while it is held, and the cell it was last over. */
  const painting = useRef<{ on: boolean; at: WeekHour } | null>(null);
  const [stop, setStop] = useState(() => cellKey({ day: 1, hour: FIRST_HOUR }));

  const walk = (event: KeyboardEvent<HTMLButtonElement>, day: number, hour: number) => {
    const step = STEPS[event.key];
    if (step === undefined) return;
    event.preventDefault();
    const next = cellKey({
      day: Math.min(7, Math.max(1, day + step[0])),
      hour: Math.min(END_HOUR - 1, Math.max(FIRST_HOUR, hour + step[1])),
    });
    setStop(next);
    grid.current?.querySelector<HTMLElement>(`[data-cell="${next}"]`)?.focus();
  };

  return (
    <div
      ref={grid}
      role="group"
      aria-label={label}
      className={styles.grid}
      onPointerDown={(event) => {
        const at = cellAt(event.target);
        if (at === null || event.button !== 0) return;
        // No focus ring and no text selection: the press paints.
        event.preventDefault();
        event.currentTarget.setPointerCapture(event.pointerId);
        const key = cellKey(at);
        painting.current = { on: !cells.has(key), at };
        onPaint(key, painting.current.on);
        setStop(key);
      }}
      onPointerMove={(event) => {
        const held = painting.current;
        if (held === null) return;
        const at = cellAt(document.elementFromPoint(event.clientX, event.clientY));
        if (at === null || cellKey(at) === cellKey(held.at)) return;
        for (const cell of cellsBetween(held.at, at)) onPaint(cellKey(cell), held.on);
        painting.current = { ...held, at };
      }}
      onPointerUp={() => {
        painting.current = null;
      }}
      onPointerCancel={() => {
        painting.current = null;
      }}
    >
      <span aria-hidden="true" />
      {DAYS.map((day) => (
        <span key={day.short} className={styles.day} aria-hidden="true">
          {day.short}
        </span>
      ))}
      {HOURS.map((hour) => (
        <div key={hour} className={styles.row}>
          <span className={styles.hour} aria-hidden="true">
            {clock(hour)}
          </span>
          {DAY_NUMBERS.map((day) => {
            const key = cellKey({ day, hour });
            return (
              <button
                key={key}
                type="button"
                role="checkbox"
                aria-checked={cells.has(key)}
                aria-label={`${DAYS[day - 1]?.long} ${clock(hour)}`}
                tabIndex={key === stop ? 0 : -1}
                data-cell={key}
                data-day={day}
                data-hour={hour}
                className={styles.cell}
                onFocus={() => setStop(key)}
                onKeyDown={(event) => walk(event, day, hour)}
                onClick={(event) => {
                  // A pointer painted on its press already; a key's click has no pointer.
                  if (event.detail === 0) onPaint(key, !cells.has(key));
                }}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}
