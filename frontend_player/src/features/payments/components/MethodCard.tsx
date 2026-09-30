/**
 * **The method card** — state B's head (mocks 46, 47; the screens A7.3; design system 7.23).
 *
 * The dark card (5.2): the brand's square on the left — the network's short name, or the wallet's —
 * then *Card •••• 4312* over *Charged by the club when a game fills*, and **Change** on the right,
 * which reopens the setup; the method keeps working until a new one is saved. The square is words,
 * not a logo: the app draws no third party's mark, and Archivo has none to draw.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, DarkCard, theme } from '@/shared/ui';

import type { SavedMethod } from '../domain/vocabulary';

import { PAYMENTS_COPY, cardLine, methodBadge, methodCardLabel } from './paymentsCopy';

export interface MethodCardProps {
  readonly method: SavedMethod;
  readonly onChange: () => void;
}

export function MethodCard({ method, onChange }: MethodCardProps) {
  return (
    <DarkCard style={s.card}>
      <View style={s.row}>
        <View
          style={s.who}
          accessible
          accessibilityRole="text"
          accessibilityLabel={methodCardLabel(method)}
        >
          <View style={s.badge}>
            <Text style={s.badgeWords} numberOfLines={2} adjustsFontSizeToFit>
              {methodBadge(method)}
            </Text>
          </View>
          <View style={s.words}>
            <Text style={s.title}>{cardLine(method)}</Text>
            <Text style={s.line}>{PAYMENTS_COPY.method.charged}</Text>
          </View>
        </View>
        <Button label={PAYMENTS_COPY.method.change} variant="onDark" size="sm" onPress={onChange} />
      </View>
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { marginBottom: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  who: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  badge: {
    width: theme.size.payments.badge,
    height: theme.size.payments.badge,
    borderRadius: theme.radius.rowLead,
    backgroundColor: theme.color.onDarkFill,
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.space.xxs,
  },
  badgeWords: { ...theme.type.btn, color: theme.color.surface, textAlign: 'center' },
  words: { flex: 1, gap: theme.space.xxs },
  title: { ...theme.type.question, color: theme.color.surface },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny },
});
