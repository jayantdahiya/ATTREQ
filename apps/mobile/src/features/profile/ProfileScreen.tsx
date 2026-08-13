import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { AttreqIcon, type AttreqIconName } from '@/design-system/icons/AttreqIcon';
import { StyleDnaCard } from '@/features/style-dna/StyleDnaCard';
import { StyleDnaProfileScreen } from '@/features/style-dna/StyleDnaProfileScreen';
import { WardrobeStatsScreen } from '@/features/stats/WardrobeStatsScreen';
import { HowRecommendationsWorkScreen } from '@/features/profile/HowRecommendationsWorkScreen';
import { LocationEditModal } from '@/features/profile/LocationEditModal';
import { StylePreferencesModal } from '@/features/profile/StylePreferencesModal';
import { ChangePasswordModal } from '@/features/profile/ChangePasswordModal';
import { DeleteAccountModal } from '@/features/profile/DeleteAccountModal';
import { MossToggle } from '@/features/profile/MossToggle';
import { profileDisplayName, profileInitials, stylePreferencesDisplay } from '@/features/profile/profileFormat';
import { profileStatTiles } from '@/features/stats/statsFormat';
import { useStyleDna } from '@/lib/query/style-dna';
import { useWardrobeStats } from '@/lib/query/stats';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/query/query-client';
import { getReminderEnabled, saveReminderEnabled } from '@/lib/storage/secure-store';
import { useAuthStore } from '@/store/auth-store';
import { useBackHandler } from '@/lib/hooks/useBackHandler';

type Screen = 'main' | 'style-dna' | 'stats' | 'how-it-works';

/**
 * A5 Profile hub (JS-only nav). Identity + stats tiles, Style DNA row,
 * Wardrobe stats + "how recommendations work" rows, a Preferences section
 * (location / daily reminder / style / change password), delete account, and
 * sign out. Edit flows are RN Modal bottom sheets (BackHandler-wired).
 */
export function ProfileScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useAuthStore((s) => s.signOut);
  const { data: user } = useQuery({ queryKey: queryKeys.me, queryFn: authApi.getCurrentUser });
  const { data: styleDna, isLoading: dnaLoading } = useStyleDna();
  const stats = useWardrobeStats();

  const [screen, setScreen] = useState<Screen>('main');
  const [showLocation, setShowLocation] = useState(false);
  const [showStyle, setShowStyle] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  // Daily reminder — persisted via AsyncStorage (existing getReminderEnabled /
  // saveReminderEnabled). NOTE: actual OS notification scheduling is DEFERRED —
  // a notifications native module lands in a later milestone (see the A5 plan).
  // Until then this is a persisted preference the toggle reflects across launches.
  const [reminderEnabled, setReminderEnabled] = useState(false);
  useEffect(() => {
    let active = true;
    void getReminderEnabled().then((v) => {
      if (active) setReminderEnabled(v);
    });
    return () => {
      active = false;
    };
  }, []);
  const toggleReminder = () => {
    const next = !reminderEnabled;
    setReminderEnabled(next);
    void saveReminderEnabled(next);
  };

  // Hardware back mirrors the on-screen back on sub-screens; at the hub (tab
  // root) fall through to the default (exit). Modal sheets register their own
  // BackHandler while visible and, being registered later, win over this one.
  useBackHandler(() => {
    if (screen === 'main') return false;
    setScreen('main');
    return true;
  });

  if (screen === 'style-dna') return <StyleDnaProfileScreen onBack={() => setScreen('main')} />;
  if (screen === 'stats') return <WardrobeStatsScreen onBack={() => setScreen('main')} />;
  if (screen === 'how-it-works') return <HowRecommendationsWorkScreen onBack={() => setScreen('main')} />;

  const dna = styleDna?.style_dna ?? null;
  const name = profileDisplayName(user?.full_name, user?.email);
  const tiles = profileStatTiles(stats.data);
  const hasCoordinates = user?.saved_latitude != null && user?.saved_longitude != null;

  const divider = <View style={{ height: 1, backgroundColor: t.colors.borderSoft }} />;

  const PreferenceRow = ({
    icon,
    label,
    sub,
    onPress,
    trailing,
    testID,
  }: {
    icon: AttreqIconName;
    label: string;
    sub: string;
    onPress?: () => void;
    trailing?: React.ReactNode;
    testID?: string;
  }) => {
    const content = (
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 16 }}>
        <AttreqIcon name={icon} size={15} color={t.colors.t2} />
        <View style={{ flex: 1, gap: 2 }}>
          <BodyText size={13} weight="regular" color={t.colors.text}>
            {label}
          </BodyText>
          <MonoLabel>{sub}</MonoLabel>
        </View>
        {trailing ?? <MonoLabel color={t.colors.accent}>Edit</MonoLabel>}
      </View>
    );
    if (!onPress) return <View testID={testID}>{content}</View>;
    return (
      <Pressable onPress={onPress} accessibilityRole="button" testID={testID}>
        {content}
      </Pressable>
    );
  };

  const LinkCard = ({
    icon,
    title,
    sub,
    onPress,
    testID,
  }: {
    icon: AttreqIconName;
    title: string;
    sub: string;
    onPress: () => void;
    testID: string;
  }) => (
    <Pressable onPress={onPress} accessibilityRole="button" testID={testID}>
      <Card padding={0}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 13, paddingHorizontal: 16 }}>
          <AttreqIcon name={icon} size={15} color={t.colors.t2} />
          <View style={{ flex: 1, gap: 2 }}>
            <BodyText size={14} color={t.colors.text}>
              {title}
            </BodyText>
            <MonoLabel>{sub}</MonoLabel>
          </View>
          <AttreqIcon name="chevron" size={13} color={t.colors.t3} />
        </View>
      </Card>
    </Pressable>
  );

  return (
    <View testID="profile-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingTop: insets.top + 24, paddingHorizontal: 24, paddingBottom: 160, gap: 18 }}>
        {/* Header */}
        <View style={{ gap: 5 }}>
          <MonoLabel>You</MonoLabel>
          <Text style={[display(30, { italic: true }), { color: t.colors.text }]}>Profile.</Text>
        </View>

        {/* Stats error banner (initial-load failure). */}
        {stats.isError && (
          <View style={{ backgroundColor: t.colors.claySoft, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 13 }}>
            <BodyText size={13} color={t.colors.clay}>
              Couldn't load your profile stats.
            </BodyText>
          </View>
        )}

        {/* Identity card + stats tiles */}
        <Card padding={0} style={{ paddingVertical: 18, paddingHorizontal: 20 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 14 }}>
            <View
              style={{
                width: 50,
                height: 50,
                borderRadius: 100,
                backgroundColor: t.colors.accent,
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <Text style={[display(19, { italic: true }), { color: t.colors.bg }]}>
                {profileInitials(user?.full_name, user?.email)}
              </Text>
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <Text numberOfLines={1} style={[display(20), { color: t.colors.text }]}>
                {name}
              </Text>
              <BodyText size={13}>{user?.email ?? ''}</BodyText>
            </View>
          </View>

          {divider}

          <View style={{ flexDirection: 'row', gap: 24, marginTop: 14 }} testID="profile-stats-row">
            {tiles.map((tile) => (
              <View key={tile.label} style={{ gap: 3 }}>
                <MonoLabel>{tile.label}</MonoLabel>
                {stats.isLoading && !stats.data ? (
                  <ActivityIndicator color={t.colors.t3} style={{ alignSelf: 'flex-start' }} />
                ) : (
                  <Text style={[display(22, { italic: true }), { color: tile.accent ? t.colors.accent : t.colors.text }]}>
                    {tile.value}
                  </Text>
                )}
              </View>
            ))}
          </View>
        </Card>

        {/* Style DNA row */}
        <MonoLabel>Style DNA</MonoLabel>
        <Pressable onPress={() => setScreen('style-dna')} accessibilityRole="button" testID="profile-style-dna-row">
          {dnaLoading ? (
            <Card padding={18}>
              <ActivityIndicator color={t.colors.t2} />
            </Card>
          ) : dna ? (
            <StyleDnaCard dna={dna} />
          ) : (
            <Card padding={0}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 13, paddingHorizontal: 16 }}>
                <AttreqIcon name="sparkles" size={15} color={t.colors.t2} />
                <View style={{ flex: 1, gap: 2 }}>
                  <BodyText size={14} color={t.colors.text}>
                    Your Style DNA
                  </BodyText>
                  <MonoLabel>Tap to view or build your profile</MonoLabel>
                </View>
                <AttreqIcon name="chevron" size={13} color={t.colors.t3} />
              </View>
            </Card>
          )}
        </Pressable>

        {/* Preferences */}
        <MonoLabel>Preferences</MonoLabel>
        <Card padding={0}>
          <PreferenceRow
            icon="location"
            label={user?.saved_city ?? user?.location ?? 'Set your location'}
            sub={hasCoordinates ? 'Coordinates saved' : 'For weather-aware suggestions'}
            onPress={() => setShowLocation(true)}
            testID="profile-row-location"
          />
          {divider}
          <PreferenceRow
            icon="bell"
            label="Daily reminder"
            sub="8:00 AM — every day"
            trailing={<MossToggle isOn={reminderEnabled} onToggle={toggleReminder} testID="reminder-toggle" />}
            testID="profile-row-reminder"
          />
          {divider}
          <PreferenceRow
            icon="sparkles"
            label="Style preferences"
            sub={stylePreferencesDisplay(user?.style_preferences)}
            onPress={() => setShowStyle(true)}
            testID="profile-row-style"
          />
          {divider}
          <PreferenceRow
            icon="person"
            label="Change password"
            sub="Update your sign-in password"
            onPress={() => setShowPassword(true)}
            testID="profile-row-password"
          />
        </Card>

        {/* Wardrobe stats + trust */}
        <LinkCard
          icon="shirt"
          title="Wardrobe stats"
          sub="Cost per wear, most worn & more"
          onPress={() => setScreen('stats')}
          testID="profile-row-stats"
        />
        <LinkCard
          icon="heart"
          title="How recommendations work"
          sub="Only your wardrobe — never ads"
          onPress={() => setScreen('how-it-works')}
          testID="profile-row-how-it-works"
        />

        {/* Danger zone + footer */}
        <View style={{ alignItems: 'center', gap: 4, marginTop: 8 }}>
          <Pressable
            onPress={() => void signOut()}
            accessibilityRole="button"
            testID="sign-out"
            hitSlop={10}
            style={{ paddingVertical: 10, paddingHorizontal: 24 }}>
            <MonoLabel size={10} color={t.colors.clay}>
              Sign out
            </MonoLabel>
          </Pressable>
          <Pressable
            onPress={() => setShowDelete(true)}
            accessibilityRole="button"
            testID="profile-row-delete"
            hitSlop={10}
            style={{ paddingVertical: 8, paddingHorizontal: 24 }}>
            <MonoLabel size={9} color={t.colors.t3}>
              Delete account
            </MonoLabel>
          </Pressable>
          <MonoLabel size={9} color={t.colors.t3} style={{ marginTop: 4 }}>
            v 0.2.0-beta.1 — ATTREQ
          </MonoLabel>
        </View>
      </ScrollView>

      {/* Edit modals */}
      <LocationEditModal
        visible={showLocation}
        onClose={() => setShowLocation(false)}
        initialCity={user?.saved_city ?? user?.location ?? ''}
      />
      <StylePreferencesModal
        visible={showStyle}
        onClose={() => setShowStyle(false)}
        current={user?.style_preferences}
      />
      <ChangePasswordModal visible={showPassword} onClose={() => setShowPassword(false)} />
      <DeleteAccountModal visible={showDelete} onClose={() => setShowDelete(false)} />
    </View>
  );
}
