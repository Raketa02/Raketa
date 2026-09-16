/**
 * The footer — the headline, its right-hand count and the hint, on the field's bottom edge
 * above the tab bar ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md)
 * §7.7, mock 16).
 *
 * Four states, one shape:
 *
 * - **A reading with rows** — *14 players in view* with *all of them* or *+8 off screen* beside
 *   it, then the hint: the privacy line, and the movement sentence while faces or levels are
 *   drawn or the card sentence once cards are. The hint switches on the **zoom state** and
 *   never on the selection.
 * - **An empty reading** — *Nobody within 10 km plays padel yet*, the reach off the pool and
 *   the sport in lower case, and the deck's own widen sentence under the privacy line.
 * - **Loading** — *Looking around…* over the privacy line.
 * - **Failure** — *The radar couldn't load*, and *Try again* in the hint's place.
 *
 * The headline and the hint are plain text and read as such; *Try again* is 6.1's on-dark
 * button, `sm`. Nothing here is a live region: the count changes on every move, and a region
 * that spoke every move would talk over the field. The headline is white and the hint the
 * on-dark tiny grey — 13,37 and 7,05 on the ground's centre (`radarGround.test.ts`).
 *
 * The footer is laid **over** the field rather than under it, so the rings run on beneath it
 * as mock 1 draws them; the field is told its height so the in-view count stops at its top
 * edge, which is what *between the header and the footer* means.
 */

import { StyleSheet, Text, View, type LayoutChangeEvent } from 'react-native';

import { Button, theme } from '@/shared/ui';

import type { ZoomState } from '../../domain/radarGeometry';
import {
  LOOKING_AROUND,
  PRIVACY_LINE,
  RADAR_FAILED,
  TRY_AGAIN,
  emptyHint,
  nobodyInReach,
  offScreen,
  playersInView,
  radarHint,
} from '../radarPresentation';

export type RadarFooterState =
  | {
      readonly kind: 'reading';
      readonly inView: number;
      readonly offScreen: number;
      readonly zoom: ZoomState;
    }
  | { readonly kind: 'empty'; readonly reachKm: number; readonly sportName: string }
  | { readonly kind: 'loading' }
  | { readonly kind: 'failed'; readonly onTryAgain: () => void };

export interface RadarFooterProps {
  readonly state: RadarFooterState;
  /** The field reads the footer's height off this, for the in-view count. */
  readonly onLayout?: (event: LayoutChangeEvent) => void;
}

export function RadarFooter({ state, onLayout }: RadarFooterProps) {
  return (
    <View style={s.footer} onLayout={onLayout} pointerEvents="box-none" testID="radar-footer">
      <View style={s.headlineRow}>
        <Text style={s.headline}>{headline(state)}</Text>
        {state.kind === 'reading' ? (
          <Text style={s.count}>{offScreen(state.offScreen)}</Text>
        ) : null}
      </View>
      {state.kind === 'failed' ? (
        <View style={s.retry}>
          <Button label={TRY_AGAIN} variant="onDark" size="sm" onPress={state.onTryAgain} />
        </View>
      ) : (
        <Text style={s.hint}>{hint(state)}</Text>
      )}
    </View>
  );
}

function headline(state: RadarFooterState): string {
  switch (state.kind) {
    case 'reading':
      return playersInView(state.inView);
    case 'empty':
      return nobodyInReach({ reachKm: state.reachKm, sportName: state.sportName });
    case 'loading':
      return LOOKING_AROUND;
    case 'failed':
      return RADAR_FAILED;
  }
}

function hint(state: Exclude<RadarFooterState, { kind: 'failed' }>): string {
  switch (state.kind) {
    case 'reading':
      return radarHint(state.zoom);
    case 'empty':
      return emptyHint();
    case 'loading':
      return PRIVACY_LINE;
  }
}

const s = StyleSheet.create({
  footer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.md,
    gap: theme.space.xxs,
  },
  headlineRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  headline: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  count: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  hint: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  retry: { alignSelf: 'flex-start', paddingTop: theme.space.xxs },
});
