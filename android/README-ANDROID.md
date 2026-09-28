# Android Guide: Face & Eye Detection (OpenCV)

This guide shows how to build a simple Android app that runs face and eye detection in real time using OpenCV’s Haar Cascades. It uses the OpenCV Android SDK and `JavaCameraView` for camera frames.

## Prerequisites
- Android Studio (latest)
- Android device with Camera
- OpenCV Android SDK (download from https://opencv.org/releases/ → Android pack, e.g. `OpenCV-4.x-android-sdk.zip`)

## Quick Steps
1) Create a new Empty Views Activity project in Android Studio.
2) Import the OpenCV SDK as a module:
   - File → New → Import Module → select `<OpenCV-android-sdk>/sdk/java` → Name it `:openCVLibrary`.
   - After import, open `openCVLibrary/build.gradle` and ensure `minSdk` matches your app.
   - In your app module `build.gradle`, add `implementation project(':openCVLibrary')`.
3) Add camera permissions in `app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera" />
<uses-feature android:name="android.hardware.camera.autofocus" />
```
4) Add cascades under `app/src/main/res/raw/`:
   - `haarcascade_frontalface_default.xml`
   - `haarcascade_eye.xml`
5) Add `JavaCameraView` to your `activity_main.xml` layout.
6) Implement the Activity shown below and wire it as your launcher Activity.
7) Build and run on a real device (grant Camera permission at runtime).

## Layout: `activity_main.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<org.opencv.android.JavaCameraView xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/camera_view"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:visibility="gone"
    android:keepScreenOn="true" />
```

## Activity (Kotlin): `FaceEyeDetectorActivity.kt`
See `android/sample/FaceEyeDetectorActivity.kt` in this repository for the complete sample implementation.

## App `build.gradle` snippet
```gradle
dependencies {
    implementation project(':openCVLibrary')
}
```

## Manifest launcher
```xml
<application ...>
    <activity android:name=".FaceEyeDetectorActivity">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity>
</application>
```

## Tips
- If the camera opens but you see no detections, ensure cascades are in `res/raw` and load correctly.
- For better performance, reduce frame size in `JavaCameraView` settings or use CameraX with a smaller target resolution.
- Run on a physical device (emulators generally don’t expose a real camera stream).
