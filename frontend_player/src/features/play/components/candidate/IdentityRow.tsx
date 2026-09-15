/**
 * The competitive card's **identity row** — the whole handle, with a tag beside it.
 *
 * ## Why this is not `CardHead`
 *
 * The two were the same object on all three cards and stopped being one here
 * ([#309](https://github.com/Raketa02/Raketa/issues/309)). `CardHead` lays out a name with the
 * **fit pill** on the same line and the interest tag beneath; this card puts the **tag** on
 * that line and the pill on a row of its own. Configuring one component to do both would take
 * two flags to say which, which is
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3's `surface === …` arriving in a smaller spelling — and the three cards are three
 * components for exactly this reason. `CardHead` has since taken the same tags under its name
 * line ([ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8 — both tags on both card styles), and its own note records why the two heads are still
 * two.
 *
 * ## The tag reverses #231's open decision #14, on the evidence that decision was missing
 *
 * #14 turned the volt tag into a **sentence** under the name — *"a full sentence does not go
 * where a two-word tag went"*, which was the right reading of the sentence it had been handed
 * and the wrong conclusion. The two-word form was never gone: `INTEREST_RECEIVED` and
 * `INTEREST_LIFT` fire for the same person and are *two facts with one tag*
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §10), so the tag is
 * bound to the admitting code and takes the twin's words. `candidateTag` owns that, the second
 * interest tag — *You said yes*, the reader's own act off their own list — and the precedence
 * of both over the coral one.
 *
 * **The row announces nothing.** §20.1 merges it into the card body, whose spoken name opens
 * with the same handle. The tag's own words are the one thing on this row that does *not*
 * reach that name — see `candidateCardLabel`, which books it rather than adding a clause the
 * reason list may already be carrying.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Tag, theme } from '@/shared/ui';

import type { CandidateTag } from '../playerCardPresentation';

export interface IdentityRowProps {
  /** §15's `playerName()` — the handle, whole. */
  readonly name: string;
  /** At most one, and often none. `candidateTag`'s answer, never a component's. */
  readonly tag?: CandidateTag;
}

export function IdentityRow({ name, tag }: IdentityRowProps) {
  return (
    <View style={s.row}>
      {/* The handle shrinks and the tag does not: a sixty-four character handle beside a
          two-word status must cost the handle its tail rather than cost the status its word,
          which is 6.4's *a status never reflows the row it sits in* read from the other side. */}
      <Text style={s.name} numberOfLines={1}>
        {name}
      </Text>

      {tag === undefined ? null : <Tag label={tag.label} variant={tag.variant} />}
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.xs,
  },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
});
