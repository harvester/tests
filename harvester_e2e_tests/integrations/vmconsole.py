import re
from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, PIPE


class VMConsole:
    def __init__(self, virctl, name, user, passwd, command_timeout=300):
        self.proc = None
        self.virctl = virctl
        self.name = name
        self.user = user
        self.passwd = passwd
        self.timeout = command_timeout

    def __repr__(self):
        return (f"{__class__.__name__}({self.virctl!r}, {self.name!r}"
                f", {self.user!r}, {self.passwd!r}, {self.timeout})")

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.logout()

    def login(self, timeout=None, **kwargs):
        self.proc = Popen(f"{self.virctl} console {self.name} 2>&1",
                          stdin=PIPE, stdout=PIPE, shell=True, **kwargs)

        endtime = datetime.now() + timedelta(seconds=timeout or self.timeout)
        while endtime > datetime.now():
            out = self.execute_command("\n\n")
            if re.search(rf"{self.name} login:\s+?", out, re.M):
                break
            print(out)
            sleep(5)
        else:
            raise TimeoutError(-1, "Login timeout: Unable to catch login hints.\n"
                               f"self.{out}")

        out = self.execute_command(self.user)

        return self.execute_command(self.passwd)

    def logout(self):
        if self.proc:
            self.execute_command("exit\n")
            self.proc.communicate()
            self.proc = None

    def execute_command(self, command, *, timeout=None):
        if not self.proc:
            self.login(timeout)
        proc = self.proc
        proc.stdin.write(command.encode() + b"\n")
        proc.stdin.flush()
        sleep(1)
        outbytes = len(proc.stdout.peek())
        return proc.stdout.read(outbytes).decode()
