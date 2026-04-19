let accessTokenReader: () => string | null = () => null
let refreshRunner: () => Promise<boolean> = async () => false
let signOutRunner: () => Promise<void> = async () => {}

export function registerSessionHandlers(handlers: {
  getAccessToken: () => string | null
  refreshSession: () => Promise<boolean>
  signOut: () => Promise<void>
}) {
  accessTokenReader = handlers.getAccessToken
  refreshRunner = handlers.refreshSession
  signOutRunner = handlers.signOut
}

export function readAccessToken() {
  return accessTokenReader()
}

export function refreshSessionWithStore() {
  return refreshRunner()
}

export function signOutWithStore() {
  return signOutRunner()
}
