/**
 * **The skill card** — a Level, how sure the platform is, what that rests on, the full scale
 * with their band on it, the likely range, and the run of five.
 *
 * ## The three headline figures are one text run
 *
 * `PADEL · 2,75 · 77 % sure · 21 counted`. They are inseparable by design — a confident-looking
 * number built on three games must not read like one built on forty — and three boxes is how
 * one of them ends up conditionally hidden. The one that would go is the one that makes the
 * other two honest.
 *
 * ## The band is a key and the scale is the bar's
 *
 * [7.5](../../../../docs/design-system.md#75-the-level-bar) draws the whole 1,00–5,00 scale as
 * four bands with theirs at full strength, and the likely range as a **bracket on its own row**
 * beneath — the separation is the whole design, because a range drawn over the bands hid
 * exactly what the bands were there to show. Which band is theirs arrives **as a name and is
 * resolved to a key**, never derived from the Level: deriving it would be a second opinion
 * about banding, and the two would eventually disagree. A band this build cannot name lights no
 * segment and the mark still says where they are.
 *
 * The `legend` is omitted, which is the form 7.5 has always specified and no shipped screen has
 * drawn: the coral mark and the bracket are both explained by the line printed above them.
 *
 * ## It is one accessibility element, and the bar is inside it
 *
 * The bar takes an `accessibilityLabel` because it is normally its own element; here it is not,
 * so the card carries the whole reading and the bar is drawn and hidden. The bracket reaches a
 * listener as `Likely 2,47–3,03` in that reading rather than as a drawn object announcing
 * itself, and the run of five reaches it as one clause counting the squares.
 */

import { StyleSheet, Text, View } from 'react-native';

import { BAND_NAMES, bandPresentation, sportLabel } from '@/features/onboarding/types';
import { Card, LevelBar, RunOfForm, theme } from '@/shared/ui';

import type { SkillPanel } from '../domain/playerRecord';

import { likelyRangeLine, skillCardLabel, skillHeadline } from './recordPresentation';

export interface SkillCardProps {
  readonly skill: SkillPanel;
}

export function SkillCard({ skill }: SkillCardProps) {
  const sportName = sportLabel(skill.sport);
  const band = bandPresentation(skill.band)?.key;

  return (
    <Card>
      <View
        accessible
        accessibilityLabel={skillCardLabel({ ...skill, sportName, likelyRange: skill.likelyRange })}
      >
        <Text style={s.headline}>{skillHeadline({ ...skill, sportName })}</Text>

        {/* Drawn and hidden: every figure on it is in the card's own reading two lines up, and
            a bar that named itself would be the fourth reading of one fact. */}
        <View
          style={s.bar}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          <LevelBar
            level={skill.level}
            range={skill.likelyRange}
            band={band}
            bandNames={BAND_NAMES}
            accessibilityLabel={likelyRangeLine(skill.likelyRange)}
          />
        </View>

        {/* Never padded: three squares means three counted results, and the gap at the end —
            where the newest results are not yet — is the honest statement. An empty run draws
            nothing rather than an empty row of the run's own height. */}
        {skill.lastFive === undefined || skill.lastFive.length === 0 ? null : (
          <View style={s.run}>
            <RunOfForm results={skill.lastFive} />
          </View>
        )}
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  headline: { ...theme.type.rlValue, ...theme.tabular, color: theme.color.ink },
  // The bar's own three rows are tall; it needs air above it and the run needs air below.
  bar: { marginTop: theme.space.md },
  run: { marginTop: theme.space.md },
});
