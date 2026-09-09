/**
 * **The Chats tab** — the inbox, and the one sentence that says what a chat is here.
 *
 * The tab stops being a placeholder ([#360](https://github.com/Raketa02/Raketa/issues/360)) and
 * becomes what it has always been described as: a screen the shell owns, composing sections
 * other features draw, exactly as Now composes `GamesSection` and You composes
 * `PlayIntentsSection`. **It owns the tab's own sentences and nothing that is drawn under
 * them.**
 *
 * `CHALLENGES` is `features/challenges`'. `CONVERSATIONS` arrives beside it with
 * [#363](https://github.com/Raketa02/Raketa/issues/363), and the panel stays last: it explains
 * the limit rather than announcing it, so it belongs under what a player came here to read
 * rather than above it.
 *
 * The panel is an **info** note, which is 5.4's *explains rather than states* — the one variant
 * with a glyph, and the right register for a sentence about how the product works.
 */

import { ChallengesSection } from '@/features/challenges/types';
import { Note } from '@/shared/ui';

import { ShellScreen } from './ShellScreen';
import { CHATS_COPY } from './shellCopy';

export function ChatsScreen() {
  return (
    <ShellScreen title={CHATS_COPY.title}>
      <ChallengesSection empty={CHATS_COPY.emptyChallenges} />

      <Note variant="info" title={CHATS_COPY.panel.title}>
        {CHATS_COPY.panel.body}
      </Note>
    </ShellScreen>
  );
}
