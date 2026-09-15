/**
 * **The declaration, at rest, on the screen the player is already on** — and the disagreement
 * as a state rather than a sheet ([#294](https://github.com/Raketa02/Raketa/issues/294)).
 *
 * Answered once, the durable value had no representation anywhere afterwards: nothing on any
 * screen said *your usual at padel is competitive*, and the only way to change it was to trip
 * the five-search drift prompt. That is what taught players the question had been a hurdle
 * rather than a setting they own — the half of the reported confusion the render order could
 * not reach, since a control that is not drawn explains nothing about itself.
 *
 * ## It belongs to the control above it, and it is not a card
 *
 * A recessed `paper2` line under the control it is about — the mode segment on Find a game, the
 * sport chips on the deck, which has no segment for it to stand under — `tiny` in `muted` with the
 * declaration in `ink` — 4.49:1 for the sentence at 11pt and 13.9:1 for the value, which is
 * the contrast table's own reading of that pair. A [5.1](../../../../docs/design-system.md#51-card)
 * card would make it a second object on a page whose subject is one question; `paper2` is the
 * recessed surface, and this is a fact set into the section rather than one standing beside it.
 *
 * ## Moving the segment writes nothing, and that is the whole of the value
 *
 * The two must be able to disagree — `domain/playMode` is where that is argued, and ADR-0094's
 * drift backstop is what it is argued for — so nothing here fires on a switch. What the flip
 * does is change this line **in place**, and the player watches the durable fact hold still
 * while the control moves. That is the clearest demonstration available that they are two
 * different things, and it costs no dismissal.
 *
 * **It does not replace the drift sheet.** `UPDATE_PLAY_INTENT` still rides on a search's own
 * response, still suppresses for thirty days on a decline, and is still asked after five
 * searches in one mode. What changes is that the sheet stops being the first time the
 * distinction is ever explained.
 *
 * ## The two controls, and why only one of them writes
 *
 * *Update* is `useDeclarePlayIntent` with the line's own `updatesTo` on `SEARCH_SWITCH` — a second
 * entry to the write the interstitial already makes from this screen, not a new one, which is
 * why the surface is the same value the interstitial reports here. The write lands in the
 * profile cache, the two values agree again, and the line returns to its resting state without
 * anything being told to.
 *
 * ***Change* is not a write and never opens a second copy of the question.** The declaration's
 * home is the You tab ([#296](https://github.com/Raketa02/Raketa/issues/296)), where it sits
 * beside the other durable facts strangers read, and drawing the three answers here would put
 * the two intent controls back on one screen — which is exactly what
 * [#293](https://github.com/Raketa02/Raketa/issues/293) took apart. So it opens that tab
 * through the shell's own move. **Leaving Play ends the Play session**, and the working week
 * goes with it: that is `resetShellStack`'s definition rather than a cost this control adds,
 * and it is the same thing pressing *You* in the tab bar has always done.
 *
 * ## On the deck it is one state, because there is nothing there to disagree with
 *
 * `POST /deck` carries no mode — `SearchEnvelope.mode` is null exactly there — so a deal runs
 * on the declaration itself and the line says so: *dealing competitive games at padel — your
 * usual* ([#295](https://github.com/Raketa02/Raketa/issues/295)). That is the plainest statement
 * available anywhere in the product of what the two values are, and it is available **because**
 * one of them is missing.
 *
 * It follows that the deck's line never writes. *Update* is the answer to a disagreement and a
 * surface with one value has none, so the only control there is *Change*, which goes where it
 * goes from the search screen. #295 §3 asked for that press to open the declaration write with
 * `DECK` on it; what changed underneath it is that #294 gave *Change* a **destination** rather
 * than a write, and one word meaning two different things on the two screens of one tab is the
 * confusion this whole run is taking apart. `DECK` therefore stays the interstitial's surface,
 * which is the caller that actually declares on that screen and the one `deck.test.tsx` asserts.
 *
 * **The deck's line is gone with the deck's declaration**
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §2): a deal runs under one ruler for everybody and reads no declaration, so there is nothing
 * on the Players tab for this line to state, and `mode` is never `undefined` from a caller that
 * exists today. The section above is kept as the record of the one state the line had there.
 *
 * The failure stays where every other one on this screen is drawn — a coral note above the
 * thing that failed, because the line itself is `muted` on a recessed ground and has no room
 * to carry a refusal in wording alone.
 */

import { usePathname } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { sportColour } from '@/features/onboarding/types';
import { useDeclarePlayIntent } from '@/features/player_profile/types';
import { openTab } from '@/features/shell/types';
import type { Sport } from '@/shared/vocabulary/sport';
import { Button, Note, theme } from '@/shared/ui';

import type { PlayIntent, SearchMode } from '../domain/vocabulary';

import type { PlayDeclarationSurface } from './DeclarationInterstitial';
import { declarationLine } from './findAGamePresentation';
import { playErrorMessage } from './playErrorMessage';

export interface DeclarationStandingProps {
  readonly sport: Sport;
  /** This app's word for that sport — the caller already drew it on a chip. */
  readonly sportName: string;
  /**
   * What the profile holds. It is a `PlayIntent` and never `undefined`: an undeclared sport is
   * the interstitial's state and draws none of this section (`FindAGameStanding`).
   */
  readonly intent: PlayIntent;
  /**
   * What the segment above is sitting on — or **`undefined` where the surface has no mode.**
   *
   * The deck is that surface, and the absence is the wire's rather than this component's:
   * `SearchEnvelope.mode` is null exactly on a deal. The key is required and the value is
   * nullable so a caller states which of the two it is instead of omitting it by accident.
   */
  readonly mode: SearchMode | undefined;
  /**
   * Which of the two Play screens this is — **the caller's to say**, exactly as it is on the
   * interstitial, and for [#280](https://github.com/Raketa02/Raketa/issues/280)'s reason.
   *
   * The deck's line has no state that writes, so this rides unused from there today. It is a
   * required prop anyway rather than a constant spelling `SEARCH_SWITCH` inside a component
   * with two callers: a field whose whole job is to say which screen it was, hard-coded to one
   * screen, is the collapse the enum was widened to prevent — and it would be the wrong value
   * on one of the two the day the deck grows a write.
   */
  readonly declaredOn: PlayDeclarationSurface;
}

export function DeclarationStanding({
  sport,
  sportName,
  intent,
  mode,
  declaredOn,
}: DeclarationStandingProps) {
  const declare = useDeclarePlayIntent();
  const here = usePathname();
  const standing = declarationLine({ intent, mode, sportName });

  return (
    <View style={s.block}>
      {declare.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {playErrorMessage(declare.error)}
        </Note>
      ) : null}

      <View style={s.line}>
        {/* **The sport's own dot**, the one the chip above already draws — so the line is
            visibly about the sport the player is standing on, and the token is spent on what
            it is named for. It adds no colour to the system (15.2): it is an existing mark
            with its existing meaning, and it is decoration to a listener, which the row's own
            name is what covers. */}
        <View style={[s.dot, { backgroundColor: sportColour(sport) }]} />

        {/* **The row is two elements: the statement, and its control** — which is §20.3's own
            worked example (*"the card is two elements: the body, and its primary button"*)
            rather than an exception to §20.1. What §20.1 merges is a part with no action into
            the object it belongs to; a control is not one of those.

            The statement is **one** element and not three, because the sentence means nothing
            in fragments read a beat apart, and the control is a sibling rather than a child so
            that it stays reachable. */}
        <View style={s.sentenceBox} accessible accessibilityLabel={standing.spoken}>
          <Text style={s.sentence}>
            {standing.lead}
            <Text style={s.value}>{standing.value}</Text>
            {standing.tail}
          </Text>
        </View>

        <Button
          label={standing.action}
          accessibilityLabel={standing.actionLabel}
          variant="secondary"
          size="sm"
          busy={declare.isPending}
          onPress={() => {
            // Which control this is was decided with the words on it: `updatesTo` is the
            // declaration *Update* commits to, and it is absent on both of the states whose
            // control is *Change*. Read rather than re-derived, so the row holds no copy of the
            // rule and needs no guard for a mode that cannot be missing where it writes.
            if (standing.updatesTo !== undefined) {
              declare.mutate({ sport, intent: standing.updatesTo, surface: declaredOn });
              return;
            }
            // Where the player is, because the shell declines a press that would land on
            // the screen already on — and this row is only ever drawn inside Play, so the
            // answer is always *somewhere else* and the press is always a move.
            openTab('you', here);
          }}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
  line: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    backgroundColor: theme.color.paper2,
    borderRadius: theme.radius.note,
    paddingVertical: theme.space.xs,
    paddingHorizontal: theme.space.sm,
  },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  // `flexShrink` and not a width: the drift sentence is the longer of the two and wraps rather
  // than pushing the control off the row.
  sentenceBox: { flexShrink: 1, flexGrow: 1 },
  sentence: { ...theme.type.tiny, color: theme.color.muted },
  value: { color: theme.color.ink },
});
