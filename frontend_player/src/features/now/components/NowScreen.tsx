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
 * 3. **An action** — and it is a **cache write rather than a fetch** (`ADR-0074`),
 *    because every act off this screen hands Now its update in its own response.
 *    Two of them this screen makes itself, and neither asks first: `useTakeSeat`
 *    writes the card and the two regions the answer carries, and `useLeaveStandby`
 *    writes the one form of the update that **removes** a card. Neither
 *    invalidates anything. The routes do the same from outside.
 * 4. **A countdown reaching zero** — `useDeadlineAsk`, one wake at a moment the
 *    server named. **There is no interval anywhere.**
 *
 * ## The one sentence this screen writes for itself
 *
 * Everything else on Now is a sentence the wire sent or a copy table resolving a
 * code the wire sent. *That seat has gone* is neither: it is the acknowledgement
 * `ADR-0062` specifies, and it exists because a refusal is answered by the
 * **corrected card** (`ADR-0070`) — which is honest, and which on its own would
 * have a card quietly stop offering a seat under her thumb. One plain line at the
 * top of Now, held and then faded, **once**, and never a dialog.
 *
 * ## The one line that is about the player
 *
 * `ADR-0070` puts exactly one viewer fact on the envelope beside the three
 * regions, and the **debt line** is it: an amount, a currency and one boolean
 * meaning *she may not create a match or book a court*. It is drawn above the
 * regions, exactly when the server sent one, and it changes nothing else on the
 * screen — no act is withheld, no button is disabled and no card is dimmed,
 * because being cut off must not make her less likely to pay for a seat in
 * somebody else's match.
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
import { useCallback, useState } from 'react';
import { useRouter } from 'expo-router';

import { useCurrentUser } from '@/features/auth/types';
import { Card, ScreenHeader, theme } from '@/shared/ui';

import { dayAndTime } from '../domain/deviceClock';
import { useDeadlineAsk } from '../hooks/useDeadlineAsk';
import { useLeaveStandby } from '../hooks/useLeaveStandby';
import { useNow } from '../hooks/useNow';
import { useSportFilter } from '../hooks/useSportFilter';
import { useTakeSeat } from '../hooks/useTakeSeat';

import type { FindPreFilter } from '../mappers/shelves';

import type { CardControl } from './ActionRow';
import { DebtLine } from './DebtLine';
import { NowClockProvider } from './NowClock';
import { EnrolledStripView, OffersRegionView, ShelvesRegionView } from './NowRegions';
import { NowShimmer } from './NowShimmer';
import { SportBar } from './SportBar';
import { TransientLine } from './TransientLine';
import {
  SEAT_GONE,
  STANDBY_LEAVE_FAILED,
  greeting,
  nowErrorMessage,
  seatFailureLine,
} from './nowCopy';
import { GUTTER } from './nowGeometry';

/**
 * The one sentence this screen writes for itself, and the count that makes it once.
 *
 * The number is not shown and is not a position: it is what tells one showing from
 * the next, so that tapping a second gone seat — or the same one twice — restarts
 * the hold rather than landing on a line that is already half faded.
 */
interface TransientNotice {
  readonly showing: number;
  readonly line: string;
}

export function NowScreen() {
  const { selected, select } = useSportFilter();
  const now = useNow(selected);
  const user = useCurrentUser();
  const router = useRouter();
  const takeSeat = useTakeSeat(selected);
  const leaveStandby = useLeaveStandby();
  const [notice, setNotice] = useState<TransientNotice | undefined>(undefined);

  const { refetch } = now;
  // Stable, so arming the deadline wake does not re-run on every render.
  const ask = useCallback(() => {
    void refetch();
  }, [refetch]);

  useDeadlineAsk(now.data, ask);

  const { mutate: take } = takeSeat;
  const { mutate: leave } = leaveStandby;

  // One line at a time, and each showing is its own. Replacing the sentence rather
  // than queueing a second is the whole of *once*: two lines stacked would be a
  // list of disappointments, and `ADR-0062` gives the screen one.
  const show = useCallback(
    (line: string) => setNotice((held) => ({ showing: (held?.showing ?? 0) + 1, line })),
    [],
  );
  const faded = useCallback(() => setNotice(undefined), []);

  // Where a card's two controls go.
  //
  // **Four of the seven acts have a destination now, and two of the four are
  // writes.** `enterResult` and `answerResult` resolve to the `result` surface —
  // one route, because `ADR-0060` makes it *"one route resolving the same situation
  // the card resolved"* and the two labels are two moments of one conversation
  // rather than two screens. `takeSeat` and `leaveStandby` resolve to no screen at
  // all: each is answered by the card it was about (`ADR-0070`, `ADR-0087`), so the
  // tap sends it and the screen corrects itself. The last two belong to tickets
  // that have not landed — `finishPaying` wants the payment sheet
  // (`Raketa02/Raketa#126`) and the Getting-in sheet is outside this map — so an
  // unwired act is received and dropped here, which is the one place each will be
  // wired.
  //
  // **Neither write asks first.** A seat is a race, and leaving standby costs
  // nothing — `ADR-0087`: *"a confirmation here would imply a cost the model says
  // does not exist"*, and there is no place to forfeit because a standby position
  // is deliberately not a fact the platform shows.
  //
  // Both routes are addressed by the **match** and carry nothing else. The card's
  // own already-composed facts are not handed across: each screen asks for what is
  // true at the instant it opens, and quoting the card would be showing a number
  // the card never checked.
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
          if (control.surface === 'result') {
            router.push({
              pathname: '/matches/[matchId]/result',
              params: { matchId: control.card.matchId },
            });
            return;
          }
          if (control.surface === 'standbyWrite') {
            // One tap and no confirmation, and the acknowledgement is the card
            // **leaving** — which the hook's cache write does (`ADR-0074`). What
            // is left here is the failure, and only the failure: nothing can
            // refuse this act, so a tap that does not apply is a tap that never
            // reached the server, and a card that stayed put while saying nothing
            // is a player wondering whether she is still queued.
            leave({ matchId: control.card.matchId }, { onError: () => show(STANDBY_LEAVE_FAILED) });
            return;
          }
          if (control.surface === 'seatClaim') {
            // The cache write is the hook's (`ADR-0074`) and runs first; what is
            // left here is the acknowledgement, which exists only because the
            // answer to a refusal is a card that quietly stops offering anything.
            // `claimed` is the server's word for it and is never worked out from
            // the card that came back (`ADR-0053`).
            take(
              { matchId: control.card.matchId },
              {
                onSuccess: (answer) => {
                  if (!answer.claimed) show(SEAT_GONE);
                },
                // The same one plain line, for the two refusals that are about her
                // rather than about the seat and for a tap that never landed. A
                // dialog would stop her to say that nothing happened.
                onError: (error) => show(seatFailureLine(error)),
              },
            );
          }
          return;
      }
    },
    [leave, router, show, take],
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
            {/* At the top of Now, above the region it is about, and keyed on the
                showing so a second tap restarts the hold rather than joining a
                fade already running (`ADR-0062`). */}
            {notice === undefined ? null : (
              <TransientLine key={notice.showing} line={notice.line} onFaded={faded} />
            )}

            {/* The one fact about the viewer, above the three regions that are
                about matches, and drawn exactly when the server sent one — the
                envelope carries a debt line when something is owed and nothing
                when nothing is, so presence is never a comparison here. */}
            {now.data.debt === undefined ? null : <DebtLine debt={now.data.debt} />}

            <OffersRegionView
              region={now.data.offers}
              onControl={onControl}
              // The card whose seat is being taken right now, so its own button
              // says so. `variables` is the intent the in-flight write went out
              // with, which is the only thing that knows *which* card it was.
              busyMatchId={takeSeat.isPending ? takeSeat.variables?.matchId : undefined}
            />
            <EnrolledStripView
              region={now.data.yourMatches}
              onControl={onControl}
              // The queue place she is leaving right now, so its own button says
              // so. The strip holds a **write** for the first time (`ADR-0087`),
              // which is the condition the offers region's own prop was withheld
              // for until this ticket.
              busyMatchId={leaveStandby.isPending ? leaveStandby.variables?.matchId : undefined}
            />
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
