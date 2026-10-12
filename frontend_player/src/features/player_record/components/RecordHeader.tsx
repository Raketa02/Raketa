/**
 * **The record's header** — the photograph with the Level on it, and who this is beside it.
 *
 * A `PhotoPanel` at record size and a column: the whole name, the `@nickname` under it, their
 * intro where they wrote one, the identity line, and one pill per rated sport.
 *
 * ## The reliability pill left, and it is now a block under the level bar
 *
 * It was a tinted `Tag` here. It is `RecordBlocks`' first box now — 7.13's own shape, the same
 * one the competitive card draws the same figure in — with the band's word or *New* under the
 * figure (#660). The move took the **tint** with it: a block's figure is `ink`, and nothing on
 * this sheet is toned since the tone ladder went with the metered rows.
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
 * ## The whole name, always — and the handle under it, here and on the You tab only
 *
 * Nothing may derive a familiar form from a name — `playerName()`'s rule, and the reason the
 * column wraps rather than truncates. On your own record the name takes `(you)` after it,
 * because a face you are reading about is a stranger until something says otherwise.
 *
 * Under it, `@nickname`: two people may share a name, and this is the screen a friend opens to
 * tell them apart, which is why the handle is drawn **here and on the reader's own You tab and
 * nowhere else** — never on a row, a card, a sentence, a sheet, a toast, a seat label or a
 * spoken name
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §4). The mark is `atNickname`'s, spelled once so the two screens cannot disagree.
 *
 * ## The intro sits under the name, and the gap closes where there is none
 *
 * One line they wrote, inside the drawing's quotation marks, drawn **upright** — the deck
 * card's own decision, for the deck card's own reason: this app loads no italic Archivo, and a
 * `fontStyle` on a custom family is ignored on Android and synthesised on iOS, so the marks
 * carry *their words* rather than a slant. `muted`, because it is what they said and not what
 * the platform measured, and the roles above and below it are the platform's. Never
 * truncated: the cap at the write is what makes an ellipsis unnecessary (ADR-0170 §4). A
 * player who wrote none draws nothing here, and the identity line closes up under the handle.
 *
 * ## The identity line is a comparison and never a place name
 *
 * `In your area · 0,6 km`, or the kilometres alone, or nothing — the kilometres to one decimal,
 * through the one formatter every surface prints a distance with (ADR-0174 §2). An `area_code` is a coordinate
 * string; the only sentence a client is licensed to write from two of them is *these two are in
 * the same square*, and a reader whose own area is unknown gets no claim in either direction.
 * On your own record the **whole line** is gone rather than the distance alone — the two codes
 * are equal by construction there, so a line that dropped only the kilometres would tell
 * somebody they are in their own area — and `identityLine` reads `isSelf` for exactly that
 * reason, rather than leaving two call sites to remember one condition.
 *
 * ## One element, and the pills merge into it — but the button does not
 *
 * §20.1: everything with no action of its own merges into the nearest action above it. The
 * panel, the name, the handle, the intro, the identity line and the pills have none, so they
 * are one element and `recordHeaderLabel` is what it says — identifying facts first, in the
 * order they are drawn, with the intro inside its marks so it is heard as their words and never
 * as a name.
 *
 * **`Player fit` is an action and therefore its own element**, which is the same rule read the
 * other way. It sits under the pills rather than at the foot of the sheet: it is the sheet's
 * only control, and one a reader has to scroll past four zones to reach is one most readers
 * never reach.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { atNickname } from '@/shared/formatting/playerName';
import { PhotoPanel, theme } from '@/shared/ui';

import type { PlayerRecord } from '../domain/playerRecord';

import { SportPills } from './SportPills';
import {
  identityLine,
  introLine,
  recordHandle,
  recordHeaderLabel,
  sportPill,
} from './recordPresentation';

export interface RecordHeaderProps {
  readonly record: PlayerRecord;
  /** Whose poster to draw where there is no photograph — a fact about an id. */
  readonly playerId: string;
  /** Kilometres to one decimal, as the contract sends them. Absent on your own record, always. */
  readonly distanceKm?: number;
  /** The reader's own coarse area, for the one comparison this line is allowed to make. */
  readonly viewerAreaCode?: string;
  /**
   * What *Player fit* opens. Absent where no pairing is behind the entry point — your own
   * record, a chat, the games list — and the button is then not drawn at all.
   */
  readonly onExplainFit?: () => void;
  /** The Fit the engine published for the two of them, printed on that control. */
  readonly fit?: number;
}

export function RecordHeader({
  record,
  playerId,
  distanceKm,
  viewerAreaCode,
  onExplainFit,
  fit,
}: RecordHeaderProps) {
  const name = recordHandle(record.name, record.isSelf);
  const handle = atNickname(record.nickname);
  const intro = record.intro === undefined ? undefined : introLine(record.intro);
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
        name,
        handle,
        onCourt: record.onCourt,
        ...(intro === undefined ? {} : { intro }),
        identity,
        sports: record.sports.map(({ sport, level }) => sportPill(sportLabel(sport), level)),
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
        <Text style={s.name}>{name}</Text>
        <Text style={s.handle}>{handle}</Text>

        {intro === undefined ? null : <Text style={s.intro}>{intro}</Text>}

        {identity === '' ? null : <Text style={s.identity}>{identity}</Text>}

        <SportPills
          sports={record.sports}
          {...(onExplainFit === undefined ? {} : { onExplainFit })}
          {...(fit === undefined ? {} : { fit })}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  header: { flexDirection: 'row', gap: theme.space.md, alignItems: 'flex-start' },
  // The column takes whatever the panel leaves, so a 64-character name wraps inside it
  // rather than pushing the panel off the sheet.
  column: { flex: 1, gap: theme.space.xs },
  name: { ...theme.type.h1, color: theme.color.ink },
  handle: { ...theme.type.tiny, color: theme.color.muted },
  // The deck card's role for the same line, on paper instead of over a photograph: a
  // sentence to read rather than small print, and in `muted` because it is what they said
  // and not what the platform measured.
  intro: { ...theme.type.rlLabel, color: theme.color.muted },
  identity: { ...theme.type.tiny, color: theme.color.muted },
});
