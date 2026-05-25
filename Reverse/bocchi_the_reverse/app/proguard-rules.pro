# Keep WebView bridge methods callable by JavaScript.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# NativeVmBridge methods are registered through JNI_OnLoad/RegisterNatives.
# Keep the class and native method names stable so the registration table stays valid.
-keep class com.example.bocchi_the_reverse.NativeVmBridge {
    native <methods>;
}

# If more JNI bridge classes are added later, keep their native method names stable as well.
-keepclasseswithmembernames class * {
    native <methods>;
}
