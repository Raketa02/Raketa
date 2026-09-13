/**
 * **The Chats tab** — the inbox, and the one sentence that says what a chat is here.
 *
 * The tab stops being a placeholder ([#360](https://github.com/Raketa02/Raketa/issues/360)) and
 * becomes what it has always been described as: a screen the shell owns, composing sections
 * other features draw, exactly as Now composes `GamesSection` and You composes
 * `PlayIntentsSection`. **It owns the tab's own sentences and nothing that is drawn under
 * them.**
 *
 * **Two sections now, and the tab is complete as a list.** `CHALLENGES` is `features/challenges`'
 * and `CONVERSATIONS` is `features/conversations`'
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)) — two contexts, two queries, two caches,
 * deliberately not merged. The obligation is first: this tab holds **one obligation and three
 * rooms**, and a challenge you can clear is the thing the badge is counting.
 *
 * **A `LINE_UP_INCOMPLETE` challenge you accepted draws a row in both of them**, which is the
 * answer rather than a duplicate — the challenge row is the obligation and the conversation row is
 * the room. It falls out of the composition rather than being arranged here: neither section knows
 * the other exists.
 *
 * **The tab composes one act into the rooms' rows, and it is the only thing it hands under them
 * that is not a sentence** ([#427](https://github.com/Raketa02/Raketa/issues/427)). *Leave the
 * game*, revealed by a swipe on a conversation row, is the **departure's** — a challenge act — and
 * the row is the conversation's; `features/challenges` already imports `features/conversations`,
 * so the row importing the act back would be the cycle Part 1 calls a defect. The shell imports
 * both, so the door is composed here, on the shape `features/plans` uses to hand `LeaveGame` into
 * the game screen (ADR-0149 §1): the section says what a row needs from an act, the challenges
 * feature exports a component that satisfies it, and neither names the other.
 *
 * The panel stays last: it explains the limit rather than announcing it, so it belongs under what
 * a player came here to read rather than above it.
 *
 * The panel is an **info** note, which is 5.4's *explains rather than states* — the one variant
 * with a glyph, and the right register for a sentence about how the product works.
 */

import { ChallengesSection, DepartureDoor } from '@/features/challenges/types';
import { ConversationsSection } from '@/features/conversations/types';
import { Note } from '@/shared/ui';

import { ShellScreen } from './ShellScreen';
import { CHATS_COPY } from './shellCopy';

export function ChatsScreen() {
  return (
    <ShellScreen title={CHATS_COPY.title}>
      <ChallengesSection empty={CHATS_COPY.emptyChallenges} />
      <ConversationsSection empty={CHATS_COPY.emptyConversations} act={DepartureDoor} />

      <Note variant="info" title={CHATS_COPY.panel.title}>
        {CHATS_COPY.panel.body}
      </Note>
    </ShellScreen>
  );
}
