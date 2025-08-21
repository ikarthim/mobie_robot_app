#!/bin/bash

echo "🤖 Building Robot Controller Android App"
echo "========================================"

# Navigate to frontend directory
cd /app/frontend

# Build the React app
echo "📱 Building React app for production..."
npm run build

# Sync with Android
echo "🔄 Syncing with Android..."
npx cap sync android

# Copy Gradle wrapper permissions
chmod +x android/gradlew

echo "✅ Android project ready!"
echo ""
echo "📋 Next Steps:"
echo "1. Download the /app/frontend/android folder to your local machine"
echo "2. Install Android Studio on your computer"
echo "3. Open the android folder in Android Studio"
echo "4. Connect your Android device or create an emulator"
echo "5. Click 'Run' to install the app on your device"
echo ""
echo "🎯 Alternative - Build APK directly:"
echo "   cd android && ./gradlew assembleRelease"
echo "   APK will be in: android/app/build/outputs/apk/release/app-release.apk"