# debugA

优化android lldb调试的一个环节 , 通过adb 和 jdb 启动被调试的应用，在回车后自动进入jdb调试。


```angular2html
usage: debugA [-h] [-p PACKAGE] [-a ACTIVITY]

start a debug activity

options:
-h, --help            show this help message and exit
-p PACKAGE, --package PACKAGE
-a ACTIVITY, --activity ACTIVITY
-s SIGN signApkPath
```

记录下打包流程，
```angular2html
python setup.py bdist_wheel --universal
twine upload dist/*
HTTPS_PROXY=socks5://192.168.50.47:7890 twine upload dist/*
```