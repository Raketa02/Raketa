/**
 * **Copy a link, and say whether it went** — the clipboard port's write, answered by a toast
 * ([#756](https://github.com/Rakieta02/Rakieta/issues/756)): *Link copied*, or that the phone would
 * not take it, so a tap never passes silently.
 *
 * Three surfaces wrote it the same way — a group page's **Copy link** (#513), an official group's
 * (#529) and the Add friends sheet's friend link (#756) — and the third caller is where it moves
 * here. **The words stay each caller's**: they are its copy module's sentences, handed in.
 */

import { showToast } from '@/shared/store/toast.store';

import { useClipboard } from './ClipboardProvider';

export interface CopyWords {
  readonly copied: string;
  readonly notCopied: string;
}

/** A copy that says so — the clipboard this tree runs against, and the toast it is answered by. */
export function useCopyAndSay(): (text: string, words: CopyWords) => Promise<void> {
  const clipboard = useClipboard();
  return async (text, words) => {
    const copied = await clipboard.writeText(text);
    showToast(
      copied ? { message: words.copied, tone: 'ok' } : { message: words.notCopied, tone: 'bad' },
    );
  };
}
