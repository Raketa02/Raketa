import type { BookingAct } from '../schemas';

/**
 * **What an act on a game posts**: which act, and on which booking. The game's name travels
 * too, since what the backend says back is said about the game the desk saw.
 */
export function GameFields({ act, id, name }: { act: BookingAct; id: string; name: string }) {
  return (
    <>
      <input type="hidden" name="act" value={act} />
      <input type="hidden" name="id" value={id} />
      <input type="hidden" name="name" value={name} />
    </>
  );
}
