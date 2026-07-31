import { zodResolver } from '@hookform/resolvers/zod'
import { Link, router } from 'expo-router'
import { useMutation } from '@tanstack/react-query'
import { LinearGradient } from 'expo-linear-gradient'
import { Controller, useForm } from 'react-hook-form'
import { Alert, KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native'
import Animated, { FadeInDown } from 'react-native-reanimated'
import { z } from 'zod'

import { EditorialCard, MonoLabel } from '@/components/attreq/editorial'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/auth-store'
import { useThemeColors } from '@/theme/colors'
import { fontFamily } from '@/theme/typography'

const loginSchema = z.object({
  username: z.string().email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginScreen() {
  const { colors } = useThemeColors()
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    defaultValues: {
      username: '',
      password: '',
    },
    resolver: zodResolver(loginSchema),
  })

  const signIn = useAuthStore((state) => state.signIn)

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (response) => {
      await signIn(response)
      router.replace('/(protected)/(tabs)')
    },
    onError: (error: Error) => {
      Alert.alert('Sign in failed', error.message)
    },
  })

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: 'padding', default: undefined })}
      className="flex-1"
      style={{ backgroundColor: colors.bgDeep }}
    >
      <LinearGradient
        colors={[colors.bgSurface, colors.bgDeep]}
        locations={[0, 0.55]}
        pointerEvents="none"
        style={{ height: 390, left: 0, opacity: 0.72, position: 'absolute', right: 0, top: 0 }}
      />
      <ScrollView className="flex-1" contentContainerStyle={{ flexGrow: 1 }}>
        <View className="flex-1 justify-between px-7 pb-10 pt-16">
          <View className="items-center pt-12">
            <MonoLabel>est. 2026 - personal styling</MonoLabel>
            <Text className="mt-5 text-center" color="accentGold" preset="wordmark">
              ATTREQ
            </Text>
            <Text className="mt-3 text-center" color="textSecondary" preset="h2" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
              Your closet, curated.
            </Text>
          </View>

          <Animated.View entering={FadeInDown.delay(220).duration(600)}>
            <EditorialCard accent="gold" className="gap-5 px-6 py-7">
              <View>
                <Text preset="h2">Welcome back</Text>
                <Text className="mt-1" color="textSecondary" preset="bodySmall">
                  Sign in to your wardrobe.
                </Text>
              </View>
              <Controller
                control={control}
                name="username"
                render={({ field: { onChange, value } }) => (
                  <Input
                    autoCapitalize="none"
                    autoComplete="email"
                    keyboardType="email-address"
                    label="Email"
                    onChangeText={onChange}
                    value={value}
                    error={errors.username?.message}
                  />
                )}
              />
              <Controller
                control={control}
                name="password"
                render={({ field: { onChange, value } }) => (
                  <Input
                    autoCapitalize="none"
                    autoComplete="password"
                    label="Password"
                    onChangeText={onChange}
                    secureTextEntry
                    value={value}
                    error={errors.password?.message}
                  />
                )}
              />

              <Button
                isLoading={loginMutation.isPending}
                label="Sign in"
                onPress={handleSubmit((values) => loginMutation.mutate(values))}
              />

              <Text className="text-center" color="textTertiary" preset="label">
                Forgot password
              </Text>
            </EditorialCard>
          </Animated.View>

          <Text className="text-center" color="textSecondary" preset="bodySmall">
            New here?{' '}
            <Link href="/(auth)/register">
              <Text color="accentGold" preset="bodySmall" style={{ fontFamily: fontFamily.bodySemi }}>
                Create account
              </Text>
            </Link>
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}
