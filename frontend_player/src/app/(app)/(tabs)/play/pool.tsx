/**
 * The pool route — where every remedy the court states sends the player.
 *
 * A sibling of the builder rather than a screen behind it in the file tree, and pushed over it
 * at runtime: the court **pops** back, which is what lets the pending seat replacement be
 * route-local and need no clearing rule
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §6).
 *
 * The two params it will read — the origin search and the seat being filled — are already
 * sent by the builder. Validating them belongs with the screen that reads them
 * ([#272](https://github.com/Raketa02/Raketa/issues/272)); nothing here trusts one, because
 * nothing here reads one.
 */

import { PoolScreen } from '@/features/play/types';

export default function PoolRoute() {
  return <PoolScreen />;
}
