import { Link } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

import { SignInScreen } from '@/features/auth/types';
import { theme } from '@/shared/ui';

export default function SignInRoute() {
  return (
    <View style={{ flex: 1 }}>
      <SignInScreen />
      {/* ⚠️ THROWAWAY — the only way into #227's tab-shell prototype without a session.
          Deleted with the prototype. */}
      <Link href="/prototype-tab-shell" asChild>
        <Pressable
          style={{
            alignItems: 'center',
            paddingVertical: theme.space.sm,
            backgroundColor: theme.color.night,
          }}
        >
          <Text style={{ ...theme.type.tag, color: theme.color.volt }}>
            ⚠ PROTOTYPE · #227 TAB SHELL
          </Text>
        </Pressable>
      </Link>
    </View>
  );
}
