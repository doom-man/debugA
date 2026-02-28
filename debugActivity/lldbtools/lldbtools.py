import os
import subprocess
import logging
import sys

logger = logging.getLogger("lldbtools")
logger.setLevel(logging.DEBUG)
# fh = logging.FileHandler('')
sh = logging.StreamHandler(sys.stdout)

# logger.addHandler(fh)
logger.addHandler(sh)

scriptPath = os.path.split(os.path.realpath(__file__))[0]
LLDB_SERVER = os.path.join(scriptPath, "lldb-server")
FRIDA_SERVER_NAME = "frida-server"
FRIDA_REMOTE_NAME = "fda"


def pushLLDBServer():
    commands = [
        "adb",
        "push",
        LLDB_SERVER,
        "/data/local/tmp"
    ]
    try:
        p = subprocess.run(commands, shell=True, check=True)
    except subprocess.CalledProcessError:
        logger.debug("push lldb-server error")


def _find_frida_server(frida_server_path=None):
    """
    Locate local frida-server binary.
    Priority:
      1) explicit arg
      2) env FRIDA_SERVER_PATH
      3) alongside this module (debugActivity/lldbtools/frida-server)
      4) current working directory ./frida-server
    """
    candidates = []
    if frida_server_path:
        candidates.append(frida_server_path)
    env_path = os.environ.get("FRIDA_SERVER_PATH")
    if env_path:
        candidates.append(env_path)
    candidates.append(os.path.join(scriptPath, FRIDA_SERVER_NAME))
    candidates.append(os.path.join(os.getcwd(), FRIDA_SERVER_NAME))

    for c in candidates:
        if c and os.path.isfile(c):
            return c
    raise FileNotFoundError(
        "cannot find local {0}. Pass --frida-server /path/to/{0} or set FRIDA_SERVER_PATH.".format(
            FRIDA_SERVER_NAME
        )
    )


def pushFridaServer(frida_server_path=None):
    local_path = _find_frida_server(frida_server_path)
    commands = [
        "adb",
        "push",
        local_path,
        "/data/local/tmp/{0}".format(FRIDA_REMOTE_NAME),
    ]
    try:
        subprocess.run(commands, check=True)
    except subprocess.CalledProcessError:
        logger.debug("push frida-server error")


def grantPermission():
    p = subprocess.Popen("adb shell ", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    commands = [
        "su",
        "chmod +x /data/local/tmp/lldb-server"
    ]
    try:
        out, err = p.communicate(input="\n".join(commands), timeout=4)  # 不设置超时，就会卡在这里如果你知道为什么请告诉我
    except subprocess.TimeoutExpired:
        p.kill()
        logger.debug("chmod +x lldd-server error")


def grantFridaPermission():
    p = subprocess.Popen("adb shell ", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    commands = [
        "su",
        "chmod +x /data/local/tmp/{0}".format(FRIDA_REMOTE_NAME)
    ]
    try:
        out, err = p.communicate(input="\n".join(commands), timeout=4)
    except subprocess.TimeoutExpired:
        p.kill()
        logger.debug("chmod +x fda error")


def startLLDBServer():
    p = subprocess.Popen("adb shell ", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    commands = [
        "su",
        "cd /data/local/tmp",
        "ls",
        "nohup ./lldb-server p --listen 127.0.0.1:9999 --server & 2>&1 lldb-server.log",
    ]
    try:
        out, err = p.communicate(input="\n".join(commands), timeout=4)  # 不设置超时，就会卡在这里如果你知道为什么请告诉我
    except subprocess.TimeoutExpired:
        p.kill()
        logger.debug("if nothing wrong , lldb-server launched successful.\nor u can commit a issue\n")
        # out,err = p.communicate()
    subprocess.run("adb forward tcp:9999 tcp:9999", shell=True, check=True)


# pushLLDBServer()
# grantPermission()
# startLLDBServer()
