---
paths:
  - "src/features/*/model/**"
  - "src/features/*/state/**"
  - "src/platform/query/**"
---

# TanStack Query, Zustand and URL state

## Query owns remote server state *(§12)*

It is not a general state container.

- **Feature-owned typed key factory** — hierarchical, deterministic, includes every input
  that changes the response *and the tenant*; never a token, never a display label. *(§12.2)*
- **Query option factories,** not `queryKey`/`queryFn`/`staleTime` duplicated per component.
  That is what makes prefetch, hydration and invalidation consistent. *(§12.3)*
- **`staleTime` is a product decision per data class,** not one global number: session,
  near-real-time availability, club config, reference data, immutable history. Choose
  `gcTime` independently. Decide focus/reconnect/mount refetch deliberately — an admin tab
  stays open for hours. *(§12.4, §12.5)*
- **Propagate the abort signal** into `fetch` — type-ahead, fast-changing filters, reports.
- **Invalidate narrowly.** Prefer updating known entries from the mutation response over a
  broad prefix invalidation after every write. *(§12.7)*
- **Mutation retry defaults off.** Optimistic updates only when rollback is deterministic
  and conflict semantics are understood — not for payments, destructive admin actions or
  permission changes. *(§12.8, §12.9)*
- **RSC and Query must not own the same live value.** Pick one per region: server-owned
  (RSC renders, refresh via navigation) or client-owned (RSC prefetches + dehydrates, then
  Query owns it). Divergence after revalidation is the failure mode. *(§12.12)*
- Server prefetch uses a **request-local** QueryClient. Never a global one shared across
  users. *(§12.11, §42.2)*

## Zustand *(§13)*

Only client UI state that belongs to neither the server nor the URL: sidebar state, command
palette, non-navigable selection, transient wizard draft, UI preferences.

**Never** a second cache for bookings, courts, members, club settings, session tokens,
server permissions, URL filters, or single-screen form state. Prefer several small stores
with a reset policy over one global store; subscribe to the smallest slice. **Never a global
mutable store on the server** — that leaks one user's state into another request. Persist
only non-sensitive, versioned, migratable, tenant-scoped state. *(§13.2–13.6)*

## URL state *(§14)*

Filters, date ranges, sort, page/cursor, active tab, search query, selected club go in
search params so back/forward, deep links, refresh and multiple tabs all work. Parse and
normalize them **once at the boundary** into a canonical typed value; do not let every
component parse strings.
