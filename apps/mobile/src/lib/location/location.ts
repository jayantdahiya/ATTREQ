export interface DeviceLocation {
  latitude: number;
  longitude: number;
  city: string | null;
}

/**
 * Device-location capture is deferred (was expo-location; removed with the pivot
 * off expo-modules-core). The register wizard's manual-city entry covers A1.
 * A New-Architecture community geolocation module is wired in a later milestone.
 */
export async function requestDeviceLocation(): Promise<DeviceLocation> {
  throw new Error("Device location isn't available yet — enter your city instead.");
}
