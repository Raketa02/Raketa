# CLUBSETUP — setup, way of working, settings, pause and official groups: market digest

Rules R-CLUBSETUP-1 to R-CLUBSETUP-35. Written 2026-10-08 from the topic files (read 2026-10-06 to
2026-10-08). Paths are relative to this folder; `market.md` means `../games-and-fill-in-market.md`. Kinds
as in the topics; *reading* is comparison, not a source.

**Read this first.** Playtomic goes live through a six-item checklist with a warning bar, then a person makes the club visible — `topics/competitor-club.md#the-go-live-checklist-and-the-warning-bar`, `topics/competitor-club.md#a-person-makes-the-club-visible`. No platform read has a booking that waits for the club, a timed release or a minimum notice — `topics/platforms.md#no-club-confirms-booking-mode-anywhere`, `topics/competitor-club.md#no-timed-release-and-the-private-club-workaround`. Only kluby.org has a club-wide pause — `topics/platforms.md#klubyorg--pausing-online-booking-and-blocking-hours`.

## 1. Before going live (R-CLUBSETUP-1 to R-CLUBSETUP-8, R-CLUBSETUP-10)

- **Competitor (R-CLUBSETUP-2, -8).** [POLICY] A plan, a Stripe account, billing, courts and prices, hours and images, contacts; if any is missing "a warning will appear at the top of your Playtomic Manager screen" — `topics/competitor-club.md#the-go-live-checklist-and-the-warning-bar`.
- **Competitor (R-CLUBSETUP-2, -10).** [POLICY] "your onboarding coordinator … will make your club visible"; [ABSENT] a self-serve go-live — `topics/competitor-club.md#a-person-makes-the-club-visible`.
- **Competitor (R-CLUBSETUP-1).** [POLICY] Form, demo and single-use code, then "Booking limits and cancellation policy" and "Court list and pricing" — `topics/competitor-club.md#applying-a-form-a-demo-a-single-use-referral-code`.
- **Competitor (R-CLUBSETUP-3).** [POLICY] Stripe is mandatory (entity type, owners ≥ 25 %, IBAN); "Stripe may request extra verification" — `topics/competitor-club.md#stripe-onboarding-through-playtomic`.
- **Competitor (R-CLUBSETUP-6).** [POLICY] A slot sells online only where a price rule covers it — `topics/competitor-club.md#which-courts-are-sold-online`.
- **Competitor (R-CLUBSETUP-8).** [ABSENT] Club help or support in Polish — `topics/competitor-club.md#nothing-for-clubs-in-polish`.
- **Provider (R-CLUBSETUP-3).** [DOCS] A Polish club is `individual` (18 fields), `company` (45) or `non_profit` (36), with no government type for a MOSiR; verification takes "a few minutes to a few business days", and a missed deadline stops payouts, then charges — `topics/local-market.md#what-a-polish-club-must-supply-to-stripe`.
- **Provider (R-CLUBSETUP-3, -8).** [DOCS] `currently_due`, `past_due`, `pending_verification`; each v2 requirement waits on `stripe` or on the `user` — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Status quo (R-CLUBSETUP-1).** [POLICY] Kraków clubs sell on tenis4U, Playmore or their own apps, and every club read keeps phone and desk booking — `topics/local-market.md#which-booking-systems-kraków-clubs-run`.

## 2. Live, and dropping out of live (R-CLUBSETUP-9, -11, -35)

- **Competitor (R-CLUBSETUP-11, -35).** [ABSENT] What Manager shows, and what happens to open matches, when a live club's Stripe account is restricted — `topics/competitor-club.md#stripe-onboarding-through-playtomic`, `market.md#story-stage-gaps-closing-hours-changing-prices-switching-courts-off-an-inactive-club`.
- **Competitor (R-CLUBSETUP-11).** [POLICY] A club unpaid for 5 days goes inactive: "no longer be visible", "will not be able to receive bookings"; [ABSENT] bookings already made — `market.md#story-stage-gaps-closing-hours-changing-prices-switching-courts-off-an-inactive-club`.
- **Competitor (R-CLUBSETUP-11).** [POLICY] An open match with no court left is cancelled, refunded in full, "Cancelled by Anemone", and "can't be restored" — `topics/competitor-club.md#automatic-cancellation-signed-anemone`.
- **Competitor (R-CLUBSETUP-9).** [POLICY] Each admin opts into an email per booking; [ABSENT] a digest — `topics/competitor-club.md#staff-logins-roles-and-who-gets-booking-emails`.
- **Provider (R-CLUBSETUP-35).** [DOCS] Stripe emails the club itself about compliance (the platform may brand it); no fixed notice before a requirement bites — `market.md#story-stage-gaps-polish-clubs-as-connected-accounts--entity-types-verification-restrictions-who-tells-the-club`.
- **Situation (R-CLUBSETUP-35).** [DOCS] A payout that "keeps getting pushed out" is "most likely due to an account verification requirement" — `situations.md` SIT-100.

## 3. The way of working (R-CLUBSETUP-12, -13)

- **Competitor.** [ABSENT] A booking that waits for the club, a timed release, a minimum notice for courts; the "private club" workaround (Book Ahead Limit 0) "will disable Open Match creation for everyone" — `topics/competitor-club.md#no-booking-that-waits-for-the-club-to-confirm`, `topics/competitor-club.md#no-timed-release-and-the-private-club-workaround`, `topics/competitor-club.md#no-minimum-notice`.
- **Competitor (Instant).** [POLICY] Desk and app sell from one calendar and cannot double-sell — `topics/competitor-club.md#manager-is-a-web-app-and-the-clubs-only-calendar`.
- **Platforms (On request).** [ABSENT] Courts booked on the club's yes at Playmore, tenis4U, kluby.org, PADO or MATCHi — `topics/platforms.md#no-club-confirms-booking-mode-anywhere`. Playmore's terms form the contract at the club's confirmation (§4.6), but only payment waits, 30 minutes — `topics/platforms.md#playmore--the-contract-waits-for-the-club-but-no-confirm-step-exists`, `topics/platforms.md#playmore--an-unpaid-booking-lapses-after-30-minutes`.
- **Platforms (Only Rakieta).** [POLICY] MATCHi's per-court "Offline only": visible, booked only by administrators — `market.md#s02-g7--a-pause-online-bookings-switch-and-what-it-does-to-bookings-already-made`.
- **Status quo (Only Rakieta).** [POLICY] Season and 12-week slots paid up front hold the prime hours — `topics/local-market.md#fixed-weekly-slots-take-the-prime-hours`, `situations.md` SIT-46; Squash4You's desk resells a late-cancelled slot first — `topics/local-market.md#the-cut-off-is-24-hours-late-means-the-full-price-unless-the-court-is-resold`.
- **Status quo.** [POLICY] "Wieczory wyprzedane, ale rano i wczesnym popołudniem korty stoją puste" (Playmore's pitch to clubs) — `topics/local-market.md#what-a-club-says-it-lacks-today`.
- **Situation (On request).** *opinion* A request arrives when nobody is at the desk — `situations.md` SIT-36.
- *Reading:* Instant is how every platform read already works; Only Rakieta and On request have no equivalent (`topics/platforms.md#no-club-confirms-booking-mode-anywhere`).

## 4. The settings, and when a change bites (R-CLUBSETUP-14 to -19)

- **Competitor (R-CLUBSETUP-17).** [POLICY] Book Ahead Limit (days), Cancellation Time (hours), per-day and active limits; no default published — `topics/competitor-club.md#booking-rules-book-ahead-cancellation-hours-per-day-and-active-limits`. The open-match 24 h is fixed — `topics/competitor-club.md#leaving-inside-24-hours-goes-through-the-club`.
- **Platforms (R-CLUBSETUP-17).** [POLICY] Playmore open games: call-off 1–48 h, free cancel 0–72 h, defaults 2 h and 12 h; [ABSENT] whether a change reaches games published, or a warning when free cancel outlasts the call-off — `topics/platforms.md#playmore--the-clubs-open-game-settings`.
- **Platforms (R-CLUBSETUP-17).** [POLICY] tenis4U: separate cut-offs for one-off and standing bookings; kluby.org: a per-booking limit — `topics/platforms.md#tenis4u--separate-cut-offs-for-one-off-and-standing-bookings`, `topics/platforms.md#klubyorg--cancellation-on-the-clubs-terms`.
- **Status quo (R-CLUBSETUP-17).** [POLICY] 24 h at Garden Padel, Fame Sport, Atras, Squash4You, Miazga, KSOS; 12 h at SAO — `topics/local-market.md#the-cut-off-is-24-hours-late-means-the-full-price-unless-the-court-is-resold`; 5 to 24 h across Poland — `situations.md` SIT-52.
- **Competitor (R-CLUBSETUP-14, -19).** [ABSENT] Whether a changed Cancellation Time or club terms reach bookings made; [POLICY] "By making a reservation, the user accepts the cancellation policy" — `topics/competitor-club.md#a-changed-setting-and-bookings-already-made`, `topics/competitor-club.md#the-clubs-own-terms-versioned-at-checkout`.
- **Platforms (R-CLUBSETUP-14, -15, -19).** [POLICY] MATCHi: "Match Settings only affect new matches — existing matches keep their values" — `topics/platforms.md#matchi--venue-matches-pay-at-join-optional-auto-cancel`; only MATCHi answers this — `market.md#71-a-club-changes-its-cancellation-hours-does-the-change-reach-bookings-already-made-s05-g-4-s01-g9`, `situations.md` SIT-40.
- **Law (R-CLUBSETUP-14, -15).** [LAW] Terms bind only if given before the contract (art. 384); [DOCS] UOKiK: new terms reach a later charge "only with the prior consent of the consumer" — `topics/local-market.md#which-terms-bind-when-a-yes-becomes-a-booking-later`.
- **Situations.** Stacja Nowa Gdynia posts rule changes 14 days ahead — `situations.md` SIT-39 (R-CLUBSETUP-19); the clock goes back on 25 Oct 2026 — SIT-22 (R-CLUBSETUP-18).

## 5. Other clubs' courts (R-CLUBSETUP-20, -31)

- **Platforms.** [ABSENT] A club passing full-court demand to a partner club; MATCHi bookings "can never be moved to a different venue" — `topics/platforms.md#no-platform-shows-a-club-the-player-groups-that-play-at-it`, `market.md#s02-g14--a-club-sending-its-own-members-or-groups-games-to-partner-clubs`.

## 6. Pausing and leaving (R-CLUBSETUP-21 to -24)

- **Competitor (R-CLUBSETUP-21).** [ABSENT] A club-wide pause; only per-court toggles, Holidays, Book Ahead 0, and staff taking the club offline — `topics/competitor-club.md#no-pause-switch`.
- **Competitor (R-CLUBSETUP-24).** [POLICY] Cancel 30 days ahead and ask the team; offline is "no longer visible … won't receive new bookings"; [ABSENT] bookings sold and the Stripe account — `topics/competitor-club.md#leaving-takes-30-days-and-a-person`. A closing club cancels bookings by hand "to enable player refunds" — `topics/competitor-club.md#late-cancellations-weather-closures`.
- **Platforms (R-CLUBSETUP-21, -22).** [POLICY] kluby.org's switch takes a reason and shows "Tymczasowo rezerwacje ONLINE zostały wyłączone" — `topics/platforms.md#klubyorg--pausing-online-booking-and-blocking-hours`; [ABSENT] at every platform: what a pause does to bookings or open games made — `market.md#s02-g7--a-pause-online-bookings-switch-and-what-it-does-to-bookings-already-made`.
- **Platforms (R-CLUBSETUP-24).** [POLICY] Playmore takes no new bookings from a leaving club and "rozliczymy te Rezerwacje, które zostały dokonane przed"; a club that cannot host tells the booked player (§8) — `topics/platforms.md#playmore--a-club-leaving-or-unable-to-host`. MATCHi won't archive a court with future bookings — `topics/platforms.md#matchi--the-club-cancels-or-blocks`.
- **Situations.** A pause — `situations.md` SIT-43; a club closing for good (about 90 Swedish padel firms bankrupt in 2023) — SIT-44; a season switch — SIT-08.

## 7. One login, and what the club sees (R-CLUBSETUP-25, -26)

- **Competitor (R-CLUBSETUP-25).** [POLICY] Each staff member is a separate admin added by the "Tenant Owner", with per-menu "view-only or view and edit" — `topics/competitor-club.md#staff-logins-roles-and-who-gets-booking-emails`.
- **Competitor (R-CLUBSETUP-26).** [POLICY] Managers message all players in a booking's chat (a push each); a player's details reach the club only "through an online payment or by the player accepting your club's Terms & Conditions" — `topics/competitor-club.md#talking-to-players-and-what-the-club-sees-of-them`. Its customer export carries email, phone, birthday — `market.md#76-clubs-leaving-pausing-blocking-courts-dating-prices-sharing-games-s02-g9-g7-g3-g5-g14`.
- **Status quo (R-CLUBSETUP-26).** [POLICY] AGH passes name, phone and email to Reservise — `situations.md` SIT-104; Playmore holds them for the club (§17) — `market.md#76-clubs-leaving-pausing-blocking-courts-dating-prices-sharing-games-s02-g9-g7-g3-g5-g14`.
- **Complaints, club.** [COMPLAINT] Clubs left Playtomic "citing a lack of accessibility to their customers" — `topics/complaints.md#clubs-lose-access-to-their-own-customers`; staff carry the platform's support load — `topics/complaints.md#club-staff-carry-the-platforms-support-load`.
- **Complaints, joiner (R-CLUBSETUP-26).** [COMPLAINT] tenis4U: a club's warning "bez poinformowania użytkownika" blocks booking everywhere — `topics/complaints.md#marked-a-no-show-warned-or-blocked-without-a-fair-hearing`.

## 8. Official groups (R-CLUBSETUP-27 to -34)

- **Platforms (R-CLUBSETUP-27, -28).** [POLICY] MATCHi Communities: "a private social space attached to a customer group at your venue", made and moderated by the venue, joined by link or QR, making the player the venue's customer — `topics/platforms.md#matchi--communities-are-a-venues-groups`.
- **Platforms (R-CLUBSETUP-28).** [ABSENT] A club shown the player groups that play at it — `topics/platforms.md#no-platform-shows-a-club-the-player-groups-that-play-at-it`.
- **Competitor (R-CLUBSETUP-32).** [POLICY] Playtomic groups are players' chat groups (one sport, ≤ 200, admin adds or removes); [ABSENT] a match for a group — `topics/competitor-organiser.md#playtomic-groups-are-chat-groups-not-game-pools`.
- **Platforms, status quo.** [POLICY] Playmore lists a club's WhatsApp and Facebook channels; PadelCity runs a WhatsApp group per location; Garden Padel points to a "WhatsApp group … Matchmaking" — `topics/platforms.md#playmore--invites-by-whatsapp-and-a-clubs-community-links`, `topics/platforms.md#operators-and-booking-systems-lean-on-whatsapp`, `topics/local-market.md#clubs-own-community-channels`.

## Rules no market fact touches

R-CLUBSETUP-4, -5, -7, -16, -23, -29, -30, -34: the website's own form and counting behaviour; no topic
records another platform's (`topics/competitor-club.md#2-onboarding`, `topics/platforms.md#12-summary`).

## Gaps round answers (read 2026-10-08)

- **R-CLUBSETUP-38.** [DOCS] A refund comes out of the club's balance and, short of it, a card refund waits as pending — `topics/gaps-CLUBSETUP.md#stripe-a-refund-needs-the-accounts-available-balance-short-of-it-a-card-refund-waits`; [ABSENT] refunds on a charges-disabled account, untested — `#whether-a-charges-disabled-account-can-refund-not-documented-not-tried`.
- **R-CLUBSETUP-11, -35, -38.** [POLICY] Playtomic Manager warns a live club "Your payments are about to be interrupted" with "Add missing information" / "Skip for now"; [ABSENT] open matches — `topics/gaps-CLUBSETUP.md#a-warning-bar-and-a-pop-up-your-payments-are-about-to-be-interrupted`.
- **R-CLUBSETUP-11.** [POLICY] tenis4U refuses every new booking once online booking is off; [ABSENT] games still gathering, anywhere — `topics/gaps-CLUBSETUP.md#tenis4u-refuses-every-new-booking-once-a-clubs-online-booking-is-off`.
- **R-CLUBSETUP-33.** [POLICY] MATCHi: any admin can moderate a community with the creator's rights; [ABSENT] a handover, or the old admin told — `topics/gaps-CLUBSETUP.md#matchi-a-community-is-the-venues-any-admin-can-be-a-moderator-with-the-creators-rights`.
- **R-CLUBSETUP-32.** [POLICY] MATCHi communities take no requests (invite, or an open link that "joins immediately"); [ABSENT] a notice to a declined asker — `topics/gaps-CLUBSETUP.md#matchi-communities-take-no-requests-an-invite-an-open-link-or-nothing`.
- **R-CLUBSETUP-25.** [POLICY] tenis4U gives each staff member a role (Recepcja, Manager, Kortowi, Organizator Turniejów); kluby.org has staff permissions since 2017; [ABSENT] desk headcount — `topics/gaps-CLUBSETUP.md#tenis4u-four-staff-roles-each-on-the-persons-own-account`.
- **R-CLUBSETUP-21, -22.** [ABSENT] What kluby.org's or tenis4U's switch does to bookings made — `topics/gaps-CLUBSETUP.md#both-have-a-club-wide-switch-neither-says-what-it-does-to-bookings-already-made`.
- **R-CLUBSETUP-3.** [DOCS] Stripe's `government_entity` is "available for US connected accounts only"; [ABSENT] a Polish budget unit as `company` — `topics/gaps-CLUBSETUP.md#stripe-offers-government-entity-to-us-accounts-only-and-lists-no-structures-for-poland`.
- **R-CLUBSETUP-10.** [POLICY] Playtomic: "You will receive an email from us with the date & time you will be LIVE" — `topics/gaps-CLUBSETUP.md#playtomic-emails-the-date-and-time-before-the-club-goes-live`.
- **R-CLUBSETUP-35, -11.** [DOCS] With a Stripe-built dashboard "Stripe will proactively reach out"; Rakieta's clubs have `dashboard: full` — `topics/gaps-CLUBSETUP.md#with-a-stripe-built-dashboard-stripe-contacts-the-account-itself`.
- **R-CLUBSETUP-13, -39.** [ABSENT] Independent evidence of how far ahead groups settle; Kraków clubs book 7–30 days ahead — `topics/gaps-CLUBSETUP.md#clubs-take-bookings-7-to-30-days-ahead-no-measure-of-when-groups-settle`.

Still open: a test-mode refund on a stopped account (R-CLUBSETUP-38); open games when a club stops selling (R-CLUBSETUP-11); a group handover elsewhere (R-CLUBSETUP-33); the effect of kluby.org's switch (R-CLUBSETUP-21, -22); Stripe and a Polish budget unit (R-CLUBSETUP-3); lead time in Kraków (R-CLUBSETUP-13, -39).

## Gaps answered 2026-10-09 (after S-01)

- **R-CLUBSETUP-38.** [DOCS] Pausing a connected account's payments blocks new charges and names no refund, is not enforced in a sandbox and is not offered for Accounts v2; [POLICY] Stripe holds a stopped account's payouts to cover refunds, and a closed account cannot refund; [COMPLAINT] the "not currently able to refund charges" message tied to a short balance. Only a Stripe test-mode run with requirements past due settles it — `topics/gaps-S-01.md#stripe-pausing-payments-blocks-new-charges-refunds-are-not-mentioned-and-pauses-are-not-enforced-in-a-sandbox`, `topics/gaps-S-01.md#stripe-keeps-a-stopped-accounts-money-to-cover-refunds-a-closed-account-cannot-refund`, `topics/gaps-S-01.md#the-refusal-message-seen-again-tied-to-a-short-balance`.
