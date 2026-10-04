/**
 * **The account's profiles, one row each, the one worn ticked** (club 6) — the switcher sheet's
 * content, and what the invitation sheet turns into once an invitation is accepted.
 *
 * A row is the profile's face, who it is — the account's name for Player, the club's for an
 * administrator profile — over which hat it is, and a tick on the one the app wears now. The whole
 * row is the control, 6.6's `.7` press, and it says whether it is the one worn (`selected`) so the
 * tick is never the only thing that does.
 *
 * Content for a sheet, so it holds no navigation and no provider (Part 13): a press is the caller's.
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { ProfileChoice } from '@/features/auth/types';
import { theme } from '@/shared/ui';

import { isWorn, type ProfileOption } from '../domain/profiles';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { profileRowLabel } from './administratorPresentation';
import { ProfileFace } from './ProfileFace';

const COPY = ADMINISTRATOR_COPY.switcher;

export interface ProfileRowsProps {
  readonly options: readonly ProfileOption[];
  readonly worn: ProfileChoice;
  readonly onChoose: (option: ProfileOption) => void;
}

export function ProfileRows({ options, worn, onChoose }: ProfileRowsProps) {
  return (
    <View style={s.rows}>
      {options.map((option) => {
        const { title, role } = rowWords(option);
        const selected = isWorn(option, worn);
        return (
          <Pressable
            key={option.kind === 'player' ? 'player' : option.clubId}
            accessibilityRole="button"
            accessibilityLabel={profileRowLabel(title, role)}
            accessibilityState={{ selected }}
            onPress={() => onChoose(option)}
            style={({ pressed }) => [s.row, pressed ? s.pressed : undefined]}
          >
            <ProfileFace option={option} size="card" />
            <View style={s.words}>
              <Text style={s.title} numberOfLines={1}>
                {title}
              </Text>
              <Text style={s.role}>{role}</Text>
            </View>
            {selected ? (
              <Feather
                name="check"
                size={theme.size.tabIcon}
                color={theme.color.ink}
                accessibilityElementsHidden
                importantForAccessibility="no"
              />
            ) : null}
          </Pressable>
        );
      })}
    </View>
  );
}

/** Who a row is and which hat — the account's name for Player, the club's for its administrator. */
function rowWords(option: ProfileOption): { readonly title: string; readonly role: string } {
  return option.kind === 'player'
    ? { title: option.name ?? COPY.player, role: COPY.player }
    : { title: option.clubName, role: COPY.administrator };
}

const s = StyleSheet.create({
  rows: { gap: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    // `space.xs` above and below a 38pt tile is 50pt, past 6.5's minimum by geometry.
    paddingVertical: theme.space.xs,
  },
  // 6.6: the press state for a row whose whole surface is the control.
  pressed: { opacity: 0.7 },
  words: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  role: { ...theme.type.tiny, color: theme.color.muted },
});
