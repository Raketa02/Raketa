/**
 * The card the answer is given against — **the promises, without the step around them.**
 *
 * The opt-in step and the You tab's *Game suggestions* draw the same card: *If you say yes*
 * over three promises, each a term above the sentence completing it, folded by hairlines. What
 * differs is which three — the step's say *from your profile*, the profile's say *from here*
 * (`optInPresentation`) — and everything around the card, so the card is here once and each
 * screen composes it under its own chrome
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, first consequence).
 *
 * Nothing here is a decision: the words are `optInPresentation`'s, and which list is drawn is
 * the caller's — the file that draws the sentences is the one that can honestly name the
 * version it stamps.
 */

import { Fragment } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Card, Hairline, theme } from '@/shared/ui';

import { OPT_IN_PROMISE_HEADING, type OptInPromise } from './optInPresentation';

export interface OptInPromisesProps {
  readonly promises: readonly OptInPromise[];
}

export function OptInPromises({ promises }: OptInPromisesProps) {
  return (
    <Card>
      <Text style={s.heading}>{OPT_IN_PROMISE_HEADING}</Text>

      {/* **Stacked, not `Row`.** 5.5 is the key-value *line* — label left, value right,
          `space-between` — and it is right for the figures and evidence rows it names.
          Here the value is a whole sentence, and a sentence pushed into the right half of
          a phone-width row is four words a line. So the term sits above what it promises,
          and only 5.5's divider rule is borrowed. */}
      <View style={s.promises}>
        {promises.map((promise, index) => {
          // One accessibility element, not two: *You may receive* and the sentence
          // completing it mean nothing read a screen apart — which is the obligation 5.5
          // states for its own rows, and it does not depend on the layout.
          const promised = (
            <View accessible accessibilityLabel={`${promise.term} ${promise.detail}`}>
              <Text style={s.term}>{promise.term}</Text>
              <Text style={s.detail}>{promise.detail}</Text>
            </View>
          );

          // The divider is drawn from the second promise onward, so the first has no rule
          // above it and the last none below it — 5.5's `index > 0`, expressed with the
          // primitive that owns the fold. **No gap on this container**: `Hairline` already
          // sets the space on both sides of the line, and a gap stacked on top of it would
          // put the rule closer to the promise below than the one above.
          return index === 0 ? (
            <Fragment key={promise.term}>{promised}</Fragment>
          ) : (
            <Hairline key={promise.term}>{promised}</Hairline>
          );
        })}
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  // The card carries no gap of its own: `Hairline` owns the space around each fold, and
  // this is the one step between the heading and the first promise, which has no fold.
  promises: { marginTop: theme.space.xs },
  heading: { ...theme.type.cardTitle, color: theme.color.ink },
  term: { ...theme.type.inlineTitle, color: theme.color.ink },
  // `ink`, not `muted`: this is the substance of what is being agreed to, and the muted
  // role is for text that is genuinely secondary to something else on the screen.
  detail: { ...theme.type.tiny, color: theme.color.ink },
});
