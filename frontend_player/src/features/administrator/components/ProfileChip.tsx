/**
 * **The profile switcher** — the chip in each profile's You header, and the sheet it opens
 * ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 134–135, club mocks 6–7;
 * ADR-0185 §3, which amends ADR-0179 §1's locked header by exactly this element).
 *
 * **The chip is club 7's**: a pill on `surface` inside a `line` border, holding the face of the
 * profile worn now — the player's own photograph, or the club's tile — beside a drawn ⇅. **Slim**
 * (the product owner's mock, 2026-10-01): a 22 face about three quarters of the pill's 30, inset
 * `xxs` inside the border, the ⇅ about two fifths of the face, `xs` after the face and `sm` after
 * the arrows — so it reads as a control beside the header rather than as a second avatar. It sits in
 * the header's right slot on the player's You tab and on the administrator's alike, and **it is not
 * drawn at all for an account with one profile** (`switcherShown`): a chip opening a list of one is
 * a control that does nothing.
 *
 * **The sheet is club 6's**: one row per profile, Player first and then one per club, the worn one
 * ticked. A row switches at once (`useChooseProfile`) — the phone keeps the choice and the app goes to
 * that profile's home — and the worn row, or the close, keeps what is worn. The sheet is a sibling of
 * the chip, and the chip is hidden from a screen reader while it is up (ExitDoor's arrangement).
 */

import { useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useCurrentUser, type ProfileChoice } from '@/features/auth/types';
import { behindOverlay, BottomSheet, theme } from '@/shared/ui';

import { isWorn, profileOptions, switcherShown, type ProfileOption } from '../domain/profiles';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { switcherChipLabel } from './administratorPresentation';
import { useChooseProfile } from './areaNavigation';
import { ProfileFace } from './ProfileFace';
import { ProfileRows } from './ProfileRows';
import { SwapMark } from './SwapMark';

const COPY = ADMINISTRATOR_COPY.switcher;

export interface ProfileChipProps {
  /** The profile the screen carrying the chip belongs to — the one the sheet ticks. */
  readonly worn: ProfileChoice;
}

export function ProfileChip({ worn }: ProfileChipProps) {
  const user = useCurrentUser();
  const chooseProfile = useChooseProfile(worn);
  const [open, setOpen] = useState(false);
  const chip = useRef<View>(null);

  const options = user.data === undefined ? [] : profileOptions(user.data);
  const wornOption = options.find((option) => isWorn(option, worn));
  if (!switcherShown(options) || wornOption === undefined) return null;

  const choose = (option: ProfileOption) => {
    setOpen(false);
    chooseProfile(option);
  };

  return (
    <>
      <View ref={chip} {...behindOverlay(open)}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={switcherChipLabel(wornName(wornOption))}
          // A 30 pill: `hit.chip`'s 9 above and below lifts it past 44.
          hitSlop={theme.hit.chip}
          onPress={() => setOpen(true)}
          style={({ pressed }) => [s.chip, pressed ? s.pressed : undefined]}
        >
          <ProfileFace option={wornOption} size="chip" />
          <SwapMark />
        </Pressable>
      </View>

      <BottomSheet
        visible={open}
        onClose={() => setOpen(false)}
        title={COPY.title}
        closeLabel={COPY.close}
        returnFocusTo={chip}
      >
        <ProfileRows options={options} worn={worn} onChoose={choose} />
      </BottomSheet>
    </>
  );
}

/** What the chip says it shows now: *Player*, or the club whose profile is worn. */
function wornName(option: ProfileOption): string {
  return option.kind === 'player' ? COPY.player : option.clubName;
}

const s = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xs,
    paddingVertical: theme.space.xxs,
    paddingLeft: theme.space.xxs,
    paddingRight: theme.space.sm,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
  },
  // 6.6: a pill's press is the chip's.
  pressed: { opacity: 0.7 },
});
