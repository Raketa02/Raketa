/**
 * **The vibe sheet** — *You and karol.t* ([#803](https://github.com/Raketa02/Raketa/issues/803); the
 * Home rows screens §6.3; the mechanics §8.5; the words §31.8; home rows 23; design-system 7.35).
 * Opened by a tile, on Home's row and in See all alike — whose sheet is up is the people lists' own
 * state (`usePersonSheet`): it draws the person's latest read, closes drawn as they last were when a
 * write moves them out of the list, and never reopens by itself.
 *
 * - **The title row**: *You and karol.t*, and the sheet's friend button at its right end — `friends`'
 *   worded twin (*✓ Friends*, *+ Add friend*, *Request sent*, *Accept*), asking from *same vibe*.
 * - **The identity row**: the face — **a tap opens the full record**, its requests found through
 *   *same vibe* — the nickname, and *6 things in common*. **No distance follows it**: the screens'
 *   *· In your area · 0,6 km* is *as the record writes it*, and the record carries no distance and a
 *   record opened from Home writes no identity line — so *nothing*, the third of §6.3's forms. A
 *   backend ask (#795's contract says the sheet reads the distance off the record, which has none).
 * - **All their photos**, the record's carousel; **the intro** in its marks, as the record draws it;
 *   and **all their tags**, the record's row, the ones the two share green and reading *· you too*.
 *
 * **It reads the record** (§8.5), so it opens only where the record would, says *This record isn't
 * available* where the record does, and is current as the record is (`player_record`'s `RecordRead`).
 * The count and the tags the two share are the tile's — the row's read — and the button moves with
 * that read, as the comparison sheet's does.
 *
 * **The record opens over this sheet, never in its place**: iOS drops a second native window opened
 * while the first is closing (#800), so the record is drawn inside this one, as the worded button's
 * own sheets are, and closing it comes back here. **It belongs to one open of one person**: when the
 * sheet closes under it — a write there moved them out of the row — it goes with it, and the next
 * sheet opens on its own. **No navigation hook** is read inside: a sheet keeps
 * the root's contexts only (`ModalStage`).
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { RoundFriendButton } from '@/features/friends/types';
import {
  RecordIntro,
  RecordRead,
  RecordTags,
  type PlayerRecord,
} from '@/features/player_record/types';
import { BottomSheet, PhotoCarousel, PlayerPhoto, theme } from '@/shared/ui';
import { thingsInCommon } from '@/shared/vocabulary/socialTagPresentation';

import { FOUND_THROUGH_TAGS, type SameVibePlayer } from '../domain/sameVibe';
import type { PersonSheet } from '../hooks/usePersonSheet';

import { closeVibeLabel, vibeTitle } from './discoveryCopy';
import { RowRecord } from './RowRecord';

export interface VibeSheetProps {
  /** Whose sheet is up, over the row or See all (`usePersonSheet`). */
  readonly sheet: PersonSheet<SameVibePlayer>;
}

export function VibeSheet({ sheet }: VibeSheetProps) {
  // Whose full record is open over the sheet — one open of one person, never carried to the next.
  const [recordOf, setRecordOf] = useState<string>();
  if (!sheet.open && recordOf !== undefined) setRecordOf(undefined);

  const player = sheet.person;
  if (player === undefined) return null;

  return (
    <BottomSheet
      visible={sheet.open}
      onClose={sheet.close}
      title={vibeTitle(player.nickname)}
      closeLabel={closeVibeLabel(player.nickname)}
      action={
        <RoundFriendButton
          playerId={player.playerId}
          nickname={player.nickname}
          relation={player.relation}
          where={FOUND_THROUGH_TAGS}
          variant="worded"
        />
      }
    >
      <View style={s.body}>
        <RecordRead playerId={player.playerId} enabled={sheet.open}>
          {(record) => (
            <Vibe record={record} player={player} onFace={() => setRecordOf(player.playerId)} />
          )}
        </RecordRead>
      </View>
      <RowRecord
        opened={
          sheet.open && recordOf === player.playerId
            ? { playerId: player.playerId, foundIn: FOUND_THROUGH_TAGS }
            : undefined
        }
        onClose={() => setRecordOf(undefined)}
      />
    </BottomSheet>
  );
}

function Vibe({
  record,
  player,
  onFace,
}: {
  readonly record: PlayerRecord;
  readonly player: SameVibePlayer;
  readonly onFace: () => void;
}) {
  return (
    <>
      <View style={s.identity}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={record.nickname}
          onPress={onFace}
          hitSlop={theme.hit.peopleRow}
          style={({ pressed }) => (pressed ? s.pressed : undefined)}
          testID="vibe-face"
        >
          <PlayerPhoto
            playerId={player.playerId}
            {...(record.photoUrl === undefined ? {} : { photoUrl: record.photoUrl })}
            box={{ kind: 'face', size: theme.size.sameVibe.face.row }}
          />
        </Pressable>
        <View style={s.who}>
          <Text style={s.name}>{record.nickname}</Text>
          <Text style={s.line}>{thingsInCommon(player.inCommon)}</Text>
        </View>
      </View>

      {/* All of their photos, in their order — none with no photo (the screens §6.3's call). */}
      <PhotoCarousel playerId={player.playerId} photos={record.photos} testID="vibe-photos" />

      {record.intro === undefined ? null : <RecordIntro intro={record.intro} />}

      <RecordTags
        tags={record.socialTags}
        overlap={{
          kind: 'shared',
          tags: player.sharedTags.map((id) => ({ id, shared: true })),
        }}
      />
    </>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  identity: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  who: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.h2, color: theme.color.ink },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
  // 6.6: a face pressed dims.
  pressed: { opacity: 0.7 },
});
