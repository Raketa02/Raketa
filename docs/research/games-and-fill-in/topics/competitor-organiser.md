# Playtomic from the organiser's side

The organiser is the player who starts a game and gathers the others. The main competitor is **Playtomic**, which
the spec compares itself with (`the-mechanics.md` Appendix B). It has no club in Kraków
([below](#playtomic-has-no-club-in-krakow)). The local rivals are in `topics/platforms.md` and
`topics/local-market.md`.

**Sources.** Playtomic's player (94 articles) and club (157 articles) help centres were read in full through their
public Zendesk API (`/api/v2/help_center/en-gb/articles.json`), since the pages return HTTP 403. Links point at the
human page. The [Legal Conditions](https://playtomic.com/legal-conditions) carry no date.

**Dates and kinds.** *Read 2026-10-06* or *2026-10-07* means the fact is carried over from
[`../../games-and-fill-in-market.md`](../../games-and-fill-in-market.md) §1, §5 or §7. *Read 2026-10-08* means it
is new, or was re-read today because its article changed or a grade will lean on it. Each fact is tagged
`[POLICY]`, `[PRICE]`, `[COMPLAINT]` or `[ABSENT]`. No `[MEASURED]`: the app was not used.

## Summary

### Read this first

- **The owner of a private booking runs the game, and an open match has no organiser.** The owner picks the
  people, can remove them, and answers for the whole court. An open match's first player sets its type, its gender and
  (through their own level) its level range, pays their own spot, and has no more power after that than anyone
  else ([powers](#who-has-organiser-powers-in-an-open-match-nobody)).
- **The organiser pays first, and at once.** Starting an open match charges your own spot and the service fee at
  once: 3,99 zł on any share of 19,95 zł or more. In a split private booking the owner pays their own share at
  booking, and in Poland any shares left unpaid most likely become **a debt that blocks new bookings**
  ([guarantees](#who-covers-unpaid-shares-three-guarantees-by-country)).
- **An open match that doesn't fill costs nothing.** Everyone is refunded in full, fee included, about 1 h before
  the start. A *private* booking is never cancelled for being short: the owner pays the court under the club's
  policy ([complaints](#a-private-booking-is-not-cancelled-when-the-group-does-not-come-together)).
- **Converting to public traps the owner:** they can't leave and pay for every empty seat
  ([converting](#converting-a-private-booking-into-a-public-match)).
- **Groups are chat rooms.** A group of up to 200 people, joined by link, exists to share links to matches. Nothing
  proposes or books a game for a group, and only clubs can create repeating bookings
  ([groups](#playtomic-groups-are-chat-groups-not-game-pools), [recurring](#recurring-games-only-the-club-can-create-them)).
- **Nobody is told who joined or left an open match.** That notice exists only for community matches, played
  outside Playtomic ([notices](#the-organiser-is-not-told-when-someone-joins-or-leaves-an-open-match)).
- **New since 2026-10-06:** the Terms define a no-show (10 minutes late, leaving early, being replaced)
  ([no-shows](#no-shows-and-late-arrivals)).

## 1. Starting a game

### Two ways to organise: a private booking or an open match

- Private booking: "You are the 'owner' of the booking"; "Use it only if you already have other players"; "You are responsible for your reservation"; pay in full or split; "It won't be cancelled automatically if you haven't added all players"; the club's cancellation policy applies. **[POLICY]** [Private Bookings vs Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831958258193-Private-Bookings-vs-Open-Matches) (updated 2026-10-07) — read 2026-10-08
- Open match: "Reserve and pay only your spot"; "You are not responsible for the reservation"; online payment only; "If all four players are not enrolled, the system automatically cancels and refunds the players"; usually 90 min. Padel and tennis only. An open match can never become private. **[POLICY]** [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/19831958258193-Private-Bookings-vs-Open-Matches) — read 2026-10-08
- Both take 2 or 4 players, never more. Two on a double court pay the full court, and single payment is advised. **[POLICY]** [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/19831958258193-Private-Bookings-vs-Open-Matches) — read 2026-10-08

### Creating an open match: the doors and what the creator sets

- Two doors: *Find a match* → sport → where → when → "opening one yourself"; or a club's *Open Matches* tab → a slot → "Create a new match". An empty search offers "**Be the first player!** — Create a new match by selecting the hour you want" and "+ Start a match". **[POLICY]** [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match-Padel-Tennis), [favourite Club](https://playerhelp.playtomic.com/hc/en-gb/articles/19831715222929-How-to-book-a-court-or-a-spot-in-a-match-in-your-favourite-Club), [image](https://playerhelp.playtomic.com/hc/article_attachments/43674616041361) — read 2026-10-08
- The creator chooses "Competitive or casual" and "the gender or keep it open for all"; "it is not possible to switch from competitive to casual or vice versa". The screen reads "Competitive Match — The result will affect your level and rankings · Match Range Level 0.25 – 1.25 · Players out of the level can request access" or "Friendly Match — The result will not affect your level or rankings". **[POLICY]** [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match-Padel-Tennis) (updated 2026-10-03), [image 6](https://playerhelp.playtomic.com/hc/article_attachments/43661025983761) — read 2026-10-08
- Gender is All Players (the default), Only Women, Only Men or Mixed. It is fixed by the first player: "the only way to change the gender is to delete (if possible) the public match and create a new one". **[POLICY]** [Gender of the match in Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831467158801-Gender-of-the-match-in-Open-Matches) — read 2026-10-08
- The creator can bring and pay for **one partner**, at creation only: "Invitation and payment for the other player can only be done when you join". The pair leaves together, and only the payer can cancel. **[POLICY]** [Add My Partner](https://playerhelp.playtomic.com/hc/en-gb/articles/19831380139793-Add-My-Partner) — read 2026-10-08
- The creator does not choose a court: "courts are assigned using the 'Autoselect' option". The court type stays fixed ("never move them to a 'Wall' court"). **[POLICY]** [How to manually book a court for a Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535050634769-How-to-manually-book-a-court-for-a-Open-Match), [How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473-How-to-configure-Open-Matches-at-your-Club) — read 2026-10-08
- "When you create an Open Match, the standard booking window applies (the same for everyone)", and members' longer windows don't. **[POLICY]** [Club Membership not working?](https://playerhelp.playtomic.com/hc/en-gb/articles/47312414385169) — read 2026-10-08
- Before starting a match you need an account and a level. A verified phone is needed for "inviting or adding players to a match", "creating a group" or "setting up a community match". A private profile can't take part in open matches. **[POLICY]** [How to verify your phone number](https://playerhelp.playtomic.com/hc/en-gb/articles/51110112972561-How-to-verify-your-phone-number) (read 2026-10-07), [Playtomic Community](https://playerhelp.playtomic.com/hc/en-gb/articles/19831992618769-Playtomic-Community) — read 2026-10-08

### The level range follows the creator

- In a competitive match the range is set from the first player: "based on the first player to join (-0.25 / +0.75)", 1.0 wide in every image ("0.25 – 1.25" for a 0.50 creator). A Friendly match is 0–7 by default. A club's own offsets apply only to matches the club launches. **[POLICY]** [How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473-How-to-configure-Open-Matches-at-your-Club), [image 5](https://playerhelp.playtomic.com/hc/article_attachments/43661039908753) — read 2026-10-07
- Someone outside the range can "Request a spot". Every enrolled player is notified, and "it is enough for one player to reject". "Spots are not reserved during the approval process". **[POLICY]** [How to request a spot in a open match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832027031569-How-to-request-a-spot-in-a-open-match) — read 2026-10-08
- No source says what happens to the range or the gender when the creator leaves after others have joined. **[ABSENT]** I searched all 251 articles for "first player", "creator" and "organizer", and searched the web — read 2026-10-08

### What the creator pays: the spot and the service fee

- "For… public matches… the user will be charged immediately, regardless of the country or model". The spot is paid online by card or Club Wallet, never at the club. **[POLICY]** [Legal Conditions §7](https://playtomic.com/legal-conditions), [How to sign up for an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19832151055121-How-to-sign-up-for-an-Open-Match-Padel-Tennis) — read 2026-10-06
- Poland's fee table: open matches 20.0 %, at least 1.24 PLN and at most 3.99 PLN; player bookings "NO FEE". **[PRICE]** [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337-Service-Fee) ([Poland table](https://playerhelp.playtomic.com/hc/article_attachments/39560464619025)) — read 2026-10-06
  - On Raketa's shares: 40 zł → 3,99 zł (20 % would be 8 zł), 43,99 zł in all; 25 zł → 3,99 zł, 28,99 zł in all. Every share of 19,95 zł or more pays 3,99 zł. **[PRICE]** (arithmetic on the table; Playtomic doesn't say this)
- The fee is folded into the checkout "Total … Playtomic service fee and Tax incl.". It is refunded "If you delete yourself from an open match or if the match is canceled", and kept when a private reservation is cancelled. **[POLICY]** [Add My Partner (image)](https://playerhelp.playtomic.com/hc/article_attachments/43751051675665), [Service Fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831779272337-Service-Fee) — read 2026-10-07
- The price per spot can change while the match fills: "players joining at different times may pay different fees based on the court available at that moment". **[POLICY]** [How to configure "Open Matches"](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473-How-to-configure-Open-Matches-at-your-Club) — read 2026-10-06
- Premium removes the fees. The Polish App Store sells it as "Basic Monthly 47,99 zł" and "Basic Annual 300,00 zł". **[PRICE]** [Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited), [App Store PL](https://apps.apple.com/pl/app/playtomic-play-padel/id1242321076) — read 2026-10-06

### Who has organiser powers in an open match: nobody

- "Each player is only responsible for their own spot and cannot delete another player, unless you use the feature 'Add My Partner'." Spot requests are decided by every enrolled player, not by the creator. **[POLICY]** [How to Change Player Positions in an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/43819065293457-How-to-Change-Player-Positions-in-an-Open-Match) (read 2026-10-06), [How to request a spot](https://playerhelp.playtomic.com/hc/en-gb/articles/19832027031569-How-to-request-a-spot-in-a-open-match) — read 2026-10-08
- No player can cancel a whole open match: each one leaves only their own spot ("click on the red cross of your photo"). Only the club cancels a match, from Manager, and "once an open match is cancelled, it can't be restored". **[ABSENT]** for a player-side cancel (searched the 94 player articles); **[POLICY]** [How can I delete myself from a Public Match?](https://playerhelp.playtomic.com/hc/en-gb/articles/19832116272785-How-can-I-delete-myself-from-a-Public-Match), [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) — read 2026-10-08
- Swaps go through the club: "it is the Club that removes one player so that another can be added", no later than 2 h before the start. **[POLICY]** [FAQ Players](https://playerhelp.playtomic.com/hc/en-gb/articles/19831519179281-FAQ-Players-Playtomic), [Common Booking Issues](https://helpmanager.playtomic.com/hc/en-gb/articles/20534585454097-How-to-Handle-Common-Booking-Issues-A-Quick-Guide-for-Your-Club) — read 2026-10-06
- The match chat is public ("Any user will be able to access it") and moderated by the club and Playtomic. **[POLICY]** [How you can chat with players in Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19832063135249-How-you-can-chat-with-players-in-Matches-or-Tournaments) — read 2026-10-08

### The organiser is not told when someone joins or leaves an open match

- The push notifications are follows, likes, comments, tags and "Contact's activity" (someone you follow "joins or creates a new match"). The emails are confirmation, receipt and cancellation ("cannot be disabled"). Nothing tells you someone joined or left *your* match. **[POLICY]** + **[ABSENT]** [How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App) (updated 2026-09-29) — read 2026-10-08
- Only a community match promises it: "When a player signs up or is removed from your match, you will receive a notification in the app." **[POLICY]** [Community Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481-Community-Match-Play-on-Any-Court-Anywhere) — read 2026-10-08

## 2. Gathering the others

### Inviting people to a private booking

- The owner adds players before paying or afterwards ("the + button where it says 'invite'"), by name, email, phone or contacts. "If you're the only one in the booking, only two out of three empty places will appear active". Friends can also add themselves through the link: *Share externally*, *Copy link* or *Forward by chat*. **[POLICY]** [Add my friends to a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/43212099147025-Add-my-friends-to-a-reservation) — read 2026-10-08
- Only the club can add someone without an account, "as a guest". **[POLICY]** [How to Add and Remove Players in a Private Reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535398512657-How-to-Add-and-Remove-Players-in-a-Private-Reservation) — read 2026-10-08

### Sharing and promoting an open match

- Players invite friends "by sharing the match link via WhatsApp or various social media platforms". A club can copy the link only once "at least one player" is registered. **[POLICY]** [Sharing a Match to increase participants](https://helpmanager.playtomic.com/hc/en-gb/articles/20535063385873-Sharing-a-Match-to-increase-participants) — read 2026-10-08
- Followers get a "Contact's activity" push when you create or join a match (you can opt out of sharing). **[POLICY]** [notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App) — read 2026-10-08
- Premium: "Matches you create or join are promoted as Golden Matches, helping you find players faster to fill your court". The Polish store text adds "we will assign [a court] to you immediately". **[POLICY]** [Premium Plan: Unlimited](https://playerhelp.playtomic.com/hc/en-gb/articles/19831696399633-Premium-Plan-Unlimited), [App Store PL lookup (v6.93.2)](https://itunes.apple.com/lookup?id=1242321076&country=pl) — read 2026-10-08
- Playtomic runs WhatsApp groups, one per level band, in Spanish cities and the Gulf (none in Poland), for "enlaces de partidos que necesitan más jugadores". **[POLICY]** [Grupos oficiales de WhatsApp… Murcia](https://playerhelp.playtomic.com/hc/es/articles/42880380517905), [Dubai](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492584721-Official-WhatsApp-groups-to-organize-matches-in-Dubai) — read 2026-10-08

### Playtomic groups are chat groups, not game pools

- "Create your own Playtomic chat group". The admin can "add or remove participants", "share the link of the group to promote your matches" and "Reset the link". A group has one sport, a name (at most 30 characters) and a description (at most 500). "These groups are 'private': only user with the link can access"; "You cannot add more than 200 users". **[POLICY]** [How to create a chat group](https://playerhelp.playtomic.com/hc/en-gb/articles/19831494082705-How-to-create-a-chat-group) — read 2026-10-08
- No article describes a match made for a group, offered only to its members, or proposed from the members' levels or hours. A group promotes matches by posting their links. **[ABSENT]** (searched 251 English articles and the Spanish ones for "group"/"grupo", and the web) — read 2026-10-08

### Community matches: the organiser books the court outside Playtomic

- *Start a match* → "I already know where I'm playing" creates a **Community Match** at any court. It has no booking or payment in the app: the creator is "Contacting the sports facility directly to book the court", "Paying for the court reservation on your own" and "Coordinating with other players on splitting the court costs". Options are an optional price per person ("the match creator is responsible for collecting payments") and "Mark the match as private" (link only). **[POLICY]** [Community Match](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481-Community-Match-Play-on-Any-Court-Anywhere) (updated 2026-06-19) — read 2026-10-08
- This organiser does have powers: "As an organizer, you can cancel the match you have created at any time", remove players, and chat with everyone. **[POLICY]** [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/19831629310481-Community-Match-Play-on-Any-Court-Anywhere) — read 2026-10-08

### Recurring games: only the club can create them

- "Can players create recurring reservations from the app? No, you must do them from Playtomic Manager." In a club's series, payments "are not automatically enforced", and "Participants can leave… at any time. The club's cancellation policy only applies to the booking owner". **[POLICY]** [Recurring booking series](https://helpmanager.playtomic.com/hc/en-gb/articles/20535145594513-Recurring-booking-series) — read 2026-10-08

## 3. The private booking's owner and the money

### Pay everything or pay your part

- At checkout the owner chooses "Pay your part" or "Pay everything", with the club's policy on the same screen. Paying your part means "if the total of the court is € 20, you only have to pay € 5". **[POLICY]** [How to split the payment of a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation) — read 2026-10-08
- "Split payment is not available on the Playtomic website"; a booking "cannot be changed from single payment to split payments, or vice versa". **[POLICY]** [Split Payment vs Single payment](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721-Split-Payment-vs-Single-payment) (updated 2026-10-05) — read 2026-10-08
- The owner can't pay someone else's share. To cover everyone, "ask the other players not to pay — their unpaid shares will be automatically charged to you 2 hours after the match ends". **[POLICY]** [How to split the payment](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation) — read 2026-10-08

### Who covers unpaid shares: three guarantees by country

- **Card on File** (US; Mexico, Spain, Belgium, France, Germany, Sweden, Cyprus, Greece, Malta, Indonesia, Switzerland, Liechtenstein): the owner pays their share and must keep a saved card. Unpaid shares are charged to it 2 h after the match, then to the owner's other cards, and if all fail they become a debt. "The booking owner cannot remove their card on file while they have an upcoming split-payment booking." **[POLICY]** [Card on File (CoF): your guarantee for split payment bookings](https://helpmanager.playtomic.com/hc/en-gb/articles/46647891110673-Card-on-File-CoF-your-guarantee-for-split-payment-bookings) — read 2026-10-08
- **Pre-authorisation** (Italy, UK, Portugal, Norway; the Netherlands until 14 Sep 2026): "The full reservation amount is temporarily frozen… on the booking owner's payment method". It is released when everyone has paid, or used 2 h after the match, "always capped at the full booking amount". **[POLICY]** [How a pre-authorization works](https://helpmanager.playtomic.com/hc/en-gb/articles/20534487294097-How-a-pre-authorization-works), [Split payment bookings: statuses and charges](https://helpmanager.playtomic.com/hc/en-gb/articles/50423411876881-Split-payment-bookings-statuses-and-charges-in-Playtomic-Manager) — read 2026-10-08
- **Debt system:** "The booking owner pays only their own share at the time of booking — no hold and no saved card required". Unpaid shares become "a debt on the booking owner's profile", because "Playtomic advances the outstanding share to the club". It is paid "using a card (wallet payment is not allowed)" and "cannot be cancelled by the club". A debt "will prevent you from making new bookings until it's settled". **[POLICY]** [Split Payment vs Single payment](https://helpmanager.playtomic.com/hc/en-gb/articles/20535331224721-Split-Payment-vs-Single-payment), [How to split the payment](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation) — read 2026-10-08
- **Poland** is on neither of the first two lists, so the Debt system applies there. That is an inference: no article names the Debt-system countries. **[ABSENT]** for a statement about Poland (searched all 251 articles for "Poland", "Polish" and "PLN"; only the fee tables mention it) — read 2026-10-08
- The Terms soften this: "Failed payments due to technical issues, expired cards, or insufficient funds do not automatically create a debt with Playtomic and may be handled directly by the corresponding club." **[POLICY]** [Legal Conditions §8](https://playtomic.com/legal-conditions) — read 2026-10-08

### Chasing the others for their share

- The others have until "2 hours after the match ends", and then "the charge falls on the booking owner". The owner's remedy is to "cover the amount and use the match chat to request reimbursement directly from them". The only tracking shown is a status list "(pending or paid)"; no automatic reminder is described. **[POLICY]** + **[ABSENT]** [How to split the payment](https://playerhelp.playtomic.com/hc/en-gb/articles/19832089052561-How-to-split-the-payment-of-a-reservation) — read 2026-10-08
- If someone pays at the desk and the club doesn't mark it within 2 h, the owner is charged, and "the club will need to refund the booking owner directly". The window closes early: "Once a player uploads the match result in the app, their payment can no longer be marked as Paid". **[POLICY]** [How to mark a booking or activity as paid](https://helpmanager.playtomic.com/hc/en-gb/articles/46928469100817) — read 2026-10-08

### Removing players and the owner leaving

- "Reservation owner: Can change player positions and remove players"; "Other players: Can only change player positions". This lasts until the results are entered. **[POLICY]** [Changing Player Positions in Your Private Booking](https://playerhelp.playtomic.com/hc/en-gb/articles/19831825132049-Changing-Player-Positions-in-Your-Private-Booking) — read 2026-10-08
- If the owner removes a player who already paid a split share, that player is refunded "and you will assume the debt". The owner "can not delete yourself from the reservation… only… cancel the entire reservation". **[POLICY]** [How to remove players from a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19831783889425-How-to-remove-players-from-a-reservation) — read 2026-10-08
- "If you are the owner of the booking and cannot play, you can cancel the reservation as long as it's within the club's cancellation policy (all players will be refunded). Then the remaining players can book the same slot again". Not even the club can remove the owner ("the first player in Team A"). **[POLICY]** [Changing Player Positions in Your Private Booking](https://playerhelp.playtomic.com/hc/en-gb/articles/19831825132049-Changing-Player-Positions-in-Your-Private-Booking), [Add and Remove Players in a Private Reservation](https://helpmanager.playtomic.com/hc/en-gb/articles/20535398512657-How-to-Add-and-Remove-Players-in-a-Private-Reservation) — read 2026-10-08

### Cancelling a private booking

- The owner can cancel in the app only inside the club's policy, which the club sets in hours, with no default. Outside it, "Playtomic will not be able to cancel or reschedule your reservation"; for weather, ask the club. A booking can't be edited: "this decision is entirely up to the Club". **[POLICY]** [How to cancel a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832121593873-How-to-cancel-a-reservation), [How to modify a reservation](https://playerhelp.playtomic.com/hc/en-gb/articles/19832144958225-How-to-modify-a-reservation), [Reservation rules](https://helpmanager.playtomic.com/hc/en-gb/articles/20535321953297-Reservation-rules) — read 2026-10-08
- Checkout shows the deadline as a date: "Valid up until 32 hours before the booking* — Before Friday 13 February | 11:30: You will receive a refund… After…: Non-cancelable." **[POLICY]** [How to make a reservation (GIF)](https://playerhelp.playtomic.com/hc/en-gb/articles/19831881490449-How-to-make-a-reservation-in-Playtomic-app) — read 2026-10-07
- Cancelling a player-made private booking costs **4.32 PLN** in Poland (with a 1-hour grace period), and the service fee is kept. In a split booking only the owner pays it. **[PRICE]** [Cancellation fee](https://playerhelp.playtomic.com/hc/en-gb/articles/19831791848721-Cancellation-fee) — read 2026-10-06

### Converting a private booking into a public match

- The owner presses "Convert to Public Match" (padel and tennis, free). Everyone invited must have an account and a level, and must have paid if the booking is split. "Your court assignment remains the same"; "You cannot convert it back to private"; the range becomes 0–7. It is blocked if anyone chose "Pay at the club" or cash, if no seat is open, or if the club doesn't allow open matches. **[POLICY]** [How to convert a Private Booking to a Public Match](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match) (updated 2026-10-01) — read 2026-10-08
- The owner: "You cannot leave. If you converted the booking, you're responsible for payment"; "you cannot cancel without paying for the court, even if you don't find enough players". If the match doesn't fill, "The match is not automatically cancelled" and "The owner will be charged for empty spots". **[POLICY]** [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match) — read 2026-10-08
- The others can leave with a refund (invited-before players lose the booking fee); later joiners are refunded 2 h after the start if it never filled. "Once the match is full and you're within 24 hours… no one can leave… No refunds will be issued." The owner can't remove later joiners. **[POLICY]** [same article](https://playerhelp.playtomic.com/hc/en-gb/articles/39545442764945-How-to-convert-a-Private-Booking-to-a-Public-Match) — read 2026-10-08
- On the club side, "Clubs cannot convert a private reservation into an open match". After a conversion players "cannot cancel it in the app, even if the booking is still within the club cancellation policy", and the club "can choose whether to approve" a cancellation. **[POLICY]** [Convert a private booking into an open match](https://helpmanager.playtomic.com/hc/en-gb/articles/46236279793425-Convert-a-private-booking-into-an-open-match) — read 2026-10-08

## 4. When the game does not fill

### The court is held in stages

- "0 or 1 player: The court is never booked. 2 players: … only if more than 12 hours remain… 3 players: … only if more than 4 hours remain… 4 players: The court is booked immediately and the match is confirmed." In 20 listed countries one player holds the court until 48 h before. Poland is not one of them. **[POLICY]** [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) (updated 2026-10-08), [Open Matches Occupy Club Calendar Slots](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929) — read 2026-10-08
- When the court is released, the match "stays open" "As long as the club still has an available court". Private reservations "always take priority over open matches that aren't full". **[POLICY]** [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) — read 2026-10-08

### Automatic cancellation and refunds

- The match is cancelled when "No court is left available for that time slot", or when it "still hasn't reached 4 players about 1 hour before the scheduled start time, even if a court happens to still be available". Everyone gets "a full automatic refund (including the Playtomic service fee)", and the app says "Cancelled by Anemone". **[POLICY]** [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) (updated and re-read 2026-10-08; it now opens with "doesn't reach 4 confirmed players and doesn't have a court booked by the time the match is about to start") — read 2026-10-08
- The player help gives no hour: "Not enough players join before the start time"; "Our system predicts match completion based on time, club popularity, and player patterns"; "Cancelled matches can't be restored". **[POLICY]** [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465-Cancellation-Policy-for-Open-Matches-Padel-Tennis) — read 2026-10-08
- If the club forces a court onto a short match, "it won't be automatically cancelled". Who then pays for the empty spots is not stated. **[POLICY]** [Open Matches Occupy Club Calendar Slots](https://helpmanager.playtomic.com/hc/en-gb/articles/20535700374929); **[ABSENT]** for the payer — read 2026-10-08
- Search engines still show a retired help centre (`help.playtomic.com`) with cancellation times by headcount (0 players 5 h before … 3 players 1 h). The domain doesn't resolve, so don't cite them. **[ABSENT]** — read 2026-10-08

## 5. Someone drops out

### Leaving an open match, the creator included

- "Match not full yet? Cancel anytime before it starts—no restrictions. Match is full? You can cancel up to 24 hours before the start time. Within 24 hours of a full match, cancellations aren't possible through the app." The club "reserves the right to make exceptions". **[POLICY]** [Cancellation Policy for Open Matches](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465-Cancellation-Policy-for-Open-Matches-Padel-Tennis) (updated 2026-09-30) — read 2026-10-08
- The club help leaves out the "not full" exception: "up to 24 hours before… they should contact the club directly, and the club will decide". Leaving refunds everything, the fee included. **[POLICY]** [How to cancel an Open Match](https://helpmanager.playtomic.com/hc/en-gb/articles/20535128515601) (updated 2026-10-08) — read 2026-10-08
- No separate rule exists for the creator, who leaves like anyone else while the match stays published. Whether someone who left can join again is not stated. **[ABSENT]** [How can I delete myself from a Public Match?](https://playerhelp.playtomic.com/hc/en-gb/articles/19832116272785-How-can-I-delete-myself-from-a-Public-Match) — read 2026-10-08

### Refilling a freed seat

- A seat freed before the 24 h line reopens to everyone in range. There is no waiting list and no offer to the next person; the nearest thing is one free priority alert (unlimited with Premium). **[ABSENT]** [How to manage the notifications](https://playerhelp.playtomic.com/hc/en-gb/articles/19831492072337-How-to-manage-the-notifications-from-Playtomic-App) — read 2026-10-06
- Nobody can transfer their own seat; the club does swaps. For a private booking the owner invites someone else or converts the booking ([above](#converting-a-private-booking-into-a-public-match)). **[POLICY]** [Change Player Positions in an Open Match](https://playerhelp.playtomic.com/hc/en-gb/articles/43819065293457-How-to-Change-Player-Positions-in-an-Open-Match) — read 2026-10-06

### No-shows and late arrivals

- The help: someone who doesn't cancel 24 h ahead and doesn't come "may be reported by the other players" to Customer Care. "The absent player will be charged for the court fees… A debt is created." Those who came and paid online are refunded within up to 10 days, plus 2–15 business days at the bank. Wallet payers are not refunded, and the result is voided. No report is possible once "the match result has already been confirmed… or the match took place more than 7 days ago". **[POLICY]** [What happens if a player doesn't show up?](https://playerhelp.playtomic.com/hc/en-gb/articles/43240624037393-What-happens-if-a-player-doesn-t-show-up) — read 2026-10-08
- The Terms' *Public Matches No Show* section (new to this research): it "may be applied" when someone "arrives ten (10) minutes or more after the scheduled start… or leaves ten (10) minutes or more before the end", "reports an injury before the start", "leaves… before ninety (90) minutes of play", or "is replaced" (the charge "shall be applied to the replaced User"). It doesn't apply once a final result is recorded, to an injury during play, or to court or facility problems. **[POLICY]** [Legal Conditions §4](https://playtomic.com/legal-conditions) — read 2026-10-08
- Facing a late player, "the group has two options". *Wait and Play*: "No refunds will be issued; The full booking fee applies". *Declare No-Show*: "The late player will receive a no-show penalty". "If a match result is added, the no-show will not be applied". **[POLICY]** [Legal Conditions §4](https://playtomic.com/legal-conditions) — read 2026-10-08
- On the club side only a player who came can report, and the window "can't be made as an exception". There is no attendance score, strike count or ban threshold. **[POLICY]** [No-Show Policy for Open Matches](https://helpmanager.playtomic.com/hc/en-gb/articles/50702064570513-No-Show-Policy-for-Open-Matches-what-clubs-need-to-know); **[ABSENT]** for strikes — read 2026-10-06

## 6. After the game

### Results

- Results can be added for 7 days. "If the opposing team does not confirm or modify the results within 24 hours, the results are automatically confirmed", and a result is valid only "if all four players… are included". Positions can be swapped only until results are entered. **[POLICY]** [Legal Conditions §4](https://playtomic.com/legal-conditions), [Change Player Positions](https://playerhelp.playtomic.com/hc/en-gb/articles/43819065293457-How-to-Change-Player-Positions-in-an-Open-Match) — read 2026-10-06

## 7. Poland

### What an organiser in Poland can pay with

- Card, Apple Pay, Google Pay or Club Wallet. No BLIK or Przelewy24 is named in Playtomic's help or Terms, and an open match can't be paid at the club. **[ABSENT]** for Polish methods; **[POLICY]** [Payment Methods in Playtomic](https://playerhelp.playtomic.com/hc/en-gb/articles/19831969439761-Payment-Methods-in-Playtomic) — read 2026-10-06

### Playtomic has no club in Krakow

- No Kraków club appears on playtomic.com. A walk outward from the Polish club pages found 33 Polish clubs (Warsaw, Poznań, Silesia, Toruń, Wrocław and four more cities), none in Kraków, and guessed Kraków addresses return 404. **[ABSENT]** [Playtomic sitemap](https://playtomic.com/sitemap.xml), [old file §1.2](../../games-and-fill-in-market.md) — read 2026-10-06
- Support runs in nine languages, none of them Polish (Mon–Fri 9:30–17:30 CET); the app itself is in Polish (4.81★, 1,479 ratings on the Polish App Store). **[POLICY]** [Customer Support](https://playerhelp.playtomic.com/hc/en-gb/articles/19831718711569-Playtomic-Customer-Support) (updated 2026-10-08), [App Store PL lookup](https://itunes.apple.com/lookup?id=1242321076&country=pl) — read 2026-10-08

## 8. What organisers say

### A private booking is not cancelled when the group does not come together

- "I booked a private padel game for 4 players, but only 2 of us joined. I assumed the booking would automatically be cancelled… I ended up paying £22… referred me back to the club's cancellation policy" (R Sepúlveda, GB, 1★, 2026-08-09). **[COMPLAINT]** [App Store GB reviews (RSS)](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08
- "Book a court and share it by accident. Says you're unable to cancel even when no one has joined" (NotTheMesiah, GB, 1★, 2026-04-25). **[COMPLAINT]** [same feed](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08

### The owner's money is held for split payments

- "it places a holding charge on the remaining players' shares… that hold can stay on your account for up to a week… I want to book another game but won't" (SPARTAN 4q2, GB, 2★, 2026-08-04). "Paid £48 split payments… Money was still held in my account until after the game… only refunded for 2 players, not 3" (Purplesars11, GB, 1★, 2026-06-10). **[COMPLAINT]** [App Store GB reviews (RSS)](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08

### Organising ahead is hard, and late drop-outs go unseen

- "Very difficult to organise games which obviously require a booking in advance. A number of situations where they hasn't let me know about last-minute cancellations" (Adam247247, GB, 1★, 2026-09-21). With no waiting list, players "keep checking" or rely on "the person cancelling via a WhatsApp group" (Kevin the Labradorable, GB, 4★, 2026-08-14). **[COMPLAINT]** [App Store GB reviews (RSS)](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08
- Polish reviewers ask for a queue: "Why do we have to waste our time chatting and checking who frees the spot" (kiloluke, 2026-04-11); "Ktoś rezygnuje, pierwsza osoba z kolejki ma opcję się zapisać np przez 15 min" (maciekmisko, 2026-02-26). **[COMPLAINT]** [App Store PL reviews (RSS)](https://itunes.apple.com/pl/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08

### A half-built game loses its court

- On a group's half-booked court "somebody else jumped on and booked one of the available spaces"; the reviewer asks for a 24-hour hold or approval by the first booker (writer biter, GB, 2024-02-03). "an initial booking can be taken by later bookings with four players" (Slab Princess, GB, 2025-02-21). **[COMPLAINT]** [App Store GB reviews](https://apps.apple.com/gb/app/playtomic-padel-tennis/id1242321076?see-all=reviews) — read 2026-10-06
- At peak hours open matches are "guaranteed to get cancelled by someone booking a private match" (mgbike98766, GB, 2★, 2023-11-16). **[COMPLAINT]** [App Store GB reviews (RSS)](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08

### No-shows the organiser can't report

- "the window for reporting a no-show is closed even though the slot for our game finished two minutes ago… There should be consequences" (shiesb, GB, 1★, 2026-05-14). **[COMPLAINT]** [App Store GB reviews (RSS)](https://itunes.apple.com/gb/rss/customerreviews/page=1/id=1242321076/json) — read 2026-10-08
