/**
 * The wire adapter for a *not now*. **One route, write-only, and nothing comes back.**
 *
 * One of the two layers allowed to read generated types, and the only place this path is
 * written down.
 *
 * **The other half of a prompt is not here, and that is the split worth knowing.** Saying
 * *yes* is a `PUT` through the route that owns the value — the radius, the week, the play
 * intent — all three of which are `player_profile`'s
 * ([#237](https://github.com/Raketa02/Raketa/issues/237) §2). Only the decline is
 * matchmaking's, because a decline **writes no value**: it is a fact about the *question*,
 * which is why it lives beside `POST /passes` rather than beside the profile it silences a
 * question about.
 *
 * **No Origin key and no idempotency key**, unlike the pass next door. A pass carries a
 * `search_id` because *pass rate on re-shown profiles* is unmeasurable without one, and
 * nothing a decline is measured by needs one — two of the four prompts are raised by a
 * background loop with no search to cite. A second *not now* is a second row with its own
 * moment, and it buys the same month the first did.
 *
 * **`KEEP_THESE_TIMES` is refused by this route** with `prompt_does_not_suppress`, and the
 * app does not send it: a week improvised for one evening is a different week next Tuesday,
 * so that one prompt is asked again and offers no *not now* to press. The typed absence in
 * `promptSuppression` is the same fact one layer up, which is what keeps the two in step.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type RecordPromptDeclineRequest = components['schemas']['RecordPromptDeclineRequest'];

/**
 * *Not now* — recorded, and returned by nothing, ever.
 *
 * `204`, like the pass: there is no shape to type as a response because there is no route
 * through which a decline reaches anybody, including the player who made it.
 */
export function recordPromptDecline(body: RecordPromptDeclineRequest): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: '/api/v1/prompt-declines',
    body,
    authenticated: true,
  });
}
