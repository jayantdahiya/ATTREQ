import React, { useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme/ThemeProvider';
import { GarmentTone } from '../theme/theme';
import { body, display } from '../theme/typography';
import { MonoLabel } from '../components/MonoLabel';
import { BodyText } from '../components/BodyText';
import { Card } from '../components/Card';
import { Chip } from '../components/Chip';
import { Pill } from '../components/Pill';
import { PrimaryButton } from '../components/PrimaryButton';
import { UnderlineInput } from '../components/UnderlineInput';
import { GarmentPlaceholder } from '../components/GarmentPlaceholder';
import { AttreqTab, TabBar } from '../components/TabBar';
import { StepNav } from '../components/StepNav';
import { ATTREQ_ICON_NAMES, AttreqIcon } from '../icons/AttreqIcon';

const CHIP_OPTIONS = ['Minimal', 'Earthy', 'Tailored', 'Layered', 'Casual', 'Formal', 'Streetwear', 'Athleisure'];
const GARMENT_TONES: GarmentTone[] = ['top', 'bottom', 'outer', 'accent', 'shoes'];

/** A0 proof screen: every design-system piece on one scrollable page, tab bar overlaid. */
export function ComponentGallery() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState('hi@natasha.com');
  const [password, setPassword] = useState('hunter2secret');
  const [selected, setSelected] = useState<Set<string>>(new Set(['Minimal', 'Earthy', 'Layered']));
  const [activeTab, setActiveTab] = useState<AttreqTab>('today');
  const [step, setStep] = useState(1);

  const toggleChip = (c: string) =>
    setSelected(prev => {
      const next = new Set(prev);
      next.has(c) ? next.delete(c) : next.add(c);
      return next;
    });

  const colorTokens: [string, string][] = [
    ['bg', t.colors.bg], ['surface', t.colors.surface], ['deep', t.colors.deep], ['text', t.colors.text],
    ['t2', t.colors.t2], ['t3', t.colors.t3], ['accent', t.colors.accent], ['accentSoft', t.colors.accentSoft],
    ['clay', t.colors.clay], ['claySoft', t.colors.claySoft], ['moss', t.colors.moss], ['mossSoft', t.colors.mossSoft],
    ['border', t.colors.border], ['borderSoft', t.colors.borderSoft],
  ];

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <View style={{ gap: 14 }}>
      <MonoLabel>{title}</MonoLabel>
      {children}
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView contentContainerStyle={{ paddingHorizontal: 24, paddingTop: insets.top + 16, paddingBottom: 120, gap: 40 }}>
        {/* Header */}
        <View style={{ gap: 8 }}>
          <MonoLabel>ATTREQ — Design System</MonoLabel>
          <Text style={[display(34), { color: t.colors.text }]}>Component Gallery</Text>
          <Text style={[display(19, { weight: 'regular', italic: true }), { color: t.colors.t2 }]}>Every token, rendered.</Text>
        </View>

        <Section title="01 — Type Ramp">
          <View style={{ gap: 12 }}>
            <Text style={[display(36), { color: t.colors.text }]}>Your closet, curated.</Text>
            <Text style={[display(24, { weight: 'medium', italic: true }), { color: t.colors.accent }]}>Define your aesthetic.</Text>
            <Text style={[display(18, { weight: 'regular' }), { color: t.colors.text }]}>Display — Cormorant Garamond, regular</Text>
            <BodyText>Body — DM Sans regular at 14pt. A few details, then we'll curate every look.</BodyText>
            <Text style={[body(14, 'semiBold'), { color: t.colors.text }]}>Body — DM Sans semibold at 14pt.</Text>
            <Text style={[body(14, 'light'), { color: t.colors.t2 }]}>Body — DM Sans light at 14pt.</Text>
            <MonoLabel>Mono label — IBM Plex Mono 9.5</MonoLabel>
          </View>
        </Section>

        <Section title="02 — Color Tokens">
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
            {colorTokens.map(([name, value]) => (
              <View key={name} style={{ width: '22%', gap: 5 }}>
                <View style={{ height: 44, borderRadius: 10, backgroundColor: value, borderWidth: 1, borderColor: t.colors.border }} />
                <MonoLabel size={7.5}>{name}</MonoLabel>
              </View>
            ))}
          </View>
        </Section>

        <Section title="03 — Buttons">
          <View style={{ gap: 12 }}>
            <PrimaryButton label="Sign in" />
            <PrimaryButton label="Create account" variant="accent" icon="chevron" />
            <PrimaryButton label="Curating…" isLoading />
          </View>
        </Section>

        <Section title="04 — Inputs, on Card">
          <Card padding={22}>
            <View style={{ gap: 20 }}>
              <UnderlineInput label="Email address" value={email} onChangeText={setEmail} keyboardType="email-address" />
              <UnderlineInput label="Password" value={password} onChangeText={setPassword} secureTextEntry />
            </View>
          </Card>
        </Section>

        <Section title="05 — Chips">
          <View style={{ gap: 8 }}>
            {[CHIP_OPTIONS.slice(0, 4), CHIP_OPTIONS.slice(4)].map((row, ri) => (
              <View key={ri} style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7 }}>
                {row.map(opt => (
                  <Chip key={opt} label={opt} selected={selected.has(opt)} onPress={() => toggleChip(opt)} />
                ))}
              </View>
            ))}
          </View>
        </Section>

        <Section title="06 — Pills">
          <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
            <Pill>Muted</Pill>
            <Pill variant="gold">Golden hour</Pill>
            <Pill variant="moss">Fresh</Pill>
            <Pill variant="clay">In laundry</Pill>
          </View>
        </Section>

        <Section title="07 — Garment Tones">
          <View style={{ flexDirection: 'row', gap: 8 }}>
            {GARMENT_TONES.map(tone => (
              <GarmentPlaceholder key={tone} tone={tone} label={tone} style={{ flex: 1, height: 96 }} />
            ))}
          </View>
        </Section>

        <Section title="08 — Icons">
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', rowGap: 18 }}>
            {ATTREQ_ICON_NAMES.map(name => (
              <View key={name} style={{ width: '25%', alignItems: 'center', gap: 6 }}>
                <AttreqIcon name={name} size={20} color={t.colors.t2} />
                <MonoLabel size={7.5}>{name}</MonoLabel>
              </View>
            ))}
          </View>
        </Section>

        <Section title="09 — Step Nav">
          <StepNav step={step} onBack={() => setStep(s => Math.max(0, s - 1))} />
        </Section>
      </ScrollView>

      <TabBar active={activeTab} onChange={setActiveTab} />
    </View>
  );
}
