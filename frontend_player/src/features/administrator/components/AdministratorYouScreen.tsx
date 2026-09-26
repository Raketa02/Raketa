/**
 * **The administrator's You tab — a placeholder**, until
 * [#517](https://github.com/Raketa02/Raketa/issues/517) gives it each group's settings and *Start
 * playing*, and [#518](https://github.com/Raketa02/Raketa/issues/518) the profile switcher chip.
 *
 * **It keeps the one thing a placeholder may not leave out: the way out.** An account that only
 * administers has no other screen with *Sign out* on it, and a tab with nothing on it would make the
 * area a place such an account can never leave. So the header — *OGRODY 33 · ADMINISTRATOR / You* —
 * and the account's own *Sign out*, the player You tab's foot (`AccountPanel`), and nothing that
 * pretends to be more.
 */

import { ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AccountPanel } from '@/features/auth/types';
import { ScreenHeader, theme } from '@/shared/ui';

import { useAreaClubName } from '../hooks/useAreaAccess';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { administratorEyebrow } from './administratorPresentation';

export function AdministratorYouScreen({ clubId }: { readonly clubId: string }) {
  const clubName = useAreaClubName(clubId);

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader eyebrow={administratorEyebrow(clubName)} title={ADMINISTRATOR_COPY.you.title} />
      <ScrollView contentContainerStyle={s.content}>
        <AccountPanel />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.lg },
});
