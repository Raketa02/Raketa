/**
 * **The filter's switch and its line** — *Play only with players of · Off | At least Medium | At
 * least High*, and under it *Your filter hides 2 of the 11 players in your groups.*
 * ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §6, [#662](https://github.com/Rakieta02/Rakieta/issues/662)).
 *
 * ```
 * ┌ PLAY ONLY WITH PLAYERS OF                           ┐   flab — it labels the control
 * │ [ Off | At least Medium | At least High ]           │   6.3, the segment that is saved raised
 * │ Your filter hides 2 of the 11 players in your groups.   while it is on
 * └─────────────────────────────────────────────────────┘
 * ```
 *
 * ## A segment, because it picks one of three
 *
 * The spec calls it a switch, and 6.12's switch has two values. *Off*, *at least Medium* and *at
 * least High* are three positions of one setting, which is 6.3's *picks one of several* exactly —
 * and the segment's `selected` is what carries which one is saved, never the colour alone.
 *
 * ## It draws what is saved, and the tap in between
 *
 * The raised segment is the record's `minimum` — read on every open, never a position this phone
 * remembered — except while a save is out, when it is the position tapped; which of the two, and
 * that a tap on the raised segment writes nothing, is `useSetReliabilityFilter`'s. The *hides*
 * line is always the saved count: it changes on the re-read, with the segment it belongs to.
 *
 * ## Nobody is named here
 *
 * Two counts and a band. The filtering player learns how many it hides and never whom, which is
 * ADR-0195 §6's rule and the reason the line is a sentence rather than a door to a list.
 */

import { StyleSheet, Text } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Card, Note, Segment, theme } from '@/shared/ui';

import type { ReliabilityFilter } from '../domain/playerRecord';
import { useSetReliabilityFilter } from '../hooks/useReliabilityFilter';

import { FILTER_LABEL, FILTER_SEGMENTS, hidesLine } from './youRecordPresentation';

export interface ReliabilityFilterCardProps {
  readonly filter: ReliabilityFilter;
}

export function ReliabilityFilterCard({ filter }: ReliabilityFilterCardProps) {
  const { shown, set, error, heldOffline } = useSetReliabilityFilter(filter);

  return (
    <Card style={s.card}>
      <Text style={s.label}>{FILTER_LABEL}</Text>
      <Segment options={FILTER_SEGMENTS} selected={shown} onSelect={set} />
      {filter.minimum === undefined ? null : <Text style={s.line}>{hidesLine(filter)}</Text>}
      {heldOffline ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}
      {error === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(error)}
        </Note>
      )}
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  // `flab`: it labels the control under it, which `eyebrow` would mistake for a section.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
});
