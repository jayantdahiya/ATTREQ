#!/usr/bin/env bash
# Build and verify the permanently signed ATTREQ Android beta artifact.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MOBILE_DIR="$REPO_DIR/apps/mobile"
ANDROID_DIR="$MOBILE_DIR/android"
KEYSTORE_FILE="${ATTREQ_ANDROID_KEYSTORE_FILE:-$HOME/Library/Application Support/ATTREQ/android-signing/attreq-upload.p12}"
KEY_ALIAS="${ATTREQ_ANDROID_KEY_ALIAS:-attreq-upload}"
KEYCHAIN_SERVICE="${ATTREQ_ANDROID_KEYCHAIN_SERVICE:-ATTREQ Android Upload Keystore Password}"
SDK_DIR="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
APKSIGNER="${ATTREQ_APKSIGNER:-$SDK_DIR/build-tools/35.0.0/apksigner}"
VERSION="$(node -p "require('$MOBILE_DIR/package.json').version")"
OUTPUT_DIR="$ANDROID_DIR/app/build/outputs/apk/release"
ARTIFACT="$OUTPUT_DIR/ATTREQ-$VERSION.apk"
CHECKSUM="$ARTIFACT.sha256"

[[ -f "$KEYSTORE_FILE" ]] || {
  printf 'error: ATTREQ upload keystore not found at %s\n' "$KEYSTORE_FILE" >&2
  exit 1
}
[[ -x "$APKSIGNER" ]] || {
  printf 'error: apksigner not found at %s\n' "$APKSIGNER" >&2
  exit 1
}

KEYSTORE_PASSWORD="$(security find-generic-password -w -a "$USER" -s "$KEYCHAIN_SERVICE")"
trap 'unset KEYSTORE_PASSWORD ATTREQ_ANDROID_KEYSTORE_PASSWORD ATTREQ_ANDROID_KEY_PASSWORD' EXIT

export ATTREQ_ANDROID_KEYSTORE_FILE="$KEYSTORE_FILE"
export ATTREQ_ANDROID_KEYSTORE_PASSWORD="$KEYSTORE_PASSWORD"
export ATTREQ_ANDROID_KEY_ALIAS="$KEY_ALIAS"
export ATTREQ_ANDROID_KEY_PASSWORD="$KEYSTORE_PASSWORD"

cd "$ANDROID_DIR"
./gradlew :app:assembleRelease --no-daemon

cp "$OUTPUT_DIR/app-release.apk" "$ARTIFACT"
CERTIFICATES="$($APKSIGNER verify --print-certs "$ARTIFACT")"
if printf '%s\n' "$CERTIFICATES" | grep -Fq 'CN=Android Debug'; then
  printf 'error: release artifact is signed with Android Debug\n' >&2
  exit 1
fi
printf '%s\n' "$CERTIFICATES"

(
  cd "$OUTPUT_DIR"
  shasum -a 256 "$(basename "$ARTIFACT")" > "$(basename "$CHECKSUM")"
)

printf 'APK: %s\n' "$ARTIFACT"
printf 'SHA-256: %s\n' "$CHECKSUM"
