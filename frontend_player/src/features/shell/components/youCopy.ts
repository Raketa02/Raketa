/**
 * **The You tab's own sentences** — its title and the three group titles
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §27).
 *
 * They are the shell's for §1's reason: they are about the **tab** — what it is called and
 * how its rows are grouped — where every row from *Skill passport* down is the feature's whose
 * fact it is, and each of those features owns its row's title and live line
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1). The group titles are exported because the screens behind the rows wear them as their
 * eyebrow: *Playing · Skill passport*, *Finding players · Your week*, *On your card · Name*.
 *
 * **Three groups, because the rows answer three questions**: what has the platform concluded
 * about me, what does the matcher read when it looks for a game, and what does a stranger read
 * about me. A fourth question — the account — is not asked on this tab (ADR-0179 §9), and
 * *Sign out* stays at the foot as the account panel draws it.
 *
 * **The eyebrow is gone too**: *Player profile* over the title said what the bar under the screen
 * already says, and went at the product owner's ask (#529, 2026-10-02).
 *
 * **The placeholder line is gone.** *Your profile, your radius, your week — not built yet*
 * was a citation for as long as the tab was unbuilt; the tab is built, and the fifth tab has
 * left the placeholder table with it.
 */

export const YOU_COPY = {
  title: 'You',
  groups: {
    playing: 'Playing',
    findingPlayers: 'Finding players',
    onYourCard: 'On your card',
  },
} as const;
