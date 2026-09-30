/**
 * **Games & money, on the You tab** — the ACCOUNT group's first row: its title, the limits in one
 * line, and the door to the screen ([#554](https://github.com/Raketa02/Raketa/issues/554); the
 * screens A7; mock 37).
 *
 * The line repeats the screen's bound — *At most 4 games a week*, with *· up to 180 zł* once a
 * ceiling is set — off the screen's own read, so a tap there is on the row the moment the player
 * comes back.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useGamesAndMoney } from '../hooks/useGamesAndMoney';

import { GAMES_AND_MONEY_TITLE, gamesAndMoneyRowLine } from './gamesAndMoneyCopy';
import { YOU_GAMES_AND_MONEY_ROUTE } from './proposalRoutes';

export type GamesAndMoneyRowProps = Pick<DoorRowProps, 'divided'>;

export function GamesAndMoneyRow({ divided }: GamesAndMoneyRowProps) {
  const router = useRouter();
  const read = useGamesAndMoney();

  return (
    <DoorRow
      glyph="sliders"
      title={GAMES_AND_MONEY_TITLE}
      line={liveLine(read, gamesAndMoneyRowLine)}
      divided={divided}
      onPress={() => router.push(YOU_GAMES_AND_MONEY_ROUTE)}
    />
  );
}
