/**
 * **One pill per sport somebody holds a rating in.**
 *
 * It is [6.4](../../../../docs/design-system.md#64-tag)'s tag with its own dot and nothing new
 * drawn: 15.1's first question — *is it one of the existing primitives?* — is answered yes here,
 * where the star row answered it no. What the composition adds is the label, and the label is
 * `recordPresentation`'s.
 *
 * It answers *what else do they play*, which is useful to a reader inside a padel four and is
 * the whole of what a pill is for: how sure the platform is and what that rests on belong to
 * the one sport the sheet is about, and repeating them four times would be four skill cards
 * drawn as jewellery.
 *
 * ## The order is the server's, and nothing here sorts
 *
 * The sports arrive in the sport registry's own order, which is the order every list of sports
 * on this surface takes. A client that sorted them — by level, say — would make the header a
 * boast about whichever sport somebody happens to be best at.
 *
 * ## Colour, and the condition attached to drawing it
 *
 * `theme.color.sport` reuses the semantic palette rather than extending it, and it does so on
 * one stated condition: *the dot is always accompanied by the sport name in text*. Every pill
 * here carries the name, which is why the dot is allowed at all — and it is why the label is
 * the sport's **name** rather than an abbreviation. Four sports fit; a fifth sport is a real
 * decision, not a shorter word.
 *
 * ## It announces nothing of its own
 *
 * The row is inside the header, which is one accessibility element and states these same pills
 * in its own label (§20.1). A tag that named itself would be the same fact read twice, and this
 * is a row of four of them.
 */

import { Pressable, StyleSheet, View } from 'react-native';

import { sportColour, sportLabel } from '@/features/onboarding/types';
import { FitPill, Tag, theme } from '@/shared/ui';

import type { RatedSport } from '../domain/playerRecord';

import { FIT_ROW_NAME, fitRowLabel, sportPill } from './recordPresentation';

export interface SportPillsProps {
  /** In the registry's own order, as served. Never re-sorted here. */
  readonly sports: readonly RatedSport[];
  /**
   * What *Player fit* opens, where there is a pairing behind the entry point.
   *
   * Absent on your own record and on any sheet opened without a search behind it, and the
   * button is not drawn — a control that provably opens nothing is the pool's own *a control
   * that returns nothing is a control lying about being useful*.
   */
  readonly onExplainFit?: () => void;
  /** The Fit the engine published for the two of them, printed beside the name. */
  readonly fit?: number;
}

export function SportPills({ sports, onExplainFit, fit }: SportPillsProps) {
  const opens = onExplainFit !== undefined && fit !== undefined;

  if (sports.length === 0 && !opens) return null;

  return (
    <>
      {sports.length === 0 ? null : (
        <View style={s.row}>
          {sports.map(({ sport, level }) => (
            <Tag key={sport} label={sportPill(sportLabel(sport), level)} dot={sportColour(sport)} />
          ))}
        </View>
      )}

      {/* **The sheet's one action, and it is 7.10's pill with a word in front of it.**

          It was 6.1's `primary` — coral, the app's one accent, worn by the thing to do on a
          screen. That is not this: the thing to do on a record is read it, and a filled coral
          control in the header competed with the photograph beside it and promised a *submit*.

          What it is instead is the object a reader has **already met**: the same pill their
          shortlist printed this pairing's Fit in, an hour and four taps ago. Reusing it is what
          makes the control need no explaining — the number under a face is the number that was
          on the card. `FitPill` keeps its own two fills, so a pairing at 90 or better draws
          coral here exactly as it does there, and that is the pill's step rather than this
          control's opinion.

          The press is this file's: `hit.btn` for reach and opacity for the pressed state, which
          is 5.1's answer for a control whose fill already means something else. */}
      {!opens || onExplainFit === undefined || fit === undefined ? null : (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={fitRowLabel(fit)}
          hitSlop={theme.hit.btn}
          onPress={onExplainFit}
          style={({ pressed }) => [s.fit, pressed ? s.pressed : undefined]}
        >
          <FitPill fit={Math.round(fit)} label={FIT_ROW_NAME} />
        </Pressable>
      )}
    </>
  );
}

const s = StyleSheet.create({
  // It wraps: four sports beside a 112pt panel is two lines on the narrowest phone, and a row
  // that scrolled sideways would hide the fourth pill behind a gesture nothing advertises.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xxs },
  // The pill sizes itself; this only places it and takes the press.
  fit: { alignSelf: 'flex-start', marginTop: theme.space.xs },
  pressed: { opacity: 0.6 },
});
