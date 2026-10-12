/**
 * **This feature's rows on the You tab** — the two facts a player cannot touch, and the door to
 * the sheet that shows them to everybody else
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1).
 *
 * *Skill passport* and *Player reliability* are the first two rows because they are the two
 * a player most wants to look at and the two they cannot change: a Level is proved, never
 * declared, and Player reliability is what the platform watched. *How others see you* is the
 * record sheet about yourself, and it is a door the shell opens — the sheet is the tab's
 * overlay, so the row takes the press rather than pushing a route.
 *
 * | Row | Read |
 * | --- | --- |
 * | Skill passport | `GET /ratings` — one clause per rating |
 * | Player reliability | `GET /players/me/record` — the points and the band, `75 · High` or `100 · New` |
 * | How others see you | nothing — the line names the sheet |
 */

import { useRouter } from 'expo-router';

import { useSkillRatings } from '@/features/onboarding/types';
import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useOwnRecord } from '../hooks/useOwnRecord';

import {
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  PLAYER_RELIABILITY_TITLE,
  SKILL_PASSPORT_TITLE,
  passportLine,
  reliabilityLine,
} from './youRecordPresentation';
import { YOU_PASSPORT_ROUTE, YOU_RELIABILITY_ROUTE } from './youRecordRoutes';

/** 5.5's `index > 0` — the shell says where in its card the row sits. */
export type YouRowProps = Pick<DoorRowProps, 'divided'>;

export function SkillPassportRow({ divided }: YouRowProps) {
  const router = useRouter();
  const ratings = useSkillRatings();

  return (
    <DoorRow
      glyph="award"
      title={SKILL_PASSPORT_TITLE}
      line={liveLine(ratings, passportLine)}
      divided={divided}
      onPress={() => router.push(YOU_PASSPORT_ROUTE)}
    />
  );
}

export function PlayerReliabilityRow({ divided }: YouRowProps) {
  const router = useRouter();
  const { record } = useOwnRecord();

  return (
    <DoorRow
      glyph="activity"
      title={PLAYER_RELIABILITY_TITLE}
      line={liveLine(record, (own) => reliabilityLine(own.reliability))}
      divided={divided}
      onPress={() => router.push(YOU_RELIABILITY_ROUTE)}
    />
  );
}

export interface HowOthersSeeYouRowProps extends YouRowProps {
  /** Opens the sheet — the tab's overlay, which the shell holds. */
  readonly onPress: () => void;
}

export function HowOthersSeeYouRow({ divided, onPress }: HowOthersSeeYouRowProps) {
  return (
    <DoorRow
      glyph="eye"
      title={HOW_OTHERS_SEE_YOU_TITLE}
      line={HOW_OTHERS_SEE_YOU_LINE}
      divided={divided}
      onPress={onPress}
    />
  );
}
