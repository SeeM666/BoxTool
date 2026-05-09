[app]
title = BoxTool
package.name = boxtool
package.domain = org.boxtool
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt
version = 5.0.0
requirements = python3,kivy==2.3.0,requests,beautifulsoup4,paramiko,pymysql,qrcode,Pillow,dnspython,shodan,python-nmap
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
splash.filename = %(source.dir)s/splash.png
splash.background_color = 237,240,245
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25.2.9519653
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = False
p4a.branch = master
p4a.source_dir =
p4a.bootstrap = sdl2
p4a.extra_args = --blacklist-requirements=libffi
log_level = 2
warn_on_root = 1
debug = 0

[buildozer]
log_level = 2
warn_on_root = 1
