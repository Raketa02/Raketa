/**
 * **The court's pairing, in the game screen's `court` slot** — the forecast block and the players
 * card, over one read ([#415](https://github.com/Raketa02/Raketa/issues/415),
 * [ADR-0161](../../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
 *
 * `GameScreen` draws the slot on the plan lead and nowhere else, and this is what fills it —
 * composed by `GameScreenWithPlan` rather than by the screen, because the faces come off the room
 * join that composition already holds for the card above, and the screen may not read it. It is
 * this feature's own component in a slot this feature declared opaque: the slot is opaque so the
 * **layout** is decided once, not so the screen never learns what a pairing is.
 *
 * ## One read, two blocks, and each is absent on its own ground
 *
 * `usePairing` is asked once here and both blocks read its answer. The **forecast block** is drawn
 * when the pairing carries a forecast — and when it does not (somebody unrated; a refusal by name;
 * the read in flight or failed) it is **absent entirely, with no sentence**, which is #410's
 * decision and ADR-0161 §4's *there is deliberately no reason beside the absence*. The **players
 * card** does not depend on the forecast and is always drawn: its rows are the court's seats, and
 * what the pairing adds is the Level under each handle, which a seat without a row simply goes
 * without.
 */

import { View, StyleSheet } from 'react-native';

import { theme } from '@/shared/ui';

import type { Game } from '../domain/game';
import { usePairing } from '../hooks/usePairing';

import { ForecastBlock } from './ForecastBlock';
import { barLabels, forecastSentence, sideNames } from './gamePresentation';
import { PlayersCard } from './PlayersCard';

export interface CourtPairingProps {
  readonly game: Game;
  /** The reader's own id — which seat is yours is a join and not a rule (ADR-0141). */
  readonly playerId: string;
  /** Each seat's photograph by player id, from the room. Absent is a poster, never an error. */
  readonly faces: ReadonlyMap<string, string>;
}

export function CourtPairing({ game, playerId, faces }: CourtPairingProps) {
  const pairing = usePairing(game).data ?? undefined;

  return (
    <View style={s.blocks}>
      {pairing?.forecast === undefined || pairing.split === undefined ? null : (
        <ForecastBlock
          forecast={pairing.forecast}
          split={pairing.split}
          {...(pairing.atStake === undefined ? {} : { stake: pairing.atStake })}
          labels={barLabels(game.seats, playerId)}
          names={sideNames(game.seats, playerId)}
          sentence={forecastSentence(game.kind)}
        />
      )}

      <PlayersCard game={game} playerId={playerId} pairing={pairing} faces={faces} />
    </View>
  );
}

const s = StyleSheet.create({
  // 4.1's step between stacked cards — the screen's own rhythm, continued through the slot.
  blocks: { gap: theme.space.sm },
});
