import * as Notifications from 'expo-notifications'

import { getReminderEnabled, saveReminderEnabled } from '@/lib/storage/secure-store'

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
})

export async function enableDailyReminder() {
  const permissions = await Notifications.requestPermissionsAsync()

  if (!permissions.granted) {
    return false
  }

  await Notifications.cancelAllScheduledNotificationsAsync()
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'ATTREQ',
      body: 'Your weather-aware outfit suggestions are ready.',
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.DAILY,
      hour: 8,
      minute: 0,
    },
  })
  await saveReminderEnabled(true)

  return true
}

export async function disableDailyReminder() {
  await Notifications.cancelAllScheduledNotificationsAsync()
  await saveReminderEnabled(false)
}

export async function getReminderStatus() {
  return getReminderEnabled()
}
