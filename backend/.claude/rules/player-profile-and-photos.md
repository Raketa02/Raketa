---
paths:
  - "app/modules/player_profile/**"
  - "docker/photo-review/**"
---

# The player profile and its photographs

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **Photo bytes live behind `PhotoStorage`, and the re-encode behind
  `ImageTranscoder`** ([ADR-0091](../../../docs/adr/0091-photo-storage-behind-a-port.md)).
  One S3-compatible adapter serves MinIO locally and S3 deployed — same class, different
  endpoint — so the deployed answer is a setting rather than a migration of live user
  data. Every port method takes a `PhotoRef` (owner **and** photo id), so ownership is the
  port's contract rather than each caller's memory. **Every upload is re-encoded to JPEG**,
  which is how EXIF — and the GPS in it — is stripped reliably rather than best-effort.
  `.importlinter` forbids `PIL`, `pillow_heif`, `aioboto3`, `boto3`, `botocore` and
  `aiohttp` to every domain and application layer, **including through the adapter**,
  because a use case that constructs the transcoder itself has bypassed the port just as
  completely.
- **The on-court photo check runs in a sidecar, and the rule it applies does not**
  ([ADR-0129](../../../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)).
  `ClipSidecarPhotoReview` is an `aiohttp` client; `docker/photo-review/` is a CLIP model
  behind one HTTP route that answers raw cosine similarities and holds **no policy**. The
  prompt set, the temperature and the threshold live in
  `player_profile/domain/photos.py` beside the size caps — behaviour a domain test can
  observe, never configuration — and `PHOTO_REVIEW_ENDPOINT_URL` /
  `PHOTO_REVIEW_TIMEOUT_SECONDS` cannot change a verdict. It **soft-warns and fails
  open**: a flagged photo is stored, and an unreachable sidecar yields **no decision at
  all** with a note saying which outage, because an outage is not a conclusion about an
  image. Every verdict records the similarity vector it was taken from, which is what makes
  today's placeholder threshold safe **and replaceable without paying for inference
  twice**: `make photo-flag-rate` (#316) walks the stored notes and prints the flag rate
  each candidate line would have produced, how many stored verdicts each move would make
  wrong, and — before the curve, because a rate is a number over a denominator — the four
  exclusions. **One curve per reviewer, never one blended**: two models are two corpora and
  a rate across both is a fact about neither, which is the way this reading can mislead —
  the seed's declared verdicts carry well-formed, current-fingerprint notes and on a laptop
  are most of the bucket. Where the rate should sit is a product judgement the command
  deliberately does not make; the chosen number goes in `photos.py` beside the caps and
  never in configuration. **No test needs the container**
  — `tests/conftest.py` overrides the port, as it does the store.
  **The verdict now crosses the wire, and only on the upload**
  ([ADR-0133](../../../docs/adr/0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)).
  `PhotoResponse.review` is an optional code — `allowed` / `flagged`, never a sentence and
  **never the note**, whose model, fingerprint, confidence and raw vector are evidence for
  re-deriving the threshold and are not about the player. `GET /photos/{id}` answers `null`
  there, which is deliberately **not** `allowed`: a warning belongs to the moment a player
  chose a photograph, and the read would pay a metadata request per tile for a fact no
  client asks it for. That ended ADR-0129's measure-only posture, which was a property of
  the tree rather than a flag — so there is nothing to toggle and the fail-open trade was
  re-examined rather than inherited: an outage now costs the player *silence*, not a
  sentence about our infrastructure dressed up as one about their photo.
  **And the verdict now reaches a stranger, on the player card, where *never checked* is a
  third answer**
  ([ADR-0138](../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
  A shield saying *checked and passed* cannot be drawn on a photo nothing looked at, so
  `verdict_when_unreviewable` records **no decision** and `review_metadata` writes no key
  — and, because three legacy populations already say `allowed` about unexamined images,
  `decision_on_record` believes a stored decision **only where the note proves a score**
  (model, prompt set, confidence, vector — all four). ADR-0132's backfill is therefore the
  cleanup and never the gate. The card **records** the verdict rather than minting it:
  `PlayerCardSource` pays one `HEAD` per shortlisted row that has a photograph and
  `RecordedCard` stores the code, so the read-back draws the shield that *was* drawn
  (ADR-0109) — the mirror of `photo_url`, which cannot be stored because it dies within the
  hour. `GET /photos/{id}` is untouched, and the note still crosses on no route at all.
  **And the owner reads what stands beside each of their own photographs on the profile
  read** ([ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §8, #466): `GET /players/me/profile` carries `photos[].review` — the same three-valued
  reading, one `HEAD` per photograph the profile holds, at most three, gathered — beside
  the tags, the intro and **the two values no other shape may carry, the owner's own
  `gender` and `gender_preference`** (§4). That is ADR-0096 §6's
  fence moved rather than lowered: `tests/unit/test_no_response_carries_a_forbidden_fact.py`
  admits the two words on that one schema by name (`PERMITTED_ON`) and asserts from both
  sides — refused on every other shape, and *present* on that one, so the admission can
  neither widen nor lapse unnoticed. The location area is still not served, and no
  `has_location` stands in for it.
  **And the five writes the tab needs land on the same surface** (ADR-0179 §6, §8, #467):
  `PUT /players/me/{social-tags,photos,intro,gender,gender-preference}`,
  one unkeyed `PUT` per fact, each the aggregate's own transition — so *Later changes, from
  the profile screen* is now a true heading. The intro's is the one that needed a new event,
  `IntroChanged` (`player_profile.intro_changed` / v1), whose `None` is the withdrawal;
  `IntroWritten` stays the commit's, the fold keeps the latest of either, and the candidate
  projection reads both so a card follows the edit and a withdrawal **clears** the column.
  Each re-validates as the commit re-validates, under the commit's codes; the photos are
  checked against the same port the upload used, and an empty list clears; **the two gender
  writes and the intro's answer `204`** so that *served on one route and no other* (§4) and
  *the card, the record and its author* (ADR-0170 §3) stay literally true of the response
  shapes — `tests/unit/test_intro.py`'s sweep is what caught the fourth. **A sixth, the
  proposals opt-in answered again from `PROFILE`, went with the search radius** (#581):
  only the "who fits whom" ranking read either, so a profile now commits without both.
  **And the reliability filter is a profile preference** (#661; ADR-0195 §6):
  `PUT /players/me/reliability-filter` (`{minimum: MEDIUM | HIGH | null}`, `204`),
  `PlayerProfile.reliability_minimum` (every profile starts off, `None`), recorded as
  `player_profile.reliability_minimum_set` / v1, a no-op on the value held, any other band
  `reliability_minimum_not_offered` (400). It sits beside the gender preference because it is a
  clause of the same pair rule — `proposals`' `MatcherPlayerFit` reads it off the profile load
  it already makes — and it is read back on the player's own record, never on the profile read.
- **A Location area is set by a reading of the phone or by a club picked in its place,
  and the intro is up to 250 characters**
  ([ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §9, §10, #726).
  The commit's `location` and `PUT /players/me/location`'s body are one union,
  `PhoneReadingRequest | PickedClubRequest` (`latitude` and `longitude`, or `club_id`), each
  `extra="forbid"` so both at once, half a reading or neither is a `422`; the commands carry
  `PhoneReading | PickedClub` (`LocationSource`), and `application/location_source.py`'s
  `area_of` is the one rule both writes run — a club's point is **rounded to the cell exactly
  as a reading is**, by `LocationArea.around`, so the desk's precise point never reaches the
  player's stream. **Nothing records which it was**: the area is a cell, so the cold start's
  next reading in another cell replaces a club-picked area (ADR-0174 §6, unchanged) and
  `player_profile.location_changed` is unchanged. Where a club is comes through **this
  context's own port**, `ClubPoints` (`ClubPoint`, precise; `None` for no club), **signed in
  `clubs/infrastructure/`** (`DirectoryClubPoints`, over `ClubDirectory`) because the arrow
  already runs `clubs → player_profile` — `.importlinter`'s
  `player-profile-does-not-know-clubs` holds it — and contracted in
  `player_profile_demands.py`. An id that names no club is `location_club_unknown` (400,
  `details.field` `club_id`), asked after the commit's pure refusals and before the object
  store. The intro's `INTRO_MAX_CHARACTERS` is **250** (from 100: the deck card it fitted went
  with Classic play); the request schemas and the column stay uncapped, and a replay
  re-checks nothing.
- **A photo URL is signed by one client per process, and the week answers *is this hour
  ticked?* by lookup** (#702, #703; ADR-0197 §2a, §2b). Presigning sends no request, so
  building an S3 client was the whole cost of a signature, once per face on every screen
  that draws faces: `s3_photo_storage.signing_client` is botocore's **synchronous** client,
  one per `SigningSetup` (host, region, credential — the bucket is in the request), built on
  first use and held for the life of the process; it opens no socket and binds to no event
  loop, which is what the per-call *talking* client cannot promise. The credentials rotate
  as the settings carrying them do, with a restart. The URL is today's URL apart from the
  signature and its date, shown against the signer it replaced. `WeeklyHours.ticked` is the
  week's hours as a `frozenset` of `(weekday, hour)`, derived once in `__post_init__` and
  **no part of the value** — out of equality, the hash and the repr, stored nowhere, carried
  by no event — so the overlap grid's millions of *is this hour ticked* on a busy deck are
  lookups. Measured on the busy seed deck: signing took a group's page from 52 to 20 ms and
  the deck read 160 → 118–137 ms; the lookup cut the overlap's share of the deck fivefold
  under cProfile (123 → 24 ms) and the read to 98 ms.
