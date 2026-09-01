/**
 * The wire for the one act in this product that reaches another person, and the list that
 * makes a refusal about it readable.
 *
 * One of the two layers allowed to read generated types, and the only place these two paths
 * are written down. The two seat answers — accept and decline — are on the same player surface
 * ([#229](https://github.com/Raketa02/Raketa/issues/229)) and arrive with the screen that
 * answers one; a route nothing calls is a route nobody is checking.
 *
 * ## No `Idempotency-Key`, and that is the stronger guarantee
 *
 * *"One open challenge per pair across sports"* is a rule that **does not expire**; a key
 * does. So a duplicate submission is **explicitly-valid repetition on the pair rule** rather
 * than a request the transport quietly swallows: the second send is made, read, and refused
 * with `open_challenge_stands` by the same check that would have refused a stranger's. A key
 * beside that rule would be a second mechanism for one fact, and the one that expires is the
 * one that would eventually disagree.
 *
 * What protects a player from a double **tap** is the control being busy, which Part 11 is
 * explicit is UX rather than correctness — and here it is allowed to be, because the rule
 * behind it is the mechanism.
 *
 * ## The two names here are the wire's, and the acts above them are the domain's
 *
 * `postChallenge` and `getChallenges` rather than `sendChallenge` and `readChallenges`, because
 * the use-cases one layer up own those words and a call aliased at the import to dodge the
 * collision hides which layer it lands in. `playSearchApi` draws the same line — `readSearch`
 * under `readSearchBack`, `expressInterest` under `sayYes`.
 *
 * ## No `signal` on the send, and one on the read
 *
 * The same asymmetry `playSearchApi` draws twice, arriving here for the same reason and not a
 * different one: **the send records before it answers**, so a cancelled one leaves a challenge
 * minted and four people asked with nobody holding its id. A `GET` records nothing, so an
 * abandoned one costs nobody a row.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type SendChallengeRequest = components['schemas']['SendChallengeRequest'];
type SentChallengeResponse = components['schemas']['SentChallengeResponse'];
type ChallengeListResponse = components['schemas']['ChallengeListResponse'];

/**
 * Send it — **one act, everybody at once**, and a `201` with the id of the challenge that now
 * stands.
 *
 * A doubles send is one challenge containing four people, answered by each of them separately,
 * and it either happens whole or writes nothing at all: *"there is no partial send that quietly
 * drops one person."*
 *
 * **The sport, the kind of evening and the week are not on this request.** They come from the
 * cited search, so there is no window picker anywhere and nothing here can disagree with the
 * court it was built on.
 */
export function postChallenge(body: SendChallengeRequest): Promise<SentChallengeResponse> {
  return httpRequest<SentChallengeResponse>({
    method: 'POST',
    path: '/api/v1/challenges',
    body,
    authenticated: true,
  });
}

/**
 * Every challenge you hold a seat in, newest first — **sent and received in one list**.
 *
 * *Challenge sent* and *Challenge for you* are one standing read from two sides, told apart by
 * whether `organiser_id` is yours; ended challenges are in it carrying `DECLINED` or `LAPSED`,
 * because *"a list that quietly dropped this morning's is a list that lies."*
 *
 * Today it has one caller, and it is the remedy the send's own contract points at: a refusal
 * names nobody, so this is what names the pair.
 */
export function getChallenges({ signal }: Cancellable = {}): Promise<ChallengeListResponse> {
  return httpRequest<ChallengeListResponse>({
    method: 'GET',
    path: '/api/v1/challenges',
    authenticated: true,
    signal,
  });
}

/** The read may be abandoned; the send may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}
