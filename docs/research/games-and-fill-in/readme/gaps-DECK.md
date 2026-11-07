# gaps-DECK — index entry

- **File:** [`topics/gaps-DECK.md`](../topics/gaps-DECK.md) answers the DECK area's missing facts (mode `gaps`). It has one `##` section per gap and every fact under a `###` heading.
- **Read:** 2026-10-08. Facts carried from other topic files link there and keep their dates.
- **Sources:**
  - Playmore's web-app code on `playmore.pl/assets/`: 1,367 chunks from the 8 Oct 2026 build. The open-games page is now `DM7ksFDa.js`.
  - Playtomic's help API, and its Android 6.93.2 strings. The lines used are saved in [`shots/gaps-DECK-playtomic-android-6.93.2-strings.txt`](../shots/gaps-DECK-playtomic-android-6.93.2-strings.txt).
  - EUR-Lex: P2B Regulation 2019/1150, the ranking guidelines and the Consumer Rights Directive guidance.
  - The Polish Language Act, Dz.U. 2026 poz. 81.
- **Images:** [`shots/gaps-DECK-playtomic-for-your-level-order.png`](../shots/gaps-DECK-playtomic-for-your-level-order.png), [`shots/gaps-DECK-playtomic-golden-matches-list.png`](../shots/gaps-DECK-playtomic-golden-matches-list.png) and [`shots/gaps-DECK-playtomic-priority-alerts-inbox.png`](../shots/gaps-DECK-playtomic-priority-alerts-inbox.png). All three are Playtomic help-centre images.
- **Counts:** 26 `[POLICY]`, 6 `[LAW]`, 5 `[DOCS]`, 5 `[COMPLAINT]`, 12 `[ABSENT]`; about 33k characters.
- **Digest:** [`areas/DECK.md`](../areas/DECK.md) has a new section, *Gap answers (2026-10-08)*. Its §5 line on "Mało czasu" and §7 not-found line were corrected to match.
- **Differs from earlier files:**
  - Playmore's open-games page does not opt into refresh-on-return or pull-to-refresh. This narrows `topics/gaps-SWIPE.md#neither-playmore-nor-playtomic-redraws-a-roster-live`.
  - "Mało czasu" is a badge in the game creator, not on the card.

## Sections (`##` gap, then `###` headings)

**R-DECK-38 — how a list of games is kept current**
- Playmore reads its open-games list when the page opens and after the player's own actions
- Playmore's open-games page does not re-read on return and has no pull-to-refresh
- Playtomic does not document how its match list refreshes; one player says it needs a restart

**R-DECK-22 — the order of games in a list, and what a platform must tell clubs about it**
- Playmore orders open games by day and hour; nothing puts nearly full games first
- Playtomic lets a player sort matches by number of players; the default is Relevance
- Playtomic's own help image lists a fuller, gold-bordered match before an earlier one
- The EU platform-to-business rule: clubs must be told the main ranking parameters in the terms

**R-DECK-18 — taking back a pass in a deck**
- Tinder lets a subscriber take back the last swipe
- Bumble's Backtrack undoes a no swipe, on a paid plan, and never a yes
- No racket deck offers an undo

**R-DECK-15 — what a club-wide pause does to bookings already made**
- kluby.org's switch is still documented only as stopping online booking
- Playmore: ending or pausing a game series keeps the games already made

**R-DECK-11 and R-DECK-14 — two games at the same hour**
- Playmore does not stop a player joining two open games at the same hour
- Playtomic's app has no same-hour warning either

**R-DECK-34 — a swipe, an "I'm in" control, or a price on the control**
- No Polish ruling or UOKiK statement on a swipe, "Dołączam", or a price on the button
- What authorities have said about order buttons, beyond the research so far

**R-DECK-32, R-DECK-33, R-DECK-34 — must the binding information be in Polish?**
- Polish law requires offers and required consumer information in Polish; other languages may stand beside

**R-DECK-33 — a Polish complaint about a late charge under a rule the player didn't see**
- Not found; the nearest Polish complaints are about refunds after cancelling

**R-DECK-9 — where Playmore's "Mało czasu" badge shows**
- In the creator's slot picker, never on the joiner's card

**R-DECK-39 — where a notice about a game lands**
- Playtomic's alerts cover courts and the last place in a match; a court alert opens the club's slot
- Playmore opens the club's open-games list with the game scrolled to the centre

**R-DECK-32 — a benefit-card holder who has paid a share online**
- Playmore: declare the card, pay a refundable card deposit, get it back when reception scans the card
