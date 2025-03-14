# debugA

优化android 分析过程、lldb调试流程 , 需要提前配置好java和adb环境，提前通过adb 和 jdb 启动被调试的应用。

* 签名用内置的jks签名
```
debugActivity -s apkPath 
```
* 调试模式启动，jdb自动附加, 需要包名 和 mainActivity的名称
```angular2html
debugActivity -p packageName -a activityName
```
* 自动将lldb-server推送到手机，并启动，绑定9999端口
```
debugActivity -l 
```
## 安装
```
pip install debugactivity
```
## usage
```angular2html
usage: debugA [-h] [-p PACKAGE] [-a ACTIVITY]

start a debug activity

options:
-h, --help            show this help message and exit
-p PACKAGE, --package PACKAGE
-a ACTIVITY, --activity ACTIVITY
-s SIGN signApkPath
-P process diff 对比前后的进程变化
-f 运行/data/local/tmp/frida-server
```

记录下打包流程，
```angular2html
pip install wheel
pip install twine
python setup.py bdist_wheel --universal
twine upload dist/* --repository PROJECT_NAME
HTTPS_PROXY=socks5://192.168.50.47:7890 twine upload dist/*
```
