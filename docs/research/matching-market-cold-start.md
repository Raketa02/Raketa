# Cold start with eleven players — what is known, what is repeated, and what nobody has measured

Research output for [`Raketa02/Raketa#162`](https://github.com/Raketa02/Raketa/issues/162), under the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**This file decides nothing.** [The thin-pool experience](https://github.com/Raketa02/Raketa/issues/166)
decides. The job here is to establish what is actually known about running a matching market
at eleven players, and — more importantly — to separate the small amount that has been
measured from the large amount that is repeated because it sounds true.

## How claims are labelled

Every claim below carries one of five tags. They are not decoration; the difference between
the first and the second is the whole point of this ticket.

| Tag | Means |
| --- | --- |
| **[EVIDENCE]** | A measured result: a controlled experiment, a published study with a method and an N, a court filing, a first-party figure with a stated population |
| **[POLICY]** | A documented fact about what a company *does* — its own help page, its own docs. Evidence that somebody chose a number, **not** evidence that the number is right |
| **[VENDOR]** | A benchmark published by a company selling the thing being benchmarked. Unaudited and selection-biased. Directional at best |
| **[ANECDOTE]** | A founder story, a maxim, a design principle, a practitioner opinion. May well be true. Has no measurement behind it |
| **[ABSENT]** | Searched for and not found. Stated so the gap is not silently filled later |

Where a source could not be fetched directly (paywall, 403, binary PDF), that is said in place
rather than papered over.

---

## Verdict — read this first

> **The cold-start problem is real, named and old, but almost nothing in the literature is
> about a market that refuses to lower its bar. The recognised strategies are overwhelmingly
> supply-manufacturing strategies, and the two best-documented cases of a product solving a
> thin pool at scale — Ashley Madison's fembots and Match.com's fake-interest emails — are
> both fabrication, both litigated, and both ruled out here by the refusals before any
> trade-off is weighed. What is left that is admissible is narrow: constrain geography, seed
> real people by hand, disclose relaxation, describe the pool, and wait.**

Four things this research changes about how #166 should be framed:

1. **The honest empty state has no measured cost and no measured benefit.** Nobody has published
   a controlled comparison of "show nothing and say why" against "show a worse match". Not
   Baymard, not NN/g, not any marketplace engineering blog. #166 will be deciding on
   principle, not on evidence, and should say so out loud.
2. **The announced relaxation ladder is a rediscovery of a 1990s database pattern**, and that
   pattern's own literature already argued for the thing §9.8 already does — capping it. The
   design is on firmer ground than it knows.
3. **The strongest evidence found bears on the measurement trap, not on the product surface.**
   Wikimedia ran the exact "lower the confidence bar to cut the zero-results number"
   experiment, and it did not even produce the short-term win it was meant to produce.
4. **Standing search's evidence base is worse than the honest empty state's.** Every conversion
   number available is vendor marketing. The one real result in the area — dynamic matching
   theory — says waiting only helps if you can tell who is about to give up, and this product
   cannot.

---

## 1. The named problem, and which strategies survive the refusals

### It is named, and the naming is older than the startup literature

**[EVIDENCE]** Evans & Schmalensee, *"Failure to Launch: Critical Mass in Platform Businesses"*,
*Review of Network Economics* 9(4), 2010 (DOI [10.2202/1446-9022.1256](https://www.degruyterbrill.com/document/doi/10.2202/1446-9022.1256/html);
[SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1353502)) is the formal statement of
the problem. Their model shows that under weak and plausible assumptions about how customers
adjust, **a platform must get a sufficient number of participants of both sides on board or it
does not ignite at all** — the failure is a property of the dynamics, not of execution quality.
*(Full text was not fetchable — 403 on SSRN and on the mirror — so this rests on the published
abstract and the journal record, not on the model's internals.)*

**[EVIDENCE]** Alvin Roth, *"What Have We Learned from Market Design?"*, *Economic Journal*
118(527), 2008 ([NBER w13530](https://www.nber.org/papers/w13530)) gives the three properties a
marketplace needs: **thickness** — attracting enough participants ready to transact;
**overcoming congestion** — giving participants enough time, or fast enough transactions, to
consider enough alternatives to reach satisfactory ones; and **safety** — making it safe to
participate straightforwardly rather than strategically or outside the market. This is the most
useful frame available for Raketa, because it says the failure modes are *symmetric*: a market
can fail by being too thin **and** by being thick but unevaluable. The quality floor is a
congestion device as much as a quality device — it is what stops a dense city from becoming an
unevaluable list. *(The PDF returns as compressed binary and could not be quoted verbatim; the
three properties are as stated in the paper's abstract and in Roth's HBR restatement,
[The Art of Designing Markets](http://web.stanford.edu/~alroth/papers/HBR.ArtOfDesigningMarkets.pdf).)*

**[EVIDENCE]** Akbarpour, Li & Oveis Gharan, *"Thickness and Information in Dynamic Matching
Markets"*, *Journal of Political Economy* 128(3), 2020, 783–815
([JPE](https://www.journals.uchicago.edu/doi/abs/10.1086/704761),
[preprint](https://scholar.harvard.edu/files/shengwu_li/files/dynamic_matching.pdf)). The result
that matters here: **waiting to thicken the market substantially reduces the unmatched fraction
only if the designer can identify which agents are about to depart.** Without that information,
matching greedily as soon as an acceptable match appears is close to optimal.

**[EVIDENCE]** Bäumler, Bullinger, Kober & Zhu, *"Superiority of Instantaneous Decisions in Thin
Dynamic Matching Markets"*, ACM EC 2023 ([arXiv 2206.10287](https://arxiv.org/abs/2206.10287))
pushes further: under a mild condition on the departure distribution, instantaneous matching is
near-optimal **even in markets that are both sparse and thin**, and it also minimises waiting
time and congestion risk.

Together those two are the sharpest formal finding in this file, and they cut against the
intuition that a thin market should batch and wait. See §5.

### What the practitioner literature adds, and what it is worth

**[ANECDOTE]** Andrew Chen's *The Cold Start Problem* (2021) supplies the vocabulary most people
now use — the **atomic network**, the smallest network that is stable and useful on its own —
with the widely-repeated illustrations of 2–3 people for Zoom, 5–10 for Slack, and ~500 students
on a college campus for Tinder ([Lenny Rachitsky's write-up](https://www.lennysnewsletter.com/p/atomic-network);
[Chen's own chapter extract](https://andrewchen.com/solve-a-hard-problem-cold-start-problem/)).
**These numbers are narrative case studies, not measurements.** No method, no counterfactual, no
population — they are the sizes those products happened to have when they started working, told
afterwards. Useful for thinking; worthless for target-setting.

**[ANECDOTE]** Paul Graham, *"Do Things That Don't Scale"*
([paulgraham.com/ds.html](https://paulgraham.com/ds.html)) — *"The most common unscalable thing
founders have to do at the start is to recruit users manually. Nearly all startups have to. You
can't wait for users to come to you."* — plus the Airbnb founders *"going door to door in New
York, recruiting new users and helping existing ones improve their listings"*, and the Facebook
one-college-at-a-time start. **Graham offers no data for any of it.** He recommends measuring
weekly growth rate generally; he presents no evidence that manual recruitment specifically causes
success. This is the most repeated piece of cold-start advice in existence and it is an essay,
not a finding.

**[ANECDOTE]** Sarah Tavel's *Hierarchy of Marketplaces* and *"minimum viable happiness"*
([Level 1](https://sarahtavel.medium.com/the-hierarchy-of-marketplaces-introduction-and-level-1-983995aa218e),
[Happy GMV](https://sarahtavel.medium.com/measuring-happy-gmv-and-why-im-over-net-promoter-score-47a5748611bc))
is the closest thing in the VC literature to Raketa's own conviction: the metric to chase is not
transaction volume but the share of transactions that made someone happy, and aggregate volume is
a vanity metric that leads you down the wrong path. **Argued, not measured** — but it is §19.1's
argument arriving from an independent direction, which is worth recording.

### Which recognised strategies survive the three refusals

The refusals: **the engine never sends a challenge on a player's behalf**; **it never returns a
bad match to avoid returning nothing**; **it never produces a number it cannot explain in one
sentence with the evidence named.**

| Recognised cold-start strategy | Verdict |
| --- | --- |
| **Narrow the market geographically** (one district, one club, one campus) | **Admissible.** Nothing is fabricated; the pool is genuinely denser. See §3 |
| **Manual / concierge seeding — recruit real players by hand, run real sessions** | **Admissible**, and the only strategy with both a long practitioner tradition and no fabrication. It costs founder time and does not scale, which is the point |
| **Subsidise or price one side in** | **Admissible but inapplicable.** There is no money side in the engine's scope |
| **Partner with clubs and venues to import existing groups** | **Admissible.** Real people, real availability |
| **Describe the pool instead of filling it** (§9.7) | **Admissible by construction** — it is the product's own answer |
| **Announced, capped relaxation** (§9.8) | **Admissible.** It shows less-good matches only above the floor, and says so. See §4 |
| **Standing search / notify-me** | **Admissible in principle**, but see §5 — and note that notifying a player *about* a candidate is not sending a challenge *on their behalf*. That line is thin and #166 must draw it explicitly |
| **Single-player utility until the network arrives** | **Admissible**, and outside the matcher's scope |
| **Seed the pool with imported, scraped or dormant profiles** | **REFUSED.** Refusal 2. A profile that cannot answer a challenge is a bad match dressed as a good one |
| **Bots or generated profiles** | **REFUSED.** Refusal 2 — and see §2 for what it has cost the products that did it |
| **Show out-of-range or below-floor candidates without saying so** | **REFUSED.** Refusals 2 and 3 together: a silent widen produces a Fit number whose evidence has been misstated |
| **Auto-send challenges or "interest" pings to manufacture liveness** | **REFUSED.** Refusal 1, explicitly and without weighing |
| **"Recently active" / "online now" badges that are not literally true** | **REFUSED.** Refusal 3 |
| **Lower the quality floor at launch and raise it later** | **Not refused outright** — the floor value is legitimately open (§23.10). But it is refusal 2 in slow motion if it is done to move the empty-result number rather than because 52 was wrong. §6 is that argument |

**[ABSENT]** No source found distinguishes fabricating from non-fabricating cold-start tactics as
an analytical category. The literature treats "seed the supply side" as one move and is largely
indifferent to whether the seeded supply is real. **That distinction is this product's own, and
it will not find external support for it.**

---

## 2. What comparable products actually do

### The honest ones

**[POLICY]** **Playtomic** — the closest analogue in the sport itself. Its Open Match sets a level
window around the first joiner (−0.25 / +0.75) and lets an out-of-range player **request** a spot
that the existing players must accept
([club configuration](https://helpmanager.playtomic.com/hc/en-gb/articles/20535035123473-How-to-configure-Open-Matches-at-your-Club),
[requesting a spot](https://helpmanager.playtomic.com/hc/en-gb/articles/20535718052241-Request-a-spot-in-an-Open-Match)).
That is relaxation-with-consent: the widen is disclosed, and the incumbents rather than the
algorithm absorb it. **[ABSENT]** Playtomic has published nothing on what happens when a match
fills with nobody; help-centre docs and player complaints indicate an unjoined open match simply
sits there. Their answer to the empty pool appears to be an unhandled case, not a designed one.

**[POLICY]** **UTR (Universal Tennis Rating)** — new players get a **provisional rating (P1–P5)**
from a questionnaire, explicitly labelled provisional, converting after roughly 3 matches and
described as reliable after about 5
([How UTR works](https://www.utrsports.net/blogs/news/how-utr-works),
[algorithm FAQ](https://support.universaltennis.com/en/support/solutions/articles/9000233354-faq-universal-tennis-rating-utr-rating-algorithm)).
The closest external precedent to §9.10's *"be honest about the band"* and §18's *no fabricated
confidence*: the number ships with its uncertainty attached rather than being suppressed or
faked. **A policy, not a measured result** — UTR publishes nothing on whether the label changes
behaviour.

**[POLICY]** **StartPlaying.games** (tabletop RPG group formation — a genuine matching market with
the same "a bad table is worse than no table" property) answers a solo player with a **disclosed
human concierge**: the game master assembles the party. Not an algorithm pretending a group
exists ([how it works](https://startplaying.games/blog/posts/how-does-startplaying-work-for-players)).

**[POLICY]** **OpenTable "Notify Me"** ships exactly the standing-search pattern for perishable
inventory — alert the diner when a cancellation frees a table
([OpenTable](https://www.opentable.com/blog/notify-me/)). Existence confirmed; **[ABSENT]** no
conversion or satisfaction data published.

**[ANECDOTE]** **Meetup's** founding tactic was the founders travelling to cities and running the
first meetups themselves ([NBC interview](https://www.nbcnews.com/id/wbna53820139)) — the
concierge seed, disclosed, again unmeasured.

**[ANECDOTE]** **Strava's Local Legends** solved sparse leaderboards *structurally*, by redefining
the prize as most-frequent-in-90-days on a segment rather than fastest overall, so a quiet segment
still has a winner ([Strava Engineering](https://medium.com/strava-engineering/building-local-legends-290879265c83)).
Worth recording as a fourth option Raketa has not considered: **change what the screen is *for* in
a thin pool**, rather than changing what clears the bar. Not evidence — a design move with no
published outcome.

**[ANECDOTE]** **Dating apps in low-density areas** appear to let match rate visibly collapse and
push the user to widen distance or drop a filter themselves — user-initiated, disclosed relaxation
([independent teardown](https://nsokolsky.substack.com/p/how-dating-app-algorithms-likely)). This
is one analyst's model of undocumented systems. Treat "the major dating apps do not silently
widen" as **unestablished**, not as established.

### The fabricating ones, and what it cost them

This is where the evidence is strongest, and it is all evidence *against*.

**[EVIDENCE]** **Ashley Madison.** After the 2015 breach, an **Ernst & Young report confirmed** the
company ran software-generated female profiles ("Angels") animated by bots that messaged paying
men. Litigation alleged **over 70,000 fembots**, and that the average paying male customer had a
**~35% chance of paying to message a bot**. The practice was withdrawn in the US, Canada and
Australia in 2014 and globally in 2015, under lawsuits and FTC scrutiny
([Gizmodo](https://gizmodo.com/how-ashley-madison-hid-its-fembot-con-from-users-and-in-1728410265),
[Money](https://money.com/ashley-madison-bots/),
[The Drum](https://www.thedrum.com/news/2016/07/07/ashley-madison-admits-using-fake-fembots-encourage-men-sign)).

**[EVIDENCE]** **FTC v. Match Group**, No. 3:19-cv-02281-K (N.D. Tex. 2019). The FTC alleged
Match.com sent non-paying users messages of the form *"He just emailed you!"* to sell
subscriptions — **including for contacts its own fraud systems had already flagged as likely
fraudulent** — and stated that *"as many as 25 to 30 percent of Match.com members who register
each day are using Match.com to attempt to perpetrate scams"*
([FTC press release](https://www.ftc.gov/news-events/news/press-releases/2019/09/ftc-sues-owner-online-dating-service-matchcom-using-fake-love-interest-ads-trick-consumers-paying)).
*(The [complaint PDF](https://www.ftc.gov/system/files/documents/cases/match_-_complaint.pdf)
returned 403; cited here via the FTC's own release and
[legal press summary](https://natlawreview.com/article/ftc-sues-matchcom-owner-alleged-fake-love-interest-ads).)*

**Note what the Match.com case actually is: a system emitting a contact signal on a user's behalf
to make the pool look alive. That is refusal 1 and refusal 2 in a single action, and it is the
most on-point external artefact in this file.**

**[EVIDENCE]** Even where fabrication is not alleged, satisfaction with match quality across the
category is dismal: MeasuringU's 2024 online-dating UX benchmark found **only 11% of users overall
said their app was "good at matching them with people"** (range 6–14% across Match, Tinder,
Bumble, Hinge, OkCupid, Plenty of Fish, Facebook Dating)
([MeasuringU](https://measuringu.com/online-dating-benchmark-2024/)). Filling the screen has not
made anybody happy.

**Not established:** allegations that Tinder or Bumble specifically fabricate profiles. The
February 2024 Match Group suit concerns compulsion-driving design, not fake profiles
([NPR](https://www.npr.org/2024/02/14/1231513991/tinder-hinge-match-group-lawsuit)). A single
unverified Facebook-group claim that a pickup-sport app "loads with bots" is **rumour**, recorded
here only because it shows what users suspect when a thin-pool app looks too full.

### Empty-state design as a discipline

**[ABSENT] — and this is a headline finding.** Across Nielsen Norman Group
([empty states](https://www.nngroup.com/articles/empty-state-interface-design/)), Shopify Polaris
([empty state pattern](https://shopify.dev/docs/api/app-home/patterns/compositions/empty-state))
and the Apple HIG ([feedback patterns](https://developers.apple.com/design/human-interface-guidelines/patterns/feedback/)),
the guidance is unanimous in direction — state the situation plainly, explain what would fill the
space, offer one next action — and **cites no measurement whatsoever**. No conversion study, no
task-completion data, no A/B test.

**Nobody has published a controlled comparison of an honest empty state against a low-quality
result.** §9.7's central conviction is unfalsified and unsupported in the published record. The
nearest measured neighbour is the Wikimedia experiment in §6, which is about search rather than
matching, and which found that lowering the bar did not even buy the short-term win.

---

## 3. Geographic seeding and density thresholds

### The one real threshold anybody publishes

**[POLICY]** **Nextdoor** is the only product found that publishes a hard, numeric density gate. A
new neighbourhood is created in **"pilot" status** and does not "launch" — does not become a
permanent neighbourhood — **until 10 members have joined and confirmed their address**. The pilot
period is **21 days**, and an unlaunched pilot **expires**
([Nextdoor help](https://help.nextdoor.com/s/article/Create-a-new-neighborhood-on-Nextdoor?language=en_GB)).

It is worth more than its size suggests, because of its *shape*:

- a **minimum viable local density**, expressed as a count of **verified** members, not signups;
- a **deadline**, after which the market is declared not to exist rather than left half-open;
- and **the product withholding itself** until the threshold is met — the structural analogue of
  the quality floor, applied to the market rather than to the candidate.

**It is a policy, not a finding.** Nextdoor has published nothing showing that 10 is the right
number, or what happens at 8 or at 15. Anyone quoting "10" as a density threshold for a matching
product is quoting one company's operating choice, for a message board, in a different domain,
with a different transaction.

### Everything else is narrative

**[ANECDOTE]** Corridor-first, city-by-city launch is universal practice. DoorDash's model is
described as route density, just-in-time matching and corridor-first launches, with the standard
warning that expanding too fast spreads supply and demand too thin to reach density anywhere
([Stanford GSB case](https://www.gsb.stanford.edu/faculty-research/case-studies/doordash-building-density-last-mile-2012-2020)).
DoorDash's own [supply/demand ML post](https://careersatdoordash.com/blog/managing-supply-and-demand-balance-through-machine-learning/)
confirms they forecast supply and demand for cities they do not yet serve, but publishes no launch
threshold. **[ABSENT]** No first-party DoorDash or Uber post found stating a density number
required to launch a market.

**[ANECDOTE]** Tinder's campus seeding — a few hundred people on one campus, sorority chapters
first and then the brother fraternity, 5,000 → 15,000 across a college tour
([Entrepreneur](https://www.entrepreneur.com/growing-a-business/1-billion-matches-later-tinder-can-trace-its-to-the-moon/253165)).
Retold constantly; never measured against a counterfactual.

**[EVIDENCE, adjacent]** The one measured fact found about how tight local matching actually is:
**92% of Olio transactions occur within 10 km and 76% within 5 km.** Cited via a secondary summary;
the original study was not reached, so treat the exact figures with caution. It is nonetheless the
only real usage-distance distribution found for a local matching product, and it supports §9.3.8's
premise that distance is a real constraint rather than a filter people will happily relax.

**[ANECDOTE]** Peerby's founder states density is a precondition for the product working at all
([Founder Institute interview](https://fi.co/insight/peerby-future-of-the-sharing-economy)) —
candid, and unmeasured.

**[EVIDENCE]** Meetup group survival has been modelled academically with real feature data,
reaching **AUC 0.86** in one model, confirming that group death and splitting are measurable
phenomena rather than folklore
([ASONAM 2016](https://cse.iitkgp.ac.in/~sprama/ASONAM16.pdf),
[ICWSM](https://ojs.aaai.org/index.php/ICWSM/article/download/7360/7214/10590)). **[ABSENT]**
Neither paper yields a minimum viable group size.

### The honest answer to item 3

**There is no published, measured density threshold at which a local matching product "feels
alive".** One product (Nextdoor) publishes a chosen threshold for a different kind of product.
One study (Olio) shows how short the distances actually are. The rest is practice and story.

If #166 wants a threshold it will have to **derive one from the product's own arithmetic** —
players per sport per district, availability overlap, and how many must clear Fit 52 to give
`MIN_SHORTLIST = 3` — and then measure it. §24 already has the right instinct: an admitted
hypothesis with a named falsifier. This belongs in that table, not borrowed from outside.

---

## 4. The relaxation ladder as a cold-start tool

### Announced, ordered, capped relaxation is a named pattern with thirty years of literature

**§9.8 is a rediscovery, and a faithful one.** The field is **cooperative query answering** and the
**empty-answer problem**.

**[EVIDENCE]** **Godfrey (1997)**, *"Minimization in cooperative response to failing database
queries"*, *IJCIS* 6(2), 95–149, formalised **Minimal Failing Subqueries** (a minimal set of
constraints explaining *why* nothing came back) and **maXimal Succeeding Subqueries** (the
least-relaxed alternative that does return something). Complexity result: finding *one* succeeding
subquery is linear in the number of constraints; finding *all* MFS/XSS is NP-hard
([survey citing it](https://www.lias-lab.fr/publications/16873/Report_MFS_XSS.pdf)). The engine's
fixed rung order is, in these terms, a hand-authored XSS ordering — chosen once by product
judgement rather than searched at query time. **That is the right trade at this scale, and the
complexity result is why.**

**[EVIDENCE]** **CoBase** (Chu et al., UCLA, 1990s) is the earliest working system of this shape:
type abstraction hierarchies relaxed step by step under a "Relaxation Manager", with an explicit
stop condition, on the stated grounds that *"relaxation without control may generate more
approximations than the user can handle"*
([CoBase paper](http://www.cobase.cs.ucla.edu/tech-docs/cobase.pdf)). **§9.8's
`MAX_RELAXATION_RUNG = 4` is the same insight, and CoBase reached it first.**

**[EVIDENCE]** Mottin, Marascu, Roy, Das, Palpanas & Velegrakis, *"A Probabilistic Optimization
Framework for the Empty-Answer Problem"*, **PVLDB 6(14), 2013**
([PDF](http://www.vldb.org/pvldb/vol6/p1762-mottin.pdf)), and the follow-on **IQR** system
(SIGMOD 2014, [PDF](https://velgias.github.io/docs/MottinMBDPV14.pdf)), implement *interactive*
one-relaxation-at-a-time: the system proposes each relaxation, the user accepts or declines, until
an answer exists **or the system can say that no relaxation will produce one**. That last
capability is exactly §9.8's terminal state — the pool description. The papers report experiments
and a user study; **the quantitative results were not retrievable from the pages fetched**, so the
framework is evidenced and its measured outcomes are not.

### What is known about how users react to a disclosed widen

**[ABSENT] — the central question of item 4 has no answer in the published record.** No A/B test,
no lab experiment and no usability study was found that isolates *disclosed widen* against *silent
widen* against *plain empty state*. That comparison does not appear to exist.

What does exist, adjacent:

**[EVIDENCE, qualitative]** **Baymard Institute** ([no-results pages](https://baymard.com/blog/no-results-page))
finds from usability testing that roughly half of e-commerce sites give users no effective recovery
path from a no-results search, and recommends — the closest thing found to a direct endorsement of
the pattern — that a query be auto-relaxed only when there is exactly one clear alternative, **and
then "with clear notice"**. Qualitative expert testing, not a controlled trial.

**[EVIDENCE]** **Nielsen Norman Group** ([no-results SERPs](https://www.nngroup.com/articles/search-no-results-serp/))
reports eye-tracking in which users **entirely missed** a lightweight no-results message and
fixated instead on ads below it, mistaking them for results. Directly relevant to §9.7: **an
honest empty state that is visually quiet is not read as an empty state at all.** If the pool
description is a small grey line, it will be missed.

**[EVIDENCE]** Herlocker, Konstan & Riedl, *"Explaining Collaborative Filtering Recommendations"*,
CSCW 2000 ([PDF](https://grouplens.org/site-content/uploads/explain-CSCW-20001.pdf)) — a real user
study showing that explanation *style* measurably changes acceptance, with a
histogram-of-neighbour-ratings interface best and a bare average-rating display worst. Support for
§12's explainability contract, and a caution that *which* explanation is given matters as much as
that one is given.

**[EVIDENCE]** Dietvorst, Simmons & Massey on **algorithm aversion**
([2014](https://marketing.wharton.upenn.edu/wp-content/uploads/2016/10/Dietvorst-Simmons-Massey-2014.pdf)) —
people abandon an algorithm faster than an equally fallible human after seeing it err, even when it
outperforms — and the 2018 follow-up
([PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2016/08/Dietvorst-Simmons-Massey-2018.pdf))
showing that **giving people even a slight ability to adjust the output substantially increases
willingness to use it, and improves outcomes.** Read against §9.8: an announced widen is close to,
but not the same as, letting the player adjust. **The measured lever is control, not disclosure.**
That is a real finding for #166 — an announced widen the player can undo has evidence behind it in
a way an announcement alone does not.

**[EVIDENCE, relayed]** The trust-calibration literature carries the counterweight: explanations
can act as a generic competence signal and raise trust **even when unwarranted** — knowing why an
aid might err has been found to increase reliance on it
([CHI 2023 survey synthesising the earlier automation-bias work](https://dl.acm.org/doi/fullHtml/10.1145/3544548.3581197)).
Applied here: *"we widened your search to 16 km"* may make a player accept a **worse** match with
more confidence, not less. **That risk is not in the design document and it should be.**

**[POLICY]** Practice, where documented, is mostly *not* auto-widening. **Indeed** shows zero
results and coaches the user to broaden the query themselves
([Indeed help](https://support.indeed.com/hc/en-us/articles/204488950-Improving-Your-Job-Searches-Tips-and-Help));
**Zillow's** documented remedy is "reset search filters"
([Zillow help](https://zillow.zendesk.com/hc/en-us/articles/360035756533)). Airbnb's *Location
Relevance* and Zillow's *Guided Search* engineering posts both exist and both returned 403;
**[ABSENT]** no first-party engineering post was successfully retrieved in which a major platform
describes disclosing an automatic widen to the user.

**So: the ladder's mechanism is well-founded, and its user-facing announcement is untested.**

---

## 5. Standing search / notify-me-later

### The conversion evidence is entirely vendor marketing

**[VENDOR]** Back-in-stock alerts are the nearest analogue with numbers, and every number is
published by someone selling alert tooling: Barilliance reports ~14% conversion and a 65.32% open
rate; Klaviyo's benchmark is reported at ~25% median conversion and ~35% for top performers; a
single MarketingSherpa case study reports 22.45%
([MarketingSherpa](https://marketingsherpa.com/article/case-study/backinstock-alert-emails-achieve-2245),
[aggregate](https://storebeep.com/blog/back-in-stock-notification-benchmarks-2026)).
**Unaudited, selection-biased, and about a fungible product returning to stock — not about a person
deciding to spend an evening with a stranger. Do not carry these numbers across.**

**[ABSENT]** No conversion figures found for job alerts (Indeed, LinkedIn), real-estate saved
searches (Zillow, Rightmove), eBay saved searches, or ticket alerts. All four products ship the
feature; none publishes how it performs. *(A "3.4× more meetings" LinkedIn figure surfaces in
search but concerns sales reps acting on job-change signals — a different thing entirely. Recorded
here so nobody else finds it and mistakes it for job-alert conversion.)*

### The staleness failure mode is real, and only proxied

**[EVIDENCE]** Pielot et al., *"An In-Situ Study of Mobile Phone Notifications"*, MobileHCI 2014
([PDF](https://pielot.org/pubs/Pielot2014-MobileHCI-Notifications-InfoBites.pdf)) — 15 participants,
7 days of logging plus diaries: **median response time ranged from 3.5 minutes for messenger apps
to 27.7 minutes for email**, against an average of **63.5 notifications per day**. Small N, but
measured. A match notification competing at email-tier salience can plausibly sit unseen for tens
of minutes.

**[EVIDENCE]** Mehrotra & Musolesi, *"My Phone and Me: Understanding People's Receptivity to Mobile
Notifications"*, CHI 2016 — 10,372 in-the-wild notifications, 20 users: perceived disruption depends
on presentation, sender relationship and current task, and **even objectively important
notifications can still be disruptive**.

**[ABSENT]** No study was found that measures the **decay of a time-sensitive alert's conversion
value with delay** — nothing of the form "usefulness drops X% per minute" for reservations, tickets
or matching. The failure mode the ticket names is real and **has never been quantified**. Pielot
gives the latency distribution; nobody has paired it with an outcome curve.

### Notification cost

**[EVIDENCE, relayed]** Wohllebe & Hübner, *"Mobile apps in retail: Effect of push notification
frequency on app user behavior"*, *Innovative Marketing* (2021) — **17,500 users, 5 frequency
conditions, 7 weeks**
([journal record](https://businessperspectives.org/index.php/journals/innovative-marketing/issue-382/mobile-apps-in-retail-effect-of-push-notification-frequency-on-app-user-behavior)).
Reported findings: uninstall probability rises with frequency; roughly **10% disable notifications
at one per week**, rising toward **~40% at three to six per week**; but **weekly push produced 2–5×
higher retention and daily 3–6× higher retention than no notifications at all.** *(Primary PDF
returned 403; relayed via the journal record and secondary summary.)* The two-sided result is the
important part: **too few notifications also costs retention.**

**[VENDOR]** Airship's 2026 benchmark reports median opt-in of 61.4% Android / 49.8% iOS and median
direct open rates around 3%
([Airship](https://www.airship.com/resources/mobile-app-push-notification-benchmarks-2026/)).
Self-published aggregate. The much-quoted *"46% disable and 32% uninstall after 6 notifications"*
figure recurs across marketing blogs with inconsistent attribution and **could not be traced to a
primary report** — treat it as folklore, not a number.

### The theory says something uncomfortable

Reread §1's dynamic-matching results in this light. Standing search is, formally, a decision to
**batch instead of match greedily**. Akbarpour–Li–Oveis Gharan says that pays **only if the system
can identify who is about to depart**; Bäumler et al. say instantaneous matching is near-optimal
even in thin, sparse markets under mild conditions.

**Raketa cannot see departures.** A player who gives up does not emit an event; §7.1's signals do
not include intent to churn. **On the best available theory, the value of holding a search open
rather than matching as soon as somebody clears the floor is unproven, and conditional on
information this product does not have.**

That does not kill the feature. It reframes it: **standing search's job is not to find a better
match by waiting — it is to keep a player who would otherwise leave.** Those are different claims
with different metrics, and #166 should not let the first smuggle in the second.

---

## 6. The measurement trap — the item with the best prior art

### Guardrail metrics are a real, named discipline

**[EVIDENCE]** Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments* (Cambridge, 2020).
Chapter 7 is *"Metrics for Experimentation and the Overall Evaluation Criterion"*
([Cambridge](https://www.cambridge.org/core/books/abs/trustworthy-online-controlled-experiments/metrics-for-experimentation-and-the-overall-evaluation-criterion/0A8BF7F06A1338FF6D10C49F4CD8A198));
Chapter 21 is *"Sample Ratio Mismatch and Other Trust-Related Guardrail Metrics"*
([Cambridge](https://www.cambridge.org/core/books/abs/trustworthy-online-controlled-experiments/sample-ratio-mismatch-and-other-trustrelated-guardrail-metrics/8DBB0F59AC7729D7BC6B94690DB9CCD5)).
The book's own framing: hundreds or thousands of metrics are computed, **many for debugging**,
**some are organisational guardrails the experimenter must not damage**, and **a small number
compose the OEC to be optimised**. §19.1 is already this taxonomy; it has simply not named it.
*(Chapter text is paywalled; this rests on the abstracts and front matter.)*

**[EVIDENCE, first-party]** **Spotify** publishes the fullest public version of the taxonomy —
success, guardrail, deterioration, and **quality/diagnostic** metrics — with guardrails tested for
**non-inferiority** rather than superiority, which *"forces teams to specify at what cost you can
accept one metric to improve at the expense of another"*, and the reported figure that **guardrail
metrics trigger rollbacks in 42% of experiments**
([Spotify Engineering](https://engineering.atspotify.com/2024/03/risk-aware-product-decisions-in-a-b-tests-with-multiple-metrics),
[Confidence blog](https://confidence.spotify.com/blog/better-decisions-with-guardrails)).

**[ANECDOTE]** The three-way **success / guardrail / diagnostic** vocabulary is now standard across
experimentation vendors, with the operative definition of a diagnostic being that it *"should not
drive decision-making independently"*
([VWO](https://vwo.com/stats-blog/three-kinds-of-metrics-the-success-the-guardrail-and-the-diagnostic/),
[Eppo](https://www.geteppo.com/blog/what-are-guardrail-metrics-with-examples)). **[ABSENT]** No
single paper coins "diagnostic metric"; it is convergent vocabulary. Airbnb's *Designing
Experimentation Guardrails* post exists and returned 403.

**This settles half of item 6: §19.1's move is standard practice with standard vocabulary.**
Raketa's empty-result rate is, in Kohavi/Spotify terms, a **diagnostic**; the return rate is the
**OEC**. Saying so in those words makes the position defensible to anyone who has run experiments
professionally, and it is a two-line edit to §19.1.

### The delayed-cost mechanism has been measured — once, properly

**[EVIDENCE]** Hohnhold, O'Brien & Tang, *"Focusing on the Long-term: It's Good for Users and
Business"*, KDD 2015
([Google Research](https://research.google/pubs/focus-on-the-long-term-its-better-for-users-and-business/)).
Google's finding, in their own abstract: *"user satisfaction is paramount: ads blindness and
sightedness are driven by the quality of previously viewed or clicked ads"*, and the work produced
two applications — an auction change emphasising quality, and **a 50% reduction in ad load on mobile
search**. The method matters as much as the result: a **cookie-cookie-day** design with daily
re-randomisation and an **A/A holdout run immediately after the treatment period**, built
specifically to separate the lagged behavioural effect from the immediate one
([methodology post](https://www.unofficialgoogledatascience.com/2015/10/experiment-design-and-modeling-for-long.html)).

**This is the closest thing that exists to the design document's causal claim**: a short-term metric
improves, a slow-moving trust effect moves the other way, and it takes deliberate apparatus to see
it at all. It is about ad load rather than a matching quality floor — but the mechanism is the one
§19.1 is describing.

**[EVIDENCE]** Athey, Chetty, Imbens & Kang, *"The Surrogate Index"*, NBER w26463 (2019)
([NBER](https://www.nber.org/papers/w26463)) — a weighted index of short-run proxies can be shown
empirically to track a long-run outcome. Worth noting that **return-rate-within-60-days is itself
already a surrogate** for the retention Raketa actually cares about; §19.1 is one level into this
literature whether it knows it or not.

### The exact analogue — and somebody already ran the experiment

**[EVIDENCE] This is the single most on-point finding in the file.** Wikimedia's Discovery team
tracked **Zero Results Rate (ZRR)** as a core KPI, then ran
[*Research:Reducing Zero Result Searches Through Confidence Changes*](https://meta.wikimedia.org/wiki/Research:Reducing_Zero_Result_Searches_Through_Confidence_Changes):
they **lowered the search confidence threshold** — returning results the system was less sure were
relevant — specifically in order to cut ZRR. One week, 10% of traffic, **13.45 million search
events** (7–14 August 2015). Result: an initial 7M-event subsample looked like a win; **the full
13.45M sample reversed it, with control 0.08% better** (Cohen's *w* = 0.001, an order of magnitude
below "small"). **They recommended disabling the change and reverting to default search.**

Two further pieces from the same team make the contrast:

- Their productive ZRR reduction came from a **completion suggester** that fixed *query
  understanding* — reported as reducing zero results by around 10% **without touching the relevance
  bar** ([Wikimedia Diff](https://diff.wikimedia.org/2015/12/23/search-and-discovery-on-wikipedia/)).
- They analysed query features to **predict** zero-result queries, found question marks a strong
  predictor, and responded by stripping punctuation — diagnosing the input rather than loosening the
  output ([Query Features and Search Performance](https://wikimedia-research.github.io/Discovery-Search-QueryFeatures-201610/)).

**The lesson for §19.1, stated as it actually is:** lowering the bar to cut the empty-result number
did not even buy the short-term win it was designed to buy. **The productive move on an empty-result
number is to attack its causes, not its threshold.** In Raketa's terms: thin pools are fixed by more
players and better availability overlap, not by a lower `QUALITY_FLOOR`.

**[ANECDOTE, expert]** Daniel Tunkelang (ex-LinkedIn, ex-Endeca), *"Making Sense of Null and Low
Results"* ([LinkedIn](https://www.linkedin.com/pulse/making-sense-null-low-results-daniel-tunkelang-nzmxc)):
*"Minimizing null and low results sounds sensible, but it confuses causes with symptoms"*, and
*"It is better to be forthright about not having what the searcher wants than to flood the searcher
with irrelevant results."* An opinion, not a study — but an independent, credentialed restatement of
§9.7 and §19.1 almost word for word, which is worth having on the record.

**[POLICY]** **Ad-quality floors are the mainstream production precedent for showing nothing rather
than something bad.** Google Ads' Ad Rank thresholds *"remove low-QS ads even when there is no
competition"* ([Google Ads Help](https://support.google.com/google-ads/answer/156066)); Microsoft
Advertising suppresses "Below Average" keywords regardless of bid
([Microsoft](https://learn.microsoft.com/en-us/advertising/msa-help/hlp_ba_conc_aboutqualityscore)).
Neither publishes the threshold value or a study of moving it. **The existence of the pattern at the
largest possible scale, in a business with maximal incentive to fill the slot, is the best available
answer to "isn't refusing to show anything commercially naive?"**

**[EVIDENCE]** McNee, Riedl & Konstan, *"Being Accurate is Not Enough: How Accuracy Metrics Have Hurt
Recommender Systems"*, CHI 2006 EA ([ACM](https://dl.acm.org/doi/10.1145/1125451.1125659)) — the
adjacent classic: optimising a single legible accuracy metric produced technically correct and
useless recommendations, and launched the beyond-accuracy literature. Same genus (proxy diverging
from value), different species (over-fitting to accuracy, not lowering a floor).

### Goodhart's law is an aphorism, and should be cited as one

**[ANECDOTE — and the provenance matters]** Goodhart's 1975 statement was about **econometric
regularities collapsing under policy pressure**, not about KPIs. The familiar phrasing — *"when a
measure becomes a target, it ceases to be a good measure"* — is **Marilyn Strathern**, *"'Improving
ratings': audit in the British University system"*, *European Review* 5(3), 1997, 305–321
([Cambridge](https://www.cambridge.org/core/journals/european-review/article/abs/improving-ratings-audit-in-the-british-university-system/FC2EE640C0C44E3DB87C29FB666E9AAB),
[full text](https://gwern.net/doc/statistics/decision/1997-strathern.pdf)) — a qualitative
anthropological essay on UK university audit culture. **Neither is an empirical finding.** The
empirical backing for §19.1's claim comes from Hohnhold et al. and Wikimedia. Cite those.

### Accountability: the error budget is the structural precedent

**[POLICY]** §23.10 says the floor needs an owner by name. The closest published mechanism is the
**error budget**, Google SRE Book ch. 3, *"Embracing Risk"*
([sre.google](https://sre.google/sre-book/embracing-risk/)). Three properties transfer directly:

1. **Two named roles, not one.** Product Management sets the SLO; SRE measures against it; *"the
   difference between these two numbers is the 'budget'"*. Setting the number and reporting on it
   are deliberately different people.
2. **The number has teeth.** It works only because *"an SRE team [has] the authority to actually stop
   launches if the SLO is broken."* A floor that only appears on a dashboard is not a floor.
3. **Loosening it is a named act, not a drift.** *"If the team is having trouble launching new
   features, they may elect to loosen the SLO (thus increasing the error budget) in order to increase
   innovation."* Allowed — but as an explicit, attributable decision to accept more risk.

**Point 3 is the answer to the design document's own worry** about whoever lowered the floor having
moved on. The protection is not that the number can never change; it is that changing it is a
recorded decision with a name on it, and that the empty-result rate is never on its own sufficient
grounds. In this repo that mechanism already exists and is called an ADR.

**[ABSENT]** No published prior art found on naming an accountable owner for a *search or match
quality threshold* specifically, outside the SRE analogy.

---

## What the three refusals actually rule out

Collected in one place, because the ticket asked for this to be explicit rather than neutral.

**Refusal 1 — the engine never sends a challenge on a player's behalf** rules out the most effective
documented liquidity tactic in the adjacent industry: manufactured contact signals. The FTC's
Match.com case is precisely this, and it is what a *"we noticed you might like each other, so we said
hello for you"* feature becomes. It also sets a boundary condition on standing search: **notifying a
player that a candidate exists is admissible; acting toward the candidate is not.** #166 has to write
that line down.

**Refusal 2 — never a bad match rather than nothing** rules out every seeding tactic that fills the
pool with entities that cannot play: bots, generated profiles, imported or scraped listings, dormant
accounts presented as live. It is the refusal with the strongest external support, and the support is
entirely negative — Ashley Madison and Match.com are what happens on the other side of it. It does
**not** rule out changing `QUALITY_FLOOR`, which is a legitimately open number (§23.10) — but §6 is the
case for never changing it *in response to the empty-result rate*.

**Refusal 3 — no number without a one-sentence explanation naming its evidence** rules out the silent
widen, which the ladder already refuses, and rules out any liveness or "recently active" signal that
is inferred rather than observed. Less obviously, it constrains the pool description itself:
*"Four padel players within 8 km this week"* is a number on a screen, and must be as defensible as a
Fit score.

---

## Where the evidence does not exist

Stated plainly, so nobody fills these in later from memory.

1. **No controlled comparison of an honest empty state against a low-quality result.** In any domain.
   §9.7's central conviction is unfalsified and unsupported.
2. **No measured density threshold for a local matching product.** Nextdoor publishes a chosen one
   (10 verified members, 21 days); nobody publishes a measured one.
3. **No test of disclosed widen vs. silent widen vs. plain empty state.** The three-way comparison
   item 4 asks about has not been run.
4. **No decay curve for a time-sensitive alert's value.** Notification response-time distributions
   exist (Pielot); outcome decay does not.
5. **No independent conversion data for saved search / notify-me** in any vertical. Every number
   available is vendor marketing.
6. **No published case of an organisation holding an empty-result rate as an explicit non-target and
   reporting what happened.** Wikimedia is the closest: they attempted the opposite move and measured
   it failing within a week. The specific chain in §19.1 — floor lowered, empty-result rate improves,
   return rate erodes at sixty days, author long gone — is a **well-grounded extrapolation** joining
   Hohnhold's delayed-cost mechanism to Wikimedia's coverage/relevance trade. **It is not a documented
   case, and the design document should not imply it is one.**
7. **No external support for the fabricate / don't-fabricate distinction as an analytical category.**
   It is this product's own line.

---

## Suggested follow-ups, for #166 to accept or discard

Not decisions — the shortest list of things this research makes newly available.

- **Name the taxonomy in §19.1.** "Empty-result rate is a diagnostic, not a target" is Kohavi's and
  Spotify's vocabulary exactly. Two lines, and the position stops sounding idiosyncratic.
- **Weigh control against disclosure in §9.8.** Dietvorst's measured lever is *letting the user
  adjust*, not *telling them what changed*. A ladder the player can push or undo has evidence behind
  it that an announcement alone does not.
- **Make the pool description visually loud.** NN/g's eye-tracking says a quiet empty state is read
  as no state at all.
- **Add a density hypothesis to §24.** Players per sport per district needed to clear
  `MIN_SHORTLIST` without relaxation, with its falsifier. It cannot be borrowed from outside; it has
  to be derived and measured.
- **Separate standing search's two claims.** "Waiting finds a better match" is contradicted by the
  dynamic-matching theory given signals this product does not have. "Standing search retains a player
  who would otherwise leave" is untested but plausible, and has a different metric.
- **Consider the Strava move as a fourth option** alongside relax / describe / notify: change what
  the thin-pool screen is *for*, rather than what clears the bar.
- **Record floor changes as ADRs.** The error-budget precedent says the protection is not
  immutability, it is attribution.
