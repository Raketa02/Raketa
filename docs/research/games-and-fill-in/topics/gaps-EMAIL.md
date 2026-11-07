# Gaps — EMAIL (what players and desks are emailed)

Answers to the EMAIL area's open gaps for PRD #530 (`$W/areas/EMAIL/gaps.md`, 18 gap lines and 8 lens opinions),
read **2026-10-08**. One section per rule; every fact sits under a `###` heading so it can be cited as
`topics/gaps-EMAIL.md#<heading>`. Facts already in `local-market.md`, `competitor-*.md` or `platforms.md` are cited
there, not repeated.

Kinds: [POLICY] a company's rule, help page or the text its own app shows · [PRICE] · [LAW] · [DOCS] a provider's,
network's, regulator's or tax authority's document · [MEASURED] seen by using the product as a visitor (screenshot
and URL trace under `../shots/gaps-EMAIL-*`) · [COMPLAINT] · [ABSENT] looked for and not found, with where.

How the Polish systems were read: tenis4U's player web app (`app.tenis4u.pl`, Angular, unminified) and club panel
(`panel.tenis4u.pl`, minified), Playmore's web app (`playmore.pl`, all 1,053 lazy chunks), and kluby.org's public
changelog 2012–2026 (`oferta.kluby.org/changelog?rok=…`) were downloaded and searched on 2026-10-08. Interface text
quoted from that code is tagged [POLICY]; the code is what every visitor's browser runs.

---

## 1. A payout that comes back (R-EMAIL-22, and the opinion that Stripe tells the platform)

### Stripe emails the account holder when a payout comes back, up to 5 business days later
- **[DOCS]** "If your bank account can't receive a payout for any reason, your bank returns the funds to us … It can take up to 5 additional business days for your bank to return the payout and inform us that it failed. If this happens, you're notified by email and in the Dashboard. If a payout fails, make sure your bank account details are correct by re-entering them. Stripe then reattempts the payout at the next scheduled payout interval." And: "When a payout fails, the status might initially show as `paid`, but then change to `failed` within 5 business days." [Stripe: Payouts — Payout failures](https://docs.stripe.com/payouts#payout-failures) — read 2026-10-08
- **[DOCS]** The email's subject is "Action required to resume payouts from your Stripe balance"; its body says "Your bank notified us that they could not process this payout" and asks for the bank details again. [Stripe support: Bank accounts and payouts FAQ](https://support.stripe.com/questions/bank-accounts-and-payouts-faq) — read 2026-10-08
- **[DOCS]** If the details were right and the bank was the problem, "After you resolve any issues with your bank, you can reactivate the payouts by clicking **Resume Payouts**." [Stripe: Payouts](https://docs.stripe.com/payouts#payout-failures) — read 2026-10-08
  - *Reading:* a club holding its own full Stripe Dashboard is told by Stripe itself, by email, and sends the money again itself (re-enter the account, or Resume Payouts); nobody at Raketa has to act for the money to move.

### The platform hears of it as an event: `payout.failed`
- **[DOCS]** For connected accounts: "`failed`: … When a payout fails, the external account involved is disabled and can't receive payouts until the platform updates the connected account's external account details." A platform listening to connected-account events receives "`payout.failed`: Sent when a payout fails … Stripe also sends an `account.external_account.updated` event because the failed external account is disabled." For accounts with the full Stripe Dashboard, "the account holder manages their external payout accounts". [Stripe: Payouts to connected accounts](https://docs.stripe.com/connect/payouts-connected-accounts) — read 2026-10-08
  - *Reading:* the club lens's opinion holds: Raketa could read the failure as it reads its other Stripe notices.

### Przelewy24 and Tpay: a payout that does not arrive
- **[POLICY]** Przelewy24's help for "the balance payout has been ordered, yet the funds have not reached the indicated account for a couple of days" answers only: "Check whether the account has been blocked due to re-verification or whether the account number is valid." [Przelewy24 help](https://www.przelewy24.pl/en/help-center/i-sell-with-przelewy24/balance-and-payouts/there-is-a-notice-in-the-panel-that-the-balance-payout-has-been-ordered-yet-the-funds-have-not-reached-the-indicated-account-for-a-couple-of-days-now-why-is-that) — read 2026-10-08
- **[ABSENT]** What P24 or Tpay tell a merchant, and whether they resend, when a bank returns a payout: not in P24's 12 "Balance and payouts" help articles, its 24-page merchant-panel manual ([PDF](https://www.przelewy24.pl/storage/app/media/do-pobrania/rozpoczecie_wspolpracy/instrukcja_obslugi_panelu_transakcyjnego_pl.pdf)), or Tpay's support FAQ (support.tpay.com, searched "wypłata", "zwrot") — read 2026-10-08

---

## 2. Staff logins and a separate address for notices (R-EMAIL-25)

### kluby.org: staff accounts with permissions, and notices to more than one address
- **[POLICY]** Changelog: "Możliwość zarządzania pracownikami: dodawanie, usuwanie, przydzielanie uprawnień" (2017); "Dostosowywanie i nadawanie szczegółowcyh [sic] uprawnień pracownikom" (2021); "Możliwość ustawienia powiadomień na więcej niż jeden adres e-mail" (2018, under Rezerwacje); "Dedykowany adres e-mail do codziennych wiadomości z systemu ligowego" (2023). The feature list names "Obsługa wielu pracowników i uprawnień" and "Powiadomienia SMS/MAIL". [kluby.org: Co nowego 2017](https://oferta.kluby.org/changelog?rok=2017), [2018](https://oferta.kluby.org/changelog?rok=2018), [2021](https://oferta.kluby.org/changelog?rok=2021), [2023](https://oferta.kluby.org/changelog?rok=2023), [Funkcje](https://oferta.kluby.org/funkcje) — read 2026-10-08

### tenis4U: staff by role, and a list of people told about bookings
- **[POLICY]** The club panel's staff tabs search users by role: reception ("Wyszukaj pracownika recepcji"), managers, court maintenance ("pracowników konserwacji"), tournament organisers; the role codes are `RECEPTION`, `MANAGER`, `COURT_MAINTENANCE`, `TOURNAMENT_ORGANIZER`. [tenis4U panel](https://panel.tenis4u.pl/) (main.333e76605ded56e6.js) — read 2026-10-08
- **[POLICY]** A court's settings hold "Lista osób powiadamianych o rezerwacji w korcie" (people picked from accounts and added with "Dodaj"), separately "Numer telefonu do powiadomień SMS" with "opcja powiadomień sms jest dodatkowo płatna 30 gr za każdy sms", and "Numer telefonu do kontaktu w przypadku awarii automatyzacji". [tenis4U panel](https://panel.tenis4u.pl/) — read 2026-10-08
  - *Reading:* who is told about a booking is a list the club keeps, not the address it signs in with. The channel of that notice (push or email) is not in the panel's text.

### Przelewy24: any number of users, a role for the bookkeeper
- **[POLICY]** "Istnieje możliwość dodania dowolnej liczby użytkowników", roles Użytkownik (full), Limit, and "Księgowy – uprawnienia konta Limit + zlecanie zwrotów, podgląd Wypłat, podgląd Faktur". [P24 panel manual, p. 14](https://www.przelewy24.pl/storage/app/media/do-pobrania/rozpoczecie_wspolpracy/instrukcja_obslugi_panelu_transakcyjnego_pl.pdf) — read 2026-10-08

### Playtomic: every admin has a login of their own
- **[POLICY]** "Each admin has their own login credentials. Changing your password won't affect other administrators' access." [Login issues on Playtomic Manager](https://helpmanager.playtomic.com/hc/en-gb/articles/39795404368913) (updated 2026-10-06) — read 2026-10-08. Each admin picks booking emails: `competitor-club.md#staff-logins-roles-and-who-gets-booking-emails`.

### Playmore (Reservise): not found
- **[ABSENT]** Staff logins or a notice address on the club side: Playmore's web app is the player side only; `reservise.com` now redirects to `join.playmore.pl/reservise/` (a migration page), and `playmore.pl/dla-klubow/` lists neither — read 2026-10-08

---

## 3. What the desk's booking email shows, and names (R-EMAIL-26)

### Playtomic's admin booking email: its contents are not published
- **[ABSENT]** The help centre documents only that each admin opts into emails for "Bookings created or cancelled by players, course enrollment cancellations"; no article shows the email or says whether it names the players. Searched helpmanager.playtomic.com (Zendesk API, "notification email", "email address", 58–99 hits each) — read 2026-10-08
- **[POLICY]** The *player's* email is filled in with "Player name, Date and time of the match, Location, Payment information". [Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145) — read 2026-10-08

### A Kraków desk gets the booker's name and contact with each booking
- **[POLICY]** kluby.org's terms: "Klubowi podczas dokonywania Rezerwacji udostępniane są następujące Dane Osobowe: a) imię, nazwisko; b) numer telefonu; c) adres e-mail; d) nazwa Użytkownika; e) zdjęcie profilowe; f) informacja o ilości blokad na Usługi Klubów." [kluby.org Regulamin](https://kluby.org/regulamin) — read 2026-10-08
- **[POLICY]** Miazga Squash (Reservise): "Podanie prawdziwych danych jest konieczne dla prawidłowego działania systemu rezerwacji. Prawidłowość podanych danych może zostać zweryfikowana przez recepcję. Jeżeli podane dane będą budziły wątpliwości, Klub może anulować rezerwację lub odmówić realizacji usługi." [Miazga regulamin §3b](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** A Kraków club that asks for the names of *every* player before it accepts a booking: not in the rules of Atras, Miazga, Squash4You, Garden Padel or Fame Sport, nor in tenis4U, kluby.org or Playmore text — read 2026-10-08
  - *Reading:* the desk's norm is to know who booked and how to reach them, and the booker answers for the court; a request email that names nobody leaves the desk without the one person it would ring.

---

## 4. How long a sent confirmation is kept (R-EMAIL-27)

### Tax law: records and the documents behind them, five years after the year
- **[LAW]** VAT Act art. 112: taxpayers keep the records kept for VAT "oraz wszystkie dokumenty … związane z tym rozliczaniem do czasu upływu terminu przedawnienia zobowiązania podatkowego". [Art. 112 (LexLege, state 2026-10-08)](https://lexlege.pl/ustawa-o-podatku-od-towarow-i-uslug/art-112/) — read 2026-10-08
- **[LAW]** Tax Ordinance art. 70 § 1: the obligation "przedawnia się z upływem 5 lat, licząc od końca roku kalendarzowego, w którym upłynął termin płatności podatku"; art. 86 § 1 the same for books and their documents. [Art. 70](https://lexlege.pl/ordynacja-podatkowa/art-70/), [Art. 86](https://lexlege.pl/ordynacja-podatkowa/art-86/) — read 2026-10-08
  - *Reading:* this binds the **club** (the seller) for its own sales records and payment evidence; it does not name a sent email.

### Consumer law: the seller proves what it told the player
- **[LAW]** Consumer Rights Act art. 24: "Ciężar dowodu spełnienia obowiązków informacyjnych określonych w art. 12 spoczywa na przedsiębiorcy." Art. 21: the trader confirms a distance contract "na trwałym nośniku … najpóźniej … przed rozpoczęciem świadczenia usługi". [Art. 24](https://lexlege.pl/ustawa-o-prawach-konsumenta/art-24/), [Art. 21](https://lexlege.pl/ustawa-o-prawach-konsumenta/art-21/) — read 2026-10-08
- **[LAW]** Civil Code art. 118: claims lapse after six years, three for claims "związanych z prowadzeniem działalności gospodarczej", the end falling on the last day of a calendar year. [Art. 118 KC](https://lexlege.pl/kc/art-118/) — read 2026-10-08

### Card disputes: 120 days, longer for a service paid ahead
- **[DOCS]** "Card networks typically allow cardholders to initiate disputes within 120 days of the original payment, but their rules allow more time in some situations … when a customer pays for a future event or service …". The evidence for a reservation is the policy "as provided to the customer", "how and where" it was shown, and the customer's messages ("A PDF of an email exchange"). [Stripe: How disputes work](https://docs.stripe.com/disputes/how-disputes-work), [Dispute categories](https://docs.stripe.com/disputes/categories) — read 2026-10-08

### Playtomic keeps a booking's data ten years after the last visit
- **[POLICY]** Privacy policy: for "Making a reservation", "Organizing public matches" and the profile, the period of storage is "10 years from the last access". Email notifications (booking, payment, matches) are listed under "Consent — Up to withdrawal of the consent", although the help says they "cannot be disabled". Nothing says whether the sent email itself is kept. [Playtomic privacy policy](https://playtomic.com/privacy-policy) — read 2026-10-08

### kluby.org shows a club the notices sent to each customer
- **[POLICY]** Changelog 2022: "Podgląd wysłanych powiadomień w historii klienta o rezerwacjach"; 2017: "Zapisywanie informacji o zmianach w rezerwacji". [kluby.org: Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022), [2017](https://oferta.kluby.org/changelog?rok=2017) — read 2026-10-08
- **[ABSENT]** tenis4U's privacy policy (`tenis4u.pl/polityka-prywatnosci/` returns 404) and Playmore's (an app shell with no text) were not readable — read 2026-10-08

### Raketa's own: the words are a function of the booking, but not stored
- *Code, not market:* the queue keeps kind, recipient, subject and times (backend/app/infrastructure/mail/mail_queue_model.py:39-58) and nulls both bodies once sent or given up (backend/app/infrastructure/mail/sqlalchemy_mail_queue.py:74-83, 100-101). The booking email's words come only from the reader's name, club, court, sport, start, amount and cut-off (backend/app/modules/payments/application/seat_charge_emails.py:69-107), so they can be re-derived from the booking's events with the code of the day it was sent — *unverified* that every input is still in the event store, and nothing records which code version wrote it.

---

## 5. Where an email's button lands (R-EMAIL-29, R-EMAIL-30)

### Playtomic Manager keeps the page a signed-out admin asked for
- **[MEASURED]** Opening `https://manager.playtomic.io/payments/payouts` signed out lands on `https://manager.playtomic.io/auth/login?return_to=%2Fpayments%2Fpayouts`. Whether the page is opened after signing in could not be tried (no account). [screenshot](../shots/gaps-EMAIL-playtomic-manager-deep-link-signed-out.png), [trace](../shots/gaps-EMAIL-signed-out-deep-links.txt) — 2026-10-08

### tenis4U's club panel forgets it
- **[MEASURED]** Opening `https://panel.tenis4u.pl/#/calendar/149` signed out shows "Dostęp tylko dla zalogowanych użytkowników" and moves to `#/login` with no return parameter. [screenshot](../shots/gaps-EMAIL-tenis4u-panel-deep-link-signed-out.png), [trace](../shots/gaps-EMAIL-signed-out-deep-links.txt) — 2026-10-08
- **[POLICY]** After signing in, the panel opens the calendar of the club's first court (`/calendar/{id}`), a tournament organiser's tournaments, or `/courts` for several courts — never the page asked for. [tenis4U panel](https://panel.tenis4u.pl/) (main.333e76605ded56e6.js) — read 2026-10-08

### tenis4U's and Playmore's player web apps return a player to the page she asked for
- **[POLICY]** tenis4U's web app stores the page in `localStorage('redirect')` before sending a player to "Zaloguj" and opens it after sign-in; it has a page per booking, `reservation/:uuid`, and a join page `j/:uuid`. [tenis4U web app](https://app.tenis4u.pl/) (main.cf446af5e9523413.js) — read 2026-10-08
- **[POLICY]** Playmore's router sends a signed-out player from any page that needs an account to `/login`, after saving the page ("pendingAuthIntent"); it has a page per booking, `/reservation/:venueId/details/:reservationId`, and signs in a player who arrives with a `login_token`, or an `authcode` and `email`, in the link. [Playmore web app](https://playmore.pl/) (index-C8d-0CWt.js) — read 2026-10-08
- **[POLICY]** A Reservise/Playmore club's confirmation email links to the booking: Miazga Squash lets a player cancel "przez aplikację lub link w wiadomości email potwierdzającej rezerwację"; its booking and cancellation are also confirmed by "wiadomość SMS wysłana z systemu". [Miazga regulamin §3c, §4a, §4c](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** Whether Playtomic's and tenis4U's confirmation emails link to the booking itself, and where such a link lands on a computer: no email sample in their help (Playtomic player and club help centres via Zendesk API, "confirmation email" 52 hits), app-store screenshots, or reviews — read 2026-10-08

### A custom-scheme button in webmail on a computer (the newcomer lens's opinion)
- **[COMPLAINT]** A FileMaker developer: an `fmp://` link "worked from Mac Mail, but in Gmail the href data was stripped out", leaving only the words "Click here". [FM Forums: fmp protocol & Gmail](https://fmforums.com/topic/92588-fmp-protocol-gmail/) (2014) — read 2026-10-08
- **[ABSENT]** Google's own statement of which link schemes Gmail keeps — searched support.google.com — read 2026-10-08
  - *Reading:* a button addressed to an app scheme can arrive as plain text, or open nothing, on a laptop; an `https` address on Raketa's own domain does not have that problem.

---

## 6. Confirming an address and changing it (R-EMAIL-35)

### Playtomic: a changed address must be confirmed by email
- **[POLICY]** "If you are updating your email, you will be emailed to verify the new account. Please follow the prompts in the email to verify." (Profile › Edit Profile.) [How to change your personal info](https://playerhelp.playtomic.com/hc/en-gb/articles/19832098474129) (updated 2026-09-29) — read 2026-10-08. The Android app carries `ERROR_EMAIL_CHANGE_NEEDS_VERIFICATION` and `VERIFY_BEFORE_CHANGE_EMAIL` (strings of the Playtomic Android package downloaded from APKPure on 2026-10-08 by the PAY/NOTIFY researchers; read here) — read 2026-10-08

### tenis4U: an SMS code activates the account; the address is never confirmed and can be edited
- **[POLICY]** Sign-up asks name, email, password and phone, then "Kod SMS jest wymagany do aktywowania konta" → "Numer potwierdzony · Możesz się zalogować". Errors include "Podany adres e-mail jest zajęty"; no email-confirmation text exists in the app. "Edytuj dane" shows an editable "Email" field next to name and town. [tenis4U web app](https://app.tenis4u.pl/) — read 2026-10-08
- **[POLICY]** A club can set "Wymagaj potwierdzenia podczas tworzenia konta użytkownika" per court (`create_users_without_confirmation`). [tenis4U panel](https://panel.tenis4u.pl/) — read 2026-10-08

### Playmore: a six-digit code by email, a verified phone, and an address that can change
- **[POLICY]** "Zaloguj się przez email … Wpisz 6-cyfrowy kod wysłany na Twój email"; routes `/confirm-email-address` ("Potwierdzenie adresu e-mail") and `/login/verify-phone` ("Aby korzystać z aplikacji, podaj i zweryfikuj swój numer telefonu"). Profile editing refuses only an address that came from Google, Facebook or Apple: "Tego adresu e-mail nie można zmienić — pochodzi z konta, przez które się logujesz." [Playmore web app](https://playmore.pl/) (chunks CccZ1mLc.js, DUA_QY46.js) — read 2026-10-08

### kluby.org: an activation email
- **[POLICY]** "ITSS wysyła na adres e-mail wskazany w Formularzu link aktywacyjny. Korzystanie z Konta staje się możliwe po kliknięciu w link aktywacyjny". [kluby.org Regulamin §V](https://kluby.org/regulamin) — read 2026-10-08
- **[POLICY]** Changelog 2022: "Automatyczne ponowne wysyłanie wiadomości e-mail aktywującej konto"; 2019: an administrator is told when a player asks to link a club record to a portal account. [kluby.org: Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022), [2019](https://oferta.kluby.org/changelog?rok=2019) — read 2026-10-08
- **[ABSENT]** Whether kluby.org lets a player change the address: not in the changelog or the regulamin — read 2026-10-08

---

## 7. The language of emails in Poland (R-EMAIL-31, and Stripe's for R-EMAIL-23, 24)

### Playtomic: the club picks the language of its players' emails; Manager follows the browser
- **[POLICY]** "Communication Language — Customize the language of the messages your players receive! … Settings > Venue > Communication … choose the language of the communications." "The language displayed in Playtomic Manager is determined by your browser's language settings." The player app follows the phone's language on Android and a per-app setting on iOS. [Communication and notifications](https://helpmanager.playtomic.com/hc/en-gb/articles/20535292080145), [Manager General FAQ](https://helpmanager.playtomic.com/hc/en-gb/articles/43539938393233), [Change the app language](https://playerhelp.playtomic.com/hc/en-gb/articles/46119983392529) — read 2026-10-08
- **[ABSENT]** The language of Playtomic's admin booking emails to a club — read 2026-10-08

### Playmore: Polish first, ten languages, saved on the account
- **[POLICY]** The web app's languages: Polski ("tier: source"), English ("baseline"), Українська, Nederlands, Deutsch, Română, Čeština and more; a signed-in player's choice is saved to the profile (`user/updateUserProfile {language}`). [Playmore web app](https://playmore.pl/) (chunks dJ5uFTvW.js, CrmOX9eO.js) — read 2026-10-08
- **[ABSENT]** Whether Playmore's emails follow that saved language — read 2026-10-08

### kluby.org: portal in English and Ukrainian since 2022; tenis4U: Polish only
- **[POLICY]** kluby.org 2022: "Tłumaczenie portalu na język angielski i ukraiński", "Wersja angielska rozwiązania dedykowanego". [Co nowego 2022](https://oferta.kluby.org/changelog?rok=2022) — read 2026-10-08
- **[POLICY]** tenis4U's player app and club panel carry Polish text only: no language switch; the translation module is commented out (`// import {TranslateModule} from '@ngx-translate/core'`), and the only language lists in the bundles belong to a PDF library. [tenis4U web app](https://app.tenis4u.pl/), [panel](https://panel.tenis4u.pl/) — read 2026-10-08
- **[ABSENT]** The language of tenis4U's emails (the app's text being Polish only) — read 2026-10-08

### Stripe speaks no Polish to a club
- **[DOCS]** The Stripe Dashboard's sign-in page offers 20 locales — de-DE, five English, es, fr, id, it, ja, nl, pt-BR, sv, th, zh — and no Polish. [dashboard.stripe.com/login (page source, hreflang list)](https://dashboard.stripe.com/login) — read 2026-10-08
- **[POLICY]** The Stripe Dashboard app: "English, Dutch, French, German, Indonesian, Italian, Japanese, Portuguese, Simplified Chinese, Spanish, Swedish, Thai". [App Store: Stripe Dashboard](https://apps.apple.com/us/app/stripe-dashboard/id978516833) — read 2026-10-08
- **[DOCS]** Paid support is in English, with redirects for German, Spanish, French, Italian, Portuguese, Simplified Chinese and Japanese. [Stripe: Language support for Paid Support users](https://support.stripe.com/questions/language-support-for-paid-support-users) — read 2026-10-08
- **[ABSENT]** A stated language for Stripe's emails to an account holder (requirements, disputes, payouts) — searched docs.stripe.com and support.stripe.com — read 2026-10-08. Customer-facing receipts and Checkout do support Polish (`pl`). [Stripe: Language options for customer emails](https://support.stripe.com/questions/language-options-for-customer-emails) — read 2026-10-08
  - *Reading:* a Kraków club's own Stripe emails most likely arrive in English.

---

## 8. The club moves a game (R-EMAIL-14)

### tenis4U and kluby.org: a desk can move a booking; nothing says the booker is told
- **[POLICY]** tenis4U's panel moves a booking by drag or "Wybierz rezerwację do przeniesienia" → "Przenieś do: Stanowisko, Data" ("Nie udało się przenieść rezerwacji" on failure); no text in the panel says the player is told. [tenis4U panel](https://panel.tenis4u.pl/) — read 2026-10-08
- **[POLICY]** kluby.org: "Możliwość zamiany miejscami rezerwacji na grafiku" (2016), "historii odwołanych i przeniesionych rezerwacji" (2020); its notices to players are listed for classes and debts, not for a moved booking. [Co nowego 2016](https://oferta.kluby.org/changelog?rok=2016), [2020](https://oferta.kluby.org/changelog?rok=2020) — read 2026-10-08
- **[ABSENT]** What the booker receives when a tenis4U or kluby.org desk moves a booking: not in either system's text, help videos (kluby.org "2.3.2. Edycja rezerwacji" is a video whose captions could not be read) or reviews — read 2026-10-08

---

## 9. How a desk hears of a new online booking (R-EMAIL-18, 19)

### tenis4U: a list of people per court, and SMS at 30 gr
- See `#tenis4u-staff-by-role-and-a-list-of-people-told-about-bookings`: "Lista osób powiadamianych o rezerwacji w korcie" and "Numer telefonu do powiadomień SMS … 30 gr za każdy sms". The homepage sells "Powiadomienia o rezerwacjach". [tenis4u.pl](https://tenis4u.pl/) — read 2026-10-08
- **[ABSENT]** A daily summary or a sound in the panel — no such text in the panel bundle — read 2026-10-08

### kluby.org: notices to staff, to several addresses, and a daily mailing
- **[POLICY]** "Powiadomienie dla pracownika o odwołanej rezerwacji" (2020), "Możliwość ustawienia powiadomień na więcej niż jeden adres e-mail" (2018), "Rozszerzenie wyświetlania się wyników w codziennym mailingu" (2020, under Liga — a daily email exists, for league results). [Co nowego 2018](https://oferta.kluby.org/changelog?rok=2018), [2020](https://oferta.kluby.org/changelog?rok=2020) — read 2026-10-08
- **[ABSENT]** Whether kluby.org emails a desk each new online booking or a daily digest of them — the changelog names notices for cancellations only — read 2026-10-08

### Playmore: not found
- **[ABSENT]** How a Playmore/Reservise desk hears of a new booking: the public web app holds player text only, and `reservise.com` is now a migration page — read 2026-10-08

---

## 10. What a club can add to its confirmation (R-EMAIL-3)

### tenis4U opens the door from the app; kluby.org gives a PIN
- **[POLICY]** tenis4U's TTLock integration: "Wejście na kort może otworzyć osoba posiadająca opłaconą rezerwację. Gracz nie musi wpisywać żadnych kodów, w wygodny sposób otwiera drzwi poprzez aplikację." The panel also writes messages "widoczna dla użytkowników". [tenis4U panel](https://panel.tenis4u.pl/) — read 2026-10-08
- **[POLICY]** kluby.org: "Wejście na obiekt za pomocą kodu", "otwieranie drzwi na PIN", "Historia wykorzystania kodów PIN" (2022). [Funkcje](https://oferta.kluby.org/funkcje), [Integracje](https://oferta.kluby.org/integracje) — read 2026-10-08
- tenis4U also gives a player a personal door code: `gaps-CHECKIN.md#tenis4us-door-code-is-personal-permanent-and-opens-only-around-the-game`.
- **[ABSENT]** A free-text message or the club's address inside tenis4U's or kluby.org's booking confirmation — read 2026-10-08

---

## 11. A tenis4U club's payouts from Przelewy24 (R-EMAIL-21)

### Przelewy24 pays out on a threshold or a schedule, and lists each payout in the panel
- **[POLICY]** "Wypłata środków na wskazany rachunek bankowy odbywa się zgodnie z harmonogramem ustawionym odgórnie na 1000 zł. Częstotliwość wypłat można dostosować … wariantu czasowego lub kwotowego"; a payout can be ordered at once; "Historia wypłat" lists each package and the transactions in it, less refunds; an invoice for the commission appears by the 7th of each month. [P24 panel manual, pp. 16–19](https://www.przelewy24.pl/storage/app/media/do-pobrania/rozpoczecie_wspolpracy/instrukcja_obslugi_panelu_transakcyjnego_pl.pdf), [P24 help: How do I pay out the funds?](https://www.przelewy24.pl/en/help-center/i-sell-with-przelewy24/balance-and-payouts/how-do-i-pay-out-the-funds) — read 2026-10-08
- **[POLICY]** Tpay: payouts manual or automatic, set in the merchant panel, arriving within three business days. [Tpay support](https://support.tpay.com/en/faq/jak-moge-wyplacic-srodki-zgromadzone-na-koncie-w-tpay-com) — read 2026-10-08
- **[ABSENT]** An email to the merchant for each P24 or Tpay payout: not in either's help or P24's manual — read 2026-10-08

---

## 12. Stripe and a connected club's account (R-EMAIL-23)

### Stripe writes to a full-Dashboard club itself when requirements change
- **[DOCS]** "When Stripe is responsible for collecting requirements (`controller.requirement_collection` is `stripe`), Stripe handles upcoming requirement changes for your connected accounts automatically." [Stripe: Handle verification updates](https://docs.stripe.com/connect/handle-verification-updates) — read 2026-10-08
- **[DOCS]** For accounts with a Stripe-built Dashboard, "Stripe will proactively reach out and collect information about your accounts whenever requirements change … If you cannot update your account information by the deadline, payouts to your bank account and your ability to accept payments will be paused." [Stripe support](https://support.stripe.com/questions/communicating-updates-to-verification-requirements-for-connected-accounts-that-have-access-to-a-dashboard-built-by-stripe) — read 2026-10-08
- **[DOCS]** "Stripe will still notify the individual Standard or Express connected accounts directly"; the platform's own emails come "near-immediate" for an action that "immediately degrades a capability", and in a daily batch for degradations "that follow a grace period, which is typically 7 to 30 days". [Stripe: Emails for connected account onboarding and risk requirements FAQ](https://support.stripe.com/questions/emails-for-connected-account-onboarding-and-risk-requirements-faq) — read 2026-10-08
- Language: see `#stripe-speaks-no-polish-to-a-club`.

---

## 13. A dispute on a court booking (R-EMAIL-24)

### Stripe tells the account holder by email, Dashboard, event and push
- **[DOCS]** "We notify you of a dispute through … Your email address, The Stripe Dashboard, A `charge.dispute.created` event …, A push notification"; the window to respond is "usually 7 to 21 days". For direct charges the response comes from the connected account and the disputed amount leaves its balance. [Stripe: Respond to disputes](https://docs.stripe.com/disputes/responding), [Disputes on Connect platforms](https://docs.stripe.com/disputes/connect) — read 2026-10-08

### The evidence Stripe asks for on an "offline service"
- **[DOCS]** "Offline services include purchases that are made in advance, such as event tickets and reservations, where evidence of a cancellation policy can be material." Fields: `cancellation_policy`/`refund_policy` (the policy "as provided to the customer"), `cancellation_policy_disclosure` ("how and where you provided the applicable policy … prior to purchase"), `cancellation_rebuttal`, `customer_communication`, `uncategorized_text`; for "Product not received", `service_date` and `service_documentation`. [Stripe: Dispute categories](https://docs.stripe.com/disputes/categories) — read 2026-10-08

---

## 14. A hold let go in seconds (R-EMAIL-7, and the club lens's opinion)

### mBank drops a hold when the shop's cancellation arrives, else after 14 days online
- **[POLICY]** "Sprzedawca może anulować transakcję" — the bank removes the hold on receiving it; otherwise "Pieniądze blokujemy do 14 dni … blokada wygaśnie po 14 dniach" for internet purchases (7 days for card-present); "maksymalny czas blokady autoryzacyjnej wynosi do 30 pełnych dni". [mBank: karty debetowe — pytania i odpowiedzi](https://www.mbank.pl/indywidualny/karty/pytania-i-odpowiedzi/karty-debetowe) — read 2026-10-08
- **[DOCS]** Stripe: "Card statements from some issuers … don't always distinguish between authorizations and captured (settled) payments, which can sometimes confuse customers." [Stripe: Place a hold on a payment method](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method) — read 2026-10-08
- **[POLICY]** Playtomic explains in its help: "A temporary hold, also known as a pre authorization, is not a charge … depending on your bank, you will see this pre-authorization reflected as a pending charge." [Playtomic: temporary hold](https://playerhelp.playtomic.com/hc/en-gb/articles/19831499991441) — read 2026-10-08
- **[ABSENT]** How many seconds or hours a Polish bank app keeps showing a hold the merchant cancelled at once: no bank publishes it (mBank, PKO BP, ING searched) — read 2026-10-08

### The name on the hold is the club's
- **[DOCS]** "The customer's statement uses the connected account's static component for … Direct charges"; "Only the first 22 characters … are sent for card payments." [Stripe: Statement descriptors for connected accounts](https://docs.stripe.com/connect/statement-descriptors) — read 2026-10-08

---

## 15. The emailed payment confirmation and the cash register (R-EMAIL-4)

### The exemption turns on the club's records, not on the email
- **[LAW]** Dz.U. 2024 poz. 1902, annex poz. 42: services to consumers paid in full through a bank or payment institution, "a z ewidencji i dowodów dokumentujących zapłatę jednoznacznie wynika, jakiej konkretnie czynności dotyczyła". Nothing in it requires anything to be sent to the buyer (poz. 41, for mail-order goods, adds "i na czyją rzecz została dokonana (dane nabywcy …)"). [Dz.U. 2024 poz. 1902 (Sejm ELI text)](https://api.sejm.gov.pl/eli/acts/DU/2024/1902/text.html) — read 2026-10-08
- **[DOCS]** In the KIS ruling cited in `local-market.md`, the identifiers sit in each payment's transfer title from the payment operator to the seller's bank account ("Każda wpłata posiada tytuł który zawiera … informacje o identyfikatorach przejazdu"); of the emailed confirmation KIS says the seller "możecie Państwo udokumentować fakt zapłaty za tą usługę dowolnym dokumentem, w tym elektronicznym potwierdzeniem płatności … elektroniczne potwierdzenia płatności nie są to dokumenty przewidziane przez przepisy o podatku od towarów i usług". [KIS 0113-KDIPT1-3.4012.602.2026.2.JM](https://eureka.mf.gov.pl/informacje/podglad/710095) — read 2026-10-08
  - *Reading:* an email with no booking number does not by itself lose the exemption; what must tie each payment to its game is the club's own record of payments and payouts. Whether a Stripe payout line carries that link is the open question, not the email.

---

## 16. Addresses with Polish letters (R-EMAIL-34, and the lenses' opinion that they are rare)

### Interia, WP and Gmail issue no address with a Polish letter
- **[POLICY]** Interia's sign-up checks "Nazwa konta": "3 - 32 znaków", `'A-Z, 0-9, ".", "_"'`, "zaczyna się od litery", ending in a letter or digit (code: `!/[^a-zA-Z0-9_\.\,\_]/`). [Interia: konto pocztowe](https://konto-pocztowe.interia.pl/) (main.202609231240.js) — read 2026-10-08
- **[POLICY]** WP (`@wp.pl`, `@o2.pl`): the login must match `/^[\w.-]+$/` (Latin letters, digits, `_`, `.`, `-`), at least 3 characters, no `..`, else "forbiden_chars". [WP Konto: rejestracja](https://konto.wp.pl/rejestracja) (pages/rejestracja-c1d19f48d02c023e.js) — read 2026-10-08
- **[POLICY]** Gmail: "Usernames can contain letters (a-z), numbers (0-9), and periods (.)". [Gmail Help: Create a username](https://support.google.com/mail/answer/9211434) — read 2026-10-08
- **[ABSENT]** Onet's rule: its registration page (konto.onet.pl/register) loads the rule from code not reachable without passing its bot challenge — read 2026-10-08

### Domains with Polish letters: under 1 % of .pl
- **[DOCS]** "At the end of the third quarter of 2025, the .pl domain Registry contained 24,330 names with national diacritical characters (so-called IDN domains), representing 0.95% of all names active in DNS. In Q3 2025, 1,940 IDNs were registered." [NASK: Q3 2025 report](https://www.dns.pl/sites/default/files/2026-02/NASK-Q3-2025-REPORT-EN.pdf), p. 13 — read 2026-10-08
- **[ABSENT]** How many Polish players use an address with a letter outside English: no survey found (NASK, UKE, GUS searched) — read 2026-10-08
  - *Reading:* the three big free mailboxes read here cannot issue one, and a domain with a Polish letter is under 1 % of .pl; such an address is a corner case, mostly a company's own IDN domain.

---

## 17. A desk that resells a late-cancelled court (R-EMAIL-11)

### Kraków rules waive the fee when the court is resold, and say nothing of telling the player
- **[POLICY]** Atras: a late canceller "zostanie obciążony opłatą wynajmu kortu za zarezerwowany okres, chyba że kort zostanie wynajęty przez innego klienta. W takiej sytuacji klubowicz, który odwołał rezerwację po terminie, będzie zwolniony z opłaty." For a no-show only: "O fakcie niestawienia się na korcie i powstałej zaległości pracownik recepcji klubu poinformuje klubowicza w danym dniu lub następnym." [Atras regulamin](https://www.atrassquash.pl/regulamin/) — read 2026-10-08
- **[POLICY]** Miazga: "Klubowicz zostanie zwolniony z opłaty za nieterminową anulację jeżeli kort zostanie zarezerwowany i opłacony przez innego gracza." [Miazga regulamin §4b](https://www.miazgasquash.pl/regulamin/) — read 2026-10-08
- **[ABSENT]** A Kraków rule or system text that tells the booker the court was, or was not, resold: not in Atras, Miazga, Squash4You, Garden Padel or Fame Sport rules, nor in tenis4U's or kluby.org's text — read 2026-10-08
  - *Reading:* today the late canceller learns the outcome when the desk asks for, or does not ask for, the money; Atras's desk tells a no-show of the debt within a day.

---

## 18. Lens opinions checked

### Kraków desks open until 23:00 or midnight (the R-EMAIL-15 opinion)
- **[POLICY]** Atras Squash: "Godziny otwarcia Pon – Pt: 7:00 – 24:00 Sob – Nd: 8:00 – 22:00". Garden Padel: "Poniedziałek - Niedziela 7:00 - 23:00". [atrassquash.pl](https://www.atrassquash.pl/), [gardenpadel.pl](https://gardenpadel.pl/) — read 2026-10-08
  - *Reading:* at 20:15 on a Thursday these desks are open; whether anyone watches an email inbox there is not published.

### Kraków's foreign workforce (the R-EMAIL-31 opinion)
- **[DOCS]** ABSL 2025: "19,6% pracowników sektora to obcokrajowcy" in Poland's business-services centres (about 96,000 people; Ukraine 23.4 %, India 10.9 %, Belarus and Italy 8.3 % each, as most-named countries); Warsaw and Kraków each employ over 100,000 in the sector. [ABSL: Sektor usług biznesowych w Polsce 2025](https://invest.lodz.pl/files/public/aktualnosci/2025/ABSL-2025-PL.pdf), pp. 38, 99, 106 — read 2026-10-08
- **[ABSENT]** A Kraków-only share of foreign or English-speaking residents among racket players — read 2026-10-08
  - *Reading:* a large, partly non-Polish workforce sits in Kraków; the most common origin is Ukrainian, not English-speaking, so neither English-only nor Polish-only emails serve everyone.

### What Poles are told to check in a suspicious email (the R-EMAIL-32 opinion)
- **[DOCS]** CERT Polska, as relayed by a voivodeship office: phishing was 64 % of incidents reported to CERT Polska in 2023 (41,423); readers are told to check "sam adres URL oraz adres nadawcy e-maila", and to distrust urgency, an unexplained account block and requests to pay. [Kielce voivodeship office: Phishing jako najczęściej spotykana forma cyberataków](https://www.kielce.uw.gov.pl/pl/biuro-prasowe/aktualnosci/28424,Phishing-jako-najczesciej-spotykana-forma-cyberatakow.pdf) — read 2026-10-08
- **[ABSENT]** Guidance that a plain, uniform layout makes a fake easier to spot — read 2026-10-08

### Bonarka Arena's door code (the R-EMAIL-3 opinion)
- Not a market question: Bonarka Arena is the seeded club in Raketa's own test data. The market facts on codes in confirmations are in §10 above and `platforms.md#matchi--access-codes-in-the-confirmation`.
