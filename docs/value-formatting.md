# How a value is rendered

**This is not a design system.** It holds no colour, weight, size or spacing — those are
per-app and never shared ([`CONTEXT-MAP.md`](../CONTEXT-MAP.md),
[ADR-0012](adr/0012-player-app-design-system.md)). It holds one thing: **the exact string a
given value becomes.**

> **After the 2026-08-25 reset, one client implements this table.** It was written when two
> did, and the drift it exists to prevent needs two. It is kept, trimmed to the values that
> still cross the wire, for one reason: a second client's first act is rendering a Level,
> and re-deriving these rules from memory is exactly how two apps end up printing `2.71` and
> `2,71` for one rating. The money rows went with the money kernel — a currency rendering
> restated from nothing is worse than one absent, so a priced context reopens this file.

## Why it lives outside the app

The backend never formats. It emits values and stable machine codes and no display text at all
([ADR-0022](adr/0022-kernel-negative-space-and-constant-homes.md)), because a preformatted
string can only be one rendering and one value usually needs several — bare inside a tile
whose header carries the unit, and labelled on a row.

So the client formats, and under
[ADR-0005](adr/0005-three-app-monorepo-ownership-boundaries.md) clients share no code to do it
with. That duplication is deliberate and it is safe, because there is no *rule* in it — only
the risk that two clients drift. This file is what they implement, and the cross-application
contract suite from [ADR-0021](adr/0021-kernel-in-backend-clients-derive-by-comparison.md) is
what proves they still agree.

## The table

| Value | Renders as | Notes |
| --- | --- | --- |
| Level | `2,71` | **Comma** decimal, always two decimals |
| Percent | `89%` | No decimal, no space |
| Time | `09:00` | 24-hour, zero-padded · **rendered in the zone the value names, never the device's** — see below |
| Duration | `60 min` · `1 h 30 min` | **Space before the unit** |
| Day, short | `Sat 8` | Grid headers |
| Day, long | `Saturday 8 August` | Page subtitles |
| Negative number | `−2,71` | **U+2212 MINUS SIGN**, never a hyphen |
| Zero | `0,00` | **A zero is a rendered value, never an omitted one** |

**A time is rendered in the zone its value names.** An instant crosses the wire as UTC with
the zone it should be read in beside it
([ADR-0024](adr/0024-instant-as-aware-datetime-minute-coordinates.md)): `19:00` means the
clock on the wall at the place the value is about, and it still reads `19:00` to someone
sitting in London. **The one exception is a value about the player rather than about a
place** — a header clock, which is the device's own, because that line says *it is now 14:30
where you are*.

**Tabular numerals wherever numbers are compared.** A column of levels in proportional figures
does not line up, and a grid of times is unreadable.

## Two things that will be got wrong otherwise

- **The minus is U+2212, not a hyphen.** At small sizes a hyphen beside a digit is nearly
  invisible.
- **A zero renders.** `0,00` says *this value is zero*; an empty cell says *we forgot*.

## Two things not to use

- **Not `Intl.NumberFormat`.** It is locale-dependent at runtime and gives different output
  depending on the ICU build, so the same value can render differently on two phones.
- **Not `toFixed`.** It rounds half-to-even in some engines and half-up in others, and it
  reintroduces a float into a number that arrived exact.

## Not here

**Copy is not formatting.** The sentence shown when something is unavailable is the app's
own, written in its own voice. The backend sends a machine code and its payload; the client
decides the words, including the case where the right answer is to show nothing at all.

**Localisation is not open yet.** One locale, stated. A second market is a new decision, and
this table changes with it.

**Money crosses the wire as integer grosze, and its rendering is not decided yet.** The
kernel's money module was removed in the reset; the first priced context is a club's
court prices (#535), and it sends every amount as an **integer in grosze**, in a field named
`…_grosze` — `price_grosze: 14000` is 140 zł, and a share is exact to the grosz because a
price that does not split among the seats is refused. How a client *renders* one — the
decimal comma, the space before `zł`, whether whole złoty drop their grosze — is still to be
decided, here, by the first client that draws a price (#561), rather than recovered from the
deleted ADR-0023.
