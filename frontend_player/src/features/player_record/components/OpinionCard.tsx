/**
 * **What opponents said** — the one thing on this sheet people wrote, under a heading that says
 * so ([#387](https://github.com/Raketa02/Raketa/issues/387)).
 *
 * ## It is a second block because the first one made a promise
 *
 * The card above is headed *counted by the system, not written by people*, and that heading is
 * the most valuable sentence on it: every metered row under it rests on it. A star average
 * sitting beneath that title would make the title false — so this stands **outside** that card,
 * under a heading naming its own author. Two headings, no lie, and the heading is the cheap
 * half of the pair.
 *
 * ## Two arms, and the subject never sees the figure
 *
 * A reader gets `4,7 / 5 · 17 players`; the person it is about gets a band and no count. That
 * is not a softening — an average beside a count is a **subtraction**, naming each new rating
 * exactly, and the subject knows who they played, so every answer would be identifiable by the
 * one person who must never see it. Which arm a record carries is decided at the wire boundary
 * from the server's `is_self`, so this component draws what it was handed and compares nothing.
 *
 * ## The band carries no tone, and that is deliberate
 *
 * `scoreTone` is this sheet's one ladder and it belongs to the Player Score — the number the
 * matcher actually reads. A coarse three-step band painted in the same three colours would
 * offer itself to be read as a second score, on the screen a held player opens to find out what
 * is holding them back. The word is the whole answer.
 *
 * ## One element, and no bar under either arm
 *
 * §20.1: there is no action on this sheet, so the block is one element and `opinionCardLabel` is
 * what it says. Nothing here is metered — a bar would be a drawing of a figure the contract
 * attaches no banding to, and the band arm has no number to draw at all.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, theme } from '@/shared/ui';

import type { Opinion } from '../domain/playerRecord';

import {
  BAND_HAS_NO_COUNT,
  OPINION_BAND_NAME,
  OPINION_CARD_TITLE_DRAWN,
  WRITTEN_BY_PLAYERS,
  opinionCardLabel,
  opinionFigure,
} from './recordPresentation';

export interface OpinionCardProps {
  /** Absent where nobody has rated them, which is most people. */
  readonly opinion?: Opinion;
}

export function OpinionCard({ opinion }: OpinionCardProps) {
  // Rating is a favour, ignoring the card costs nothing, and nothing records that somebody did
  // not answer — so an absence here is drawn the way every absence on this sheet is.
  if (opinion === undefined) return null;

  return (
    <Card>
      <View accessible accessibilityLabel={opinionCardLabel(opinion)}>
        <Text style={s.title}>{OPINION_CARD_TITLE_DRAWN}</Text>

        {opinion.kind === 'figure' ? (
          <Text style={s.figure}>{opinionFigure(opinion)}</Text>
        ) : (
          <>
            <Text style={s.band}>{OPINION_BAND_NAME[opinion.band]}</Text>
            <Text style={s.note}>{BAND_HAS_NO_COUNT}</Text>
          </>
        )}

        <Text style={s.note}>{WRITTEN_BY_PLAYERS}</Text>
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  // The eyebrow labels a region you are reading, which is what this heading is — the same role
  // the counted card's own heading takes one block up.
  title: { ...theme.type.eyebrow, color: theme.color.muted, marginBottom: theme.space.xs },
  figure: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
  // A word rather than a figure, so it takes a sentence's family: mono is for numbers, and a
  // band drawn in a figure's register is a band inviting arithmetic.
  band: { ...theme.type.h2, color: theme.color.ink },
  note: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
});
