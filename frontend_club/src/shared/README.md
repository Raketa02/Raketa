# `src/shared/` — generic capability that knows no feature

If something here starts to know about courts, bookings or clubs, it belongs in a
feature. If it is application infrastructure — the API clients, auth, request context,
query client, config, observability — it belongs in [`../platform/`](../platform/README.md).

| Folder | Holds |
| --- | --- |
| `ui/` | Design-system primitives: button, input, select, dialog, tooltip, table parts, badge, typography, form-field layout, loading/error primitives. Plus `tokens.css`, the source of every value. |
| `lib/` | Pure, generic helpers. Domain-independent only. |
| `hooks/` | Truly generic browser hooks. |
| `types/` | Generic types with no feature meaning. |
| `test/` | Shared test utilities and factories. |

## Rules

- **`shared/` imports no business feature.** Ever. That direction is what keeps it
  genuinely shared rather than a back door between features. *(§6.1)*
- **A primitive does not know what a booking is.** `BookingStatusBadge` and
  `CourtAvailabilityGrid` belong to their feature's `ui/`, composed from these
  primitives. *(§39.1, §39.2)*
- **Accessibility is encoded once, here.** Focus management, ARIA semantics and keyboard
  behavior live in the primitives so feature code cannot reimplement them incorrectly.
  *(§39.3)*
- **`lib/` is not a `utils/` dump.** A helper earns a place here only when it is truly
  domain-independent. A booking calculation stays in the booking feature even if two
  screens use it — directories named `common`, `misc`, `helpers` become architecture
  bypasses. *(§17.8, §39.4)*
- **Never a literal design value in a component.** Every colour, size, space, radius,
  shadow and z-index comes from `ui/tokens.css` as `var(--…)`. Styling is CSS Modules
  colocated with the component. See [`../../docs/design-system.md`](../../docs/design-system.md)
  and [ADR-0011](../../../docs/adr/0011-club-console-design-system.md).

## What moved to `platform/`

`lib/http/`, `lib/auth/`, `lib/query-client/`, `config/`, `errors/` and `store/` used to
live here. They are application infrastructure with a server/client split and a
`server-only` boundary to enforce, which is what `platform/` exists for. Cross-cutting
Zustand now lives in `platform/` or in the owning feature's `state/` — not in a single
global store. *(§13.3)*
