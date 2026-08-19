# How a value is rendered

**This is not a design system.** It holds no colour, weight, size or spacing — those are
per-app and never shared ([`CONTEXT-MAP.md`](../CONTEXT-MAP.md),
[ADR-0011](adr/0011-club-console-design-system.md),
[ADR-0012](adr/0012-player-app-design-system.md)). It holds one thing: **the exact string a
given value becomes**, so that a price rendered in the club console and the same price
rendered in the player app are the same characters.

## Why it lives outside both apps

The backend never formats. It emits values and stable machine codes and no display text at all
([ADR-0022](adr/0022-kernel-negative-space-and-constant-homes.md)), because a preformatted
string can only be one rendering and one price needs three — struck through beside its
discounted twin, bare inside a tile whose header carries the unit, and plain on a row.

So each client formats, and under
[ADR-0005](adr/0005-three-app-monorepo-ownership-boundaries.md) they share no code to do it
with. That duplication is deliberate and it is safe, because there is no *rule* in it — only
the risk that the two drift. This file is what they implement, and the cross-application
contract suite from [ADR-0021](adr/0021-kernel-in-backend-clients-derive-by-comparison.md) is
what proves they still agree.

## The table

| Value | Renders as | Notes |
| --- | --- | --- |
| Money | `38,00 zł` | **Comma** decimal · non-breaking space before `zł` · **always** two decimals |
| Money, thousands | `2 474,25 zł` | **Non-breaking space** as the thousands separator, never a comma |
| Money, inside a tile | `2 474,25` | The `zł` is dropped only where the label already carries it |
| Money, discounted | `38,00` struck through, then `30,00 zł` | Plus a tag reading `card −8,00` |
| Money, negative | `−38,00 zł` | **U+2212 MINUS SIGN**, never a hyphen |
| Money, zero | `0,00 zł` | **A zero fee is a rendered row, never an omitted one** |
| Level | `2,71` | Comma, always two decimals |
| Percent | `89%` | No decimal, no space |
| Time | `09:00` | 24-hour, zero-padded |
| Duration | `60 min` · `1 h 30 min` | **Space before the unit** |
| Day, short | `Sat 8` | Grid headers |
| Day, long | `Saturday 8 August` | Page subtitles |

**Tabular numerals wherever numbers are compared.** A column of prices in proportional figures
does not line up, and a grid of times is unreadable.

## Three things that will be got wrong otherwise

- **The minus is U+2212, not a hyphen.** At small sizes a hyphen beside a digit is nearly
  invisible.
- **Both spaces are non-breaking** — the thousands separator and the one before `zł`. An
  ordinary space lets a price wrap mid-number at the end of a line.
- **A zero renders.** `0,00 zł` says *there is no fee*; an empty cell says *we forgot*.

## Two things not to use

- **Not `Intl.NumberFormat`.** It is locale-dependent at runtime and gives different output
  depending on the ICU build, so the same value can render differently on two phones.
- **Not `toFixed`.** It rounds half-to-even in some engines and half-up in others, and it
  reintroduces a float into a number that arrived as exact integer grosze
  ([ADR-0023](adr/0023-money-integer-grosze-gross-whole-zloty.md)).

## Not here

**Copy is not formatting.** The sentence shown when something is unavailable — *"Not enough
players in yet to forecast"* — is each app's own, written in its own voice. The backend sends
a machine code and its payload; the client decides the words, including the case where the
right answer is to show nothing at all.

**Localisation is not open yet.** One locale, stated. A second market is a new decision, and
this table changes with it.
