# Gaps round: CLUBMONEY

Answers to the facts the CLUBMONEY grades needed (`$W/areas/CLUBMONEY/gaps.md`), read 2026-10-08. Each `###` heading
answers part of one gap and names its rule. Sources: Stripe's documentation (fetched as the Markdown the docs site
serves) and support articles; Przelewy24's general terms (OWU v2.0, in force 15 May 2026), its payer regulation, its
REST API reference and its merchant-panel manual; Tpay's general terms for merchants (in force 24 March / 8 April 2026)
and its payer terms (in force 20 April 2021); PayU's developer guide and its merchant agreement (v. 2020-04-10); the
shipped JavaScript of tenis4U's club panel and player app and of Playmore's web app; the Kraków clubs' own rules
(Miazga, Garden Padel, Atras, Squash4You, Fame Sport, AGH Sports Hall); and the Ministry of Finance's ruling database
Eureka, searched through its own public search API. No screenshot was taken: nothing is `[MEASURED]`. A line marked
*reading* is this researcher's inference from the facts above it, not a source.

Kinds: `[POLICY]` a rule, term or interface text a club or platform publishes or ships; `[DOCS]` a payment provider's
or regulator's documents; `[LAW]`; `[COMPLAINT]` one person's account; `[ABSENT]` looked for and not found, with where.

Facts already in the folder are cited, not repeated: the payout-failure email and the `payout.failed` event are in
`gaps-EMAIL.md#stripe-emails-the-account-holder-when-a-payout-comes-back-up-to-5-business-days-later` and
`gaps-EMAIL.md#the-platform-hears-of-it-as-an-event-payoutfailed`; Przelewy24's payout schedule in
`gaps-EMAIL.md#przelewy24-pays-out-on-a-threshold-or-a-schedule-and-lists-each-payout-in-the-panel`; the receipt a
direct charge sends in `local-market.md#receipts-on-a-direct-charge-come-from-the-clubs-stripe-settings`.

---

## 1. A payout the bank sends back (R-CLUBMONEY-20)

### Stripe sends a returned automatic payout again at the next scheduled payout, once the details are fixed

- **[DOCS]** "If a payout fails, make sure your bank account details are correct by re-entering them. Stripe then
  reattempts the payout at the next scheduled payout interval." If the details were right and the bank was the
  problem: "After you resolve any issues with your bank, you can reactivate the payouts by clicking **Resume
  Payouts**." [Stripe: Receive payouts — Payout failures](https://docs.stripe.com/payouts#payout-failures) — read
  2026-10-08
- **[DOCS]** "When a payout fails, the status might initially show as `paid`, but then change to `failed` within 5
  business days." [same page](https://docs.stripe.com/payouts#payout-failures) — read 2026-10-08
  - *Reading:* on Stripe's own daily schedule nobody at Rakieta has to act: the club re-enters its account (or presses
    Resume Payouts) and the next daily payout carries the money again, together with whatever came in since.

### A returned payout's money goes back to the club's Stripe balance

- **[DOCS]** Payout object, `failure_balance_transaction`: "If the payout fails or cancels, this is the ID of the
  balance transaction that reverses the initial balance transaction and returns the funds from the failed payout back
  in your balance." `failure_code` values include `account_closed`, `account_frozen`, `bank_account_restricted`,
  `bank_account_unusable`, `could_not_process`, `declined` ("Please contact the bank before retrying").
  [Stripe API: The Payout object](https://docs.stripe.com/api/payouts/object) — read 2026-10-08

### On manual payouts nothing says Stripe sends it again

- **[DOCS]** With the interval set to `manual`, "we hold funds in the account holder's balance until you specify
  otherwise. You must pay out the funds within" 90 days (all countries but Thailand and the US).
  [Stripe: Using manual payouts](https://docs.stripe.com/connect/manual-payouts) — read 2026-10-08
- **[ABSENT]** Any Stripe statement that a failed **manual** payout is re-sent by Stripe: the retry sentence above
  speaks only of "the next scheduled payout interval"; searched docs.stripe.com `payouts`, `connect/manual-payouts`,
  `connect/payouts-connected-accounts`, the Payout API object, and support.stripe.com — read 2026-10-08
  - *Reading:* when Rakieta asked for the payout itself, the money lands back in the
    club's balance and stays there until someone asks for a payout again — or until a later automatic payout sweeps
    it, if the account is on a schedule.

### The failed bank account is switched off until the account holder changes it

- **[DOCS]** "`failed`: … When a payout fails, the external account involved is disabled and can't receive payouts
  until the platform updates the connected account's external account details"; "For connected accounts with access
  to the full Stripe Dashboard or Express Dashboard, the account holder manages their external payout accounts."
  [Stripe: Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — read 2026-10-08
  - *Reading:* for a Rakieta club (full Dashboard) the fix is the club's own: Rakieta cannot change its bank account,
    only tell it.

### A failed payout shows in Stripe's report only on an automatic schedule

- **[DOCS]** The payout reconciliation report's "**Failed payouts** section provides a breakdown of failed automatic
  payouts", and the report "is only available for users with **automatic payouts** enabled, or a platform on manual
  payouts whose Connected Accounts have automatic payouts enabled." [Stripe: Payout reconciliation report](https://docs.stripe.com/reports/payout-reconciliation)
  — read 2026-10-08

---

## 2. Which inbox Stripe's emails reach (R-CLUBMONEY-8, R-CLUBMONEY-20)

### Stripe writes to the club's own account users, directly

- **[DOCS]** "Yes, Stripe will still notify the individual Standard or Express connected accounts directly"; the
  platform's own copies are "enabled by default for Admins and Connect Risk Analysts" of the platform.
  [Stripe support: Emails for connected account onboarding and risk requirements FAQ](https://support.stripe.com/questions/emails-for-connected-account-onboarding-and-risk-requirements-faq)
  — read 2026-10-08
- **[DOCS]** A payout that comes back: "you're notified by email and in the Dashboard" — see
  `gaps-EMAIL.md#stripe-emails-the-account-holder-when-a-payout-comes-back-up-to-5-business-days-later`.
- **[DOCS]** Stripe's Connect email settings list each category with the accounts it reaches, "for example: 'Applies to
  12 connected accounts who use the Express Dashboard.'" The recipients CSV has the columns "Email Address" and "User
  has claimed primary user email address". [Stripe: Connected account email configuration](https://docs.stripe.com/connect/account-emails-config)
  — read 2026-10-08
- **[DOCS]** v1 Account `email`: "An email address associated with the account. It's not used for authentication";
  v2 `contact_email`: "The primary contact email address for the Account." [Stripe API: Account](https://docs.stripe.com/api/accounts/object),
  [Stripe API v2: Account](https://docs.stripe.com/api/v2/core/accounts/object) — read 2026-10-08

### Each Dashboard user picks their own notices, and payouts are not in the published list

- **[DOCS]** "You can configure email notifications under **Communication preferences** … on a per-user basis. If
  your team members also want to receive notifications, they must customize their own settings." The published list:
  a successful payment, an application fee collected, a dispute, an elevated-risk payment, a mention, a wrong invoice
  amount, a failed webhook delivery — "For a full list of notification events, go to your **Communication
  preferences**." [Stripe: Teams — Receive email notifications](https://docs.stripe.com/get-started/account/teams)
  — read 2026-10-08
- **[DOCS]** The same list in support: payments, disputes, elevated risk, application fees, connected-account risk
  requirements (platforms), mentions; "Team members can enable or disable notifications in their user settings."
  [Stripe support: Set up account email notifications](https://support.stripe.com/questions/set-up-account-email-notifications)
  — read 2026-10-08
- **[ABSENT]** Which of a club's Stripe users receives a payout-failure or a requirements email (the owner who
  onboarded, every Administrator, or the account's contact email): not in the pages above, the roles page
  ([Stripe: User roles](https://docs.stripe.com/get-started/account/teams/roles)) or the FAQ — read 2026-10-08
  - *Reading:* the person who completed Stripe's onboarding for the club holds the Stripe login, so the email reaches
    that person's inbox — often the owner, not the desk — unless the club invites the desk as a team member.

### Rakieta cannot rebrand or redirect a full-Dashboard club's requirement emails

- **[DOCS]** On the requirement emails Stripe sends Standard or Express accounts: "We don't currently support
  customization." [Stripe support FAQ](https://support.stripe.com/questions/emails-for-connected-account-onboarding-and-risk-requirements-faq)
  — read 2026-10-08
- **[DOCS]** The co-branded, platform-customised emails (business name, logo, colours, sending domain, links to the
  platform's own pages) are written for embedded integrations, where "Stripe sends email communications directly to
  them. Those emails direct your connected accounts to embedded components on your website." [Stripe: Email
  communications in embedded Connect integrations](https://docs.stripe.com/connect/embedded-comms) — read 2026-10-08
- **[DOCS]** With platform controls, branding reaches the club's **Dashboard**, not its email: "All new accounts
  onboarding to your platform see your icon and branding color in their Dashboard."
  [Stripe: Platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts) —
  read 2026-10-08

### Rakieta's own admins hear when a club is about to lose payments or payouts

- **[DOCS]** "Platforms can receive email notifications before, or immediately when, capabilities degrade for their
  connected accounts": near-immediate for an action that immediately degrades a capability, a daily batch for those
  after a grace period. [Stripe support FAQ](https://support.stripe.com/questions/emails-for-connected-account-onboarding-and-risk-requirements-faq)
  — read 2026-10-08; the role list includes "Receive email notifications for connected account rejections and risk
  requirements that are upcoming, due, or past due". [Stripe: User roles](https://docs.stripe.com/get-started/account/teams/roles)
  — read 2026-10-08

---

## 3. What a full-Dashboard club opens (R-CLUBMONEY-25)

### A full-Dashboard club signs in at dashboard.stripe.com; login links exist only for Express

- **[DOCS]** "Your connected accounts have access to the Stripe Dashboard after they've completed onboarding. Consider
  linking to the [Dashboard](https://dashboard.stripe.com) from your application." [Stripe: Stripe Dashboard for
  connected accounts](https://docs.stripe.com/connect/stripe-dashboard) — read 2026-10-08
- **[DOCS]** "**You can only create login links for accounts that use the Express Dashboard** and are connected to your
  platform." [Stripe API: Create a login link](https://docs.stripe.com/api/accounts/login_link/create) — read
  2026-10-08
- **[DOCS]** For a club under platform controls: "There are no changes to your Stripe login or access."
  [Stripe support: Platform controls for connected accounts](https://support.stripe.com/questions/platform-controls-for-connected-accounts)
  — read 2026-10-08
  - *Reading:* one address for every club, opened with the club's own Stripe login, is what Stripe itself recommends
    for this account type.

---

## 4. The real fee, and which charges a payout carried (R-CLUBMONEY-13, R-CLUBMONEY-24)

### The fee is on the charge's balance transaction, which may arrive after the capture

- **[DOCS]** "You can check a payment's processing fees after the payment processes and Stripe creates the balance
  transaction. The `charge.updated` event references the `balance_transaction` property … indicating that it's ready
  to use." "A PaymentIntent must be captured and have a status of `succeeded` for the Stripe fees to be available."
  With `automatic_async` ("the default `capture_method` since version `2024-04-10`") "The `balance_transaction` field
  on the Charge object might be `null` immediately after confirmation"; "You can listen for the `charge.updated` event
  to know when the balance transaction becomes available." [Stripe: Use cases for expanding responses — See the Stripe
  fee for a given payment](https://docs.stripe.com/expand/use-cases) — read 2026-10-08
- **[DOCS]** Balance transaction: `fee` "Fees … paid for this transaction"; `fee_details` "Detailed breakdown of fees";
  `net` = amount − fee. [Stripe API: Balance transaction](https://docs.stripe.com/api/balance_transactions/object) —
  read 2026-10-08
- **[DOCS]** "*IC+ users* … can't retrieve payment fee information from the balance transaction." [same page](https://docs.stripe.com/expand/use-cases)
  — read 2026-10-08
  - *Reading:* the actual fee is readable per charge on the club's account; a reader that looks only at the capture
    response will often find no balance transaction yet, and must read it again on `charge.updated`.

### Stripe lists a payout's charges only for automatic payouts

- **[DOCS]** Payout `reconciliation_status`: `completed` — "you can use the Balance Transactions API to list all balance
  transactions that are paid out in this payout"; `not_applicable` — "We don't support listing Balance Transactions for
  this payout. We only support this for standard automatic payouts." [Stripe API: The Payout object](https://docs.stripe.com/api/payouts/object)
  — read 2026-10-08
- **[DOCS]** "You control the timing and amount of manual payouts, so Stripe can't identify which transactions are
  included in each payout. You're responsible for reconciling payouts you create against your transaction history."
  [Stripe: Payout reconciliation](https://docs.stripe.com/payouts/reconciliation) — read 2026-10-08
- **[DOCS]** The payout reconciliation report's **Itemized** CSV lists "every payment, refund, dispute, fee, and other
  balance transaction included in the payout", with `fee`, `automatic_payout_id` and, for Connect,
  `connected_account_direct_charge_id`; on manual payouts Stripe points to the Balance report instead. [Stripe: Payout
  reconciliation report](https://docs.stripe.com/reports/payout-reconciliation) — read 2026-10-08
  - *Reading:* a payout Rakieta creates itself is one Stripe cannot itemise; the link between a payout and its games
    exists only if Rakieta keeps it (the club's statement shows a lump sum).

### Przelewy24 lists each payout package's transactions and the refunds taken off it (status quo)

- **[DOCS]** "W Historii wypłat istnieje możliwość podejrzenia wszystkich wygenerowanych do wysyłki na rachunek paczek.
  Po kliknięciu numeru paczki otworzą się wszystkie transakcje wysłane tą paczką. Jeśli pole Zwroty ma wartość
  dodatnią to oznacza to, że ta konkretna paczka została pomniejszona o wartość zleconego zwrotu."
  [Przelewy24: instrukcja obsługi panelu, p. 18](https://www.przelewy24.pl/storage/app/media/do-pobrania/rozpoczecie_wspolpracy/instrukcja_obslugi_panelu_transakcyjnego_pl.pdf)
  — read 2026-10-08
- **[DOCS]** The API's `report/batch/details` "returns all transactions and refunds paid in the specified batch";
  each transaction carries `batchId`, "Batch number in which the transaction was settled".
  [Przelewy24 REST API](https://developers.przelewy24.pl/index.php?en) — read 2026-10-08

### tenis4U lets a club download a period report and plug in its own Przelewy24 account (status quo)

- **[POLICY]** The club panel ships "Konfiguracja Przelewy24 — Używaj dedykowanej konfiguracji dla tego kortu" with the
  fields "Client ID", "CRC Key", "Raport Key"; and a report screen "Początek okresu / Koniec okresu — Cały obiekt /
  Stanowisko / Gracz — Pobierz raport". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js)
  — read 2026-10-08

---

## 5. A payout Rakieta asks of Stripe (R-CLUBMONEY-19)

### A payout above the available balance is refused with `balance_insufficient`

- **[DOCS]** "Your Stripe balance must cover the payout amount. If it doesn't, you receive an 'Insufficient Funds'
  error." [Stripe API: Create a payout](https://docs.stripe.com/api/payouts/create) — read 2026-10-08
- **[DOCS]** `balance_insufficient`: "Stripe can't complete this operation because the associated account doesn't have
  enough available balance. For transfers and payouts, use an amount less than or equal to the account's available
  balance." `payouts_not_allowed`: "Payouts have been disabled on the connected account."
  [Stripe: Error codes](https://docs.stripe.com/error-codes) — read 2026-10-08
- **[DOCS]** "You can't create payouts for greater than the aggregate available balance."
  [Stripe: Using manual payouts](https://docs.stripe.com/connect/manual-payouts) — read 2026-10-08

### A platform may pay out a full-Dashboard account only through platform controls, which new accounts have

- **[DOCS]** "To schedule automatic payouts or perform manual payouts for an account that has access to the full
  Stripe Dashboard, the platform must configure Platform controls for the account."
  [Stripe: Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — read 2026-10-08
- **[DOCS]** Platform controls are for accounts "relying on Stripe to manage onboarding, reporting, and loss
  liability"; with them "You can also initiate payouts on behalf of your connected accounts programmatically"; but
  "Connected accounts can still make manual payouts after you … restrict connected accounts from updating their own
  payout schedule" — full control means contacting Stripe. [Stripe: Platform controls](https://docs.stripe.com/connect/platform-controls-for-stripe-dashboard-accounts)
  — read 2026-10-08
- **[DOCS]** "Newly-created connected accounts on Stripe have platform controls enabled"; the platform may act by
  "Creating new payouts on your behalf" and "Updating your account's payout schedule".
  [Stripe support: Platform controls for connected accounts](https://support.stripe.com/questions/platform-controls-for-connected-accounts)
  — read 2026-10-08
- **[DOCS]** Without them: `not_allowed_on_standard_account` — "Transfers and payouts on behalf of a Standard
  connected account aren't allowed." [Stripe: Error codes](https://docs.stripe.com/error-codes) — read 2026-10-08

### Not found: a platform payout while the account stays on an automatic schedule

- **[DOCS]** The `manual` interval "prevents automatic payouts. You'll have to manually pay out the account's balance
  using the Payouts API". [Stripe: Manage payout schedule](https://docs.stripe.com/connect/manage-payout-schedule) —
  read 2026-10-08
- **[ABSENT]** Whether Stripe accepts a payout created by the platform while the club's account is on Stripe's
  automatic daily schedule, and what happens when both draw on the same balance: not in `payouts`,
  `connect/manual-payouts`, `connect/manage-payout-schedule`, the Payout API pages, or support.stripe.com
  ("Understanding daily, automatic, and manual payout schedules") — read 2026-10-08

---

## 6. A partial refund soon after the charge (R-CLUBMONEY-2)

### Stripe processes a refund made shortly after the charge as a reversal, and withholds no fee on a reversal

- **[DOCS]** "Some refunds—those issued shortly after the original charge—appear in the form of a *reversal* … instead
  of a refund." Glossary: "A reversal is the cancellation of a transaction. Stripe doesn't withhold any fees for
  payment reversals." A reversal shows as `destination_details[card][type] = 'reversal'` on the refund.
  [Stripe: Refund and cancel payments — Refund and reversal](https://docs.stripe.com/refunds#refund-and-reversal),
  [Stripe glossary](https://docs.stripe.com/glossary) — read 2026-10-08
- **[DOCS]** Otherwise: "For all refunds, payment processing, Connect, and currency conversion fees from the original
  charge are not returned." [Stripe support: Understanding fees for refunded payments](https://support.stripe.com/questions/understanding-fees-for-refunded-payments)
  — read 2026-10-08

### A partial refund can be a partial reversal

- **[DOCS]** "A partial refund made soon after the original charge can be processed as a partial reversal. The
  original charge will be replaced with a lower amount on the customer's bank statement instead of a separate line
  item refund." [Stripe support: Where is my customer's refund?](https://support.stripe.com/questions/no-refund-credit-on-customer-statement-after-ten-business-days)
  — read 2026-10-08

### No published window, and nothing on the fee of a partial reversal

- **[ABSENT]** How soon is "shortly after": no hour or day in Stripe's refunds page, glossary or support — read
  2026-10-08. A US practice-management platform built on Stripe tells its users a reversal works "on the same day
  before the batch is sent for the day (currently 8 pm EST)" — **[POLICY]** third party, not Stripe.
  [DrChrono: Stripe Refunds and Reversals](https://support.drchrono.com/home/18415644438939-drchrono-payments-stripe-refunds-and-reversals)
  — read 2026-10-08
- **[ABSENT]** Whether a **partial** reversal returns all of the original fee, a share, or none: the glossary line
  speaks of reversals in general; searched docs.stripe.com `refunds`, `glossary`, support.stripe.com — read 2026-10-08
- **[DOCS]** Stripe's own advice for refunds close to the payment: manual authorisation and capture, "canceling
  payments before they're captured, or … reducing your captured amount rather than processing a refund".
  [Stripe: Refunds](https://docs.stripe.com/refunds) — read 2026-10-08
  - *Reading:* a leaver's refund is a reversal only if it comes within hours of the charge, in practice on the same
    day the game filled. A leaver days later gets an ordinary refund, and the 1,60 zł fee is lost.

---

## 7. How fast Polish operators pay a Kraków club, and refunds beyond the balance (R-CLUBMONEY-14, -15, -17)

### Przelewy24: available by the end of the next business day; paid out on demand, on a schedule, or at 1000 zł

- **[DOCS]** "Środki pieniężne ze zrealizowanej Płatności Dostawca udostępnia Akceptantowi do wypłaty nie później niż
  do końca następnego Dnia Roboczego po otrzymaniu Płatności"; the merchant may opt in the panel for a later date.
  "Wypłaty realizowane są na żądanie … albo w sposób cykliczny", for example on a set weekday or once a set sum is
  reached; by default "wypłata następuje w Dniu Roboczym w którym suma udostępnionych, a dotychczas niewypłaconych
  Płatności, osiągnie lub przekroczy kwotę 1000 zł". Payouts may go "zbiorczo (w tzw. „paczkach”)". (§10 ust. 6–8)
  [Przelewy24 OWU v2.0, from 15 May 2026](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf)
  — read 2026-10-08
- **[PRICE]** First four payouts a month to a Polish bank 0 zł, each further one 0,99 zł; refunds 0 zł (Annex 4, Tabela opłat 3).
  [same OWU](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf) — read 2026-10-08
- **[DOCS]** "Zwrot Płatności … nie stanowi podstawy do zwrotu przez Przelewy24 opłat, prowizji" (§10 ust. 13) — the
  commission is kept on a refund. [same OWU](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf)
  — read 2026-10-08

### Tpay: available by the end of the next business day; paid out automatically every day; arrives within 3 business days

- **[DOCS]** "KIP umożliwia dostęp do środków … nie później niż do końca następnego dnia roboczego"; "Wypłaty …
  realizowane są po pozytywnej weryfikacji … w sposób zautomatyzowany każdego dnia … po zgromadzeniu minimalnej kwoty";
  they may also follow the merchant's own schedule or threshold; Tpay transfers the money "w czasie nie dłuższym niż 3
  dni robocze" from the instruction. (§7 ust. 1–4) [Tpay OWU, in force 24 March / 8 April 2026](https://tpay.com/user/assets/files_for_download/owu.pdf)
  — read 2026-10-08

### PayU: automatic payouts at a frequency and minimum the shop sets

- **[DOCS]** "You can also turn on automatic payouts … enable automatic payouts, specify the minimum payout amount, and
  schedule the frequency of payouts, determining the number of days after which payouts will be processed"; "each Shop
  has a seperate balance". [PayU: Payouts via Panel](https://developers.payu.com/europe/docs/payouts/payouts-panel/)
  — read 2026-10-08
- **[DOCS]** Payout dates are set in the commercial terms; below a minimum PayU may hold a payout to the next date.
  (art. 5.1, 5.5) [PayU merchant agreement v. 2020-04-10](https://poland.payu.com/wp-content/uploads/sites/14/2020/09/umowa_z_akceptantem.pdf)
  — read 2026-10-08
- **[COMPLAINT]** Allegro sellers: PayU has "czas do końca następnego dnia roboczego od zleceniu wypłaty".
  [Allegro community: Wypłata z PayU](https://spolecznosc.allegro.pl/t5/pocz%C4%85tkuj%C4%85cy-sprzedawcy/wyp%C5%82ata-z-payu/m-p/137389)
  — read 2026-10-08

### A refund larger than the balance is refused by all three

- **[DOCS]** Przelewy24: "Zwrot można zlecić na każdej transakcji Dokonanej pod warunkiem, że saldo konta nie jest
  mniejsze niż wartość zlecanego zwrotu" ([panel manual, p. 12](https://www.przelewy24.pl/storage/app/media/do-pobrania/rozpoczecie_wspolpracy/instrukcja_obslugi_panelu_transakcyjnego_pl.pdf));
  the refund API answers "`Insufficient funds available` - insufficient funds are available to process the refund"
  ([Przelewy24 REST API](https://developers.przelewy24.pl/index.php?en)) — read 2026-10-08
- **[DOCS]** Tpay executes a refund "w czasie nie dłuższym niż 7 dni roboczych … pod warunkiem: wystarczającego salda na
  pokrycie kwoty zwracanej Transakcji i opłaty za zwrot"; otherwise it "może cofnąć dyspozycję zwrotu"; "prowizja
  Spółki nie podlega zwrotowi". (§7 ust. 7) [Tpay OWU](https://tpay.com/user/assets/files_for_download/owu.pdf); "Jeżeli
  środki nie są dostępne na koncie Sprzedawcy w Tpay, nie będzie on miał możliwości wykonania zwrotu."
  [Tpay support](https://support.tpay.com/faq/czy-jest-mozliwosc-wykonana-zwrotow-bezposrednio-z-konta-tpay-com-do-osob-ktore-dokonaly-platnosci)
  — read 2026-10-08
- **[DOCS]** PayU's refund API error `NO_BALANCE` (9102) "Lack of funds in account."
  [PayU: Refunds](https://developers.payu.com/europe/docs/payment-flows/refunds/) — read 2026-10-08

### PayU and Przelewy24 set a shortfall against later payouts, or ask for it

- **[DOCS]** PayU keeps refunds, chargebacks and fees from what it owes; "Jeśli wartość Opłat i kwot … przekroczy łączną
  wartość Wypłaty … pozostała brakująca kwota może zostać potrącona … w następnych Terminach Wypłaty", and PayU may
  demand it at once. (art. 5.3–5.4) [PayU merchant agreement v. 2020-04-10](https://poland.payu.com/wp-content/uploads/sites/14/2020/09/umowa_z_akceptantem.pdf)
  — read 2026-10-08
- **[DOCS]** Przelewy24 sets its dues off against payments it owes; "Jeśli wierzytelność Przelewy24 wobec Akceptanta jest
  wyższa … Przelewy24 może wezwać Akceptanta do zapłaty", also by an amount on its VAT invoice. (§11 ust. 4–5)
  [Przelewy24 OWU v2.0](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf) — read
  2026-10-08
  - *Reading:* a Kraków club on Przelewy24 or Tpay today has each court's money the next business day after the
    booking, days before the game, and pays out daily or at a threshold; a refund owed later needs money still in the
    balance, or it fails. Paying after the game, as Rakieta does, is slower than the status quo but never meets that
    failure.

---

## 8. While documents are checked, or the account is blocked (R-CLUBMONEY-5, R-CLUBMONEY-8)

### Tpay: no payments until verified, and the verification is confirmed by email

- **[DOCS]** "Umowa ramowa zostaje zawarta po pozytywnej weryfikacji Akceptanta … z chwilą potwierdzenia pozytywnej
  weryfikacji przez Spółkę drogą mailową"; "Usługi płatnicze … świadczone są po pozytywnej weryfikacji"; verification
  includes an activation fee paid from the payout account. Tpay "może wstrzymać dokonywanie wypłat" on reasonable doubts
  about identity, and may block panel access or freeze funds on suspicion. (§3 ust. 2–3, 6; §9 ust. 1–2)
  [Tpay OWU](https://tpay.com/user/assets/files_for_download/owu.pdf) — read 2026-10-08

### Przelewy24: the contract starts only after verification; later requests come by email; outdated documents block the account

- **[DOCS]** The contract enters into force only once the merchant passes the verification procedure and makes the
  verification transfer, and "Przelewy24 powiadomi Akceptanta niezwłocznie o spełnieniu warunków zawieszających"; in
  listed cases Przelewy24 may "bez uprzedniego powiadomienia wstrzymać natychmiastowo przyjmowanie … Płatności, w tym
  ze skutkiem wstrzymania wszystkich wypłat". (§3 ust. 6–8; §5 ust. 8) [Przelewy24 OWU v2.0](https://www.przelewy24.pl/storage/app/media/owu/przelewy24/owu-przelewy24-v.2.0.pdf)
  — read 2026-10-08
- **[DOCS]** A request for documents comes by email (its authenticity can be checked at merchant.service@przelewy24.pl);
  "It is possible to attach filled-out forms as well as the scan of the ID directly in the client's panel."
  [P24 help](https://www.przelewy24.pl/en/help-center/i-sell-with-przelewy24/periodic-data-update/how-do-i-know-if-the-request-for-the-submission-of-documents-has-been-sent-by-przelewy24)
  — read 2026-10-08
- **[DOCS]** "If the documents are invalid, we are obligated to prevent our Partner from using our service by blocking
  their account … once the documents are verified, we will be able to unblock the account"; updates are handled "in the
  order that the documents are uploaded in the Panel", with no stated time.
  [P24 help: account blocked](https://www.przelewy24.pl/en/help-center/i-sell-with-przelewy24/periodic-data-update/my-account-is-blocked-because-my-details-are-out-of-date-how-can-i-unblock-it),
  [P24 help: how long](https://www.przelewy24.pl/en/help-center/i-sell-with-przelewy24/periodic-data-update/how-long-does-the-update-process-take-once-the-documents-are-delivered)
  — read 2026-10-08

### Not found: the screens a club sees while checked or restricted

- **[ABSENT]** What Playtomic Manager shows a club while its Stripe documents are checked or once its account is
  restricted: not in the 157 club help articles (`competitor-club.md#stripe-onboarding-through-playtomic`), nor in a web
  search for Playtomic Manager with Stripe verification or restriction — read 2026-10-08
- **[ABSENT]** The panel text Przelewy24 or Tpay show during verification or a block: not in P24's 24-page panel manual,
  its 11 "periodic data update" help articles, or Tpay's support FAQ — read 2026-10-08

---

## 9. What a Kraków club gives a player who paid online (R-CLUBMONEY-26)

### The payment operator emails the payer a confirmation

- **[DOCS]** Przelewy24: "Osoby wykonujące płatności przez Serwis Przelewy24 wyrażają zgodę na otrzymanie potwierdzenia
  dokonania Płatności w formie maila. Serwis zobligowany jest przepisami prawa do wysyłki tej informacji."
  [Przelewy24 Regulamin](https://www.przelewy24.pl/regulamin) — read 2026-10-08
- **[DOCS]** Tpay: "The Payer shall be informed of the initiation of the Payment Order and of the execution of the
  Payment by means of an electronic message … and by electronic mail to previously indicated address."
  [Tpay terms for payers, in force 20 April 2021](https://tpay.com/user/assets/files_for_download/terms-and-conditions-of-payments.pdf)
  — read 2026-10-08

### The club confirms the booking itself, by SMS or in its app

- **[POLICY]** Miazga: "Potwierdzeniem zrobienia rezerwacji telefonicznej, internetowej lub przez recepcję jest
  wiadomość SMS wysłana z systemu"; in the app, the booking appearing under Rezerwacje/Nadchodzące.
  [Miazga regulamin](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Fame Sport, for an extra event bought in its app and paid through Stripe: "Gdy proces płatności przebiegnie poprawnie, Użytkownik otrzyma
  wiadomość mailową z potwierdzeniem." [Fame Sport regulamin](https://famesport.pl/regulamin) — read 2026-10-08

### An invoice on request, by email with proof of payment

- **[POLICY]** AGH Sports Hall, Kraków (booked through Reservise, paid online through PayU): "Za wniesioną opłatę klient
  może otrzymać fakturę. Chcąc otrzymać fakturę należy wysłać na adres squash-rezerwacja@agh.edu.pl swoje imię,
  nazwisko, adres wraz z kodem pocztowym oraz potwierdzenie dokonania przelewu." In force from 1 Sept 2026.
  [Regulamin kortów do squasha Hali Sportowej AGH](https://swfis.agh.edu.pl/home/swfis/dokumenty/REGULAMIN_KORZYSTANIA_Z_KORTU_DO_SQUASHA.pdf)
  — read 2026-10-08
- **[ABSENT]** Any mention of a receipt (paragon), an invoice (faktura) or a payment confirmation in the rules of Garden
  Padel, Atras, Squash4You or tenis4U's terms (each fetched and searched for "paragon", "faktur", "potwierdzen") — read
  2026-10-08

### Playmore keeps a player's invoice details on the account

- **[POLICY]** Playmore's web app account menu: "Dane do faktury — Zarządzaj danymi do faktury dla rezerwacji i
  zakupów"; also "Rozliczenia — Przeglądaj i opłacaj zaległe rozliczenia za rezerwacje", "Eksport danych".
  [Playmore web bundle](https://playmore.pl/assets/CccZ1mLc.js) — read 2026-10-08

### tenis4U's player app ships no receipt or invoice

- **[ABSENT]** Any receipt, invoice or tax-number field in tenis4U's player web app: its bundle (4,1 MB, decoded) has no
  "faktur", "paragon", "NIP", "receipt" or "invoice"; payment goes by redirect to Przelewy24 (`PaymentPrzelewy24`).
  [tenis4U player app bundle](https://app.tenis4u.pl/main.cf446af5e9523413.js) — read 2026-10-08
  - *Reading:* today a Kraków player who prepays online gets the operator's emailed payment confirmation and the club's
    booking SMS or app entry; a fiscal receipt is not issued for a fully online payment, and an invoice comes only by
    asking the club, by email, with proof of payment.

### Not found: how often an organiser needs one company invoice for the whole court

- **[ABSENT]** Any count, survey or forum thread on organisers asking a club for one company invoice for a shared court:
  searched Polish web and tax forums ("faktura na firmę za wynajem kortu", "zrzutka na kort faktura"), the Allegro and
  Reddit results, and the clubs' rules above — read 2026-10-08

### Not found: a tax ruling on the cash-register exemption for sales taken by Stripe Connect

- **[ABSENT]** A KIS ruling on a service paid through Stripe (Connect or otherwise) to the seller: Eureka's public search
  API (`/api/public/v1/wyszukiwarka/informacje`), full phrase "Stripe" in content — 151 rulings; the five that touch the
  cash register concern goods shipped from outside the EU under IOSS (0114-KDIP1-2.4012.153.2022.1.RD,
  0113-KDIPT1-2.4012.1175.2025.2.AB, 0113-KDIPT1-2.4012.181.2026.2.AB) or a 2018 deposit case
  (0114-KDIP1-3.4012.270.2018.2.KC); full phrase "Stripe Connect" —
  0 rulings — read 2026-10-08. The closest precedents stay those in
  `local-market.md#no-cash-register-for-sales-paid-fully-online` and
  `gaps-EMAIL.md#the-exemption-turns-on-the-clubs-records-not-on-the-email`.
