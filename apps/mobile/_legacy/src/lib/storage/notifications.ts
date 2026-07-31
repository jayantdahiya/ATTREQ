import { getReminderEnabled, saveReminderEnabled } from '@/lib/storage/secure-store'

type NotificationsModule = typeof import('expo-notifications')

let notificationsModule: NotificationsModule | null | undefined
let handlerConfigured = false

function getNotificationsModule() {
  if (notificationsModule !== undefined) {
    return notificationsModule
  }

  try {
    notificationsModule = require('expo-notifications') as NotificationsModule
  } catch {
    notificationsModule = null
  }

  return notificationsModule
}

function configureNotificationHandler(module: NotificationsModule) {
  if (handlerConfigured) {
    return
  }

  try {
    module.setNotificationHandler({
      handleNotification: async () => ({
        shouldPlaySound: true,
        shouldSetBadge: false,
        shouldShowBanner: true,
        shouldShowList: true,
      }),
    })
    handlerConfigured = true
  } catch {
    notificationsModule = null
  }
}

export async function enableDailyReminder() {
  const Notifications = getNotificationsModule()

  if (!Notifications) {
    await saveReminderEnabled(false)
    return false
  }

  configureNotificationHandler(Notifications)

  try {
    const permissions = await Notifications.requestPermissionsAsync()

    if (!permissions.granted) {
      await saveReminderEnabled(false)
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
  } catch {
    await saveReminderEnabled(false)
    return false
  }
}

export async function disableDailyReminder() {
  const Notifications = getNotificationsModule()

  if (Notifications) {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync()
    } catch {
      notificationsModule = null
    }
  }

  await saveReminderEnabled(false)
}

export async function getReminderStatus() {
  return getReminderEnabled()
}
