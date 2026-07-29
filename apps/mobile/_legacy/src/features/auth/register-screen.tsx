import { zodResolver } from '@hookform/resolvers/zod'
import { Link, router } from 'expo-router'
import { useMutation } from '@tanstack/react-query'
import { Ionicons } from '@expo/vector-icons'
import { LinearGradient } from 'expo-linear-gradient'
import { Controller, useForm } from 'react-hook-form'
import { Alert, KeyboardAvoidingView, Platform, Pressable, ScrollView, View } from 'react-native'
import Animated, { FadeInDown, FadeInRight } from 'react-native-reanimated'
import { useState } from 'react'
import { z } from 'zod'

import { EditorialCard, MonoLabel } from '@/components/attreq/editorial'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/auth-store'
import { useThemeColors } from '@/theme/colors'
import { fontFamily } from '@/theme/typography'

const registerSchema = z
  .object({
    email: z.string().email('Enter a valid email address'),
    full_name: z.string().min(2, 'Enter your name'),
    location: z.string().optional(),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Confirm your password'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Passwords must match',
    path: ['confirmPassword'],
  })

type RegisterFormValues = z.infer<typeof registerSchema>

const STYLE_OPTIONS = ['Minimal', 'Earthy', 'Tailored', 'Layered', 'Casual', 'Formal', 'Streetwear', 'Athleisure']
const STEPS = ['Account', 'Style', 'Location'] as const

export function RegisterScreen() {
  const { colors } = useThemeColors()
  const [step, setStep] = useState(0)
  const [selectedStyles, setSelectedStyles] = useState<string[]>(['Minimal', 'Earthy', 'Layered'])
  const [occasions, setOccasions] = useState('')

  const {
    control,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: { email: '', full_name: '', location: '', password: '', confirmPassword: '' },
    resolver: zodResolver(registerSchema),
  })

  const signIn = useAuthStore((state) => state.signIn)

  const registerMutation = useMutation({
    mutationFn: async (values: RegisterFormValues) => {
      await authApi.register({
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        location: values.location || undefined,
      })
      return authApi.login({ username: values.email, password: values.password })
    },
    onSuccess: async (response) => {
      await signIn(response)
      router.replace('/(protected)/(tabs)')
    },
    onError: (error: Error) => {
      Alert.alert('Registration failed', error.message)
    },
  })

  const toggleStyle = (s: string) => {
    setSelectedStyles((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]))
  }

  const handleBack = () => {
    if (step > 0) setStep((s) => s - 1)
    else router.back()
  }

  const handleNext = async () => {
    if (step === 0) {
      const valid = await trigger(['email', 'full_name', 'password', 'confirmPassword'])
      if (valid) setStep(1)
    } else if (step === 1) {
      setStep(2)
    }
  }

  const stepHeadings = [
    { label: 'Make this', italic: 'your closet.' },
    { label: 'Define your', italic: 'aesthetic.' },
    { label: 'Set your', italic: 'world.' },
  ]
  const stepSubtitles = [
    "A few details, then we'll curate every look.",
    "Tell us how you dress. We'll learn the rest.",
    'Your city shapes every recommendation.',
  ]

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: 'padding', default: undefined })}
      style={{ flex: 1, backgroundColor: colors.bgDeep }}
    >
      <LinearGradient
        colors={[colors.bgSurface, colors.bgDeep]}
        locations={[0, 0.55]}
        pointerEvents="none"
        style={{ height: 300, left: 0, opacity: 0.7, position: 'absolute', right: 0, top: 0 }}
      />

      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1 }}>
        <View style={{ flex: 1, paddingHorizontal: 28, paddingTop: 56, paddingBottom: 32 }}>

          {/* Step nav */}
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
            <Pressable onPress={handleBack} style={{ height: 32, width: 32, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons color={colors.textSecondary} name="chevron-back" size={22} />
            </Pressable>
            <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center' }}>
              {STEPS.map((_, i) => (
                <View
                  key={i}
                  style={{
                    height: 3,
                    width: i === step ? 24 : 8,
                    borderRadius: 100,
                    backgroundColor: i <= step ? colors.accentGold : colors.borderSubtle,
                  }}
                />
              ))}
            </View>
            <MonoLabel>{`0${step + 1}/${STEPS.length}`}</MonoLabel>
          </View>

          {/* Heading */}
          <Animated.View key={step} entering={FadeInRight.duration(300)}>
            <MonoLabel color="accentGold" className="mb-2">
              {`Step 0${step + 1} — ${STEPS[step]}`}
            </MonoLabel>
            <Text preset="display" style={{ lineHeight: 42, marginBottom: 6 }}>
              {stepHeadings[step].label}{'\n'}
              <Text
                preset="display"
                color="accentGold"
                style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic', lineHeight: 42 }}
              >
                {stepHeadings[step].italic}
              </Text>
            </Text>
            <Text color="textSecondary" preset="bodySmall" style={{ marginBottom: 24 }}>
              {stepSubtitles[step]}
            </Text>
          </Animated.View>

          {/* Card content */}
          <Animated.View key={`card-${step}`} entering={FadeInDown.delay(80).duration(360)}>
            <EditorialCard style={{ padding: 22 }}>

              {step === 0 && (
                <View style={{ gap: 18 }}>
                  <Controller
                    control={control}
                    name="email"
                    render={({ field: { onChange, value } }) => (
                      <Input
                        autoCapitalize="none"
                        autoComplete="email"
                        keyboardType="email-address"
                        label="Email"
                        onChangeText={onChange}
                        value={value}
                        error={errors.email?.message}
                      />
                    )}
                  />
                  <Controller
                    control={control}
                    name="full_name"
                    render={({ field: { onChange, value } }) => (
                      <Input label="Full name" onChangeText={onChange} value={value} error={errors.full_name?.message} />
                    )}
                  />
                  <Controller
                    control={control}
                    name="password"
                    render={({ field: { onChange, value } }) => (
                      <Input
                        autoCapitalize="none"
                        autoComplete="new-password"
                        label="Password"
                        onChangeText={onChange}
                        secureTextEntry
                        value={value}
                        error={errors.password?.message}
                      />
                    )}
                  />
                  <Controller
                    control={control}
                    name="confirmPassword"
                    render={({ field: { onChange, value } }) => (
                      <Input
                        autoCapitalize="none"
                        label="Confirm password"
                        onChangeText={onChange}
                        secureTextEntry
                        value={value}
                        error={errors.confirmPassword?.message}
                      />
                    )}
                  />
                </View>
              )}

              {step === 1 && (
                <View style={{ gap: 14 }}>
                  <MonoLabel>Style keywords</MonoLabel>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                    {STYLE_OPTIONS.map((s) => {
                      const on = selectedStyles.includes(s)
                      return (
                        <Pressable
                          key={s}
                          onPress={() => toggleStyle(s)}
                          style={{
                            paddingVertical: 7,
                            paddingHorizontal: 14,
                            borderRadius: 100,
                            borderWidth: 1,
                            borderColor: on ? colors.accentMoss : colors.borderSubtle,
                            backgroundColor: on ? colors.mossSoft : 'transparent',
                          }}
                        >
                          <Text
                            preset="bodySmall"
                            style={{ color: on ? colors.accentOlive : colors.textSecondary }}
                          >
                            {s}
                          </Text>
                        </Pressable>
                      )
                    })}
                  </View>
                  <View style={{ height: 1, backgroundColor: colors.borderSoft, marginVertical: 6 }} />
                  <Input
                    label="Occasions (optional)"
                    onChangeText={setOccasions}
                    placeholder="Work, weekend, travel…"
                    value={occasions}
                  />
                </View>
              )}

              {step === 2 && (
                <View style={{ gap: 18 }}>
                  <Pressable
                    style={{
                      borderRadius: 16,
                      height: 110,
                      backgroundColor: colors.glowMoss,
                      borderWidth: 1,
                      borderStyle: 'dashed',
                      borderColor: colors.borderSubtle,
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'row',
                      gap: 12,
                    }}
                  >
                    <Ionicons name="location-outline" size={22} color={colors.accentMoss} />
                    <View>
                      <Text preset="bodySmall" style={{ fontFamily: fontFamily.bodyMedium }}>
                        Use device location
                      </Text>
                      <Text preset="caption" color="textSecondary">
                        For weather-aware suggestions
                      </Text>
                    </View>
                  </Pressable>
                  <Controller
                    control={control}
                    name="location"
                    render={({ field: { onChange, value } }) => (
                      <Input
                        label="Or enter your city"
                        placeholder="New York, London, Tokyo…"
                        onChangeText={onChange}
                        value={value}
                        error={errors.location?.message}
                      />
                    )}
                  />
                </View>
              )}

            </EditorialCard>
          </Animated.View>

          <View style={{ marginTop: 18 }}>
            {step < 2 ? (
              <Button label="Continue" onPress={handleNext} />
            ) : (
              <Button
                isLoading={registerMutation.isPending}
                label="Create account"
                onPress={handleSubmit((values) => registerMutation.mutate(values))}
                variant="premium"
              />
            )}
          </View>

          <Text style={{ textAlign: 'center', marginTop: 14 }} color="textSecondary" preset="bodySmall">
            Already have an account?{' '}
            <Link href="/(auth)/login">
              <Text color="accentGold" preset="bodySmall" style={{ fontFamily: fontFamily.bodySemi }}>
                Sign in
              </Text>
            </Link>
          </Text>

        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}
