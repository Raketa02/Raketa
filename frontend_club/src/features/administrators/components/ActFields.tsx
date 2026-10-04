import type { Administrator } from '../mappers';
import type { Act } from '../schemas';

/**
 * **What an act on a row posts**: which act, and on whom. The name travels too, since a refusal
 * is said about the person the desk saw on the row.
 */
export function ActFields({ act, administrator }: { act: Act; administrator: Administrator }) {
  return (
    <>
      <input type="hidden" name="act" value={act} />
      <input type="hidden" name="id" value={administrator.id} />
      <input type="hidden" name="name" value={administrator.name} />
    </>
  );
}
