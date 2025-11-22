[app]

# عنوان التطبيق
title = City Mover - تطبيق الانتقال

# اسم الحزمة (يجب أن يكون فريداً)
package.name = citymover

# اسم النطاق (domain)
package.domain = com.example

# إصدار التطبيق
version = 1.0

# رقم الإصدار
source.dir = .

# الملف الرئيسي
source.include_exts = py,png,jpg,kv,atlas,txt

# مكتبات Python المطلوبة
requirements = python3,flet,sqlite3,pathlib

# نظام التشغيل المستهدف
osx.android_api = 28
osx.minapi = 21

# الأيقونة (سنضيفها لاحقاً)
icon.filename = %(source.dir)s/assets/icon.png

# شاشة البداية
presplash.filename = %(source.dir)s/assets/presplash.png

# التوجيه
orientation = portrait

# الأذونات
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# سمات واجهة المستخدم
android.meta_data = android.app.lib_name=citymover

# إعدادات البناء
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.ndk_path = 
android.sdk_path = 

# بنية المعالج
android.arch = arm64-v8a,armeabi-v7a

# التوقيع
android.release_artifact = .apk