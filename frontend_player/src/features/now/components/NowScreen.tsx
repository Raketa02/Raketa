/**
 * Now — the player app's home, and the first screen after onboarding.
 *
 * **A status surface before a search box.** Three regions top to bottom — offers,
 * the enrolled strip, the shelves — with the sport bar above them and the tab bar
 * (`Raketa02/Raketa#93`) below. There is no promo block and no MultiSport card:
 * `ADR-0050`'s rule is that a row that is neither a thing the player is in nor a
 * thing she could join is furniture.
 *
 * ## The phone holds no rules
 *
 * `ADR-0053`. No kernel here in any form. Nothing is derived locally, nothing is
 * provisional, nothing is marked and nothing is reconciled — the only permitted
 * derivation in the whole feature is subtracting a card's one moment from the
 * current time, which is `domain/countdown.ts` and is read by exactly one hook.
 * A client cannot disagree with the server about a rule because it holds none.
 *
 * ## Four asks, and nothing else
 *
 * `ADR-0054`, and every one of them is visible in this file:
 *
 * 1. **Arrival** — the app *foregrounding*, which is `focusManager` plus
 *    `refetchOnWindowFocus: 'always'` in `useNow`. Not a screen becoming visible:
 *    popping back off a route is none of the four, which is what
 *    `staleTime: Infinity` with `refetchOnMount: false` buys.
 * 2. **Pull** — the `RefreshControl` below, which keeps the screen exactly where
 *    it is and puts its indicator at the top.
 * 3. **An action** — invalidating `nowKeys`. Nothing on this screen is an action
 *    yet; the routes that will be (`#89`, `#91`, `#92`) hand Now its update in
 *    their own response, at which point this becomes a cache write and not a
 *    fetch.
 * 4. **A countdown reaching zero** — `useDeadlineAsk`, one wake at a moment the
 *    server named. **There is no interval anywhere.**
 *
 * ## The second timer repaints and never asks
 *
 * `NowClockProvider` holds the screen's one repaint clock (`ADR-0088`): a card's
 * countdown redraws once a second inside ten minutes and once a minute above,
 * which is a **repaint** and not a fifth occasion to fetch. The two timers are
 * kept apart by shape rather than by discipline — the repaint module cannot reach
 * Query at all, and `nowDiscipline.test.ts` walks it.
 *
 * ## What the screen never says
 *
 * It never admits staleness: no marker, no dot, no banner, no *"can't reach
 * Raketa"*. It either shows what is true or shows that it is fetching. A refresh
 * that fails over a populated screen changes nothing on it — she keeps reading
 * what she had, and her next ask will try again.
 */

import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useCallback } from 'react';
import { useRouter } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { Card, ScreenHeader, theme } from '@/shared/ui';

import { dayAndTime } from '../domain/deviceClock';
import { useDeadlineAsk } from '../hooks/useDeadlineAsk';
import { useNow } from '../hooks/useNow';
import { useSportFilter } from '../hooks/useSportFilter';

import type { FindPreFilter } from '../mappers/shelves';

import type { CardControl } from './ActionRow';
import { NowClockProvider } from './NowClock';
import { EnrolledStripView, OffersRegionView, ShelvesRegionView } from './NowRegions';
import { NowShimmer } from './NowShimmer';
import { SportBar } from './SportBar';
import { greeting, nowErrorMessage } from './nowCopy';
import { GUTTER } from './nowGeometry';

export function NowScreen() {
  const { selected, select } = useSportFilter();
  const now = useNow(selected);
  const user = useCurrentUser();
  const router = useRouter();

  const { refetch } = now;
  // Stable, so arming the deadline wake does not re-run on every render.
  const ask = useCallback(() => {
    void refetch();
  }, [refetch]);

  useDeadlineAsk(now.data, ask);

  // Where a card's two controls go.
  //
  // **The exit has a destination; the act still has none.** Leaving is a route
  // that states the price before anything happens (`ADR-0086`), and it is the
  // first control on this screen to reach one. Every act's destination still
  // belongs to a ticket that has not landed — the seat claim and its payment are
  // `Raketa02/Raketa#89`, the result screen `#90`, leaving standby `#92`, and the
  // Getting-in sheet is outside this map — so an act is still received and
  // dropped here, which is the one place each will be wired.
  //
  // The route is addressed by the **match**, because that is what the departure
  // is about and it is the only thing the server needs to answer. Nothing about
  // the card is carried across: the screen asks for what leaving is worth at the
  // instant it opens, and handing it the card's own already-composed facts would
  // be quoting a number the card never checked.
  const onControl = useCallback(
    (control: CardControl) => {
      switch (control.kind) {
        case 'exit':
          router.push({
            pathname: '/matches/[matchId]/departure',
            params: { matchId: control.card.matchId },
          });
          return;
        case 'act':
          return;
      }
    },
    [router],
  );

  // Where a shelf's tail card goes: Find, carrying that shelf's claim and the sport
  // the screen is already filtered to.
  //
  // **The pre-filter is composed and cannot yet be delivered**, which is reported
  // rather than faked (`Raketa02/Raketa#115`). Find is the placeholder route `#93`
  // shipped: no feature, no filter and no parameters. Inventing a query-string shape
  // here would decide Find's contract from Now, which is the one thing
  // `FindPreFilter` is a value object rather than a URL to avoid. So the tap opens
  // the destination the tab bar already reaches, and the claim stops here.
  const onOpenFind = useCallback(
    (preFilter: FindPreFilter) => {
      void preFilter;
      router.push('/find');
    },
    [router],
  );

  // The door, and the only thing this screen knows about the questionnaire: an
  // address (`ADR-0084` — *"a route into that sport's questionnaire"*). Starting
  // or resuming a run, the pass it belongs to and the whole tail after it are
  // onboarding's, and none of it is imported here.
  //
  // The chip the request carried is what names the sport, because the door's block
  // deliberately does not — she named it and still holds it, and a second copy on
  // the answer is a second thing that can disagree. `all` never produces a door, so
  // the value is always a sport; a link that somehow named one anyway is turned
  // away by the route's own validation rather than by a guard here.
  const onEnterDoor = useCallback(() => {
    router.push({ pathname: '/rate/[sport]', params: { sport: selected } });
  }, [router, selected]);

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScrollView
        contentContainerStyle={s.content}
        // The greeting scrolls away; the bar does not. A greeting is not a control.
        stickyHeaderIndices={[1]}
        refreshControl={
          <RefreshControl
            refreshing={now.isFetching && now.data !== undefined}
            onRefresh={ask}
            accessibilityLabel="Refresh"
          />
        }
      >
        <ScreenHeader
          title={greeting(user.data?.nickname)}
          // The device's own clock — the one line on Now that is about the player
          // rather than about a club. It does not tick; the screen composes on
          // arrival, which is the overwhelming majority of the reads.
          eyebrow={dayAndTime(Date.now())}
        />

        <SportBar selected={selected} onSelect={select} />

        {now.data !== undefined ? (
          <NowClockProvider screen={now.data}>
            <OffersRegionView region={now.data.offers} onControl={onControl} />
            <EnrolledStripView region={now.data.yourMatches} onControl={onControl} />
            <ShelvesRegionView
              region={now.data.shelves}
              sport={selected}
              onEnterDoor={onEnterDoor}
              onControl={onControl}
              onOpenFind={onOpenFind}
            />
          </NowClockProvider>
        ) : now.error !== null ? (
          <View style={s.gutter}>
            <Card>
              <Text style={s.failure}>{nowErrorMessage(now.error)}</Text>
            </Card>
          </View>
        ) : (
          <NowShimmer />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: { paddingBottom: theme.space.xxxl },
  gutter: { paddingHorizontal: GUTTER },
  failure: { ...theme.type.tiny, color: theme.color.muted },
});
