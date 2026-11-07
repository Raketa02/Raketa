# Payments gaps 06 — CLUBBOOK and SECURITY

Answers to the market gaps the payments-pass Moderator left on **R-CLUBBOOK-24** and **R-SECURITY-4, -13, -15,
-20, -22, -23, -26**. Written 2026-10-20. Each gap is a `###` heading naming its rule ID.

**Sources this round.** Rivals' help centres, terms and sign-up pages, and the login/sign-up pages their sites serve
to every visitor (read, not signed into); Stripe, Visa and MATCHi documents; app-store pages; web, forum and Reddit
searches. Facts already in this folder are cited by anchor, not repeated. Kinds: `[POLICY]` the company's own
rule/help/interface text · `[DOCS]` a provider's document · `[MEASURED]` what a served page showed, dated ·
`[ABSENT]` looked for and not found, with where. Lines marked *reading* are not sources.

---

### R-CLUBBOOK-24 — How soon a Polish bank's app drops a hold Raketa let go: unpublished, and the email can only say so

**Already answered in this folder.** The grade can rest on these.

- **[ABSENT]** No Polish bank publishes a minutes-or-hours figure for how long a *cancelled* hold keeps showing in its
  app. Searched again across PKO BP, ING, Pekao, Erste (ex-Santander) and Millennium terms, FAQs and help, plus
  forums and Reddit; only mBank says the shop's cancellation lifts the hold, with no delay given —
  `topics/gaps-S-01A-hold.md#how-soon-each-polish-banks-app-drops-a-cancelled-hold-still-unpublished`,
  `topics/gaps-EMAIL.md#mbank-drops-a-hold-when-the-shops-cancellation-arrives-else-after-14-days-online`.
- **[DOCS]** Stripe: on a reversal "the original charge drops off the customer's statement, and a separate credit
  isn't issued"; some banks update available balances instantly, others take "a bit longer", a delay that "reflects
  bank processing cycles, not business decisions"
  (`topics/gaps-S-01B.md#a-cancelled-hold-drops-off-the-statement-how-soon-each-banks-app-shows-that-is-still-unpublished`,
  `topics/gaps-S-01A-hold.md` §1 *Stripe: some banks update the balance at once, others later*).
- **[DOCS]** Visa: a reversal that matches tells the issuer to lift the hold "as quickly as possible"; one the issuer
  cannot match leaves the funds 1 to 8 days (`topics/gaps-S-01A-hold.md` §1, Visa *Authorization Reversals*). The only
  named end-to-end figure anywhere is MATCHi's (Adyen, Nordic markets, none in Poland): released "within 24 hours …
  entirely on your bank's side" (`topics/gaps-S-01A-hold.md` §1, MATCHi).

*Reading:* because no Polish bank states the time, the cancel email cannot promise one. The honest wording is what the
market's own documents say: the hold has been released, it will clear on the bank's own cycle, and that can take from
seconds to a few days — never a Raketa-set deadline. The grade's missing fact (a published Polish release time) is
settled as genuinely absent, which is itself the answer.

### R-SECURITY-22 — No Kraków rival publishes a login lockout, a CAPTCHA, or a new-sign-in / password-change email (covers both gap lines)

The gap asks two things: whether Playtomic, Playtomic Manager, Playmore's desk panel, tenis4U or kluby.org lock, slow
or CAPTCHA after wrong passwords, and whether any Kraków club system emails the club on a new sign-in or a password
change. Both resolve to the same finding.

- **[POLICY]** None of the rivals documents a second factor or a lockout for staff sign-in. Playmore Manager's login
  is email + password + "Zapamiętaj mnie" + a reset link + a magic link, no second factor; Playtomic Manager has no
  2FA in its help centre and its password-reset links expire after an hour; MATCHi's security page claims "strong
  password policies and multi-factor authentication (MFA)" without saying venue admins use it; tenis4U and kluby.org
  name no second factor
  (`../../club-software/customers-staff-and-messages.md` §13.8, read 2026-10-12).
- **[MEASURED]** 2026-10-20: the served login pages of Playtomic Manager (`manager.playtomic.io/auth/login`), Playmore
  Manager (`manager.playmore.pl`) and the tenis4U panel (`panel.tenis4u.pl`) carry no CAPTCHA widget, and no visible
  lockout or new-device notice. Playtomic Manager's and Playmore Manager's pages hold no reCAPTCHA / hCaptcha /
  Turnstile reference at all; tenis4U's panel is a Polish single-page app that merely holds generic "locked" / 429
  strings, not a published policy.
- **[ABSENT]** Whether any of them *actually* locks, slows or CAPTCHAs after repeated wrong passwords, and whether any
  emails the account on a new sign-in or a password change, is published nowhere: not in Playtomic's or MATCHi's help
  centres (searched for 2FA, login, password, security), not in Playmore's, tenis4U's or kluby.org's help or terms.
  Measuring it would need wrong-password attempts on real accounts at each rival, which this round cannot do.

*Reading:* the grade's missing fact resolves to parity by absence. No Kraków rival advertises any of these protections,
and the players' status quo (WhatsApp + a club desk) has no account login that moves money at all. So Raketa having no
published lockout / CAPTCHA / sign-in alert is level with the market (=), and the club's provisional "?" can settle on
that. The positive facts (an actual lockout threshold, a sign-in email) stay **not found** — unmeasurable without
accounts — but the grade no longer depends on them.

### R-SECURITY-15 — Raketa's way back from the bank is documented; the real-Android misroute and the rivals' flow stay device-gated

- **Raketa's own mechanism is answered.** The React Native SDK sets the 3-D Secure return to the custom scheme
  `raketa://safepay`; a `Linking` listener hands the incoming address to Stripe only while a confirmation is running,
  and the router ignores any address it does not know — so a stray or misrouted return lands nowhere rather than into
  another screen. Universal (https) links are not supported by the SDK version in the app
  (`topics/stripe-authentication.md#the-way-back-from-the-banks-own-app`,
  `topics/stripe-gaps-07.md` R-SECURITY-15).
- **[ABSENT]** Whether the mobile return, as opposed to the web redirect, actually carries `payment_intent` and
  `payment_intent_client_secret`, and whether the hand-back misroutes on a real Android phone, is not on Stripe's
  pages and can only be seen on a device with a challenge card (`topics/stripe-gaps-07.md` R-SECURITY-15,
  marked *unverified*). This is a device-walk item, not a market fact.
- **[ABSENT]** How Playtomic's and Playmore's own apps bring a player back after the bank's check is published
  nowhere. Their help centres and terms say nothing about 3-D Secure (`topics/competitor-joiner.md#3-d-secure-and-failed-payments`,
  `topics/competitor-newcomer.md`). A web search for Playtomic's Android 3DS return turned up only the generic pattern
  that mobile SDKs (Braintree, PayPal, Adyen) use a custom-scheme or App-Links return — not Playtomic's or Playmore's
  actual behaviour. Reachable only by driving their apps on a device with a challenge card.

*Reading:* the grade-bearing half — can a misrouted return leak or confuse Raketa — is answered: the listener is
scoped to an in-flight confirmation and unknown addresses are dropped. The device-level and competitor comparisons
remain **not found**, both gated on a real Android phone.

### R-SECURITY-4 — No published case of a club platform leaving clubs unpaid because it ran on test money

- **[ABSENT]** Searched for any account of a court / club booking platform that left clubs unpaid because it was
  running on test keys or in test mode: Playtomic + Stripe "clubs not paid", generic "booking platform test mode
  clubs unpaid". Nothing. What the market does publish is the opposite guard: Playtomic makes each club create its own
  Stripe account and pass KYC before it can receive transfers, and pays manually when automatic payout "has an issue"
  ([Playtomic: Online payments with Stripe](https://helpmanager.playtomic.com/hc/en-gb/articles/20535417606161),
  [Payout cycle for clubs](https://helpmanager.playtomic.com/hc/en-gb/articles/37355604106129), read 2026-10-20); and
  Stripe's own Unacceptable Risk Policy holds a restricted user's payouts 120 days
  ([Stripe](https://stripe.com/legal/unacceptable-risk-policy), read 2026-10-20) — restrictions, not a test-money
  mix-up.
- The test/live-key facet for Raketa itself is already a **code** matter, not a market one: a live key accepted where
  a test key belongs (or the reverse) is a SECURITY family attack, and a deployed server refusing test keys is a
  product rule (`topics/stripe-gaps-07.md` R-SECURITY-4 on key shape and the organisation-key `Stripe-Context`;
  SECURITY area digest). No market precedent bears on it.

*Reading:* the gap's missing fact (a real case) is settled as genuinely absent, so the club's "?" rests on Raketa's own
code rule that a deployed server must run on live keys, not on any market comparator.

### R-SECURITY-13 — No gateway publishes a per-payment card-try cap, and no Kraków club card-testing case was found

- **Stripe's side is already answered:** on the sandbox a PaymentIntent cancels after ten declined confirmations, and
  a direct charge is screened by the club's own Radar; the platform's Radar rules do not reach a full-Dashboard club
  (`topics/stripe-gaps-07.md` R-SECURITY-13 ×2).
- **[ABSENT]** Przelewy24 and Tpay publish no per-card or per-payment attempt cap for card payments. Przelewy24's
  merchant docs and FAQ describe amount limits (50 PLN–250 000 PLN) and a bank-transfer-first model, not card-attempt
  velocity (searched Przelewy24 docs / help / fraud, 2026-10-20). Tpay likewise names no published card-try limit.
- **[ABSENT]** Playtomic publishes no card-try limit per payment (its help covers payment *methods* and failed
  payments, not attempt caps).
- **[ABSENT]** No complaint or report was found of a Kraków club hit by card testing through its booking system.
  *Reading:* Kraków clubs take money mostly as bank transfers / pay-by-link through Przelewy24, Tpay or PayU rather
  than raw card entry (`topics/local-market.md#the-club-is-the-seller-the-platform-is-not-a-party`,
  `topics/gaps-S-01A-hold.md` §6), which is a bank-authenticated rail where card testing — many small card-number
  guesses — barely applies; so the local status quo has little exposure, and none is reported.

*Reading:* the gap resolves to absence on every market side. The grade rests on Stripe's documented ten-try ceiling and
the club's Radar, not on a gateway or competitor cap, and Raketa's card-entry flow is the one place in this market that
takes a raw card, so the comparison is with the gateways' bank-transfer rails rather than a like-for-like card cap.

### R-SECURITY-20 — Only Playmore's "remember me" is published; Playtomic Manager's and tenis4U's session lengths are not found

- **[POLICY]** Playmore Manager's login offers "Zapamiętaj mnie" (remember me), a persistent session the staff member
  chooses (`../../club-software/customers-staff-and-messages.md` §13.8).
- **[ABSENT]** Neither Playtomic Manager nor the tenis4U panel publishes a session length or an idle timeout. Searched
  Playtomic Manager help ("stay signed in", "session", "log out") and tenis4U panel / help ("automatyczne
  wylogowanie", "sesja", "czas logowania"), 2026-10-20 — nothing. The only comparable published figure is a different
  platform's (OpenPlay: auto sign-out after 7 days idle or 30 days absolute), which does not apply to these rivals.

*Reading:* the gap's own framing holds: the club's "=" rests on Playmore's remember-me alone, because that is the only
staff-session behaviour any Kraków rival publishes. Playtomic Manager's and tenis4U's actual session lengths stay
**not found**, measurable only by signing in and waiting.

### R-SECURITY-23 — Playtomic Manager's post-sign-in return is a same-origin relative path; it cannot be bent off-site

- **[MEASURED]** 2026-10-20, from the code `manager.playtomic.io` serves to every visitor: the login URL's
  `return_to` is assembled from the app's own router location, not from any caller-supplied address. The app takes its
  current in-app location (`pathname` + `search`), builds a relative path-and-query from it, and sets that as
  `return_to` — and only for routes the app itself navigated to (an auth-route map decides whether to append it at
  all). The value is therefore a same-origin, relative in-app path; there is no point in that flow that accepts an
  absolute external URL. A signed-out admin who opens a deep link lands on
  `…/auth/login?return_to=%2F<the in-app path>` and, after signing in, is returned to that in-app page
  (consistent with `topics/gaps-EMAIL.md#playtomic-manager-keeps-the-page-a-signed-out-admin-asked-for`).

*Answer:* **no** — as served, Playtomic Manager's return address after sign-in cannot be bent to another site; it is a
relative path within `manager.playtomic.io`, built from the router's own location rather than from input. (This is the
rival's behaviour; it sets the market bar that Raketa's own return handling meets or exceeds.)

### R-SECURITY-26 — Every rival gates a club behind a human onboarding step or payment-processor KYC; none lets a fake club self-serve into taking money

- **[MEASURED]** 2026-10-20: tenis4U's "dodaj korty" page is only a contact form — "W celu dodania kortów tenisowych
  do aplikacji tenis4U wypełnij poniższy formularz", data used "wyłącznie w celu nawiązania kontaktu". It asks for no
  NIP, KRS or document on the form itself; a club is added by tenis4U staff after contact, so a person vets the club
  before its courts go live ([tenis4u.pl/dodaj](https://tenis4u.pl/dodaj/)).
- **[MEASURED]** 2026-10-20: Playmore's sign-up / migration page (`join.playmore.pl`) is a sales-and-migration flow —
  "book a call", phone +48 452 857 244 — with no self-serve "create a live club" path; onboarding is Playmore-staff-led,
  itself a gate against a fake club self-registering.
- **[POLICY]** twojtenis.pl states club accounts need "weryfikacja działalności" (business verification)
  (`../../club-software/switching-and-business-model.md`, carried).
- **[POLICY]** Playtomic makes it "mandatory for your club to create a Stripe account" with an SMS check, a legal type,
  a registration number and address, owners "with at least 25% ownership" and an IBAN — i.e. Stripe's KYC is the
  business check before a club can take payments (`topics/competitor-club.md`, carried).
- **[ABSENT]** kluby.org publishes no self-serve registration-with-verification flow; joining is via its "oferta" /
  contact route (its feature and pricing pages answered 403/403 to a direct read, 2026-10-20). A web search surfaced no
  self-serve kluby.org club sign-up.

*Answer:* the market norm is that a club cannot self-serve straight into taking bookings and money. Every rival gates
it — tenis4U, Playmore and kluby.org by a human onboarding/contact step, Playtomic (and, by the same logic, Raketa via
Stripe Connect onboarding) by payment-processor KYC. No Kraków rival lets an unvetted fake club register itself and
immediately take payments, so the gap is answered: Raketa's Stripe-Connect onboarding gate is at or above the market
bar.
