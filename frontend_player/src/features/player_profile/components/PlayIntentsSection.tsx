/**
 * **The play intents, listed where the other durable facts live** — one row per rated sport,
 * on the You tab ([#296](https://github.com/Rakieta02/Rakieta/issues/296)).
 *
 * A player rated in three sports holds three declarations and, until this shipped, had no page
 * that listed them: the only surface either one was ever seen on was the search form, which is
 * exactly what kept teaching people it was a search setting. ADR-0094 makes it a fact about the
 * player, read by other people's searches, and `PlayIntentSurface`'s closed five has been
 * carrying `PROFILE_SCREEN` for a client screen that did not exist. This is that screen's first
 * section; nothing about it changes a contract.
 *
 * ## Why it is here and not in `play/`
 *
 * The three writes behind the profile surface are this feature's — *"a read whose three paired
 * writes live in another feature is a read in the wrong feature"* — and
 * `PlayerProfileSurface`'s own docblock has said since it was written that *You* would draw the
 * same three facts from the same route. The week follows. It also cannot be in
 * Play: `player_profile` does not import that feature, and `playIntent.ts` records what
 * happened the last time this vocabulary travelled through a feature's front door.
 *
 * The **words for the three answers** come from `shared/vocabulary` for that reason, promoted
 * the day this became the second screen to print one.
 *
 * ## Deliberately narrow
 *
 * It is the list behind the You tab's *What kind of game* row, under that screen's one line —
 * *This changes how people find you* — which replaced the heading and the body this section
 * used to carry ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §9). The row list is a projection of two reads and **nothing is copied into a store** —
 * in particular nothing touches `playPreferences`, so a player who changes a declaration here
 * and then opens Play in a mode that disagrees is the drift backstop's own case, working as
 * designed. An **unrated** sport is not listed at all: a rating is what makes a sport
 * matchable, and offering the question for one would be collecting an answer no search could
 * ever read.
 *
 * ## The answers open in place, and they are not the interstitial
 *
 * Find a game's `DeclarationInterstitial` is a **gate** — a dark card standing in for a form
 * that may not be drawn until it is answered — and this is a list of facts you may edit. So a
 * row expands into the three answers rather than opening a copy of that card, and the row's own
 * value stays visible above them. Answering closes it; the value it draws is the route's answer
 * arriving in the cache, never the request echoed back.
 *
 * **The one in flight is busy and the other two are shut**, which is `Button`'s own
 * distinction, and the refusal is the coral note every other write in this app draws.
 *
 * ## Each answer says what it costs
 *
 * Since Q127 a change takes the player off the cards they have not answered of a kind they
 * dropped, in every group ([ADR-0201](../../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §3, §6; [#742](https://github.com/Rakieta02/Rakieta/issues/742)). So an open **declared** row
 * also reads its sport's cards across the groups, and under each answer that changes something
 * one line says so: *Your 7 competitive cards in your groups go. Games you’re In on stay.*, or
 * *Keep your competitive cards and get for-fun ones too.* Which line is
 * `domain/intentChangeCost`'s; the answer held and an undeclared sport's answers say nothing.
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { sportLabel, useSkillRatings } from '@/features/onboarding/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Card, Note, theme } from '@/shared/ui';
import { PLAY_INTENTS } from '@/shared/vocabulary/playIntent';
import {
  declarationOptionLabel,
  intentGloss,
  intentLabel,
} from '@/shared/vocabulary/playIntentPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import { intentChangeCost, sportToCount } from '../domain/intentChangeCost';
import { anySportUndeclared, playIntentRows } from '../domain/playIntentRows';
import { useDeckCounts } from '../hooks/useDeckCounts';
import { useDeclarePlayIntent, useProfileSurface } from '../hooks/useProfileSurface';

import {
  NOT_DECLARED_LINE,
  PLAY_INTENTS_ROW_HINT,
  declaredValue,
  intentCostLine,
  playIntentRowLabel,
} from './playIntentsPresentation';

/** The one surface value this screen may report, and the one screen that may report it. */
const DECLARED_ON = 'PROFILE_SCREEN' as const;

export function PlayIntentsSection() {
  const ratings = useSkillRatings();
  const profile = useProfileSurface();
  const declare = useDeclarePlayIntent();

  /**
   * Which row is open, and **at most one**.
   *
   * Route-local because it is a disclosure rather than a value: leaving the tab closes it, and
   * a second store holding *which row was open* would be UI state outliving the screen it is
   * about. One at a time, because three open rows are nine near-identical buttons in a column.
   */
  const [open, setOpen] = useState<Sport>();

  const rated = ratings.data ?? [];
  /**
   * **`undefined` until the profile read lands, and never `{}` in its place.**
   *
   * The two reads are separate and the ratings answer first, so an empty map stood in for
   * *nothing is declared* for as long as the second was in flight — and every row said *Not
   * set* under a sentence telling the player they could not search in any of their sports. A
   * read that failed said the same thing and never stopped. *Not set* is the discovery this
   * section exists to make, so drawing it falsely is the one thing that inverts it.
   */
  const declarations = profile.data?.playIntents;
  /**
   * The list, or nothing to list yet — `domain/playIntentRows` decides which sports are on it
   * and what absence means, because both are rules rather than a shape this component chose.
   */
  const rows =
    declarations === undefined
      ? undefined
      : playIntentRows(
          rated.map((rating) => rating.sport),
          declarations,
        );
  /**
   * **The open row's cards across the groups**, read only while it is a declared sport's
   * (`sportToCount`), and kept only while it stays open (`useDeckCounts`). Absent while on its way
   * and after a failure, and the lines then say no number rather than a zero: what a change costs
   * is said whether or not it can be counted, and a failure here stops no answer.
   */
  const deckCounts = useDeckCounts(sportToCount(open, declarations)).data;

  // Nothing to list until the ratings land. The screen's own line is still above this, so the
  // section simply is not there yet rather than drawing an empty card.
  if (rated.length === 0) return null;

  return (
    <View style={s.section}>
      {/* The read's own failure, and **no retry beside it**: a retry belongs to the act that
          failed, and nobody performed this read — it is one block on a tab with other content,
          and Query refetches it when the player comes back to the tab. What would be wrong is
          drawing rows over a read that did not land, which is what the sentence above
          `declarations` is about. */}
      {profile.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(profile.error)}
        </Note>
      ) : null}

      {declare.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(declare.error)}
        </Note>
      ) : null}

      {rows === undefined ? null : (
        <Card>
          {rows.map(({ sport, intent: declared }, index) => {
            const sportName = sportLabel(sport);
            const isOpen = open === sport;
            // Which answer is being written, and therefore which one is *busy* rather than shut.
            const inFlight = declare.isPending ? declare.variables?.intent : undefined;

            return (
              <View key={sport} style={index > 0 ? s.divided : undefined}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={playIntentRowLabel(sportName, declared)}
                  accessibilityHint={PLAY_INTENTS_ROW_HINT}
                  accessibilityState={{ expanded: isOpen }}
                  hitSlop={theme.hit.btn}
                  onPress={() => setOpen(isOpen ? undefined : sport)}
                  style={({ pressed }) => [s.row, pressed ? s.rowPressed : undefined]}
                >
                  <Text style={s.rowLabel}>{sportName}</Text>
                  <Text style={s.rowValue}>{declaredValue(declared)}</Text>
                </Pressable>

                {isOpen ? (
                  <View style={s.answers}>
                    {PLAY_INTENTS.map((intent) => {
                      const cost = intentChangeCost(declared, intent, deckCounts);
                      return (
                        <View key={intent} testID={`answer-${intent}`} style={s.answer}>
                          {/* One button is one element to a listener, and the gloss is the
                              sighted half of the name it already carries. */}
                          <Button
                            label={intentLabel(intent)}
                            gloss={intentGloss(intent)}
                            accessibilityLabel={declarationOptionLabel(intent, sportName)}
                            variant="secondary"
                            selected={declared === intent}
                            busy={inFlight === intent}
                            disabled={declare.isPending && inFlight !== intent}
                            onPress={() =>
                              declare.mutate(
                                { sport, intent, surface: DECLARED_ON },
                                { onSuccess: () => setOpen(undefined) },
                              )
                            }
                          />
                          {/* What the answer costs, under its gloss, which stays (the You
                              screen 3.3). The answer held, and any answer to an undeclared
                              sport, says nothing. */}
                          {cost === undefined ? null : (
                            <Text style={s.cost}>{intentCostLine(cost)}</Text>
                          )}
                        </View>
                      );
                    })}
                  </View>
                ) : null}
              </View>
            );
          })}
        </Card>
      )}

      {/* Only where somebody is in that state — see `NOT_DECLARED_LINE` — and never before the
          read that would say so has landed. */}
      {rows !== undefined && anySportUndeclared(rows) ? (
        <Text style={s.footnote}>{NOT_DECLARED_LINE}</Text>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.xs },
  // 5.5's rule: the divider is drawn from the second row onward, so the first has no rule
  // above it and the last none below it without anybody counting.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
  },
  rowPressed: { opacity: 0.7 },
  rowLabel: { ...theme.type.rlLabel, color: theme.color.muted, flexShrink: 1 },
  rowValue: { ...theme.type.rlValue, color: theme.color.ink },
  answers: { gap: theme.space.xs, paddingBottom: theme.space.sm },
  answer: { gap: theme.space.xxs },
  cost: { ...theme.type.tiny, color: theme.color.muted },
  footnote: { ...theme.type.tiny, color: theme.color.muted },
});
