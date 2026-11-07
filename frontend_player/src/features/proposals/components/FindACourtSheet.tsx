/**
 * ***Find a court*** — every court the line-up could take in the next 14 days, by day, each row
 * tinted by how many of them are free then ([#757](https://github.com/Raketa02/Raketa/issues/757);
 * the friends screens §7.3; friends 10, 11, README note 5).
 *
 * ```
 * Find a court                                        (×)
 * TOMORROW                                               the day, eyebrow
 * ┌ 19:00  Bonarka Arena · Court 2        32 zł each ┐   brightest: everybody free
 * │        Everybody free                            │
 * └──────────────────────────────────────────────────┘
 * SATURDAY
 * ┌ 10:00  Wisła Park · Court 3           25 zł each ┐   dimmer: one of them busy
 * │        ania.k busy                               │
 * │        Ogrody 33 is full at 10:00                │   another club, at the home club's full hour
 * └──────────────────────────────────────────────────┘
 * ```
 *
 * **9.1's sheet on `ModalStage`** (ADR-0178), over the Friends tab — mocks 10–11's game header
 * behind it is a leftover (README note 3). **Asked only once it opens**: the list is every court
 * hour the group's court rule offers, hundreds of rows on a busy club, and the card has already
 * proposed one. **So it is virtualised** (`docs/architecture.md` Part 12): a `SectionList`, a day a
 * section, in a sheet that hands it the scrolling (`scrollsItself`, `SHEET_LIST`). Every other
 * state — reading, offline, failed, nothing free — is the list's empty component.
 *
 * ## Four steps of tint, and the words under each
 *
 * **Brightest for everybody free, then dimmer for one busy, two, three** (Q36; `freeStepOf`) —
 * mock 10's green first, on the palette's own steps rather than a new ramp: `mintSoft` bordered in
 * `mint`; then the white card bordered in `mintLine`; then the white card with `line`; then the
 * recessed `paper2`. **Never the tint alone** (Part 13): every row says who is busy — *Everybody
 * free*, *ania.k busy*, *You and ania.k busy* — and is spoken with it.
 *
 * **Every row can be picked** (the mechanics §7.6): friends who arrange things themselves are not
 * stopped by a busy line. A press closes the sheet and the card asks again for that court. The row
 * the card shows now is ringed in `ink`, `SlotSheet`'s picked court, and spoken *picked*.
 */

import { ActivityIndicator, Pressable, SectionList, StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { BottomSheet, Note, SHEET_LIST, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from '../domain/deck';
import {
  courtsByDay,
  freeStepOf,
  isShownCourt,
  type CardPerson,
  type FriendsCourt,
} from '../domain/friendsCard';
import { useFriendsCourts } from '../hooks/useFriendsCard';

import { FRIENDS_CARD_COPY } from './friendsCardCopy';
import {
  busyLine,
  courtDayHeading,
  courtRowHour,
  courtRowName,
  courtRowSpoken,
  courtShare,
  fullAtLine,
} from './friendsCardPresentation';
import { ReadFailed } from './ReadFailed';

const COPY = FRIENDS_CARD_COPY;

export interface FindACourtSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  readonly groupId: string;
  readonly sport: Sport;
  readonly friendIds: readonly string[];
  readonly people: readonly CardPerson[];
  readonly readerId: string | undefined;
  /** The court the card shows now — ringed. */
  readonly shown: FriendsCourt | undefined;
  readonly onPick: (court: FriendsCourt) => void;
}

export function FindACourtSheet({
  visible,
  onClose,
  groupId,
  sport,
  friendIds,
  people,
  readerId,
  shown,
  onPick,
}: FindACourtSheetProps) {
  const read = useFriendsCourts(groupId, sport, friendIds, { enabled: visible });
  const list = read.data;
  // A day a section, each carrying the home club its rows' marker names.
  const days =
    list === undefined
      ? []
      : courtsByDay(list.courts, read.dataUpdatedAt).map((day) => ({
          ...day,
          data: day.courts,
          homeClub: list.homeClub,
        }));

  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={COPY.findACourt.title}
      closeLabel={COPY.findACourt.close}
      scrollsItself
    >
      <SectionList
        {...SHEET_LIST}
        testID="find-a-court-list"
        sections={days}
        keyExtractor={(court) => `${court.courtId}-${court.startsAt}`}
        stickySectionHeadersEnabled={false}
        renderSectionHeader={({ section }) => (
          <Text style={s.heading} accessibilityRole="header">
            {courtDayHeading(section.when)}
          </Text>
        )}
        renderItem={({ item: court, section }) => (
          <CourtRow
            court={court}
            homeClub={section.homeClub}
            busy={busyLine(court.busy, readerId, people)}
            picked={isShownCourt(court, shown)}
            onPress={() => onPick(court)}
          />
        )}
        ListEmptyComponent={
          list !== undefined ? (
            <Note>{COPY.noCourt}</Note>
          ) : read.fetchStatus === 'paused' ? (
            <Note variant="amber">{offlineMessage('resumes')}</Note>
          ) : read.error !== null && !read.isFetching ? (
            <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
          ) : (
            <View style={s.reading} accessible accessibilityLabel={COPY.findACourt.reading}>
              <ActivityIndicator color={theme.color.muted} />
            </View>
          )
        }
      />
    </BottomSheet>
  );
}

function CourtRow({
  court,
  homeClub,
  busy,
  picked,
  onPress,
}: {
  readonly court: FriendsCourt;
  readonly homeClub: DeckCard['club'];
  readonly busy: string;
  readonly picked: boolean;
  readonly onPress: () => void;
}) {
  const fullAt = fullAtLine(court, homeClub);
  const step = freeStepOf(court);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={courtRowSpoken(court, busy, fullAt, picked)}
      accessibilityHint={COPY.findACourt.rowHint}
      accessibilityState={{ selected: picked }}
      onPress={onPress}
      style={({ pressed }) => [
        s.row,
        TINT[step],
        picked ? s.picked : undefined,
        pressed ? s.pressed : undefined,
      ]}
      testID={`find-a-court-${court.courtId}-${court.startsAt}`}
    >
      <Text style={s.hour}>{courtRowHour(court)}</Text>
      <View style={s.middle}>
        <Text style={s.court} numberOfLines={1}>
          {courtRowName(court)}
        </Text>
        <Text style={s.line}>{busy}</Text>
        {fullAt === undefined ? null : <Text style={s.line}>{fullAt}</Text>}
      </View>
      <Text style={s.each}>{courtShare(court)}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // The list's gap stands between every row; a day's heading takes a step more above it.
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    paddingTop: theme.space.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.md,
  },
  picked: { borderColor: theme.color.ink, borderWidth: theme.size.postingGrid.pickRing },
  pressed: { opacity: 0.7 },
  hour: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  middle: { flex: 1, gap: theme.space.xxs },
  court: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  each: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  reading: { paddingVertical: theme.space.lg, alignItems: 'center' },
});

/** The four steps, brightest first — see the module note. */
const TINT = StyleSheet.create({
  0: { backgroundColor: theme.color.mintSoft, borderColor: theme.color.mint },
  1: { backgroundColor: theme.color.surface, borderColor: theme.color.mintLine },
  2: { backgroundColor: theme.color.surface, borderColor: theme.color.line },
  3: { backgroundColor: theme.color.paper2, borderColor: theme.color.line },
});
