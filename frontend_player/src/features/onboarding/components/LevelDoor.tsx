/**
 * **The door where play begins** — one dark card in place of a player group's Games, Fill in and
 * Friends, its *Post a game* and its Members, for a player rated in nothing
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §2, §5,
 * [#730](https://github.com/Rakieta02/Rakieta/issues/730)).
 *
 * - ***Get your level*** — *pick the sports you play, a few questions each* — opens *Which sports
 *   do you play?* over every sport, with nothing ticked.
 * - ***Carry on with your padel questions*** — *you're on question 5* — with a run left halfway,
 *   opens that run where it stands. It never offers to start again.
 *
 * The pass it begins returns to `from`: the group and the tab the door stands on, so the last
 * *Your rating* says *Back to Wednesday padel* and lands there, with the chip on the sport just
 * rated. **Nothing is drawn until the door knows which it is**, so it never says one and then the
 * other — and offline, with nothing cached, it says it is waiting rather than drawing nothing.
 *
 * **On Home it is the card** ([#731](https://github.com/Rakieta02/Rakieta/issues/731), ADR-0200 §7):
 * the same door, `from` Home, whose line says why nothing is happening — *your groups can't deal you
 * games until you have one* — and whose pass ends on Home. Where it is drawn is `groups`' rule.
 *
 * The page's dark card, as the official group's own card (`AddSportCard`) and every starting
 * tab's (`LinkCard`) are: a headline, the line under it, and the one bright door. It lives here
 * rather than in `groups` because its words are the questionnaire's, and Home's card says the same
 * carry-on.
 */

import { StyleSheet, Text } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { Button, DarkCard, Note, theme } from '@/shared/ui';

import type { DoorOrigin } from '../domain/onboardingPass';
import { useLevelDoor } from '../hooks/useLevelDoor';

import {
  LEVEL_DOOR_COPY,
  carryOnHeadline,
  carryOnHint,
  carryOnLine,
} from './levelDoorPresentation';

export interface LevelDoorProps {
  /** Where the pass it begins returns to — the group and the tab it stands on, or Home. */
  readonly from: DoorOrigin;
}

export function LevelDoor({ from }: LevelDoorProps) {
  const { door, offline, open } = useLevelDoor(from);

  // Offline with nothing cached, the door cannot say which it is — so it says why, and draws itself
  // the moment the connection is back. The picker's own offline note, for the same pause.
  if (door === undefined) {
    return offline ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null;
  }

  const carrying = door.kind === 'carry-on';

  return (
    <DarkCard style={s.card}>
      <Text style={s.headline}>
        {carrying ? carryOnHeadline(door.run.sport) : LEVEL_DOOR_COPY.headline}
      </Text>
      <Text style={s.line}>
        {carrying ? carryOnLine(door.question) : LEVEL_DOOR_COPY.line[from.kind]}
      </Text>
      <Button
        label={carrying ? LEVEL_DOOR_COPY.carryOn : LEVEL_DOOR_COPY.start}
        accessibilityHint={carrying ? carryOnHint(door.run.sport) : LEVEL_DOOR_COPY.startHint}
        variant="volt"
        onPress={open}
      />
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { alignItems: 'center', gap: theme.space.md },
  // 3.3: `h2` titles a card — `AddSportCard`'s and `LinkCard`'s headline.
  headline: { ...theme.type.h2, color: theme.color.surface, textAlign: 'center' },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
});
