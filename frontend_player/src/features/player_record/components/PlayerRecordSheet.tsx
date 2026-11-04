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
 * **The refusal draws one line and nothing else.** Never disclosed, held, an account that may
 * not be shown, and no such player answer the same code with the same body, byte for byte — a
 * block is not a gate any more, either way round (ADR-0193 §2). There is no retry on it,
 * because re-asking a refusal returns the refusal —
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
 * ## A foot, filled by one surface
 *
 * The sheet had no control but the pairing row until the radar
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [#464](https://github.com/Raketa02/Raketa/issues/464)): reached from a radar card it ends
 * in *Not today* and *Let's play*, or in what already stands between the two. That foot is an
 * **optional slot** — `foot`, drawn under everything else and only where the caller fills it —
 * and not a prop set this sheet reads, because what stands between two people is the caller's
 * to know and this sheet reads no global state. The deck's *i* and the long press fill nothing,
 * by decision: the deck's own buttons are one tap away and two places to answer at once invites
 * a double tap. It is drawn with the record and never over the skeleton or the refusal — a
 * refused record is somebody the reader may not act on, and the buttons would say otherwise.
 * The next surface that wants a foot has to argue for one.
 *
 * ## It ends in Block or Unblock — but not on your own
 *
 * The last row is **`blocks`' `BlockRow`** ([#587](https://github.com/Raketa02/Raketa/issues/587),
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)):
 * *Block kuba.w* behind a confirm sheet, or *Unblock kuba.w* once the reader
 * has. It is not the foot — no caller fills it, and every surface that opens a record gets it —
 * and it reads no global state either: whether the reader blocked the subject is **this read's
 * own answer**, `blocked_by_you`, folded to `blockedByYou` at the wire boundary and absent on your
 * own record and where the server could not read the blocks, so neither row is drawn there. A
 * press re-reads the record — **this sheet hands its own re-read down**, so `blocks` never names
 * this feature's keys while this feature draws its row — and the row is the re-read's answer.
 * Drawn with the record only, as the foot is.
 *
 * ## The account is folded under the blocks
 *
 * The three blocks — Player reliability, Last 5, Counted — are the summary; the counted card and
 * the tags are its account, and they sit under one row, a centred chevron spoken *Full record*,
 * shut each time the sheet opens (`RecordDetails`). A face is tapped to ask *who is this*, which
 * the header and the blocks answer; the reader who wants *why that number* asks for it. The pairing row and the foot stay
 * outside the fold — they are things to do, not things to read. No fold is drawn over nothing.
 *
 * ## Six regions, six elements
 *
 * There is no interactive element inside it other than the pairing row, the Block or Unblock row
 * and the foot, where a caller fills it — so every group merges
 * into the nearest heading (§20.1) and `recordPresentation` writes what each of them says. The
 * counted card and *What opponents said* are two of them for a reason that is not layout: one
 * is headed with a promise about **authorship**, and the other is what would break it. The
 * **block row** is a sixth for a reason that is not layout either: the skill card above it is
 * about one sport and the Player Score in it is about the whole person, so folding the two into
 * one element would announce a reliability figure inside a sentence that opened with *Tennis*.
 * Focus lands on the **title** on the way in, which is `BottomSheet`'s flat rule for every sheet
 * — and there is **no `returnFocusTo`**: up to four faces open this from one card, so there is
 * no one control to return to.
 */

import type { ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { BlockRow } from '@/features/blocks/types';
import { codeMessage, type AppError } from '@/shared/errors';
import { BottomSheet, Note, Button, SocialTagRow, theme } from '@/shared/ui';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayerRecord, RecordSubject } from '../domain/playerRecord';
import { recordTagRow } from '../domain/tagRow';
import { usePlayerRecord } from '../hooks/usePlayerRecord';

import { RecordBlocks } from './RecordBlocks';
import { RecordCard } from './RecordCard';
import { RecordDetails } from './RecordDetails';
import { RecordHeader } from './RecordHeader';
import { SkillCard } from './SkillCard';
import {
  READING_RECORD_LABEL,
  RECORD_UNAVAILABLE,
  RECORD_UNAVAILABLE_CODE,
  RETRY_RECORD_LABEL,
  recordCloseLabel,
  recordTitle,
  socialTagsLabel,
} from './recordPresentation';

/** The one code, for all four causes — and the one sentence this client draws from it. */
const RECORD_FAILURES: Readonly<Record<string, string>> = {
  [RECORD_UNAVAILABLE_CODE]: RECORD_UNAVAILABLE,
};

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
  /**
   * Kilometres to one decimal, the candidate's own. Absent where no search is behind the entry
   * point — and on your own record.
   */
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
  /**
   * **The action slot** — what the sheet ends in, where the surface that opened it has
   * something to offer. Drawn under the record and only with it; nothing here decides what it
   * says. See the module note.
   */
  readonly foot?: ReactNode;
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
  foot,
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
            {...(foot === undefined ? {} : { foot })}
            rereadRecord={() => record.refetch()}
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
    return (
      <ActivityIndicator accessibilityLabel={READING_RECORD_LABEL} color={theme.color.muted} />
    );
  }

  if (error.code === RECORD_UNAVAILABLE_CODE) {
    return <Text style={s.refusal}>{RECORD_UNAVAILABLE}</Text>;
  }

  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {codeMessage(RECORD_FAILURES, error)}
      </Note>
      <Button label={RETRY_RECORD_LABEL} variant="secondary" onPress={onRetry} />
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
  foot,
  rereadRecord,
}: {
  readonly record: PlayerRecord;
  readonly playerId: string;
  /** This read again — what a block or an unblock at the foot awaits before it settles. */
  readonly rereadRecord: () => Promise<unknown>;
} & Pick<
  PlayerRecordSheetProps,
  'distanceKm' | 'viewerAreaCode' | 'tagOverlap' | 'pairing' | 'foot'
>) {
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
        {...(pairing === undefined ? {} : { onExplainFit: pairing.onExplain, fit: pairing.fit })}
      />

      {/* Absent where they hold no rating at all — the pills speak instead, and there is no
          panel of noughts to mistake for a bad record. */}
      {record.skill === undefined ? null : <SkillCard skill={record.skill} />}

      {/* 7.13's three blocks, under the band bar. **A row of the sheet rather than a footer on
          the card above it**, and the reason is an absence: two of the three are that sport's
          and Player reliability is the whole person's, so a block nested in a card drawn only
          when a Level resolves would take a newcomer's *100 · New* down with the sport. */}
      <RecordBlocks
        reliability={record.reliability}
        {...(record.skill?.lastFive === undefined ? {} : { lastFive: record.skill.lastFive })}
        {...(record.skill === undefined ? {} : { countedGames: record.skill.countedGames })}
      />

      {/* Everything under the blocks is folded under *Full record* (`RecordDetails`): the
          blocks are the summary, and this is its account. Always drawn now — the four counts
          are on every record since ADR-0195 §1, a newcomer's included (#660). */}
      <RecordDetails>
        {/* The counts, then two absences that do not move together, handed down separately and
            drawn as whatever survives them. What other players said is a row on the card rather
            than a block under it — the card's heading promised *counted by the system, not
            written by people*, and the heading is what went. */}
        <RecordCard
          counts={record.reliability.counts}
          {...(record.variety === undefined ? {} : { variety: record.variety })}
          {...(record.opinion === undefined ? {} : { opinion: record.opinion })}
        />

        {tagsLabel === '' ? null : (
          <View accessible accessibilityLabel={tagsLabel}>
            <SocialTagRow row={tags} />
          </View>
        )}
      </RecordDetails>

      {/* The foot, last, where the surface filled it. A sheet reads statement first and answer
          last, which is the whole reason it is at the end and inside the scroll (9.1). */}
      {foot === undefined ? null : <View style={s.foot}>{foot}</View>}

      {/* **Block or Unblock, last** (#587, ADR-0193): on every record but your own, from the
          record's own answer — absent on yours, and where the blocks could not be read. The
          act is `blocks`'; whether the reader blocked them is this read's, and so is the
          re-read the act awaits. */}
      {record.blockedByYou === undefined ? null : (
        <BlockRow
          playerId={playerId}
          name={record.nickname}
          blocked={record.blockedByYou}
          rereadRecord={rereadRecord}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  // The standing height, so the skeleton and the filled sheet are one surface. `minHeight`
  // rather than `height`: a long record grows past it and `BottomSheet`'s cap is what stops it.
  body: { minHeight: STANDING_HEIGHT, gap: theme.space.sm },
  // A step above the record, so the answers read as the sheet's foot and not the tags' tail.
  foot: { marginTop: theme.space.xs },
  refusal: { ...theme.type.tiny, color: theme.color.muted },
  failure: { gap: theme.space.sm },
});
