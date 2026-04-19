import { zodResolver } from '@hookform/resolvers/zod'
import { Link, router } from 'expo-router'
import { useMutation } from '@tanstack/react-query'
import { Controller, useForm } from 'react-hook-form'
import { Alert, KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native'
import Animated, { FadeInDown } from 'react-native-reanimated'
import { z } from 'zod'

import { Divider } from '@/components/ui/divider'
import { ScreenHeader } from '@/components/common/screen-header'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/store/auth-store'
import { useThemeColors } from '@/theme/colors'

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
      <ScrollView className="flex-1" contentContainerStyle={{ flexGrow: 1 }}>
        <View className="flex-1 justify-between px-6 pb-10 pt-16">
          <View>
            <Text color="accentGold" preset="display">
              ATTREQ
            </Text>
            <View className="mt-5">
              <ScreenHeader
                heading="Your closet, curated."
                label="WELCOME BACK"
                subtitle="Sign in to restore your wardrobe and continue your daily styling loop."
              />
            </View>
          </View>

          <Animated.View entering={FadeInDown.delay(220).duration(600)}>
            <Card className="mt-10 gap-5" variant="premium">
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

              <Divider variant="subtle" />

              <Text className="text-center" color="textSecondary" preset="bodySmall">
                Need an account?{' '}
                <Link href="/(auth)/register">
                  <Text color="accentGold" preset="bodySmall" style={{ fontFamily: 'DMSans_600SemiBold' }}>
                    Create one
                  </Text>
                </Link>
              </Text>
            </Card>
          </Animated.View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}
