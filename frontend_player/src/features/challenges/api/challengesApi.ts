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
type ChallengeDetailResponse = components['schemas']['ChallengeDetailResponse'];
type ChallengeSchema = components['schemas']['ChallengeSchema'];
type FillSeatsRequest = components['schemas']['FillSeatsRequest'];

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

/**
 * **One challenge, richly** — the screen you answer on.
 *
 * The list tells you what you have been asked; this tells you who is asking and what this
 * platform makes of playing them. **The pairing is computed when you open it, in your own
 * direction** — nothing is copied at send and nothing is replayed from the organiser's search,
 * which is why a challenge born of a mutual yes draws the same screen as one built from a
 * shortlist ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
 *
 * `404 challenge_not_found` is **one code for two cases** — it does not exist, or you are not on
 * its court — because separating them would answer *is this id real* about a stranger's evening.
 *
 * It takes a `signal`, on this module's own asymmetry: a `GET` records nothing, so an abandoned
 * one costs nobody a row.
 */
export function getChallenge(
  challengeId: string,
  { signal }: Cancellable = {},
): Promise<ChallengeDetailResponse> {
  return httpRequest<ChallengeDetailResponse>({
    method: 'GET',
    path: `/api/v1/challenges/${challengeId}`,
    authenticated: true,
    signal,
  });
}

/**
 * **Your yes**, and the challenge as it now stands.
 *
 * It matters on its own and is not conditional on the other seats: the conversation opens on the
 * **first** acceptance and grows with each one, so there is no waiting room and no single moment
 * where the game becomes real. **The seat is not in the path** because you hold at most one in
 * any challenge, and nobody may answer for anybody else.
 *
 * **No `signal`, for the send's reason rather than the read's**: this records before it answers,
 * and an accept that filled the last seat has opened a game and a conversation by the time a
 * cancelled request would have been abandoned.
 *
 * The reply is `ChallengeSchema` — the list's shape, cards and all absent — which is the server's
 * own derived standing and therefore **the redraw**.
 */
export function postAccept(challengeId: string): Promise<ChallengeSchema> {
  return httpRequest<ChallengeSchema>({
    method: 'POST',
    path: `/api/v1/challenges/${challengeId}/accept`,
    authenticated: true,
  });
}

/**
 * **Your no**, and the challenge as it now stands.
 *
 * It reopens exactly your seat and disturbs nothing else: the people who already agreed did
 * nothing wrong and are still in the game. **Nobody is told you declined**, and no response
 * anywhere names you as having done so.
 *
 * **Saying nothing is not this.** Silence past your day is a *lapse*, which is a different fact
 * and is counted apart — the platform never files it as a judgement you made.
 */
export function postDecline(challengeId: string): Promise<ChallengeSchema> {
  return httpRequest<ChallengeSchema>({
    method: 'POST',
    path: `/api/v1/challenges/${challengeId}/decline`,
    authenticated: true,
  });
}

/**
 * **The open seats, offered to the people you just built a line-up around** — and the court as
 * it now stands.
 *
 * *"The send's shape minus the mint"*: the challenge is in the path, so what is left is the two
 * things a fill has to say. Everything else about the game is already on the challenge — the
 * sport, the kind of evening, and the **window**, which is stamped when a challenge is sent and
 * never again ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md) §6).
 *
 * **Any live member may do this; ending a court is a different act** — removing one that was
 * never a game is the organiser's while nobody has joined and nobody's once somebody has, and
 * calling off the game a court became is any player's on it (ADR-0165 §4–§5). A challenge born of
 * two mutual yeses has an organiser who is only whoever said yes second.
 *
 * **The whole court goes, not the new seats.** An acceptance is to the game and not to the side,
 * so somebody already in may be moved across the net and may never be taken out.
 *
 * **No `signal`**, on this module's own asymmetry: it records before it answers, and each newly
 * seated player's own day is dated from the moment it lands.
 */
export function postSeats(challengeId: string, body: FillSeatsRequest): Promise<ChallengeSchema> {
  return httpRequest<ChallengeSchema>({
    method: 'POST',
    path: `/api/v1/challenges/${challengeId}/seats`,
    body,
    authenticated: true,
  });
}

/**
 * **Two acts on one route, told apart by whether the court has been a game**
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4–§5). *Remove the challenge*: the organiser's, admitted exactly while nobody besides them
 * holds an accepted seat — before anybody has answered, whatever seats are still deciding — and
 * refused with `somebody_has_joined` once anybody is in. *Call it off*: on a court that has been a
 * game, any player's on it, while a seat is open; the game reaches `CALLED_OFF` in the act.
 * Whole-challenge either way, and it never removes one person; irreversible, with no route back —
 * asking the same people again is a **new** challenge
 * ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)).
 * Nobody who was still deciding is charged a lapse for it.
 *
 * **A noun and not a verb**, because what this creates is the withdrawal — the one thing in this
 * context a fold of the seats could never produce. The reply is `ChallengeSchema` at `WITHDRAWN`,
 * which is the server's own derived standing and therefore the redraw.
 *
 * **No `signal`**, for the send's reason rather than the read's: it destroys the conversation in
 * the same transaction where one exists, so a cancelled one has already deleted what people wrote.
 */
export function postWithdrawal(challengeId: string): Promise<ChallengeSchema> {
  return httpRequest<ChallengeSchema>({
    method: 'POST',
    path: `/api/v1/challenges/${challengeId}/withdrawal`,
    authenticated: true,
  });
}

/**
 * *I'm leaving this game.* **A noun and not a verb, like the withdrawal**: what this creates is
 * the departure. The reply is the challenge as it now stands — `LINE_UP_INCOMPLETE`, with the
 * caller's seat `LEFT` — and the game it became keeps its id with that seat open (ADR-0162).
 */
export function postDeparture(challengeId: string): Promise<ChallengeSchema> {
  return httpRequest<ChallengeSchema>({
    method: 'POST',
    path: `/api/v1/challenges/${challengeId}/departure`,
    authenticated: true,
  });
}

/** The read may be abandoned; the send may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}
