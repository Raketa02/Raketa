/**
 * **A cell's sheet** — what is free at a day's range: the poster's best fits, the courts, and what
 * is already happening there ([#558](https://github.com/Raketa02/Raketa/issues/558); the screens
 * A5.3; mocks 34, 35; the mechanics §9.1 step 6).
 *
 * ```
 * Saturday evening                                         (×)
 * [5] 5 of your best fits free then
 * [2,75][2,69][2,68][2,60][2,80]                 → each one's record
 *  Karol  Zofia  Ania  Ewa   Kuba   2,75 · 93
 * FREE COURTS · HOME CLUB FIRST
 * ┌ 17:00  Ogrody 33 [4 free]                  27 zł each ┐   → picks it
 * │        2,4 km · 27 zł if it fills · book by Sat 15:00  │
 * └────────────────────────────────────────────────────────┘
 * ALREADY HAPPENING HERE
 * ┌ Padel · Sunday 20:00                         [2 seats] ┐
 * │ Centrum Ruchu · Court 2 · 30 zł each                   │   a rescue: pays at once
 * │ [KW][AK][?][?]  any level ✓ · you are free ✓   [Pay 30 zł]
 * └────────────────────────────────────────────────────────┘
 * (a post still filling: its poster, no court number, I'm in — Pay 32 zł on its last seat)
 * [ Remove this pick ]                                         on the picked cell only
 * ```
 *
 * **9.1's sheet on `ModalStage`**, never a React Native `Modal` (ADR-0178). Everything on it is the
 * slot's read, asked for the controls the grid was read with; nothing is re-derived. **A court
 * tapped is the pick** — one hour, one court, replacing the last — and the sheet closes on it so the
 * cell's ring and ✓ and the enabled button are what the player sees next; on the picked cell the
 * picked row says so and *Remove this pick* sits at the foot. **Joining** — a rescue's *Pay 30 zł*,
 * a post's *I'm in* — is the screen's to do (`onJoinRescue`, `onJoinPost`): it closes this sheet
 * first, so the payment setup or a confirmation never opens over it. **A post's last seat says *Pay
 * 32 zł*** (Q124), because the yes that takes it books the game (`yesOnPost`, `chargesAtOnce`).
 *
 * The ticks after *any level* and *you are free* are drawn (Feather) — Archivo has no ✓ — and the
 * line is true of every row: the read lists only games the poster fits and is free for.
 */

import Feather from '@expo/vector-icons/Feather';
import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { offlineMessage } from '@/shared/errors';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { BottomSheet, Button, Note, PHOTO_PANEL, PhotoPanel, Tag, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { chargesAtOnce } from '../domain/deck';
import type { SeatToFill } from '../domain/fillIn';
import {
  courtPickable,
  isPicked,
  isPickedCourt,
  yesOnPost,
  type CellAt,
  type FreeCourt,
  type PostingAsk,
  type PostingSlot,
  type PostPick,
  type PostStillFilling,
  type SlotFit,
} from '../domain/posting';
import { usePostingSlot } from '../hooks/usePosting';

import { LINE_JOIN, clubName, payLabel, paySpoken, yesButtonLabel } from './deckPresentation';
import { FillInSquares } from './FillInSquares';
import { POSTING_COPY } from './postingCopy';
import { PROPOSALS_COPY } from './proposalsCopy';
import {
  courtHour,
  courtRowLine,
  courtRowSpoken,
  eachWords,
  fitLine,
  fitName,
  fitReasonsSpoken,
  fitSpoken,
  fitsFreeTag,
  happeningSpoken,
  happeningTitle,
  postLine,
  rangeOfDay,
  rescueLine,
  seatsTag,
  slotHeadline,
} from './postingPresentation';
import { ReadFailed } from './ReadFailed';

const COPY = POSTING_COPY.sheet;

export interface SlotSheetProps {
  readonly groupId: string;
  readonly ask: PostingAsk;
  /** The cell open — absent while the sheet is down. */
  readonly cell: CellAt | undefined;
  /** The grid's clock — the title's *today* and *tomorrow*. */
  readonly readAt: number;
  readonly pick: PostPick | undefined;
  readonly onPick: (court: FreeCourt, slot: PostingSlot) => void;
  readonly onUnpick: () => void;
  readonly onFit: (fit: SlotFit) => void;
  readonly onJoinRescue: (row: SeatToFill) => void;
  readonly onJoinPost: (post: PostStillFilling) => void;
  readonly onClose: () => void;
}

export function SlotSheet({ cell, readAt, onClose, ...props }: SlotSheetProps) {
  return (
    <BottomSheet
      visible={cell !== undefined}
      onClose={onClose}
      title={cell === undefined ? '' : rangeOfDay(cell.day, cell.range, readAt)}
      closeLabel={COPY.close}
    >
      {cell === undefined ? null : <SlotBody cell={cell} {...props} />}
    </BottomSheet>
  );
}

function SlotBody({
  groupId,
  ask,
  cell,
  pick,
  onPick,
  onUnpick,
  onFit,
  onJoinRescue,
  onJoinPost,
}: Omit<SlotSheetProps, 'cell' | 'readAt' | 'onClose'> & { readonly cell: CellAt }) {
  const read = usePostingSlot(groupId, ask, cell);
  const slot = read.data;

  if (slot === undefined) {
    if (read.fetchStatus === 'paused') {
      return <Note variant="amber">{offlineMessage('resumes')}</Note>;
    }
    if (read.error !== null && !read.isFetching) {
      return <ReadFailed error={read.error} onRetry={() => void read.refetch()} />;
    }
    return <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />;
  }

  const headline = slotHeadline(slot.cell);
  const slotReadAt = Date.parse(slot.readAt);
  const picked = isPicked(slot, pick);
  const happening = slot.rescues.length + slot.posts.length > 0;

  return (
    <View style={s.body}>
      <View
        style={s.headline}
        accessible
        accessibilityRole="header"
        accessibilityLabel={headline.words}
      >
        {headline.count === undefined ? null : (
          <View style={s.badge}>
            <Text style={s.badgeCount}>{headline.count}</Text>
          </View>
        )}
        <Text style={s.headlineWords}>{headline.words}</Text>
      </View>

      {slot.fits.length === 0 ? null : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={s.fits}
          testID="slot-fits"
        >
          {slot.fits.map((fit) => (
            <FitCard key={fit.playerId} fit={fit} sport={ask.sport} onPress={() => onFit(fit)} />
          ))}
        </ScrollView>
      )}

      <View style={s.section}>
        <Text style={s.eyebrow} accessibilityRole="header">
          {COPY.freeCourts}
        </Text>
        {slot.freeCourts.length === 0 ? (
          <Text style={s.none}>{COPY.noCourt}</Text>
        ) : (
          slot.freeCourts.map((court) => (
            <CourtRow
              key={`${court.club.id}-${court.startsAt}`}
              court={court}
              picked={isPickedCourt(court, pick)}
              onPress={courtPickable(court) ? () => onPick(court, slot) : undefined}
            />
          ))
        )}
      </View>

      {happening ? (
        <View style={s.section}>
          <Text style={s.eyebrow} accessibilityRole="header">
            {COPY.happening}
          </Text>
          {slot.rescues.map((row) => {
            const title = happeningTitle(row, slotReadAt);
            const line = rescueLine(row);
            const share = formatZloty(row.shareGrosze);
            return (
              <HappeningRow
                key={row.bookingId}
                testID={`slot-rescue-${row.bookingId}`}
                title={title}
                line={line}
                open={row.openSeats}
                spoken={happeningSpoken(title, line, row.openSeats)}
                squares={
                  <FillInSquares
                    people={row.players}
                    open={row.openSeats}
                    question
                    onHold={(person) => onFit({ playerId: person.playerId })}
                  />
                }
                act={
                  <Button
                    label={payLabel(share)}
                    accessibilityLabel={paySpoken(share, row.fillsByTheCutOff)}
                    variant="volt"
                    size="md"
                    onPress={() => onJoinRescue(row)}
                  />
                }
              />
            );
          })}
          {slot.posts.map((post) => {
            const title = happeningTitle({ ...post, sport: ask.sport }, slotReadAt);
            const line = postLine(post);
            return (
              <HappeningRow
                key={post.proposalId}
                testID={`slot-post-${post.proposalId}`}
                title={title}
                line={line}
                open={post.openSeats}
                spoken={happeningSpoken(title, line, post.openSeats)}
                squares={
                  <FillInSquares
                    people={post.peopleIn}
                    open={post.openSeats}
                    question={false}
                    onHold={(person) => onFit({ playerId: person.playerId })}
                  />
                }
                act={
                  <Button
                    label={yesButtonLabel(
                      chargesAtOnce(yesOnPost(post)),
                      formatZloty(post.shareGrosze),
                    )}
                    variant="volt"
                    size="md"
                    onPress={() => onJoinPost(post)}
                  />
                }
              />
            );
          })}
        </View>
      ) : null}

      {picked ? (
        <Button label={COPY.remove} variant="secondary" size="lg" onPress={onUnpick} />
      ) : null}
    </View>
  );
}

/** A fit: the photo panel with their Level, the name whole under it, and *2,75 · 93*. */
function FitCard({
  fit,
  sport,
  onPress,
}: {
  readonly fit: SlotFit;
  readonly sport: Sport;
  readonly onPress: () => void;
}) {
  const line = fitLine(fit);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={fitSpoken(fit)}
      accessibilityHint={COPY.fitHint}
      onPress={onPress}
      style={({ pressed }) => [s.fit, pressed ? s.pressed : undefined]}
      testID={`slot-fit-${fit.playerId}`}
    >
      <PhotoPanel
        playerId={fit.playerId}
        {...(fit.photoUrl === undefined ? {} : { photoUrl: fit.photoUrl })}
        {...(fit.level === undefined
          ? {}
          : { rating: { level: fit.level, sportName: sportLabel(sport) } })}
        onCourt={false}
      />
      <Text style={s.fitName} numberOfLines={1}>
        {fitName(fit)}
      </Text>
      {/* The reader's own friend, in Members' green: a word on paper (#753; Q68). */}
      {fit.friend === true ? (
        // A tag stands at its own top-left (6.4); the box centres it under the name.
        <View>
          <Tag label={PROPOSALS_COPY.friendSpoken} variant="ok" />
        </View>
      ) : null}
      {line === undefined ? null : <Text style={s.fitLine}>{line}</Text>}
    </Pressable>
  );
}

/**
 * *17:00 · Ogrody 33 [4 free] · 2,4 km · 27 zł if it fills · book by Sat 15:00 · 27 zł each*. A court
 * hour nobody who fits is free at is drawn and shut (`courtPickable`): its *0 free* says why.
 */
function CourtRow({
  court,
  picked,
  onPress,
}: {
  readonly court: FreeCourt;
  readonly picked: boolean;
  /** `undefined` shuts the row. */
  readonly onPress: (() => void) | undefined;
}) {
  const shut = onPress === undefined;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={courtRowSpoken(court, picked)}
      accessibilityHint={shut ? undefined : COPY.courtHint}
      accessibilityState={{ selected: picked, disabled: shut }}
      disabled={shut}
      onPress={onPress}
      style={({ pressed }) => [
        s.court,
        picked ? s.courtPicked : undefined,
        shut ? s.shut : undefined,
        pressed ? s.pressed : undefined,
      ]}
      testID={`slot-court-${court.club.id}-${court.startsAt}`}
    >
      <Text style={s.hour}>{courtHour(court)}</Text>
      <View style={s.courtMiddle}>
        <View style={s.courtTitle}>
          <Text style={s.club} numberOfLines={1}>
            {clubName(court)}
          </Text>
          <Tag label={fitsFreeTag(court)} variant={shut ? 'base' : 'ok'} />
        </View>
        <Text style={s.courtLine}>{courtRowLine(court)}</Text>
      </View>
      {picked ? (
        <Feather
          name="check"
          size={theme.size.rowLeadGlyph}
          color={theme.color.ink}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      ) : (
        <Text style={s.each}>{eachWords(court.shareGrosze)}</Text>
      )}
    </Pressable>
  );
}

/** A game already happening at this range — a rescue's or a post's, the act handed in. */
function HappeningRow({
  title,
  line,
  open,
  spoken,
  squares,
  act,
  testID,
}: {
  readonly title: string;
  readonly line: string;
  readonly open: number;
  readonly spoken: string;
  readonly squares: ReactNode;
  readonly act: ReactNode;
  readonly testID: string;
}) {
  return (
    <View style={s.happening} testID={testID}>
      <View style={s.happeningHead} accessible accessibilityLabel={spoken}>
        <View style={s.happeningWords}>
          <Text style={s.happeningTitle}>{title}</Text>
          <Text style={s.happeningLine}>{line}</Text>
        </View>
        <Tag label={seatsTag(open)} variant="hot" />
      </View>
      <View style={s.happeningFoot}>
        {squares}
        <View style={s.reasons} accessible accessibilityLabel={fitReasonsSpoken()}>
          <Text style={s.reason}>{COPY.anyLevel}</Text>
          <Tick />
          <Text style={s.reason}>
            {LINE_JOIN}
            {COPY.youAreFree}
          </Text>
          <Tick />
        </View>
      </View>
      <View style={s.act}>{act}</View>
    </View>
  );
}

/** A drawn ✓ — Archivo has none. */
function Tick() {
  return (
    <Feather
      name="check"
      size={theme.size.availability.tick}
      color={theme.color.mintInk}
      accessibilityElementsHidden
      importantForAccessibility="no"
    />
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.lg },
  headline: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // The count's badge: white on `mintInk` (Rule C), the grid's hot fill.
  badge: {
    minWidth: theme.size.fit,
    height: theme.size.fit,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.mintInk,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeCount: { ...theme.num.xs, ...theme.tabular, color: theme.color.surface },
  headlineWords: { ...theme.type.h2, color: theme.color.ink, flexShrink: 1 },
  fits: { gap: theme.space.xs },
  fit: { gap: theme.space.xxs, alignItems: 'center' },
  // The name under its panel, cut by the panel's width rather than running into the next.
  fitName: { ...theme.type.cardTitle, color: theme.color.ink, maxWidth: PHOTO_PANEL.card.width },
  fitLine: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  pressed: { opacity: 0.7 },
  // 6.1's disabled: the row is there and shut — nobody who fits is free at its hour.
  shut: { opacity: 0.4 },
  section: { gap: theme.space.sm },
  // 3.3: the section heading is `eyebrow` in `muted`, the only one.
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  none: { ...theme.type.rlLabel, color: theme.color.muted },
  court: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    padding: theme.space.md,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.surface,
  },
  courtPicked: { borderColor: theme.color.ink, borderWidth: theme.size.postingGrid.pickRing },
  hour: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  courtMiddle: { flex: 1, gap: theme.space.xxs },
  courtTitle: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  club: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  courtLine: { ...theme.type.tiny, color: theme.color.muted },
  each: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  happening: {
    gap: theme.space.sm,
    padding: theme.space.md,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.surface,
  },
  happeningHead: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.sm },
  happeningWords: { flex: 1, gap: theme.space.xxs },
  happeningTitle: { ...theme.type.h2, color: theme.color.ink },
  happeningLine: { ...theme.type.rlLabel, color: theme.color.muted },
  happeningFoot: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    flexWrap: 'wrap',
  },
  reasons: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  reason: { ...theme.type.tiny, color: theme.color.mintInk },
  act: { alignItems: 'flex-end' },
});
