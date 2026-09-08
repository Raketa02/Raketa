/**
 * **`SH.player`** — everything the platform will say about one *person*, current at the moment
 * the sheet was opened ([#384](https://github.com/Raketa02/Raketa/issues/384)).
 *
 * Tapping a photograph and receiving a weights-and-contributions table was always slightly
 * wrong: somebody tapping a picture of a person is asking **who is this**. So a face opens the
 * person, and the pairing gets a row.
 *
 * ## It reads no global state, and that is what lets three surfaces share it
 *
 * Everything arrives as a prop — the subject, the sport the reader arrived from, the distance,
 * the reader's own area and the pairing. The builder's forecast card opens it today; the chat
 * header and the game screen open it next, with no search behind them and therefore no
 * distance, no overlap and no pairing row. A sheet that reached for a store would have to be
 * told which of those it was in.
 *
 * ## The pairing row exists only where a pairing does
 *
 * Opened from the forecast card there is a Fit and a row; opened later from Now, a chat or the
 * games list there is neither. It is the same discipline the Social tag overlap already takes,
 * applied to the other pairwise fact on this sheet: **a pairing fact appears only when a
 * pairing is in hand**. The Fit breakdown is not deleted — the figure in the pill has no other
 * account anywhere in the app — it moves behind a label that names a pairing rather than
 * sitting behind a photograph.
 *
 * ## Your own face opens the same sheet, retitled
 *
 * *How others see you*, with the distance gone because it would always be nought. The argument
 * is legibility rather than symmetry: the reliability number has been deciding who you are
 * shown to since you signed up, and **a penalty nobody can look up is a penalty nobody can
 * fix**. Which title is drawn is the server's `is_self` and never a comparison made here.
 *
 * ## Three states, and the sheet is up for all three
 *
 * It opens instantly and fills — which is the whole reason a second round trip is affordable
 * here and was not on the twenty-row shortlist. A skeleton, the record, or the refusal.
 *
 * **The refusal draws one line and nothing else.** Never disclosed, blocked in either
 * direction, held, and no such player answer the same code with the same body, byte for byte,
 * and a response that named which would deliver a block to the one person a block is meant to
 * be invisible to. There is no retry on it, because re-asking a refusal returns the refusal —
 * where a failure to *reach* the platform gets the recovery sentence and a control, since that
 * one genuinely can succeed on a second press.
 *
 * ## Tall, with an internal scroll and a pinned header
 *
 * 9.1's own shape: the grab, the title and the close control stay put and the body scrolls
 * under them, so the name of whoever is being read stays visible while the reader works down.
 * It is a sheet rather than a screen because leaving the four you are building is a heavier
 * action than tapping a face should feel like — and it opens at a **standing height** so the
 * skeleton and the record are the same size and the panel does not jump when the answer lands.
 *
 * ## Four regions, four elements
 *
 * There is no interactive element inside it other than the pairing row, so every group merges
 * into the nearest heading (§20.1) and `recordPresentation` writes what each of them says.
 * Focus lands on the **title** on the way in, which is `BottomSheet`'s flat rule for every
 * sheet — and there is **no `returnFocusTo`**: up to four faces open this from one card, so
 * there is no one control to return to.
 */

import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { codeMessage, type AppError } from '@/shared/errors';
import { BottomSheet, Note, Button, PressableCard, SocialTagRow, theme } from '@/shared/ui';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayerRecord, RecordSubject } from '../domain/playerRecord';
import { recordTagRow } from '../domain/tagRow';
import { usePlayerRecord } from '../hooks/usePlayerRecord';

import { RecordHeader } from './RecordHeader';
import { SkillCard } from './SkillCard';
import {
  FIT_ROW_BODY,
  RECORD_UNAVAILABLE,
  RECORD_UNAVAILABLE_CODE,
  fitRowLabel,
  fitRowTitle,
  recordCloseLabel,
  recordTitle,
  socialTagsLabel,
} from './recordPresentation';

/** The one code, for all four causes — and the one sentence this client draws from it. */
const RECORD_FAILURES: Readonly<Record<string, string>> = {
  [RECORD_UNAVAILABLE_CODE]: RECORD_UNAVAILABLE,
};

const RETRY_LABEL = 'Try again';
const LOADING_LABEL = 'Reading their record';

/**
 * How tall the sheet stands before it knows anything.
 *
 * A skeleton the height of a spinner would open a sheet three lines tall and then grow it to
 * most of the screen when the answer landed, which reads as two different surfaces. The
 * standing height is roughly what a filled record occupies; `BottomSheet`'s own 88 % cap is
 * still what bounds it, so this never becomes the screen.
 */
const STANDING_HEIGHT = 380;

export interface PlayerRecordSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Whose record, and through which of the two routes. */
  readonly subject: RecordSubject;
  /**
   * Which sport the reader arrived from.
   *
   * It selects what the sheet is **about** and never who may be seen: where the subject holds
   * no rating in it the server falls back to the sport they have played most, and the panel
   * states which it chose.
   */
  readonly sport?: Sport;
  /** Whole kilometres. Absent where no search is behind the entry point — and on your own record. */
  readonly distanceKm?: number;
  /** The reader's own coarse area, for the one comparison a client is licensed to make. */
  readonly viewerAreaCode?: string;
  /**
   * Which of their tags the reader also chose — **the engine's published answer, never
   * recomputed here.**
   *
   * It is a fact about a *pair*, and it supplies the **register** rather than the tags: the tags
   * drawn are the record's own live list, because a candidate whose tag terms stood down carries
   * none on its card and this sheet's whole promise is that it is current (`domain/tagRow`).
   * Absent, their tags draw untinted and nothing is claimed — which is *we do not know* rather
   * than *there is nothing*.
   */
  readonly tagOverlap?: SocialTagOverlap;
  /** The pairing behind the entry point, where there is one. See the module note. */
  readonly pairing?: {
    /** The Fit the engine published for the two of them, as the pill printed it. */
    readonly fit: number;
    readonly onExplain: () => void;
  };
}

export function PlayerRecordSheet({
  visible,
  onClose,
  subject,
  sport,
  distanceKm,
  viewerAreaCode,
  tagOverlap,
  pairing,
}: PlayerRecordSheetProps) {
  const record = usePlayerRecord({
    subject,
    ...(sport === undefined ? {} : { sport }),
    enabled: visible,
  });

  // The title is the server's answer where there is one, and the parameterised route's own
  // default until it lands. A sheet opened from your own face is `kind: 'me'`, which is what
  // the caller knows rather than what it compared.
  const isSelf = record.data?.isSelf ?? subject.kind === 'me';

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={recordTitle(isSelf)}
      closeLabel={recordCloseLabel(isSelf)}
    >
      <View style={s.body}>
        {record.data === undefined ? (
          <Standing error={record.error} onRetry={() => void record.refetch()} />
        ) : (
          <Filled
            record={record.data}
            playerId={subject.playerId}
            {...(distanceKm === undefined ? {} : { distanceKm })}
            {...(viewerAreaCode === undefined ? {} : { viewerAreaCode })}
            {...(tagOverlap === undefined ? {} : { tagOverlap })}
            {...(pairing === undefined ? {} : { pairing })}
          />
        )}
      </View>
    </BottomSheet>
  );
}

/**
 * The two states that are not a record: still reading, and could not.
 *
 * A refusal is **one line and no control**. Everything else is the recovery sentence with the
 * control the failure belongs to, which is this read and nothing else on the screen underneath.
 */
function Standing({
  error,
  onRetry,
}: {
  readonly error: AppError | null;
  readonly onRetry: () => void;
}) {
  if (error === null) {
    return <ActivityIndicator accessibilityLabel={LOADING_LABEL} color={theme.color.muted} />;
  }

  if (error.code === RECORD_UNAVAILABLE_CODE) {
    return <Text style={s.refusal}>{RECORD_UNAVAILABLE}</Text>;
  }

  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {codeMessage(RECORD_FAILURES, error)}
      </Note>
      <Button label={RETRY_LABEL} variant="secondary" onPress={onRetry} />
    </View>
  );
}

function Filled({
  record,
  playerId,
  distanceKm,
  viewerAreaCode,
  tagOverlap,
  pairing,
}: {
  readonly record: PlayerRecord;
  readonly playerId: string;
} & Pick<PlayerRecordSheetProps, 'distanceKm' | 'viewerAreaCode' | 'tagOverlap' | 'pairing'>) {
  // Their live tags, in whichever register the pairing licenses. The claim about nothing is the
  // engine's and is kept; every other silence draws the tags and says nothing.
  const tags = recordTagRow(record.socialTags, tagOverlap);
  const tagsLabel = socialTagsLabel(tags);

  return (
    <>
      <RecordHeader
        record={record}
        playerId={playerId}
        {...(distanceKm === undefined ? {} : { distanceKm })}
        {...(viewerAreaCode === undefined ? {} : { viewerAreaCode })}
      />

      {/* Absent where they hold no rating at all — the pills speak instead, and there is no
          panel of noughts to mistake for a bad record. */}
      {record.skill === undefined ? null : <SkillCard skill={record.skill} />}

      {tagsLabel === '' ? null : (
        <View accessible accessibilityLabel={tagsLabel}>
          <SocialTagRow row={tags} />
        </View>
      )}

      {pairing === undefined ? null : (
        <PressableCard onPress={pairing.onExplain} accessibilityLabel={fitRowLabel(pairing.fit)}>
          <Text style={s.fitTitle}>{fitRowTitle(pairing.fit)}</Text>
          <Text style={s.fitBody}>{FIT_ROW_BODY}</Text>
        </PressableCard>
      )}
    </>
  );
}

const s = StyleSheet.create({
  // The standing height, so the skeleton and the filled sheet are one surface. `minHeight`
  // rather than `height`: a long record grows past it and `BottomSheet`'s cap is what stops it.
  body: { minHeight: STANDING_HEIGHT, gap: theme.space.sm },
  refusal: { ...theme.type.tiny, color: theme.color.muted },
  failure: { gap: theme.space.sm },
  fitTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  fitBody: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
});
