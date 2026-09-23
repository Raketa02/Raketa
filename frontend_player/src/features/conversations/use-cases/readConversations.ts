/**
 * **The rooms you are in** — the fetch, and the whole of what a use-case owes when the domain
 * owns the questions.
 *
 * There is no rule to run over the answer here. The order is the server's, the membership is the
 * server's fold, and everything a client could be wrong about — who a `{name}` may name, what a
 * code says, which weekday a recorded day is — is asked of one row at the moment it is drawn.
 * `_template/README.md`'s uniform-strict rule is explicit that a pass-through is the honest shape
 * when a feature has no business rule at this layer, and inventing one to fill the folder is what
 * it forbids.
 */

import { getConversations, type Cancellable } from '../api/conversationsApi';
import type { Conversation } from '../domain/conversation';
import { toConversations } from '../mappers/conversationMappers';

export async function readConversations({ signal }: Cancellable = {}): Promise<
  readonly Conversation[]
> {
  return toConversations(await getConversations({ signal }));
}
