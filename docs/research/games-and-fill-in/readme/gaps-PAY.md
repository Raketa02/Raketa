# Gaps PAY — index entry

Written 2026-10-08 by the PAY gaps researcher, answering `$W/areas/PAY/gaps.md` (13 gaps, 12 rules). Sources tried for each:
help centres and terms, the Playtomic and Playmore Android packages (their own text), the Playmore and kluby.org web
apps, Stripe's and Apple's docs, Visa's developer pages, bank card terms (mBank, ING, PKO BP), the World Bank's Findex
2025 data, the Eureka tax-ruling search, and press and web searches in Polish and English.

### [topics/gaps-PAY.md](../topics/gaps-PAY.md)

Answers by rule, every fact kind-tagged, linked and dated 2026-10-08. About 28k characters.

- **R-PAY-24, removing a card:** Playtomic asks before it removes a card · Playmore saves no card, so there is nothing
  to remove · kluby.org lets a card go at any time; a confirm step is not described
- **R-PAY-42, history after removal:** Playtomic keeps transactions apart from payment methods · Playmore's history sits
  in the wallet and the bookings · kluby.org's payment history is not public
- **R-PAY-1, the club's card cost:** What a desk terminal costs a Polish club per card payment · Stripe's custom pricing
  in Poland: on request, for large volume
- **R-PAY-4:** How many Poles use a card at all, and pay online
- **R-PAY-6:** Apple's merchant tokens are not for an unscheduled card on file
- **R-PAY-11:** Card disputes in Poland run on the card schemes' rules · Where an internet address counts in a dispute,
  and where it does not
- **R-PAY-17:** What a declined setup hands back · Banks and rivals name the reason
- **R-PAY-26 / 27:** Automatic card updates are not documented for Polish issuers · Polish cards do move between networks
- **R-PAY-34:** The statement shows the club's descriptor · How Polish banks rename the line · How long a released hold
  stays in a Polish bank app
- **R-PAY-39:** How often issuers ask, and how fast people answer
- **R-PAY-40:** The closest ruling: tennis courts booked online through an operator

Still *not found* (each an [ABSENT] line in the file): whether kluby.org confirms a removal or keeps history; what a
named Kraków club pays at its desk, and a published IC+ threshold; the share of Poles with no card for online use;
Polish guidance on an internet address in a dispute; the code a Polish issuer returns for a 0 zł internet limit;
whether Polish issuers send card updates, and how often cards change network; how other Polish banks rename the
statement line, and how fast an app drops a cancelled hold; the Polish rate of bank checks on charges made without
the player, and answer times; a ruling on one service paid in several parts.

### [areas/PAY.md](../areas/PAY.md) — section added

**11. Gap answers, 2026-10-08** (R-PAY-1, 4, 6, 11, 17, 24, 26, 27, 34, 39, 40, 42): 13 lines citing `GP#…`
(= `topics/gaps-PAY.md`); the "Candidate gaps" line now keeps only R-PAY-18/19. The digest is about 18.3k characters.

### [shots/gaps-PAY-playtomic-android-6.93.2-strings.txt](../shots/gaps-PAY-playtomic-android-6.93.2-strings.txt)

The Playtomic Android 6.93.2 strings quoted in the topic file (removing a card, *Your payments* and receipts, decline
messages), extracted from the package's resources on 2026-10-08.
