import type { Court } from '../mappers';
import type { CourtAct } from '../schemas';

/**
 * **What an act on a court posts**: which act, and on which court. The name travels too, since a
 * refusal is said about the court the desk saw.
 */
export function CourtActFields({ act, court }: { act: CourtAct; court: Court }) {
  return (
    <>
      <input type="hidden" name="act" value={act} />
      <input type="hidden" name="id" value={court.id} />
      <input type="hidden" name="name" value={court.name} />
    </>
  );
}
