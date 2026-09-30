---
paths:
  - "app/modules/payments/**"
  - "app/api/v1/webhooks.py"
  - "app/bootstrap/payments_demands.py"
---

# Payments

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **Money goes through one port, and the terms come before the secret**
  ([ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4,
  [ADR-0190](../../../docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md), #536).
  `app/modules/payments/` holds the **Payment method** — event-sourced, one stream per player
  under the player's own id, born by being used — and **`PaymentProvider`**
  (`domain/provider.py`), the one port every movement of money goes through, in Raketa's words:
  a setup, a card on file, an authorised payment, a refund with the fee withheld, a club
  account's three states. It already covers what #537, #541, #545 and #548 need, so reach for it
  rather than widening it. Four things are load-bearing. **Two adapters, one demand suite**:
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
  signed in `proposals/infrastructure/`, so the arrow runs `proposals → payments`); booked
  games are nought until bookings exist (#541). Seeded by `app/seeds/payments.py`: every named account and cohort member saves a fake
  card through the three use cases — the protagonist the mock's Visa •••• 4312, two through the
  wallets — and `brand-new-player` has none.
