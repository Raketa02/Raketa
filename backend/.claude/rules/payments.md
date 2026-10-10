---
paths:
  - "app/modules/payments/**"
  - "app/api/v1/webhooks.py"
  - "app/bootstrap/payments_demands.py"
  - "app/bootstrap/payment_demands.py"
  - "app/modules/proposals/application/club_money.py"
---

# Payments

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **Money goes through one port, and the terms come before the secret**
  ([ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4,
  [ADR-0190](../../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md), #536).
  `app/modules/payments/` holds the **Payment method** — event-sourced, one stream per player
  under the player's own id, born by being used — and **`PaymentProvider`**
  (`domain/provider.py`), the one port every movement of money goes through, in Raketa's words:
  a setup, a card on file, an authorised payment and its hold's **last moment**, a capture and
  the **real fee** kept on it, an **exact refund**, a club account's three states. It covers
  what #537, #541 and #545 needed, **#548 widened it twice** — `pay_out` (a club's money
  released to its bank, below) and `Payment.fee_grosze` — and **#636 once more**, for Q113
  (ADR-0190's 2026-10-10 amendment): `Payment.last_moment` (Stripe's
  `payment_method_details.card.capture_before` on the authorised charge), a fee that may be
  *not yet known* (`None` — a club on its own negotiated pricing is told it later), and
  `refund(amount_grosze=…)` in place of the withhold-the-fee flag. `charge_now` is gone: money
  taken at once is a hold taken in the act, as the fill's and a rescue's are. Four things are
  load-bearing. **Two adapters, one demand suite**:
  `StripePayments` (Connect direct charges on the club's account, Accounts v2 with
  `fees_collector`/`losses_collector` = `stripe`, v1 Customers, a clone per charge, a key on every
  write) and `FakePayments`, controlled by **the card the phone entered** — Stripe's own five test
  cards, in `domain/entered_cards.py` — and `app/bootstrap/payments_demands.py` runs
  `tests/demands/test_payments_demands.py` against both, the fake always and Stripe only with a
  **test** key. **Which one is configuration** (`PAYMENTS_PROVIDER`): a laptop is on a fake that
  confirms every setup with Visa •••• 4242, every test on its own fake (the `payments` fixture),
  and a deployed environment refuses the fake; a live key is refused off production and a test
  key in it. **The setup's secret is the answer to the terms**: `POST …/setup` answers the setup
  id and the publishable key and never the secret, `POST …/terms` records version, moment and
  address and answers it, and the save refuses a setup without them however it arrives — so *the
  terms before anything is saved* is the contract's. **The provider is called inline only where
  its answer is the response**, before anything is written; a replaced or removed card is
  released, and a replaced setup cancelled, by outbox subscribers, and the provider is a
  **per-run delivery seam** (`create_event_batch_for(..., payments=)`) beside `nudges`; a key
  is the act and **the hour**, so a failure Stripe stored against it lasts an hour, not a day. And **the webhook is on no
  surface**: `POST /api/v1/webhooks/stripe` (`app/api/v1/webhooks.py`) is in no OpenAPI
  document, verifies the signature with a five-minute tolerance before reading, and reads a
  notice **once** through `payment_notices`, in the transaction that acts on it, and treats it
  as a prompt — the card or setup it names is **read from the provider as it stands**, because
  notices arrive out of order; a notice finds its player through `payment_customers`, a
  projection the repository writes. *Remove* asks
  `PaymentCommitments`, answered by `proposals` with the player's live yeses (an adapter
  signed in `proposals/infrastructure/`, so the arrow runs `proposals → payments`), and the
  booked games still ahead, off the bookings (#541). **The port grew one read for #541**,
  `read_payment` — a refused payment confirmed on the phone, and a notice about a seat's
  payment, are both read as they stand — and a payment **waiting for its player** answers its
  secret (`AWAITING_THE_PLAYER`: the bank's check, or a decline confirmed with another card).
  The **Seat charge** — one stream per payment for one share, its verdict, its refund and the
  provider's answers — is `bookings.md`'s. **A refusal with time to pay keeps every other
  hold** (#625, #626; `GameToCharge.pay_by`): the holds just made are recorded held and none
  is released, so the payment in time books on them; the confirm email names the time, and
  with no time left at the club's yes nobody is emailed — the game is called off. **A refund
  is decided in the act and made from the outbox** (#544): `SeatChargeRefundDecided` then
  `SeatChargeRefunded`; receipts list it as its own `REFUND` row (`card_fee_grosze`), dated
  from the decision. **The settler computes the amount** (#636, `refund_to_ask_grosze`): the
  whole share, or the share less **the fee kept on that payment** (`fee_taken_grosze`), and
  records what was kept as the share less what came back. A fee not yet known at the capture
  is asked for again (`read_payment`, recorded `SeatChargeFeeReported`), and while it is still
  unknown the delivery raises `PaymentsUnavailable`, so the refund waits and the outbox
  retries. A Seat charge records each hold's `last_moment` (`SeatChargeAuthorised`, and
  `SeatChargeConfirmed` for one its player confirmed). `domain/card_fee.py`'s **estimate**
  (Stripe's EEA price, the personal EU card's) is still what the reads quote before the money
  moves, until #641 retires it.
  **Held until the cut-off, taken at it** (#637; ADR-0189's 2026-10-10 amendment): a game
  booked before its club's cut-off **keeps** each hold for the booked game (`SeatCharge.keep`,
  `SeatChargeKept` with `until`, status `HELD`, the projection's `held_until`), nothing moves at
  the provider, and the cut-off job takes it (`TakeTheHeldShares`, `SeatChargeTaken` with
  `kept=True`); one booked after it is taken at once. A `HELD` charge is **not paid** (`PAID`
  is `TAKING`/`CAPTURED`: no receipt, no *Collected*) and **not settled** (the payout waits for
  the take); `release` lets go undecided holds only, so **a held share is let go by `let_go`**
  (`SeatChargeReleased` with the reason), which `GiveTheSharesBack` (was `RefundTheSeats`) does
  for a leave before the cut-off, a game short at it and the club's cancel before it — a share
  taken is refunded as before. **The terms in force are `2026-10-10`**: `terms_needed` is also
  true for a consent to older words, so the fill refuses `TERMS_NEEDED` without asking the
  provider until the player accepts again (the seed accepts them on a re-run).
  **The fake models card kinds and hold windows** (#636): `EnteredCard.kind`
  (`domain/entered_cards.py` — personal EU by default, business, UK, outside Europe) keeps
  that kind's real fee when the share is taken (`CARD_PRICES`: 1,5 / 1,9 / 2,5 / 3,25 % + 1 zł,
  so 1,60 / 1,76 / 2,00 / 2,30 zł on 40 zł); a hold made without its player lasts its network's
  window on the fake's `clock` (`HOLD_WINDOWS`: Visa 4 days 18 hours, Mastercard 7 days; 7 days
  on either once confirmed in the app) and **lapses** after its last moment — read cancelled,
  and a capture refused (`FakeRefusal`); `fees_reported_later` holds a club's fee back until
  `reports_fee`. **A test's fake has no clock** unless the test gives it one, and then says no
  last moment and lets nothing lapse; a test that lets a capture wait days gives its players
  Mastercards (`test_club_money.py`).
  **The games test console steers the laptop's fake** (#591, `app/api/dev/provider.py`): it
  reads and sets a saved card's behaviour (`card_behaviour_of`, `card_behaves`) and, since
  #636, its kind and network (`card_is`, `card_kind_of`, `card_network_of` — the fake's record
  only; the player's method keeps the brand they saved), confirms a
  waiting payment as the phone's bank would (`phone_confirms_payment`), makes refunds wait
  (`refunds_wait` answers a refund `PaymentsUnavailable`, so the outbox retries, until
  `gives_refund` or the wait is lifted) and delivers one through `SettleSeatCharges.settle`
  — the outbox's own step for one charge — and **replays the notices the fake records** for
  every move of a payment (`notices`: the `payment_intent.*` Stripe would have sent, as
  `SeatPaymentChanged`) through `ReceivePaymentNotice`. Seeded by `app/seeds/payments.py`:
  every named account and cohort member saves a fake card through the three use cases — the
  protagonist the mock's Visa •••• 4312, two through the wallets — and `brand-new-player` has
  none.
- **A club connects payments through the provider's pages, and the arrow runs
  `payments → clubs`** (#537). The club's account at the provider is recorded on its **Club
  courts** stream (`clubs/domain/payments_account.py`) — `PaymentsAccountOpened`, once, and
  `PaymentsStatusChanged` whenever the provider says it moved — and the checklist reads it
  (see `clubs.md`). The Club context asks for it through **its own** port,
  `PaymentsAccounts` (open, a link, the status), and this context answers it over the
  provider in `infrastructure/club_accounts.py`; the notice that an account changed goes
  the other way through **this** context's port, `ConnectedAccounts`, answered in the same
  module over the club's `HeedPaymentsAccount`. The club's link route,
  `POST /api/v1/club/payments/onboarding-link`, is this context's too
  (`presentation/club_routes.py`, mounted on the club surface), because the provider
  dependency is — and `.importlinter`'s `clubs-does-not-know-payments` holds the arrow.
  **The Connected accounts webhook is a second endpoint with its own secret**:
  `POST /api/v1/webhooks/stripe-connect`, verified with `STRIPE_CONNECT_WEBHOOK_SECRET`
  (required wherever the platform's is), read by the same `StripeNotices` over that secret
  and acted on by the same `ReceivePaymentNotice`, so one inbox dedupes both. Stripe still
  sends v1 `account.updated` there for an Accounts v2 account, naming it at the top level
  (`account`); that is `ConnectedAccountChanged`, and on the platform endpoint — where it names
  no connected account — it is nothing. The notice is a prompt: the account is **read from
  the provider as it stands**, and every link also reads it — a club recorded ready before
  it is refused one — so neither a late nor a lost notice strands a desk. `FakePayments.onboarding_completes`
  finishes a club's onboarding on its link (a laptop's always does);
  `account_opened_for(club_id)` is the account a test's notice names.
- **The club is paid after the game is played, once a day** (#548; the mechanics §12.6,
  §16.11, §16.12; the screens B7, B9; `application/payouts.py`, rules in
  `domain/club_payout.py`). Every share is taken on the club's own account and **waits
  there** — a refund before the start comes out of it — until the **close of a club day**
  (`last_closed_day`: the end of its last court hour, 23:00 in Kraków). Then the
  `club-payouts` job (see `jobs.md`) decides, per club, **one payout** — a **Club payout**,
  event-sourced, one stream per club per day (`payout_id_for`, `uuid5`), so a second process
  collides — carrying every game of a closed day that is **over** (`GamesOver`: played, or
  called off *and recorded so* — a game short at its cut-off before the cut-off job reaches
  it is not, since its refunds are not decided yet; answered by `proposals`'
  `BookedGamesOver`, contracted in `payment_demands.py`) and **settled** (no capture or
  refund still on its way, `SeatCharge.settled`), for what they **kept**: each share taken,
  less what was given back, less **the card fee** (`SeatCharge.net_grosze` /
  `card_fee_grosze` — the provider's own figure, recorded on `SeatChargeCaptured.fee_grosze`
  or the refund that kept it back, the estimate until then). **A day that left less than
  nothing pays nothing out**: its games wait and are netted against the next day that leaves
  the club something, so a payout never sends more than the games left (a game given back
  whole costs the club its card fees). **Decided in the job, made from the outbox**, as a
  refund is: `ClubPayoutDecided` (the games — `club_payout_games`, a game carried **once**,
  its primary key a conflict — and the amount) commits in the job's transaction, and
  `SendClubPayout` (`handlers/send_club_payouts.py`, subscribed per delivery run over its
  session and provider) calls `pay_out` under `raketa-payout-<id>` and records
  `ClubPayoutSent` with the desk's email *A payout was sent* (`payout_emails.py`; the desk is
  `Seller.email`, the club's one sign-in); a provider that cannot take it yet
  (`PaymentsUnavailable` — Stripe's `balance_insufficient` too) fails the delivery, which the
  outbox retries under the same key. **How Stripe holds the money is open item O2**: a
  full-dashboard account with Stripe as losses collector cannot be kept on manual payouts by
  the platform except through Platform controls, and even then the club can pay itself out;
  `StripePayments.pay_out` is a manual payout (`POST /v1/payouts` on the account), proven by
  no test, and accounts are still opened on Stripe's own schedule. **The club's reads**:
  `GET /api/v1/club/payouts` (this context's, `presentation/club_routes.py`, the provider's
  list as it stands) and `GET /api/v1/club/money?month=YYYY-MM` (Proposals', beside the
  Bookings page — `bookings.md`), whose `paid_out` is true once a payout the provider took
  carried the booking. The fake pays out only when asked, dating the arrival two days off
  its `clock` (a laptop's and the seed's fakes have the wall clock; a test sets
  `payments.clock`).
