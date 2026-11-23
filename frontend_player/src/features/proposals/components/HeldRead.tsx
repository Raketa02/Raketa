/**
 * **A read a board could not draw** — held while offline, which resumes, or refused, with why and
 * the retry. Fill in's and You’re in's alike, each drawing it for its own read, so one read failing
 * never touches the other's rows (the screens A3).
 */

import { offlineMessage, type AppError } from '@/shared/errors';
import { Note } from '@/shared/ui';

import { ReadFailed } from './ReadFailed';

export interface HeldReadProps {
  readonly read: {
    readonly fetchStatus: string;
    readonly error: AppError | null;
    readonly refetch: () => unknown;
  };
}

export function HeldRead({ read }: HeldReadProps) {
  if (read.error === null || read.fetchStatus === 'paused') {
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  }
  return <ReadFailed error={read.error} onRetry={() => void read.refetch()} />;
}

/** **Whether a read has nothing to show and never will without help** — held offline, or refused. */
export function isHeld(read: {
  readonly data: unknown;
  readonly fetchStatus: string;
  readonly error: AppError | null;
}): boolean {
  return read.data === undefined && (read.fetchStatus === 'paused' || read.error !== null);
}
