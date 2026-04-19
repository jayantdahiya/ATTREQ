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

export function RegisterScreen() {
  const { colors } = useThemeColors()
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: {
      email: '',
      full_name: '',
      location: '',
      password: '',
      confirmPassword: '',
    },
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

      return authApi.login({
        username: values.email,
        password: values.password,
      })
    },
    onSuccess: async (response) => {
      await signIn(response)
      router.replace('/(protected)/(tabs)')
    },
    onError: (error: Error) => {
      Alert.alert('Registration failed', error.message)
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
                heading="Build your personal style loop."
                label="CREATE ACCOUNT"
                subtitle="Create your account and start training recommendations around your wardrobe."
              />
            </View>
          </View>

          <Animated.View entering={FadeInDown.delay(220).duration(600)}>
            <Card className="mt-10 gap-5" variant="premium">
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
                name="location"
                render={({ field: { onChange, value } }) => (
                  <Input
                    label="Location (optional)"
                    onChangeText={onChange}
                    value={value}
                    error={errors.location?.message}
                  />
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

              <Button
                isLoading={registerMutation.isPending}
                label="Create account"
                onPress={handleSubmit((values) => registerMutation.mutate(values))}
              />

              <Divider variant="subtle" />

              <Text className="text-center" color="textSecondary" preset="bodySmall">
                Already have an account?{' '}
                <Link href="/(auth)/login">
                  <Text color="accentGold" preset="bodySmall" style={{ fontFamily: 'DMSans_600SemiBold' }}>
                    Sign in
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
