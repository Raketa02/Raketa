/**
 * Being offline, as a sentence that sits **beside the act that is waiting**.
 *
 * ## Why this is a function and not a banner
 *
 * `docs/architecture.md` Part 11 names `OfflineBanner` as a shared component to build, and
 * [#239](https://github.com/Raketa02/Raketa/issues/239) declines it there in writing. A
 * screen-level banner assumes that being offline makes what is on screen *wrong*. In the Play
 * tab it does not: every ranked list is a mutation-minted record pinned at
 * `staleTime: Infinity`, so **a pool held offline is not stale — it is the record**. What
 * breaks offline is never the data, it is the **acts**, and each act has a control this
 * sentence can sit beside. A banner over correct data teaches the player to ignore banners.
 *
 * ## Why it is here, beside `recoveryMessage`
 *
 * Because a paused query produces **no `AppError` at all** — nothing was attempted, so there
 * is no failure to categorise, and neither `recoveryMessage` nor any feature's `code` table
 * can reach this state. And because the app had answered the question three times before it
 * was asked: `SocialRadiusStep`, `SocialTagsStep` and `SportsPickerScreen` each rendered their
 * own copy of it inline. Three copies is precisely the threshold `recoveryMessage.ts`
 * documents as the signal to promote.
 *
 * ## The split is resumption, never the HTTP verb
 *
 * `networkMode: 'online'` **pauses** rather than fails, so nearly everything in this app
 * resumes on reconnect and can say so. `features/challenges/` overrides that and therefore
 * cannot, for the reason written at its own site
 * (`features/challenges/hooks/challengeMutationOptions.ts`), which is where that argument lives
 * rather than here. That is the whole distinction, and it is one distinction — hence exactly
 * two values.
 *
 * Mapping it onto GET-versus-POST gets it wrong: the line-up **forecast is a `POST` that
 * pauses**, and it takes the first sentence.
 */

/** Does this act come back by itself when the connection does? */
export type Resumption = 'resumes' | 'does-not-resume';

const BY_RESUMPTION: Readonly<Record<Resumption, string>> = {
  /**
   * Everything the global `networkMode: 'online'` holds — every read, and every mutation but
   * one. It really will run itself on reconnect, which is why the sentence promises it.
   */
  resumes: "You're offline. This will load as soon as you're back.",
  /**
   * The send, and only the send. A challenge's answer window is derived **at send**, so a tap
   * deferred to the next reconnect would carry a deadline the player did not choose — the tap
   * and the send have to be one moment. It fails now, and the sentence says so rather than
   * promising a queue that does not exist.
   */
  'does-not-resume': "You're offline. This can't be sent until you're back.",
};

/**
 * The sentence for an act that cannot run because there is no connection.
 *
 * It names no subject on purpose: it is rendered at the paused control, so *this* is whatever
 * the player is looking at. A sentence that named its subject would be a third copy waiting to
 * happen the first time two screens paused the same thing.
 */
export function offlineMessage(resumption: Resumption): string {
  return BY_RESUMPTION[resumption];
}
