# What number should a racket-sport Rankings board sort by?

Research for the per-sport **Rankings** leaderboard (General / Friends; row = position, form of last
five, places moved this week, sort number; card "0,04 behind Karol · one win closes it").
Compiled 2026-11-07. Primary sources were preferred: official help centres, rulebooks, the systems'
own published methodology, source code, and peer-reviewed papers. Where something could only be
reached through a secondary source, or could not be found at all, it says so.

---

## TL;DR

- **Every serious system keeps two numbers apart.** One is a *rating*: skill, expected-score based,
  with a confidence measure (Playtomic level, UTR, WTN, DUPR, SquashLevels, Glicko/Elo). The other
  is a *ranking*: points earned in a rolling window, with best-N results counted (ATP, FIP, PSA,
  PZPadla, PZT's amateur TOP list). USTA spells the difference out: "Match wins make up your USTA
  ranking … Match scores make up your WTN rating."
- **Leaderboards built on a rating always gate who can appear.** lichess requires 30 or more rated
  games, a rated game in the last 7 days and RD < 75. chess.com requires 20 games, one of them in
  the last 90 days. Microsoft's TrueSkill sorts by the conservative score μ − 3σ, so a new player
  starts at 0. DUPR uses 60% reliability as "reliable", and UTR shows "(P)" for a projected rating
  until about 5 matches.
- **Playtomic, our closest analogue, ran both kinds of board.** Its documentation describes a
  General/Season/Club **points** ranking: +10 for playing, +100 for a win, +25 per set won, and a
  bonus for beating a higher-ranked team. Seasons reset to zero. It also describes a separate
  **Level ranking** sorted by the 0–7 level. The current player help centre (2026) documents only
  the level and club leagues.
- **Inactivity is handled in one of three ways.** (a) Results expire: rolling 52 weeks or 12
  months, best N. (b) Uncertainty grows and the rating does not move: Glicko RD, WTN confidence,
  DUPR reliability. (c) The player leaves the list: lichess after 7 days, chess.com after 90 days,
  FIDE after a year. WTN (Aug 2026) now also applies a small decay after more than a year without
  play.
- **Doubles:** Playtomic, DUPR and UTR compare **team averages**. TrueSkill uses **sums**. WTN (from
  its Aug 2026 change) **stops using the partner's rating** in doubles. UTR ignores a doubles match
  when the two partners are more than 4.00 apart.
- **Engagement evidence favours small, close, refreshing comparisons.** The N-effect (Garcia & Tor
  2009, *Psych. Science*): fewer competitors means more motivation, and rivals near a standard
  compete harder. Duolingo's weekly XP leagues (activity, not skill) raised learning time by 17%
  and tripled highly engaged learners. Strava's Local Legend rewards *most efforts in 90 days*
  "regardless of pace". A leaderboard plus badges in a classroom *lowered* intrinsic motivation
  (Hanus & Fox 2015).

---

## 1. Playtomic

### How the level (0–7) moves
Sources: [How the Playtomic level system works](https://playerhelp.playtomic.com/hc/en-gb/articles/43310980754193-How-the-Playtomic-level-system-works)
(updated 2026-10-31), [Levels: ups & downs](https://playerhelp.playtomic.com/hc/en-gb/articles/19831827459345-The-Playtomic-Levels-ups-downs),
[Levels & Algorithm (manager help)](https://helpmanager.playtomic.com/hc/en-gb/articles/20563641264145-The-Playtomic-Levels-Algorithm).

- **Starting level:** a one-time questionnaire, then automatic updates. Levels exist for padel,
  tennis and pickleball.
- **Inputs to each update:** the result, the opponents' levels, the partner's level, and the
  player's own **reliability** ("more matches = higher reliability").
- **Size of the change:** low reliability means large swings, high reliability means small ones.
  "Each player has a different reliability score", so two partners move by different amounts after
  the same match.
- **Doubles:** "calculates the average level per team, compares the expected outcome with the
  actual result, and adjusts each player's level accordingly".
- **Ties move levels:** "The team with the higher combined level will lose points, while the team
  with the lower level will gain points."
- **Only competitive matches count.** Casual matches never change a level. A result needs at least
  one levelled player per team in private and open matches, and all four players levelled in
  Community matches. Results the players reject do not count, and a set needs a valid score (6–4,
  7–5, 7–6; 6–5 is invalid).
- **Reliability** is set by the system and cannot be edited. A paid leveling session at a certified
  club sets it to **50%** ([Leveling Clubs](https://playerhelp.playtomic.com/hc/en-gb/articles/19832024478097-Playtomic-Leveling-Clubs)).
  An older article describes three tiers (low, medium, high). No formula is published.
- **Self-correction:** a player can *lower* their own level manually but cannot raise it.
- **Size of a typical move:** the [10-Match Challenge](https://playerhelp.playtomic.com/hc/en-gb/articles/42759192068369-What-is-the-10-Match-Challenge-and-how-does-it-work)
  is open to players at **≥85% confidence** and lets them multiply their level changes ×2, ×3 or ×4
  for 10 matches. Its worked example: "if a match would normally change your level by +0.04, with a
  3x multiplier it becomes +0.12". On a draw the minimum guaranteed change is ±0.04. There is a
  3-month cooldown, and the challenge "may expire after 90 days of inactivity". **Read for us:** a
  high-reliability player moves roughly 0.0x per match, so a gap of "0,04" is about one win.
- **Inactivity:** nothing is published about the level or reliability decaying with time.

### Leaderboards and rankings at Playtomic
- **[Rankings Score on Playtomic](https://helpsyltek.playtomic.com/hc/en-gb/articles/23182764145681-Rankings-Score-on-Playtomic)**
  (Syltek help centre, 2024-03-08). Syltek is Playtomic's club-software brand. The article lists four
  boards:
  - **General ranking**, "timeless", counting every match and reservation with a result entered.
    Points: **+10** for playing (owner or guest, awarded once the match is played), **+100** for a
    win, **+25** per set won, plus an "extra boost" when a team beats a higher-scored team.
  - **Season ranking:** the same points over published dates, where "all players start from
    scratch, having a winner for each season".
  - **Club ranking:** points earned only at that club, continuous and never reset, plus +25 for
    playing a club tournament. Clubs show the top players on the in-club TV display.
  - **Level ranking:** "a general classification based on the level you have … every time you play
    and your level changes your position in this ranking can change."
- The current **player** help centre (searched through its API for "ranking", "leaderboard" and
  "league" in Nov 2026) has **no** ranking or leaderboard article. Its only standings are **club
  leagues**: teams, groups or divisions, rounds with promotion and relegation, points per match, and
  tie-breaks of head-to-head, then sets, then games
  ([League standings](https://playerhelp.playtomic.com/hc/en-gb/articles/19831994572689-How-to-look-at-the-League-Standings),
  [League scoring](https://helpmanager.playtomic.com/hc/en-gb/articles/20535702278289-Scoring-system-and-set-validation-in-Leagues),
  [League concepts](https://helpmanager.playtomic.com/hc/en-gb/articles/20535742113681-Main-concepts-about-Leagues)).
  An absent team loses 1 point.
- **Anti-gaming levers visible in Playtomic:**
  - Competitive matches are restricted to a level range set from the first player's level.
    Out-of-range players can join only if everyone agrees
    ([Casual vs Competitive](https://helpmanager.playtomic.com/hc/en-gb/articles/20535188135185-Casual-vs-Competitive-Open-Matches)).
  - Results must be confirmed, and players can reject them.
  - Players can lower their level but not raise it.

## 2. Padel federations

### FIP / Premier Padel (individual world ranking)
[Ranking System & Points Breakdown](https://www.padelfip.com/ranking-system-points-breakdown/),
[2025 points announcement](https://www.padelfip.com/2025/01/fip-and-premier-padel-announce-new-2025-fip-ranking-points-and-tournament-criteria/).
- **Window:** points are defended on "a continuous 52-week cycle". "The loss of points is automatic"
  and each result is replaced by the one from the matching week of the current year.
- **Counting:** the **22 best results** from Premier Padel and CUPRA FIP Tour events in 2026 (a
  Premier Padel note says this drops to 21 in 2027). A separate **Race** ranking counts the
  calendar-year best 22.
- **Points by round and category:** examples include P2 winner 600, FIP World Cup Pairs winner
  2,000 (finalist 1,200), FIP Platinum winner 300, Gold 150 and CUPRA FIP Finals 225. The full
  points table is published as an image on the FIP page; the image could not be retrieved.
- Points belong to the **individual**, although pairs play together.

### Poland: Polski Związek Padla (PZPadla)
Sources: [Dla zawodników](https://www.polskizwiazekpadla.org/dla-zawodnikow),
[Rozgrywki](https://www.polskizwiazekpadla.org/rozgrywki),
[Punktacja 01.01.2026 (PDF)](https://www.polskizwiazekpadla.org/s/PZPpunktacja202631122025publikacjaa.pdf).
- **Where the ranking is published:** the official ranking tool is **kluby.org**.
- **Rule:** **the 10 best-scoring tournaments** within **12 months** for men and juniors, and
  within **24 months** for women, 45+ and mixed.
- **Tournament tiers:** Mistrzostwa Polski (MP), Masters, Gold, Silver, Bronze and Club Series. Each
  tier is split into categories A, B and C, and Club Series further into B1, B2 and B3.
- **Points by place:**

  | Tier | Winner | 2nd | 3rd | Lowest placing in the table |
  | --- | --- | --- | --- | --- |
  | MP | 2000 | 1500 | 1340 | 4th = 1200; 128th = 38–40 |
  | GST A | 1200 | | | |
  | SST A | 800 | | | |
  | BST A | 400 | | | |
  | CST A | 180 | | | |
  | CST B3 | 40–60 | | | |

- **Licence fee per player per tournament:** 10–30 zł.
- **2026 starting ranking:** carried over from earlier circuits with multipliers: FIP ×40, PFP
  (Polska Federacja Padla) ×2, Silesia Padel ×0.2, Interpadel ×0.04. For the domestic circuits,
  only the best result of each day counts.
- **Takeaway:** the federation ranking is tournament-only and rewards *attendance plus placing*. It
  is a different object from a skill level. A recreational player who never enters a tournament
  never appears on it.

## 3. Tennis

### ATP / WTA (points, rolling)
- **Window:** the ranking period is the past 52 weeks; tournaments "remain in the system for 52
  consecutive weeks" ([2026 ATP Rulebook ch. 9](https://www.atptour.com/-/media/files/rulebook/2026/2026-rulebook-chapter-9_pif-atp-rankings_22dec25.pdf)).
- **Counting:** singles count **18 events, plus the ATP Finals as a 19th** ([ATP Rankings FAQ](https://www.atptour.com/en/rankings/rankings-faq)).
  Mandatory events count even when a player skips them ("zero-pointers").
- **Injury:** a protected ranking ("Entry Protection") applies after at least 6 months out. It is
  set from the player's average ranking and lasts for about 9 tournaments or 9 months.

### UTR (Universal Tennis Rating, 1.00–16.50)
Sources: [Projected → reliable](https://support.universaltennis.com/en/support/solutions/articles/9000151963),
[Algorithm summary](https://support.universaltennis.com/en/support/solutions/articles/9000151830),
[Algorithm FAQ](https://support.universaltennis.com/en/support/solutions/articles/9000233354).
- **Method:** a weighted average of up to **30 most recent match ratings** from the **last 12
  months**. Matches weigh more when they are longer, more competitive, against a reliable opponent,
  and recent. "Time degradation" lowers old matches' weights, so a rating can drift with no new play.
- **New players:** "One match is all it takes to get a 'projected' UTR", shown as **(P)**. The
  rating becomes **reliable after about 5 matches**.
- **Excluded matches:**
  - A gap of more than 2.00 where the favourite wins. This counters farming weaker players.
  - Withdrawals, and matches where neither player won 4 games.
- **Doubles:** compares team averages, and both partners move by the same amount. A match does not
  count when the partners are more than 4.00 apart (as quoted from UTR by
  [Tennis Sydney](https://tennissydney.org.au/news/utr-verified-compass-doubles-official-clarification-from-utr)).
- **Inactivity:** matches older than 12 months fall off.

### ITF World Tennis Number (WTN, 40 → 1)
Sources: [LTA/ITF principles guide](https://www.lta.org.uk/4ad8ae/siteassets/about-lta/file/lta-itf-wtn-principles-guide-a5.pdf),
[ITF/USTA 2024 algorithm notice](https://ustasocal.com/wp-content/uploads/2025/02/WTN-Algorithm-Changes.pdf),
[Confidence level explained](https://worldtennisnumber.com/eng/news/wtn-your-confidence-level-explained),
[LTA FAQ on the Aug 2026 algorithm changes](https://www.lta.org.uk/siteassets/compete/wtn--rankings/faqs-wtn-algorithm-changes-august-2026.pdf),
[USTA top-10](https://www.usta.com/es/content/dam/usta/2022-pdfs/ITF-World-Tennis-Number-Top-10-Things-to-Know.pdf).
- **Model:** Glicko-like. **Confidence** is derived from rating deviation, "based on the amount and
  recency of match data".
  - A number at ≥70% confidence is "verified" (blue tick).
  - Example: "15 sets over five consecutive weeks" can raise confidence to high.
- **Scoring unit:** the *set*, with "Every Game Counts" added in 2026: 6-4 and 6-0 are now
  treated differently.
- **New players** start from a questionnaire (the PSQ). It recalculates weekly on Wednesdays.
  Singles and doubles have separate numbers.
- **Aug 2026 changes:**
  - A **three-year window**.
  - **Inactivity:** confidence falls, and after more than a year without play "a small and gradual
    adjustment may be applied".
  - **Doubles "will stop considering the rating of your partner".**
  - Playing far weaker or stronger opponents "will not negatively impact your rating if your
    performance aligns with expectations".
- **Rating versus ranking:** "Match wins make up your USTA ranking … Match scores make up your WTN
  rating."

### PZT (Polish Tennis Association)
- **[Tenis Open Polska (TOP) amateur programme regulations](https://top.pzt.pl/FileDownload.aspx?FileID=31FD34C7-1FD5-44E3-A8A3-C6BAB602C35A)**
  (in force from 2021). Rule IV.3.4: the ranking is "the sum of points from a **maximum of 10
  tournaments** in the **last 12 months**" with the highest scores, and it rolls ("klasyfikacja
  krocząca").
  - **Ties:** the player with **fewer tournaments** ranks higher, then the one with more points from
    higher-ranked tournaments.
  - **Lists** are published on the first Wednesday of each month.
  - **Points:** placings by tournament rank (1–5) and field size. Examples: rank 1 winner 300, rank 5
    winner 40–60. A first-round loss always earns 1 point.
  - **Eligibility:** players need a TOP licence (50–75 zł a year).
- **Elite PZT lists** ([Regulamin Turniejowy 2026](https://www.pzt.pl/FileDownload.aspx?FileID=ADF28EDB-6A2E-4349-8F8A-62EF87014C5F&FileName=Regulamin+Turniejowy+PZT+2026)):
  a 12-month sum. Junior lists count at most 6 domestic singles tournaments. This document was read
  only through a search summary.

## 4. Pickleball: DUPR (2.000–8.000)
Sources: [How it works](https://www.dupr.com/how-it-works),
[Introducing the Reliability Score](https://dupr.com/post/introducing-the-dupr-reliability-score),
[How your DUPR is calculated](https://www.dupr.com/post/how-your-dupr-rating-is-calculated),
[Rankings](https://www.dupr.com/rankings).
- **Starting rating:** new players are **NR** (not rated). A coach or AI assessment can seed the
  first rating.
- **Separate ratings** exist for singles, gender doubles, mixed doubles and the 50–65+ age group.
- **How it moves:** score-based. "If your team scores more points than expected, your rating goes
  up." The team rating is "the average of each player's DUPR".
- **Weighting:** recent matches weigh more. Club and tournament results count more than
  self-posted recreational ones, which "carry less weight".
- **Reliability Score (1–100%):**
  - Driven by the number of matches, their recency, and **how varied your partners and opponents
    are**. 60% or more counts as "reliable", and organisers use it as an eligibility threshold. It
    updates weekly on Tuesdays.
  - **Decays with inactivity:** 100% falls to about 60% after roughly 6 months without results, and
    60% to about 30% in roughly 3 months.
  - DUPR's (now 404) post "Paths to reliability" described the route to 60% as "2 or more unique
    partners" and "6 or more unique teams" faced, and the route to 100% as 4+ partners and 12+
    teams within a 0.5 range. This is quoted from search snippets. **It is a direct defence against
    "playing only with friends".**
- **Leaderboards:** "Top Ranked Players", continental, club and college rankings are lists in
  descending rating order. The pages publish no eligibility rule.

## 5. Squash

- **PSA world ranking:** weekly since Aug 2022. It counts the **best 10 results for men and best 9
  for women**, and points drop off **52 weeks** after they are added
  ([SquashMad report, 23 Aug 2022](https://squashmad.com/breaking-news/psa-announces-switch-to-weekly-ranking-lists/);
  the PSA's own page was not reachable).
- **SquashLevels** (used by the WSF and PSA as "Official World Squash Ratings"):
  - **How it moves:** each match compares expected and actual results using *points and game
    scores*. More important matches carry more weight. "Behavioural modelling" covers gaps in
    history and fast risers
    ([algorithm](https://blog.squashlevels.com/the-squashlevels-algorithm/)).
  - **Weak opponents:** a FAQ answers "How can I give my lesser opponent a runaround without getting
    penalised?" — you don't have to crush weaker players
    ([FAQ](https://blog.squashlevels.com/how-can-i-give-my-lesser-opponent-a-runaround-without-getting-penalised/)).
  - **Level confidence:** rises with matches and falls with unexpected results. Public player pages
    show it falling over time without play, for example "79% after last match, 10% now". The decay
    rule itself is unpublished.
  - **Rankings** are worldwide, national and club lists sorted by level
    ([rankings](https://squashlevels.com/features/rankings/)).
  - **The Dutch federation uses SquashLevels with four layered numbers**
    ([Squash Bond Nederland](https://www.squash.nl/media/lyfhxnfj/samenvatting_presentatie_sl_kennissessie.pdf)):
    - a per-match *rating*;
    - a daily *grade*;
    - a monthly-averaged *speelsterkte* (playing strength), frozen for the month and used for team
      selection;
    - a *ranglijst*, the position within an age, region or club.

    This is a useful pattern: **the displayed number is smoothed and frozen**, so the board does
    not jitter.
  - **Eligibility on a SquashLevels-run site:** its player-of-the-month page requires a level above
    200, **at least 5 matches in the last 12 months**, and **level confidence above 40%**. This was
    seen in search results only.
- **US Squash, Universal Squash Rating** ([ratings](https://ussquash.org/ratings/)):
  - **Scale:** 1.5–7.0.
  - **First rating** after at least one win and one loss.
  - Updates daily. "Reliability" comes from the amount of recent results, and recent matches weigh
    more. A secondary source says the window is 45 months.
- **England Squash rankings** ([help](https://support.englandsquash.com/article/298-how-do-i-appear-on-the-rankings-list)):
  players appear only with current membership and **at least one sanctioned competition in the
  last 12 months**.

## 6. Social / app leaderboards

| Product | Sorted by | Reset | Minimum / eligibility | Movement shown |
| --- | --- | --- | --- | --- |
| Playtomic (2024 doc) | General/Season/Club: **activity + result points** (+10 play, +100 win, +25/set, upset bonus); Level ranking: **level** | Season: reset to 0; General and Club: never | Result entered (and confirmed) | The level chart on the profile |
| [lichess](https://lichess.org/faq) | Glicko-2 rating | Continuous | ≥30 rated games, a rated game **in the last week**, RD < 75 (standard) / < 65 (variants), top 10. "The 2nd requirement is so that players who no longer use their accounts stop populating leaderboards." | — |
| [chess.com](https://support.chess.com/article/857-what-does-percentile-mean) | Rating | Continuous | Account ≥7 days, ≥20 games of that type, ≥1 in the **last 90 days**; drop off after 90 days idle | Percentile |
| [Duolingo leagues](https://blog.duolingo.com/duolingo-leagues-leaderboards/) | **Weekly XP** (effort) | **Weekly** (Sunday) | Matched with "similar study habits" in a similar time zone; 10 tiers with promotion and demotion; opt out by making the profile private | Promotion and demotion zones |
| [Strava Local Legends](https://support.strava.com/hc/en-us/articles/360043099552-Local-Legends) | **Most efforts in a rolling 90 days**, "regardless of your pace or speed" | Rolling | Public activities only | Your count against the leader; overall, women's and **"mutual followers' efforts"** views |
| [Strava segment leaderboards](https://support.strava.com/hc/en-us/articles/360030851772-Segment-Leaderboard-Filters) | Fastest time | All-time / this year / today / week / month filters | — | Filters by gender, age, weight and following |
| DUPR / UTR / SquashLevels lists | Rating | Continuous | Implicit reliability: (P) for UTR, a reliability % for DUPR, level confidence for SquashLevels | — |
| Padel Mates, MATCHi, RacketPal | **No public methodology found.** App-store pages mention per-game level feedback (Padel Mates) and "rankings and leader boards" (RacketPal, via a partner leisure centre) | ? | ? | ? |

## 7. Rating algorithms

### Elo / FIDE
[FIDE Rating Regulations 2024](https://handbook.fide.com/chapter/B022024).
- **K-factor** (how far one game moves a rating):
  - **K = 40** until a player has 30 games, and for under-18s rated under 2300;
  - K = 20 below 2400;
  - K = 10 once a published rating reaches 2400.
- A **first rating** needs at least 5 games against rated opponents.
- **Inactivity:** a player "is considered to commence inactivity if they play no rated games in a
  one-year period". Older handbooks say inactive players are left off the list but stay rated.
- **What this means for us:** Elo has no explicit uncertainty term. "Provisional" is approximated by
  a larger K for the first N games.

### Glicko / Glicko-2
[Glickman, *Example of the Glicko-2 system*, 2022](http://www.glicko.net/glicko/glicko2.pdf).
- **The three numbers:** each player has a rating r, a rating deviation RD (uncertainty) and a
  volatility σ. A new player starts at 1500 / RD 350 / σ 0.06.
- **Report an interval:** "One way to do this is to report a 95% confidence interval … rating minus
  twice the RD … plus twice the RD." **r − 2RD** is therefore the natural conservative score.
- **Inactivity:** "if a player does not compete during the rating period … the rating and
  volatility parameters remain the same, but the RD increases": φ′ = √(φ² + σ²). The system works
  best with 10–15 games per player per rating period.
- **lichess's choices** ([source](https://github.com/lichess-org/lila/blob/master/modules/rating/src/main/Glicko.scala)):
  - max RD 500, start 1500;
  - **`standardRankableDeviation = 75`**, **`variantRankableDeviation = 65`**;
  - provisional when RD > 110;
  - periods per day chosen "so a typical player's RD goes from 60 → 110 in 1 year";
  - FAQ: "it might take around a year of inactivity for your rating to become provisional again".

### TrueSkill
[Microsoft Research](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/).
- **Model:** belief about a player's skill is N(μ, σ²); a new player gets μ = 25, σ = 8.333.
- **Leaderboard:** "conservative skill estimate" = **μ − 3σ** (the FAQ calls it "the 1% quantile").
  A new player's shown value starts at **0** and rises as σ shrinks, so *playing raises your shown
  score even at constant skill*. This is the canonical fix for "new players topping the board".
- **Teams:** "the team's skill is assumed to be the sum of the skills of the players". If two
  players only ever play together, the system **cannot separate their individual skills**. This
  matters for padel duos who always partner each other.
- **Uncertainty over time:** σ grows by a constant amount between consecutive *games*, not with
  calendar time as in Glicko. Inactivity therefore needs an explicit rule if TrueSkill-style
  dynamics are used.

### How doubles are combined, summary

| System | Method |
| --- | --- |
| Playtomic | Team average |
| DUPR | Team average |
| UTR | Team average, equal moves for both partners, partner gap > 4.00 excluded |
| TrueSkill | Sum |
| WTN (2026) | Ignores the partner's rating |

In every case each individual keeps one number, which is what an individual leaderboard needs.

## 8. Engagement research

- **N-effect** ([Garcia & Tor 2009, *Psychological Science* 20(7)](https://public.websites.umich.edu/~smgarcia/pubs/n-effect.pdf)):
  "increasing the number of competitors (N) can decrease competitive motivation". People told they
  competed against 10 rather than 100 finished faster, and social comparison mediates the effect.
  The paper also cites evidence that "competitive behavior occurs more frequently when rivals are
  in proximity to a standard … ranked 3 and 4". **This supports the Friends board and the "0,04
  behind Karol" proximity card over a long General list.**
- **Duolingo** ([Jorge Mazal, ex-CPO, Lenny's Newsletter](https://www.lennysnewsletter.com/p/how-duolingo-reignited-user-growth)):
  weekly leaderboards **raised overall learning time by 17%** and **tripled highly engaged
  learners**. Users "are matched with other users who had a similar level of engagement in the
  prior week". The board ranks *effort*, resets weekly, and groups people of similar activity.
- **Strava Local Legends:** explicitly chosen to reward repeat activity "regardless of your pace or
  speed". It is the activity-board counterpart to speed-based KOMs.
- **Hanus & Fox 2015** (*Computers & Education* 80:152–161, doi:10.1016/j.compedu.2014.08.019): a
  leaderboard plus badges in a 16-week course left students *less* motivated, satisfied and
  empowered, with lower exam scores. A caution that a global rank list can hurt mid and low
  performers.
- **Jia, Liu, Yu & Voida, CHI 2017**, "Designing Leaderboards for Gamification"
  ([repository](https://scholarworks.indianapolis.iu.edu/items/e2899582-c736-4f38-b1dc-a7a3c8324094)):
  a player's position (top, middle or bottom) significantly changes how they perceive the
  leaderboard and the app. Leaderboards were rated **most favourably in fitness apps**. Only the
  abstract was read.
- **Read-across:**
  1. A skill-sorted General list is mostly static and puts most users far from anyone they could
     pass. That is the low-motivation zone.
  2. Small N, proximity and a weekly refresh drive motivation.
  3. Activity-based boards let everyone move.

## 9. Inactivity across systems

| System | Treatment |
| --- | --- |
| **Expiry** (ranking systems) | FIP and ATP: 52 weeks. PSA: 52 weeks. PZPadla: 12 or 24 months, best 10. PZT TOP: 12 months, best 10. UTR: 12 months, best 30, with time-decayed weights. WTN: 3-year window. |
| **Uncertainty grows, rating frozen** | Glicko-2 RD. WTN confidence (a two-month guideline appears in a USTA FAQ snippet). DUPR reliability (100% → 60% in about 6 months). SquashLevels level confidence. |
| **Removed from the board** | lichess: no game in 7 days. chess.com: no game in 90 days. FIDE: inactive after 1 year. England Squash: needs a competition in the last 12 months. |
| **Rating itself decays** | WTN only, from 2026: a small gradual adjustment after more than a year. |
| **No rule published** | Playtomic level. |

---

## Comparison table

| System | Number shown | What moves it | Inactivity rule | Provisional / min-games rule | Leaderboard scope |
| --- | --- | --- | --- | --- | --- |
| Playtomic level | 0–7, 2 decimals, + reliability % | Competitive results vs expectation (team average, partner, own reliability); ties move it | None published | Questionnaire start; low reliability = big swings; leveling session sets 50% | "Level ranking" (2024 doc); level shown on profile |
| Playtomic rankings (2024 doc) | Points | +10 play, +100 win, +25/set, upset bonus | Season board resets; General and Club never | — | General (all-time), Season, per Club |
| FIP / Premier Padel | Points | Round reached × tournament category | 52-week defence | Best 22 results | World, individual |
| PZPadla (PL) | Points | Placing × tier (MP 2000 … CST 40) | 12 mo (men, juniors) / 24 mo (women, 45+, mixed) | Best 10 tournaments; licence | National, on kluby.org |
| ATP | Points | Round × tier | 52 weeks | Best 18 + Finals; zero-pointers | World |
| UTR | 1.00–16.50 | Games-won % vs expected, weighted | 12-month / 30-match window | (P) until ~5 matches | Lists by rating |
| WTN | 40 → 1 | Sets (+ games from 2026) vs expected; Glicko-like | Confidence decays; small decay after >1 yr; 3-yr window | PSQ start; "verified" at ≥70% confidence | Grouping tool, not a board |
| PZT TOP (PL amateur) | Points | Placing × tournament rank and field size | 12-month rolling | Best 10; TOP licence; ties → fewer tournaments wins | National, by age and category |
| DUPR | 2.000–8.000 + reliability % | Points scored vs expected; team average | Reliability decays (100 → ~60% in 6 mo) | NR until rated; 60% = "reliable"; variety of partners and opponents needed | Top-ranked, club and college lists by rating |
| PSA | Points | Round × event | 52 weeks | Best 10 (men) / 9 (women) | World |
| SquashLevels | Level + confidence % | Points and game scores vs expected; match importance | Confidence falls over time (observed) | Confidence gates (e.g. ≥40% plus 5 matches in 12 mo on one SL site) | World, national, club; most-improved |
| lichess | Glicko-2 rating | Results | RD grows (60 → 110 / yr) | Provisional "?" if RD > 110 | ≥30 games, game in last **7 days**, RD < 75 |
| chess.com | Glicko rating | Results | Off the board after **90 days** | 20 games of that type | Global and friends |
| TrueSkill | μ − 3σ | Results (team = sum) | σ grows per game, not per time | Starts at 0 and rises with play | Xbox leaderboards |
| Duolingo | Weekly XP | Effort | Weekly reset | Matched by prior-week engagement | Leagues of similar learners |
| Strava Local Legend | Effort count | Repeat activity | Rolling 90 days | Public activities | Per segment, with "mutual followers" view |

---

## What this means for us

Two rules apply to all three options:

- **The number on the row must be the number the list is sorted by, and the number the gap card
  quotes.** If the row shows a level but the list sorts by something else, "0,04 behind Karol"
  stops being true.
- **"Places moved this week" requires a weekly snapshot.** ATP updates on Mondays, WTN on
  Wednesdays, DUPR reliability on Tuesdays, PZT lists on the first Wednesday of the month. Movement
  is position(now) − position(last snapshot). Pick a fixed cut-off, for example Monday 00:00
  Europe/Warsaw.

### Option A — Sort by the Skill level itself, gated

**What it is.** The board shows the level (two decimals) and sorts by it. Like lichess and
chess.com, only **established and active** players appear on General, for example:

- at least N confirmed competitive games in the sport (lichess uses 30, UTR about 5, Playtomic's
  reliability tiers sit in between, so roughly 10);
- reliability or confidence above a threshold;
- at least one confirmed game in the last X days (lichess 7, chess.com 90; recreational padel
  suggests about 30–60).

Friends shows everyone, with provisional and inactive rows marked.

**Pros**
- One number everywhere: the profile, matching and the board agree. This is the same as
  Playtomic's "Level ranking" and the DUPR, UTR and SquashLevels lists.
- Nothing new to explain.
- Hard to farm. Expected wins barely move a rating: UTR drops favourite wins over a 2.00 gap, and
  WTN says weaker opponents "will not negatively impact" you.

**Cons**
- Most rows rarely move. Low and mid players sit far from anyone they can pass (the N-effect and
  the Hanus & Fox risk).
- The questionnaire seeds the level, so a lucky or optimistic seed can sit high until the gate
  hides it.
- "One win closes it" is only an **estimate**: compute the expected delta of a win against a
  same-level team at the player's current reliability, and say "about one win". Playtomic's own
  example puts an established player's normal move at about 0.04.
- It encourages "rating protection" (not playing). The activity gate counters this.

**Anti-gaming**
- Rely on the rating's expected-score maths for farming.
- Sandbagging corrects itself because low reliability means big moves.
- For friend-only play, require partner and opponent variety before a player counts as
  "established", following DUPR's 2+ partners and 6+ opposing teams.

### Option B — A separate points standing that rewards activity

**What it is.** A season or rolling points total: Playtomic's +10 for playing, +100 for a win, +25
per set and an upset bonus; or PZT and PZPadla's "best N in 12 months". It resets weekly, monthly or
by season (Playtomic seasons, Duolingo weeks). The level stays on the profile.

**Pros**
- Everyone can climb. Movement every week makes "places moved" lively.
- "One win closes it" is **exact and deterministic**.
- Fresh starts each season.
- Matches the evidence that effort-based, refreshing boards drive engagement (Duolingo +17%
  learning time, Strava Local Legends).
- No provisional problem: new players start at 0.

**Cons**
- A second number next to the level ("why is Karol above me if my level is higher?").
- Volume beats quality.
- Needs explicit anti-farming rules:
  - points scaled by opponent strength (Playtomic's upset bonus), or zero for wins over a large gap
    (as UTR does);
  - a cap on counted games per week or per identical foursome (against playing only friends);
  - best-N counting (PZT and PZPadla);
  - a tie-break of fewer games played (PZT).
- Gives a doubles partner identical points whether they carried the match or were carried.

### Option C — Hybrid: conservative skill, shown only once established

**What it is.** Sort by a conservative score: level − k·uncertainty (TrueSkill μ − 3σ, Glicko
r − 2RD). Let uncertainty grow with inactivity, Glicko-style. Optionally hide players below a
reliability floor from General, as with lichess RD < 75 and DUPR 60%.

**Pros**
- New players cannot top the board on a questionnaire seed.
- Playing raises your shown score even at constant skill, because uncertainty shrinks. This rewards
  activity without a second currency.
- Inactivity lowers the score smoothly, with no cliff.

**Cons**
- The board's number is no longer the profile level. Either show the conservative value with its
  own name, or show the level and accept that the sort order and the "0,04" gap disagree; the
  second choice is not allowed by the rule above.
- Needs a real uncertainty value in our engine. If reliability is only a match counter, k·σ is
  invented.
- Harder to explain.
- Tuning k and the inactivity growth needs data we do not yet have.

### Pattern worth borrowing whichever option is chosen

Smooth and freeze the displayed number per period, as the Dutch SquashLevels setup freezes
*speelsterkte* monthly. Snapshot weekly, so the board, "places moved" and the gap card all read the
same frozen values and do not jitter after every game. Keep the Friends board **un-gated**: small N
is where comparison motivates most, and the proximity card ("0,04 behind Karol") works best there.
