# Gaps round: CLUBSETUP

Answers to the facts the CLUBSETUP grades needed (`$W/areas/CLUBSETUP/gaps.md`), read 2026-10-08. Each `###` heading
answers part of one gap and names its rule. Sources: Stripe's docs (read as Markdown from `docs.stripe.com/*.md`) and
support pages; Playtomic Manager's help centre (through its Zendesk API), its web app's code as shipped and the English
text files it loads (`manager.playtomic.io/locales/en/*.json`); Playtomic's player help; MATCHi's venue help centre
(Zendesk API); tenis4U's club panel as shipped (its JavaScript bundle, decoded); kluby.org's changelog 2014–2026;
Playmore's page for clubs; KSOS's pages and its statute on the City of Kraków's BIP; and the Shopify community forum.
No screenshot was taken: nothing is `[MEASURED]`. A line marked *reading* is this researcher's inference, not a source.

Kinds: `[POLICY]` a rule, term, help text or interface text the operator publishes or ships; `[DOCS]` a provider's or
regulator's documents; `[COMPLAINT]` one person's account; `[ABSENT]` looked for and not found, with where.

## 1. A club account Stripe has stopped, and refunds (R-CLUBSETUP-38)

### Stripe: a refund needs the account's available balance; short of it, a card refund waits

- **[DOCS]** "Refunds use your available Stripe balance (not including pending amounts). If your available balance
  doesn't cover the amount of the refund, Stripe holds the refund as pending for card transactions (refunds for other
  payment method types fail) until your Stripe balance becomes sufficient." A refund still pending past "the pending
  refund expiration window" fails with `insufficient_funds`. [Stripe: Refunds](https://docs.stripe.com/refunds) — read 2026-10-08
- **[DOCS]** "When charging on a connected account, a refund or chargeback comes from the connected account."
  [Stripe: Connected account balances](https://docs.stripe.com/connect/account-balances) — read 2026-10-08
- **[DOCS]** On missed requirements: "Stripe typically disables payouts on the account if we don't receive the
  information by the `current_deadline`. However, other consequences might apply". [Stripe: Handle verification updates](https://docs.stripe.com/connect/handling-api-verification) — read 2026-10-08

### The refusal message seen in the wild, with no account state attached

- **[COMPLAINT]** A merchant on the Shopify forum got "This account is not currently able to refund charges." and did
  not recognise the Stripe account it named; nothing in the thread ties it to charges being disabled (Combekk,
  2021-07-14). [Shopify Community](https://community.shopify.com/t/store-money-in-wallet-as-its-currently-empty-and-therefore-refunds-cant-take-place/52879) — read 2026-10-08

### Whether a charges-disabled account can refund: not documented, not tried

- **[ABSENT]** A Stripe statement on refunds from an account whose `charges_enabled` or `payouts_enabled` is false.
  Searched Stripe's Refunds, Account capabilities, Handle verification updates, Connected account balances, Risk
  management and Error codes pages (the error list has `charge_already_refunded`, `charge_disputed`,
  `refund_disputed_payment`, nothing for a restricted account). — read 2026-10-08
- **[ABSENT]** A test-mode trial: it needs a Stripe test key and a connected account pushed into the disabled state;
  no key was used in this round. Still open.
- *reading:* what is documented is that the refund comes out of the club's own balance and waits when that balance is
  short; so a club paid out before the refund, or one whose money is frozen, is the case to test.

## 2. What Playtomic Manager shows a live club whose Stripe account wants more (R-CLUBSETUP-11, -35, -38)

### A warning bar and a pop-up: "Your payments are about to be interrupted"

- **[POLICY]** For a club that is live (onboarding finished, club and tenant active) and whose Stripe account has
  required fields outstanding, Manager shows a warning notification and opens a dialog. Text: title "Your payments are
  about to be interrupted"; body "Your Stripe Connect Account has missing information. Solve this issue immediately,
  otherwise online payments and payouts will be interrupted."; buttons "Add missing information" (to Stripe) and "Skip
  for now". [Manager code: stripeConnect chunk](https://manager.playtomic.io/assets/stripeConnect-fr7yLnF1.js) (the
  condition `onboarding_status===FINISHED && playtomic_status===ACTIVE && tenant_status===ACTIVE && requiredFields.length>0`),
  [Manager strings: integrations](https://manager.playtomic.io/locales/en/integrations.json) — read 2026-10-08
- **[POLICY]** Playtomic's clubs hold Stripe Express accounts, and "Playtomic cannot update your personal information on
  your behalf. You are solely responsible for managing any changes". [How to update your personal details in Stripe](https://helpmanager.playtomic.com/hc/en-gb/articles/20534135185937-How-to-update-your-personal-details-in-Stripe) (updated 2026-08-31) — read 2026-10-08
- **[ABSENT]** What Manager shows once payments have actually stopped, and what happens to open matches then. Searched
  the integrations, billing, onboarding, dashboard, matches and schedule strings ("restricted", "paused", "disabled",
  "interrupted") and the 157 club help articles. — read 2026-10-08
- *reading:* Playtomic warns the desk before Stripe stops the account and says plainly that payments and payouts will
  stop; it says nothing about the games already in play.

## 3. Games still filling when a club stops selling (R-CLUBSETUP-11)

### tenis4U refuses every new booking once a club's online booking is off

- **[POLICY]** The club settings have "Kort włączony" and "Aktywacja rezerwacji"; with booking off the server refuses a
  new booking with `COURT_DISABLED`: "Nie można dodać rezerwacji gdyż kort ma wyłączoną możliwość dokonania rezerwacji
  online, aktywuj rezerwacje online" (shown even on the panel's own tournament booking form). [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

### Playtomic and MATCHi: not written

- **[POLICY]** Playtomic keeps a match whose court was released "open" "As long as the club still has an available
  court": `competitor-organiser.md#the-court-is-held-in-stages`. A cancelled subscription "does not automatically take
  your club offline": `gaps-ENGINE.md` section 2.
- **[ABSENT]** What any platform does to open games still gathering, or to bookings made, when the club stops selling
  (switch off, unpaid plan, Stripe stopped). Searched Playtomic's club help and Manager strings, MATCHi's help
  ("archive", "inactive venue"), tenis4U's panel and kluby.org's changelog. — read 2026-10-08

## 4. Handing a group to another admin (R-CLUBSETUP-33)

### MATCHi: a community is the venue's; any admin can be a moderator with the creator's rights

- **[POLICY]** "To create a community, your admin role needs the 'Community' permission. Other admins can be added as
  moderators with the same rights as the creator." "Each Group can have at most one community". [MATCHi: Communities](https://matchi.zendesk.com/hc/en-gb/articles/36758141080093-Communities) (updated 2026-09-15) — read 2026-10-08
- *reading:* MATCHi has no single runner to hand over: every moderator holds the whole group.

### Playtomic: a chat group has one admin and no handover

- **[POLICY]** "As a group admin, you can: create a group, add or remove participants, share the link …, Reset the link
  …, Edit the group information"; "You cannot add more than 200 users to a group". [Playtomic: How to create a chat group](https://playerhelp.playtomic.com/hc/en-gb/articles/19831494082705-How-to-create-a-chat-group) (updated 2026-03-05) — read 2026-10-08
- **[ABSENT]** Making another member admin, or the previous admin being told of a handover, at Playtomic or MATCHi.
  Searched both help centres for "group admin", "moderator", "transfer". — read 2026-10-08

## 5. Who answers a request to join, and the declined asker (R-CLUBSETUP-32)

### MATCHi Communities take no requests: an invite, an open link, or nothing

- **[POLICY]** "Anyone with the link — anyone with the link or QR code joins immediately. No approval needed." "Closed —
  the link doesn't let anyone join. It shows a page saying the community is invite-only." A removed player "can't
  rejoin without a new invite" in a closed community and "receive[s] a push notification when removed".
  [MATCHi: Communities](https://matchi.zendesk.com/hc/en-gb/articles/36758141080093-Communities) — read 2026-10-08

### Playtomic and MATCHi tell the accepted asker; a declined one is not mentioned

- **[POLICY]** Playtomic, a request for a place: "it is enough for one player to reject"; "Once the player has been
  accepted, they will receive a notification"; a rejection can be undone from "Requests for places". [Playtomic: How to request a spot in an open match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832027031569-How-to-request-a-spot-in-a-open-match),
  [Manager help: Request a spot](https://helpmanager.playtomic.com/hc/en-gb/articles/20535718052241-Request-a-spot-in-an-Open-Match) (updated 2026-09-09) — read 2026-10-08
- **[POLICY]** MATCHi public matches: "the booking holder gets a notification and decides whether to accept or decline";
  one pending request per player per booking. [MATCHi: Public Matches](https://matchi.zendesk.com/hc/en-gb/articles/21816050971933-Introducing-MATCHi-s-New-Feature-Public-Matches) (updated 2026-09-14) — read 2026-10-08
- **[ABSENT]** A notice to the person declined, at Playtomic or MATCHi. Same articles. — read 2026-10-08

## 6. Staff logins and roles at the Kraków systems (R-CLUBSETUP-25)

### tenis4U: four staff roles, each on the person's own account

- **[POLICY]** The panel's "Zarządzanie Rolami Użytkowników" page ("Dodaj rolę", "Edytuj role użytkownika") gives a
  tenis4U user one or more roles: "Recepcja" ("Dostęp do automatyzacji, stanowisk, użytkowników kortu i kalendarza
  rezerwacji"), "Manager", "Kortowi" ("Dostęp do listy stanowisk i kalendarza rezerwacji") and "Organizator Turniejów";
  each row shows the person's name, when the role was given and by whom. Owners (`is_admin`) see everything; the routes
  a role may not open are refused with "Brak uprawnień — Nie masz dostępu do tej sekcji". [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08

### kluby.org: staff with permissions since 2017

- **[POLICY]** "Możliwość zarządzania pracownikami: dodawanie, usuwanie, przydzielanie uprawnień" (2017); "Spersonalizowanie
  liczby dni do przodu dla pracownika" and "Wyłączenie lub ograniczenie możliwości odwoływania rezerwacji dla
  pracownika" (2018); "Dostosowywanie i nadawanie szczegółowych uprawnień pracownikom" (1 August 2021); "Dodatkowe
  uprawnienia zarządcy" (2023). [kluby.org: Co nowego 2017](https://oferta.kluby.org/changelog?rok=2017),
  [2018](https://oferta.kluby.org/changelog?rok=2018), [2021](https://oferta.kluby.org/changelog?rok=2021),
  [2023](https://oferta.kluby.org/changelog?rok=2023) — read 2026-10-08

### Playmore and the size of a desk: not published

- **[POLICY]** Playmore sells to clubs with "Mniej pracy na recepcji" and "Recepcja wie, kto ma dyżur"; one customer runs
  weekends without a desk: "Nie muszę nikogo zatrudniać na sobotę i niedzielę" (KS Zakręt). [Playmore dla klubów](https://join.playmore.pl/) — read 2026-10-08
- **[ABSENT]** Whether Playmore/Reservise gives each staff member a login (its pages for clubs do not say), and how many
  people a Kraków desk runs (no club publishes it). — read 2026-10-08
- *reading:* both systems Kraków padel clubs use give each desk worker a login and a role; one shared login is behind
  them.

## 7. Pausing online booking at kluby.org and tenis4U (R-CLUBSETUP-21, -22)

### Both have a club-wide switch; neither says what it does to bookings already made

- **[POLICY]** kluby.org added "Możliwość dodania powodu wyłączenia rezerwacji online" on 1 December 2022; the switch
  itself is in `platforms.md#klubyorg--pausing-online-booking-and-blocking-hours`. [kluby.org: Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[POLICY]** tenis4U's switch is "Aktywacja rezerwacji"; when it is off new bookings are refused (section 3).
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[ABSENT]** What either switch does to bookings already made, or what the club's own panel shows while it is off.
  Searched kluby.org's changelog 2014–2026 ("wyłącz", "online", "przełącznik") and tenis4U's panel; kluby.org's club
  help is video only. — read 2026-10-08

## 8. A Polish city budget unit as a Stripe account (R-CLUBSETUP-3)

### Stripe offers "government entity" to US accounts only, and lists no structures for Poland

- **[DOCS]** Business types: `individual`, `company`, `non_profit`, and "`government_entity` (available for US connected
  accounts only)". The business-structure tables cover AU, CA, DE, SG, TH, AE, GB, HK and US; Poland is not among them.
  [Stripe: Identity verification for connected accounts](https://docs.stripe.com/connect/identity-verification) — read 2026-10-08
- **[POLICY]** Rakieta opens every club as `entity_type: "company"` in Poland (`backend/app/modules/payments/infrastructure/stripe_payments.py:310`).

### KSOS is a school sports centre run by the City of Kraków

- **[POLICY]** KSOS's statute (2026) names "Gmina Miejska Kraków" as the body running it and the education superintendent
  as its pedagogical supervisor; its financing chapter (§ 27) begins "Krakowski Szkolny [Ośrodek] Sportowy jest …
  Gminy" (the PDF's text layer drops the words with Polish letters, so the legal form is not legible). KSOS publishes on
  the City's BIP and sells court time "w kasie Administratora, poprzez system rezerwacyjny". [KSOS statut (BIP)](https://www.bip.krakow.pl/zalaczniki/dokumenty/n/708824/karta),
  [KSOS: regulamin rezerwacji](https://obiekty.ksos.pl/regulamin-rezerwacji-kortow-ksos/) — read 2026-10-08
- **[ABSENT]** Whether Stripe accepts a Polish municipal budget unit (MOSiR, OSiR, KSOS) as a `company`; it is answered
  only by Stripe support or by onboarding one. — read 2026-10-08

## 9. Telling a club it is live (R-CLUBSETUP-10)

### Playtomic emails the date and time before the club goes live

- **[POLICY]** At the end of onboarding: "Our Customer Team is reviewing it. You will receive an email from us with the
  date & time you will be LIVE."; until then a banner reads "Review in progress. Pending to go Live". [Manager strings: onboarding](https://manager.playtomic.io/locales/en/onboarding.json) — read 2026-10-08
- **[POLICY]** "Once your onboarding coordinator confirms everything is complete, they will make your club visible …
  We will provide you with materials to help communicate with players". [Go live and start accepting online reservations](https://helpmanager.playtomic.com/hc/en-gb/articles/20535378377745-Go-live-and-start-accepting-online-reservations) (updated 2026-09-17) — read 2026-10-08
- **[ABSENT]** A go-live email at tenis4U or kluby.org: neither the panel nor the changelog has one. — read 2026-10-08

## 10. Stripe's own emails to Rakieta's clubs (R-CLUBSETUP-35, -11)

### With a Stripe-built dashboard, Stripe contacts the account itself

- **[DOCS]** "If your connected accounts have access to a Dashboard built by Stripe, Stripe will proactively reach out and
  collect information about your accounts whenever requirements change"; the platform's FAQ for its accounts starts "I
  just received an email from Stripe. Who is Stripe? Is this email real?" and tells them to "Follow the link from
  Stripe's email". [Stripe support: Communicating updates to verification requirements for connected accounts that have access to a dashboard built by Stripe](https://support.stripe.com/questions/communicating-updates-to-verification-requirements-for-connected-accounts-that-have-access-to-a-dashboard-built-by-stripe) — read 2026-10-08
- **[POLICY]** Rakieta opens clubs with `"dashboard": "full"` (Stripe's own dashboard) and Stripe as fees and losses collector
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:309`, `:316-319`).
- *reading:* Stripe's compliance emails reach a Rakieta club directly, whatever the platform's email settings; the
  club's `=` on both rules holds.

## 11. How far ahead Kraków groups settle a game (R-CLUBSETUP-13, -39)

### Clubs take bookings 7 to 30 days ahead; no measure of when groups settle

- **[POLICY]** tenis4U's default booking horizon is 14 days (`reservation_days_ahead=14` in the club settings object);
  Kraków padel clubs on tenis4U take 14 days, Fame Sport 30, Padel SPOT 7: `gaps-POSTGRID.md#tenis4u-most-kraków-padel-clubs-take-bookings-14-days-ahead-two-take-30-one-7`.
  [tenis4U club panel bundle](https://panel.tenis4u.pl/main.333e76605ded56e6.js) — read 2026-10-08
- **[ABSENT]** Independent evidence of how far ahead Kraków players settle a game; Playmore's "3 razy częściej" stays its
  own figure: `gaps-ENGINE.md#no-independent-measure-of-fill-by-lead-time`. Kraków WhatsApp and Facebook groups need a
  login (`platforms.md#kraków-groups-could-not-be-read`). — read 2026-10-08
