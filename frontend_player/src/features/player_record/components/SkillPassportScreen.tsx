/**
 * **The Skill passport** — the result card once per rating, the record's three blocks under
 * each, *Add a sport*, and the ladder
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2–§3).
 *
 * A passport is a document other people read and you cannot write. The Skill ratings this
 * player holds — one per rated sport, never per format — are drawn as the card each was first
 * met on: `Verdict`, the result screen's dark card, unchanged, with two additions across its
 * top the result never needed because one card has one status: the sport tag in the on-dark
 * variant, and a **status chip** — *Initial estimate* on-dark, *Calibrating* in amber,
 * *Stable* in mint — because a list of three cards is scanned by its chips. The *Rating status*
 * row under the bar stays as well; the card is the result card plus a chip, never a redesign.
 *
 * ## The blocks under each card are the record's, per sport
 *
 * `RecordBlocks` — *Player reliability · Last 5 · Counted* — from `GET /players/me/record?sport=`
 * for each rated sport: the first the whole person's and the same on every card, the other two
 * this sport's. They sit under the card as a sibling, exactly as they sit under the record's
 * skill card, and for the same reason — a block nested in a card drawn per sport would take
 * the person's one reliability figure down with the sport. A player rated in four sports reads
 * their score four times; the author preferred the record's row intact under each card.
 *
 * ## No tick on the ring, and why
 *
 * The ring's ceiling tick is drawn where a ceiling was served and nowhere else (7.8, as
 * amended 2026-08-14): the number is version-scoped and this client holds no copy of it.
 * `GET /ratings` serves no ceiling today, so the passport's rings draw no tick — the rule
 * ADR-0179 §2 states, *only on an Initial estimate*, is `passportCeiling`'s and takes effect
 * the day the ratings read carries the number. A constant 30 here would be the copy the
 * amendment removed.
 *
 * ## *Add a sport* is the second door into the onboarding pass
 *
 * One chip per unrated sport in the registry — the registry minus `GET /ratings`, so a player
 * rated in all four sees no card — and pressing one is onboarding's `useAddASport` (§3): the
 * sport's assessment starts through the picker's own start, a pass of that one sport begins
 * at the question route, and the pass ends back here with the new card drawn. The chip says
 * *Starting…* while the start is in the air, and a failed start is said above the chips with
 * the chip offered again — the player is still on this screen, and a start that failed began
 * nothing. Where the pass lands afterwards is the entry gate's, read off the pass's origin.
 *
 * ## The ladder prints the edges it was sent
 *
 * The four bands with their meanings and the player's own rungs marked — and an edge only on
 * a rung one of this player's ratings carries, because **band boundaries come from the
 * response** and this client restates them nowhere (7.5; `theme.ts` on `band`). A rung the
 * player is not on has no served edge and prints none.
 *
 * ## One popover for every card
 *
 * Each card holds its three marks and hands the pressed one up; the screen draws one popover
 * as a sibling of its root, as the result screen does, and the root is hidden behind it.
 */

import { useRouter } from 'expo-router';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import {
  BAND_NAMES,
  STARTING_LABEL,
  Verdict,
  VerdictPopover,
  bandPresentation,
  ratingStatusLabel,
  sportColour,
  sportLabel,
  useAddASport,
  useSkillRatings,
  useSports,
  useVerdictExplainer,
  type Explaining,
  type SkillRating,
} from '@/features/onboarding/types';
import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { formatRange } from '@/shared/formatting/ratingFormat';
import { Button, Card, Chip, Note, Tag, behindOverlay, theme, type BandKey } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { passportCeiling } from '../domain/passport';
import { useOwnRecord } from '../hooks/useOwnRecord';

import { RecordBlocks } from './RecordBlocks';
import { RETRY_RECORD_LABEL } from './recordPresentation';
import {
  ADD_A_SPORT,
  ADD_A_SPORT_BODY,
  LOADING_RATINGS,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
  ladderRung,
  rateSportChip,
  statusChipVariant,
} from './youRecordPresentation';

/** The ladder's rungs, low to high — the bar's own order. */
const LADDER: readonly BandKey[] = ['new', 'developing', 'established', 'advanced'];

export function SkillPassportScreen() {
  const router = useRouter();
  const ratings = useSkillRatings();
  const sports = useSports();
  const addASport = useAddASport();

  // One popover for every card, and every card's explainers are the same sentences, because
  // no card has a served ceiling.
  const explainer = useVerdictExplainer(undefined);

  const rated = ratings.data ?? [];
  const unrated = (sports.data ?? []).filter(
    (sport) => !rated.some((rating) => rating.sport === sport),
  );

  return (
    <>
      <View style={s.root} {...behindOverlay(explainer.open)}>
        <ShellScreen
          eyebrow={YOU_COPY.groups.playing}
          title={SKILL_PASSPORT_TITLE}
          onBack={router.back}
        >
          {ratings.isPending ? (
            <ActivityIndicator accessibilityLabel={LOADING_RATINGS} color={theme.color.muted} />
          ) : null}

          {ratings.error !== null ? (
            <View style={s.failure}>
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(ratings.error)}
              </Note>
              <Button
                label={RETRY_RECORD_LABEL}
                variant="secondary"
                onPress={() => void ratings.refetch()}
              />
            </View>
          ) : null}

          {rated.map((rating) => (
            <PassportCard key={rating.sport} rating={rating} onExplain={explainer.explain} />
          ))}

          {unrated.length === 0 ? null : (
            <Card style={s.addASport}>
              <Text style={s.cardTitle}>{ADD_A_SPORT}</Text>
              <Text style={s.tiny}>{ADD_A_SPORT_BODY}</Text>
              {/* The one thing this card can fail at, said beside the control that retries
                  it — the chip, offered again. */}
              {addASport.error !== null ? (
                <Note variant="coral" accessibilityRole="alert">
                  {recoveryMessage(addASport.error)}
                </Note>
              ) : null}
              <View style={s.chips}>
                {unrated.map((sport) => (
                  <Chip
                    key={sport}
                    label={rateSportChip(sport)}
                    dot={sportColour(sport)}
                    // The start's own word for the wait, cited from onboarding as the status
                    // chip's is — one spelling, three controls.
                    busy={addASport.starting === sport}
                    busyLabel={STARTING_LABEL}
                    onPress={() => addASport.rate(sport)}
                  />
                ))}
              </View>
            </Card>
          )}

          {ratings.data === undefined ? null : <Ladder ratings={rated} />}
        </ShellScreen>
      </View>

      <VerdictPopover {...explainer.popover} />
    </>
  );
}

/**
 * One rating's card and the record's blocks under it — the blocks from this sport's read of
 * the record, so *Last 5* and *Counted* are this sport's and the score is the person's.
 */
function PassportCard({
  rating,
  onExplain,
}: {
  readonly rating: SkillRating;
  readonly onExplain: (explaining: Explaining) => void;
}) {
  const { record } = useOwnRecord(rating.sport);
  const own = record.data;
  // The record's skill panel is for the sport the server resolved, which is this one wherever
  // the player is rated in it; read rather than assumed, so a mismatch draws the score alone.
  const thisSport = own?.skill?.sport === rating.sport ? own.skill : undefined;

  return (
    <>
      <Verdict
        rating={{ ...rating, confidenceCeiling: passportCeiling(rating) }}
        top={
          <>
            <Tag
              label={sportLabel(rating.sport)}
              variant="onDark"
              dot={sportColour(rating.sport)}
            />
            <Tag
              label={ratingStatusLabel(rating.status)}
              variant={statusChipVariant(rating.status)}
            />
          </>
        }
        onExplain={onExplain}
      />
      <RecordBlocks
        {...(own?.reliability === undefined ? {} : { playerScore: own.reliability.playerScore })}
        {...(thisSport?.lastFive === undefined ? {} : { lastFive: thisSport.lastFive })}
        {...(thisSport === undefined ? {} : { countedGames: thisSport.countedGames })}
      />
    </>
  );
}

/**
 * The four bands, the player's own marked, an edge only where a rating served one.
 */
function Ladder({ ratings }: { readonly ratings: readonly SkillRating[] }) {
  const rungs = LADDER.map((key) => {
    const mine = ratings.filter((rating) => bandPresentation(rating.band.name)?.key === key);
    // Every rating on a rung carries the same served edges; the first is as good as any.
    const served = mine[0]?.band;
    return {
      key,
      name: BAND_NAMES[key],
      sports: mine.map((rating) => rating.sport) as readonly Sport[],
      edges:
        served === undefined ? undefined : formatRange({ low: served.lower, high: served.upper }),
      meaning: bandPresentation(BAND_NAMES[key])?.meaning,
    };
  });

  return (
    <Card>
      <Text style={s.eyebrow}>{THE_LADDER}</Text>
      {rungs.map((rung, at) => (
        // 5.5's row — the name as the key, the served edge as the value in the band's ink —
        // with the meaning under it: one element per rung, spoken as the name, the edge where
        // there is one, and the meaning.
        <View
          key={rung.key}
          style={[
            s.rung,
            at > 0 ? s.divided : undefined,
            rung.sports.length === 0 ? s.notMine : undefined,
          ]}
          accessible
          accessibilityLabel={[ladderRung(rung.name, rung.sports), rung.edges, rung.meaning]
            .filter((part) => part !== undefined)
            .join('. ')}
        >
          <View style={s.rungLine}>
            <Text style={s.rungName}>{ladderRung(rung.name, rung.sports)}</Text>
            {rung.edges === undefined ? null : (
              <Text style={[s.edges, { color: theme.band[rung.key].ink }]}>{rung.edges}</Text>
            )}
          </View>
          {rung.meaning === undefined ? null : <Text style={s.tiny}>{rung.meaning}</Text>}
        </View>
      ))}
    </Card>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  failure: { gap: theme.space.sm },
  addASport: { gap: theme.space.xxs },
  cardTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  tiny: { ...theme.type.tiny, color: theme.color.muted },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs, marginTop: theme.space.xs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  rung: { gap: theme.space.xxs, paddingVertical: theme.space.xs },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  // 7.5's inactive opacity, the bar's own word for *not the player's band*, on the rungs the
  // player is not on — the absent *you* carries it too, never the fade alone.
  notMine: { opacity: theme.size.levelBar.inactiveOpacity },
  rungLine: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  rungName: { ...theme.type.rlValue, color: theme.color.ink, flexShrink: 1 },
  edges: { ...theme.num.xs, ...theme.tabular },
});
