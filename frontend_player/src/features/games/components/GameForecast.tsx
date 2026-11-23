/**
 * **A game's balance forecast, on its own** — the block `CourtPairing` draws at the top of the game
 * screen, for a surface that draws its own people ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A4.1, details 9: *as built today*).
 *
 * A booked game's details draw their tiles from the booking, with *paid* on each, so the players
 * card would be the second drawing of four people on one screen; what they take from this feature
 * is the forecast alone. It is the same read (`usePairing`, the Game's own pairing) and the same
 * block, absent on the same ground — no game in the list yet, a pairing with no forecast, a read
 * in flight or failed — with no sentence beside the absence (ADR-0161 §4). Whether it is drawn at
 * all is the composer's: a booking draws it while the full game awaits its entry.
 *
 * **The block is `shared/ui`'s** since a competitive game's details drew it too
 * ([#839](https://github.com/Raketa02/Raketa/issues/839), ADR-0207 §6); what this feature hands it
 * is its own read — the Game's pairing — and its own words for the kind (`forecastSentence`). A
 * booked For-fun game is a `FRIENDLY` one and still draws it here, until #841's Social vibe card.
 */

import { ForecastBlock } from '@/shared/ui';

import type { Game } from '../domain/game';
import { useGame } from '../hooks/useGames';
import { usePairing } from '../hooks/usePairing';

import { barLabels, forecastSentence, sideNames } from './gamePresentation';

export interface GameForecastProps {
  /** The Game whose pairing is read — a booking's `game_id`. */
  readonly gameId: string;
  /** The reader: your side is the bar's left, *You* first (ADR-0141's join). */
  readonly playerId: string;
}

export function GameForecast({ gameId, playerId }: GameForecastProps) {
  const { game } = useGame(gameId);
  return game === undefined ? null : <Forecast game={game} playerId={playerId} />;
}

/** The read, once the game is known — a hook cannot wait for its argument. */
function Forecast({ game, playerId }: { readonly game: Game; readonly playerId: string }) {
  const pairing = usePairing(game).data ?? undefined;
  if (pairing?.forecast === undefined || pairing.split === undefined) return null;

  return (
    <ForecastBlock
      forecast={pairing.forecast}
      split={pairing.split}
      {...(pairing.atStake === undefined ? {} : { stake: pairing.atStake })}
      labels={barLabels(game.seats, playerId)}
      names={sideNames(game.seats, playerId)}
      sentence={forecastSentence(game.kind)}
    />
  );
}
