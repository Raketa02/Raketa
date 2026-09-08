/**
 * **The record's header** — the photograph with the Level on it, and who this is beside it.
 *
 * A `PhotoPanel` at record size and a column: the whole handle, the identity line, one pill per
 * rated sport, and the reliability pill.
 *
 * ## The panel is the same drawn object the candidate card carries
 *
 * [7.16](../../../../docs/design-system.md#716-the-photo-panel) at its second size — *in this
 * product your rating is your face, and the photograph is scenery* — so the Level is the
 * biggest text on the panel, the resolved Sport sits under it, and the **ON COURT** mark is
 * drawn on *checked and passed* and on nothing else. A player with no photograph draws their
 * generated poster, which is never a broken image and never a grey box.
 *
 * **The Level and the Sport come off the resolved skill panel**, so a person rated in nothing
 * draws a poster with nothing printed on it rather than a nought. There is no panel of noughts
 * anywhere on this sheet.
 *
 * ## The whole handle, always
 *
 * There is no name on this platform and nothing may derive a familiar form from a handle —
 * `playerName()`'s rule, and the reason the column wraps rather than truncates. On your own
 * record the handle takes `(you)` after it, because a face you are reading about is a stranger
 * until something says otherwise.
 *
 * ## The identity line is a comparison and never a place name
 *
 * `In your area · 4 km`, or the kilometres alone, or nothing. An `area_code` is a coordinate
 * string; the only sentence a client is licensed to write from two of them is *these two are in
 * the same square*, and a reader whose own area is unknown gets no claim in either direction.
 * On your own record the **whole line** is gone rather than the distance alone — the two codes
 * are equal by construction there, so a line that dropped only the kilometres would tell
 * somebody they are in their own area — and `identityLine` reads `isSelf` for exactly that
 * reason, rather than leaving two call sites to remember one condition.
 *
 * ## One element, and the pills merge into it
 *
 * §20.1: everything with no action of its own merges into the nearest action above it. There is
 * no action here at all, so the whole header is one element and `recordHeaderLabel` is what it
 * says — identifying facts first, in the order they are drawn.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { PhotoPanel, Tag, theme } from '@/shared/ui';

import type { PlayerRecord } from '../domain/playerRecord';
import { scoreTone } from '../domain/scoreTone';

import { SportPills } from './SportPills';
import {
  identityLine,
  recordHandle,
  recordHeaderLabel,
  scorePill,
  sportPill,
} from './recordPresentation';

export interface RecordHeaderProps {
  readonly record: PlayerRecord;
  /** Whose poster to draw where there is no photograph — a fact about an id. */
  readonly playerId: string;
  /** Whole kilometres, as the contract sends them. Absent on your own record, always. */
  readonly distanceKm?: number;
  /** The reader's own coarse area, for the one comparison this line is allowed to make. */
  readonly viewerAreaCode?: string;
}

/**
 * The three tones a Player Score is drawn in, as `Tag` variants.
 *
 * The pill adds no colour: `ok`, `base` and `bad` are the palette's existing semantics, and the
 * figure is printed inside the pill so nothing rests on the tint
 * ([Part 13](../../../../docs/design-system.md#part-13--accessibility)).
 */
const SCORE_VARIANT = { good: 'ok', neutral: 'base', poor: 'bad' } as const;

export function RecordHeader({ record, playerId, distanceKm, viewerAreaCode }: RecordHeaderProps) {
  const handle = recordHandle(record.nickname, record.isSelf);
  const identity = identityLine({
    areaCode: record.areaCode,
    isSelf: record.isSelf,
    ...(viewerAreaCode === undefined ? {} : { viewerAreaCode }),
    ...(distanceKm === undefined ? {} : { distanceKm }),
  });

  return (
    <View
      style={s.header}
      accessible
      accessibilityLabel={recordHeaderLabel({
        handle,
        onCourt: record.onCourt,
        identity,
        sports: record.sports.map(({ sport, level }) => sportPill(sportLabel(sport), level)),
        ...(record.playerScore === undefined ? {} : { playerScore: record.playerScore }),
      })}
    >
      {/* The Level and the Sport are the resolved panel's, so somebody rated in nothing draws
          their poster with nothing over it — never a nought. */}
      <PhotoPanel
        size="record"
        playerId={playerId}
        {...(record.photoUrl === undefined ? {} : { photoUrl: record.photoUrl })}
        {...(record.skill === undefined
          ? {}
          : {
              rating: {
                level: record.skill.level,
                sportName: sportLabel(record.skill.sport),
              },
            })}
        onCourt={record.onCourt}
      />

      <View style={s.column}>
        <Text style={s.handle}>{handle}</Text>

        {identity === '' ? null : <Text style={s.identity}>{identity}</Text>}

        <SportPills sports={record.sports} />

        {record.playerScore === undefined ? null : (
          <View style={s.score}>
            <Tag
              label={scorePill(record.playerScore)}
              variant={SCORE_VARIANT[scoreTone(record.playerScore)]}
            />
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  header: { flexDirection: 'row', gap: theme.space.md, alignItems: 'flex-start' },
  // The column takes whatever the panel leaves, so a 64-character handle wraps inside it
  // rather than pushing the panel off the sheet.
  column: { flex: 1, gap: theme.space.xs },
  handle: { ...theme.type.h1, color: theme.color.ink },
  identity: { ...theme.type.tiny, color: theme.color.muted },
  // Pushed right, which is where a figure about the whole person belongs on a header whose
  // left half is one sport's.
  score: { alignSelf: 'flex-end' },
});
