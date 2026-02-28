# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import argparse
import subprocess
import logging
import time
import os
import tempfile
import re

from debugActivity.lldbtools.lldbtools import (
    pushLLDBServer,
    pushFridaServer,
    grantPermission,
    grantFridaPermission,
    startLLDBServer,
)

logger = logging.getLogger("debugActivity")

parser = argparse.ArgumentParser(
    prog='debugActivity',
    description='start a debug activity',
    epilog='-p packageName\n -a AcivityName -s signApkPath')

scriptPath = os.path.split(os.path.realpath(__file__))[0]


_PS_LINE_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def _extract_block(text: str, begin_marker: str, end_marker: str) -> str:
    in_block = False
    out_lines: list[str] = []
    for line in text.splitlines():
        if begin_marker in line:
            in_block = True
            continue
        if in_block and end_marker in line:
            break
        if in_block:
            out_lines.append(line)
    return "\n".join(out_lines)


def _parse_ps_pid_name(text: str) -> set[str]:
    """
    Parse output of: ps -A -o PID -o NAME

    Returns a set of "PID NAME" lines, normalized, filtering prompts/echo lines.
    """
    out: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith("PID"):
            continue
        m = _PS_LINE_RE.match(line)
        if not m:
            continue
        out.add(f"{m.group(1)} {m.group(2)}")
    return out


def _adb_shell_interactive(commands: list[str], timeout: int = 10) -> str:
    """
    Run multiple commands in a single `adb shell` interactive session.
    """
    p = subprocess.Popen(
        ["adb", "shell"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        stdout, _ = p.communicate(input="\n".join(commands) + "\n", timeout=timeout)
        return stdout or ""
    except subprocess.TimeoutExpired:
        p.kill()
        raise


def _ps_pid_name_via_adb_shell_su(timeout: int = 10) -> tuple[set[str], str]:
    """
    Execute `adb shell` -> `su` -> `ps -A -o PID -o NAME` in three steps, and return parsed set + raw output.
    """
    begin = "__DEBUGACTIVITY_PS_BEGIN__"
    end = "__DEBUGACTIVITY_PS_END__"
    raw = _adb_shell_interactive(
        [
            "su",
            f"echo {begin}",
            "ps -A -o PID -o NAME",
            f"echo {end}",
            "exit",
            "exit",
        ],
        timeout=timeout,
    )
    ps_block = _extract_block(raw, begin, end)
    return _parse_ps_pid_name(ps_block), raw


def sign(path):
    cwd = os.getcwd()
    fileName = os.path.splitext(path)[0]
    suffix = os.path.splitext(path)[-1]
    outpath = os.path.join(cwd, path)
    tmpDir = tempfile.TemporaryDirectory()
    tmpApk = os.path.join(tmpDir.name, "temp.apk")
    print(tmpApk)
    zipArgs = "zipalign -f " + " -v 4 " +  outpath + "  " + tmpApk
    print(zipArgs)
    subprocess.run(zipArgs, shell=True, check=True)

    apksigner = os.path.join(scriptPath, "apksigner", "apksigner.jar")
    jsk = os.path.join(scriptPath, "apksigner", "pareto.jks")
    signArgs = "java -jar " + apksigner + " sign " + "--ks " + jsk + " --ks-pass pass:pareto " + "--in " + tmpApk + " --out " + fileName+"_signed"+suffix
    subprocess.run(signArgs, shell=True, check=True)


# def startLLDBServer():


def main():
    # parser.add_argument('filename')
    parser.add_argument('-p', '--package')
    parser.add_argument('-a', '--activity')
    parser.add_argument('-s', '--sign')
    parser.add_argument('-l', '--lldbserver', action='store_true')
    parser.add_argument('-P', '--process', action='store_true')
    parser.add_argument('-f' , '--frida' , action='store_true')
    parser.add_argument(
        '--push-servers',
        action='store_true',
        help='push lldb-server and frida-server (rename frida-server to fda on device)'
    )
    parser.add_argument(
        '--frida-server',
        dest='frida_server',
        default=None,
        help='local path to frida-server binary (optional; can also set FRIDA_SERVER_PATH)'
    )

    args = parser.parse_args()
    package = args.package
    activity = args.activity

    print("process: " + str(args.process))
    if args.push_servers != False:
        pushLLDBServer()
        pushFridaServer(args.frida_server)
        grantPermission()
        grantFridaPermission()
        print("push servers done: /data/local/tmp/lldb-server and /data/local/tmp/fda")
        return
    elif args.lldbserver != False:
        grantPermission()
        startLLDBServer()
        return
    elif args.sign != None:
        sign(args.sign)
        return
    elif args.frida != False:
        p = subprocess.Popen("adb shell ", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        commands = [
            "su",
            "cd /data/local/tmp",
            "ls",
            "nohup ./fda &",
        ]
        try:
            out, err = p.communicate(input="\n".join(commands), timeout=4)  # 不设置超时，就会卡在这里如果你知道为什么请告诉我
        except subprocess.TimeoutExpired:
            p.kill()
            logger.debug("if nothing wrong , frida launched successful.\nor u can commit a issue\n")
    
        return
    # -P 枚举进程，然后比较
    elif args.process == True:
        prcList0, raw0 = _ps_pid_name_via_adb_shell_su(timeout=10)
        print(f"[snapshot0] count={len(prcList0)}")

        input("Press Enter to take snapshot1...")
        prcList1, raw1 = _ps_pid_name_via_adb_shell_su(timeout=10)
        print(f"[snapshot1] count={len(prcList1)}")

        diffPrc = sorted(prcList1.difference(prcList0))
        print(f"[diff] new_process_count={len(diffPrc)}")
        for i in diffPrc:
            print(i)

        if len(prcList0) == 0 or len(prcList1) == 0:
            print("\n[warn] ps parsed result is empty; dumping raw adb shell output for debugging.\n")
            print("----- raw snapshot0 -----")
            print(raw0)
            print("----- raw snapshot1 -----")
            print(raw1)

        return
    elif package == None or activity == None:
        parser.print_help()
        exit(0)

    startcom = "adb shell am start -D {0}/{1}".format(package, activity)

    subprocess.run(startcom, shell=True, check=True)
    time.sleep(1)

    if os.name in ('nt', 'dox'):
        getpid = "adb shell \" ps | grep {0} | awk '{{print $2}}'\"".format(package);
    elif os.name in ('linux', 'osx', 'posix'):
        getpid = "adb shell \" ps -A| grep {0} | awk '{{print \\$2}}'\"".format(package);

    # cmd
    # getpid = "adb shell \" ps -A| grep {0} | awk '{{print $2}}'\"".format(package);
    # bash
    # getpid = "adb shell \" ps -A| grep {0} | awk '{{print \$2}}'\"".format(package);
    # command
    # getpid = "adb shell \" ps | grep {0} | awk '{{print $2}}'\"".format(package);
    spid = subprocess.run(getpid, shell=True, capture_output=True, text=True).stdout

    print("app pid :" + spid)

    spid = "adb forward tcp:8700 jdwp:{0}".format(spid)
    spid = spid.replace('\n', '')
    logger.info(spid)
    subprocess.run(spid, shell=True)

    input("Press Enter to run app...")
    proc = subprocess.run("jdb -connect com.sun.jdi.SocketAttach:hostname=localhost,port=8700", shell=True, text=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()