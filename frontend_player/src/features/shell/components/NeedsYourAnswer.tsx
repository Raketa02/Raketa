/**
 * **Needs your answer** — the envelope on Home's header, and the sheet it opens
 * ([#816](https://github.com/Raketa02/Raketa/issues/816), [#817](https://github.com/Raketa02/Raketa/issues/817),
 * [ADR-0205](../../../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
 * §1–§2; home refactor 1 and 2).
 *
 * ```
 * Home                                   ✉   🔔   (🏆 #7)     ← the envelope only while something waits
 * ─────────────────────────────────────────────────────────
 *                ───                                         ← the grab: a pull down closes it
 * Needs your answer                                    (✕)
 * TO CONFIRM · 1                                             ← `proposals`' sections
 * FRIENDS GAME · 1
 * FRIEND REQUESTS · 2                                        ← `friends`' sections
 * ASKED FOR A LEVEL · 1
 * ```
 *
 * ## The envelope
 *
 * **A Feather `mail` mark in `ink`**, in a 44pt target, named *Needs your answer* (ADR-0205 §2;
 * Part 16): the header's envelope, beside the friend button's volt one, and one meaning for both —
 * *someone asked you*. **It is drawn only while something waits** (`envelopeShows`): a payment to
 * confirm, a friends game invitation, a friend request or an ask for a level, each counted off its
 * read (`proposals`' `useAnswersWaiting`) — a read in flight or refused counts nothing, so a failed
 * *To confirm* read draws no envelope by itself. Its count is #819's. Without it the bell and the
 * trophy keep their places, since the header's right slot is right-aligned and the envelope is its
 * first item.
 *
 * ## The sheet
 *
 * **The app's own sheet** (`BottomSheet`), only as tall as what it holds up to its cap, scrolling
 * beyond it, closing on ✕, a pull down on its head (`closesOnSwipe`) or the backdrop. **It stays
 * mounted**, its `visible` switched, so opening it moves a screen reader's focus to its title, and
 * closing it returns focus to the envelope while there is one — after the last answer there is
 * none, and focus is the screen reader's to place (ADR-0198 asks no more). Where it stands is
 * `needsYourAnswer`'s, in `domain/`:
 *
 * - **The last answer closes it for good**, and the envelope goes. Something arriving while it is
 *   open appears in it, since the sections read their reads.
 * - **A face opens the record over it**, drawn inside it, as `discovery`'s vibe sheet draws its
 *   record: iOS drops a native window opened while another is still closing. Closing the record
 *   leaves the sheet up if anything still waits, and closes both if nothing does.
 * - **Confirm, Fix and an invitation's Accept open the fill's sheets over it** (#817): the payment
 *   confirmation and the card setup, drawn inside it for the record's reason (`FillInASheet`), the
 *   sheet stepping aside under them and back when they close, if anything still waits. ***It's a
 *   game!* closes it for good.**
 * - **Get your level, or Carry on, closes it for good** and starts the questionnaire. The start
 *   navigates, so it is run here, outside the sheet (`useGetAskedLevel`): nothing in a sheet reads
 *   the navigation (`docs/architecture.md` Part 13). A start that fails says the *level asked*
 *   notice's own sentence over Home (`OPEN_NOTICE_WORDS.unstarted`).
 * - **A link or a notice asks for it** (#817; `openNeedsYourAnswer`): Home with the sheet up, once
 *   the reads they re-read land — Home as it is, with no sheet, when nothing waits by then.
 *
 * ## The sections are their features'
 *
 * TO CONFIRM and FRIENDS GAME are `proposals`', FRIEND REQUESTS and ASKED FOR A LEVEL `friends`',
 * in that order, each drawing nothing while it holds nothing. The shell hands them what is other
 * features': the reliability chip and the record (`player_record`'s), the bell's re-read
 * (`notifications`'), since answering takes a row off the bell — and **the fill**, which a sheet
 * cannot reach by itself: it keeps the root's contexts only, and the fill is mounted around the tabs.
 * So it is read here and carried in.
 */

import Feather from '@expo/vector-icons/Feather';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useReducer, useRef } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import {
  FriendRequestsSection,
  LevelAsksSection,
  useGetAskedLevel,
} from '@/features/friends/types';
import { OPEN_NOTICE_WORDS, rereadNotices } from '@/features/notifications/types';
import { PlayerRecordSheet, PlayerScoreTag } from '@/features/player_record/types';
import {
  FillInASheet,
  FriendsGameSection,
  ToConfirmSection,
  useAnswersWaiting,
  useSheetFill,
} from '@/features/proposals/types';
import { showToast } from '@/shared/store/toast.store';
import { BottomSheet, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  CLOSED,
  envelopeShows,
  needsYourAnswer,
  readingRecordOf,
  sheetIsAsked,
  sheetIsUp,
} from '../domain/needsYourAnswer';

import { whenNeedsYourAnswerAsked } from './needsYourAnswerAsked';
import { NEEDS_YOUR_ANSWER_COPY as COPY } from './shellCopy';

export function NeedsYourAnswer() {
  const client = useQueryClient();
  const answers = useAnswersWaiting();
  const waits = envelopeShows(answers.counts);
  const fill = useSheetFill();
  const [sheet, dispatch] = useReducer(needsYourAnswer, CLOSED);
  const envelope = useRef<View | null>(null);
  const rereadBell = useCallback(() => rereadNotices(client), [client]);
  const start = useGetAskedLevel(rereadBell);

  // The last answer, here or anywhere else: the sheet closes for good, and the envelope goes.
  useEffect(() => {
    if (!waits) dispatch({ kind: 'emptied' });
  }, [waits]);

  // A link or a notice asks for it, and it opens once the reads they re-read land.
  useEffect(() => whenNeedsYourAnswerAsked(() => dispatch({ kind: 'asked' })), []);
  const asked = sheetIsAsked(sheet);
  useEffect(() => {
    if (asked && !answers.reading) dispatch({ kind: 'settled', stillWaits: waits });
  }, [asked, answers.reading, waits]);

  // What the fill puts up from a tile — the sheet steps aside under it — and takes down. Told again
  // as the sheet opens too: one a link or a notice opened over a fill sheet already up steps aside.
  const { over } = fill;
  const open = sheet.kind === 'open';
  useEffect(() => {
    dispatch(
      over === 'none'
        ? { kind: 'fillGone', stillWaits: waits }
        : { kind: 'fillRaised', itsAGame: over === 'itsAGame' },
    );
  }, [over, waits, open]);

  const reading = readingRecordOf(sheet);
  const onFace = (playerId: string) => dispatch({ kind: 'faceTapped', playerId });
  const getLevel = (sport: Sport) => {
    dispatch({ kind: 'handedToScreen' });
    start.get(sport, (error) => showToast(OPEN_NOTICE_WORDS.unstarted(sport, error)));
  };

  return (
    <>
      {waits ? (
        <Pressable
          ref={envelope}
          accessibilityRole="button"
          accessibilityLabel={COPY.title}
          onPress={() => dispatch({ kind: 'envelopePressed' })}
          style={({ pressed }) => [s.envelope, pressed ? s.pressed : undefined]}
          testID="needs-your-answer-envelope"
        >
          <Feather
            name="mail"
            size={theme.size.tabIcon}
            color={theme.color.ink}
            accessibilityElementsHidden
            importantForAccessibility="no"
          />
        </Pressable>
      ) : null}
      <BottomSheet
        visible={sheetIsUp(sheet, waits)}
        onClose={() => dispatch({ kind: 'dismissed' })}
        title={COPY.title}
        closeLabel={COPY.close}
        returnFocusTo={envelope}
        closesOnSwipe
      >
        <FillInASheet fill={fill}>
          <ToConfirmSection />
          <FriendsGameSection invitations={answers.friendsGames} onAnswered={rereadBell} />
          <FriendRequestsSection
            scoreTag={(request) => (
              <PlayerScoreTag
                score={request.playerScore}
                {...(request.reliabilityBand === undefined
                  ? {}
                  : { band: request.reliabilityBand })}
              />
            )}
            onFace={onFace}
            onAnswered={rereadBell}
          />
          <LevelAsksSection
            onFace={onFace}
            onAnswered={rereadBell}
            onStart={getLevel}
            starting={start.starting}
          />
          {/* Over the sheet, drawn inside it — see the module note. */}
          {reading === undefined ? null : (
            <PlayerRecordSheet
              visible
              onClose={() => dispatch({ kind: 'recordClosed', stillWaits: waits })}
              subject={{ kind: 'player', playerId: reading }}
            />
          )}
        </FillInASheet>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  // 6.5's whole target, the mark centred in it, as the bell's.
  envelope: {
    width: theme.size.minTouch,
    height: theme.size.minTouch,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { opacity: 0.7 },
});
