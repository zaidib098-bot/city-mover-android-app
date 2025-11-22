[app]

title = City Mover
package.name = citymover
package.domain = com.example
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

requirements = python3,kivy,sqlite3,pathlib

orientation = portrait
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 21
android.arch = arm64-v8a,armeabi-v7a
android.release_artifact = .apk
android.build_tools_version = 33.0.2
