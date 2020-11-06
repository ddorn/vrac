import os
from time import sleep, time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from collections import defaultdict
from operator import itemgetter
from typing import List

import click

ONE_SEC = timedelta(seconds=1)
LOG = Path(__file__).parent / "data" / "log"
LOG.touch()

logs = []


@dataclass
class LogEntry:
    start: datetime
    klass: str
    name: str
    end: datetime

    def __repr__(self):
        return f"{sec2str(self.duration)}: {self.klass} || {self.name}"

    @property
    def duration(self) -> int:
        return (self.end - self.start).total_seconds()

    def write_log(self, file=LOG, last_line=False):
        if not last_line:
            txt = "\n".join([
                "---",
                self.start.isoformat(),
                self.klass,
                self.name
            ])
        else:
            txt = self.end.isoformat()

        with open(file, "a") as f:
            f.write(txt + "\n")

    @classmethod
    def from_logfile(cls, log) -> "LogEntry":
        lines = log.splitlines()
        assert len(lines) in (3, 4), lines

        start = datetime.fromisoformat(lines[0])
        return cls(
                datetime.fromisoformat(lines[0]),
                lines[1],
                lines[2],
                start + ONE_SEC if len(lines) == 3 else datetime.fromisoformat(lines[3])
            )

    @classmethod
    def from_xprop(cls, output) -> "LogEntry":

        wm_name = ""
        wm_class = ""
        for l in output.splitlines():
            if l.startswith("WM_NAME"):
                wm_name = l
            elif l.startswith("WM_CLASS"):
                wm_class = l

        wm_name = wm_name.partition(" = ")[2][1:-1]
        wm_class = wm_class.partition(" = ")[2]

        return cls(
                datetime.now(),
                wm_class,
                wm_name,
                datetime.now() + ONE_SEC,
            )

    @classmethod
    def get_log(cls) -> "LogEntry":
        a = subprocess.check_output("xprop -id $(xdotool getwindowfocus)", shell=True, text=True)
        return cls.from_xprop(a)


class Logs(list):
    def __init__(self, *args, file=None):
        super().__init__(*args)
        self.first = True
        self.file=file

    @classmethod
    def load(cls, file=LOG):
        txt = file.read_text()
        txt = txt[4:]  # Remove the first line of ---
        if txt:
            return cls([LogEntry.from_logfile(lines)
                    for lines in txt.split("---\n") if lines], file=file)
        return cls(file=file)

    def append(self, log: LogEntry):
        if self.first:
            list.append(self, log)
            if self.file:
                log.write_log(self.file)
        else:
            last = self[-1]

            if last.name == log.name and last.klass == log.klass and abs(last.end - log.start) < ONE_SEC:
                last.end = log.end
            else:
                list.append(self, log)
                if self.file:
                    # Write last line of last log
                    last.write_log(self.file, True)
                    log.write_log(self.file)

        self.first = False

    def __del__(self):
        if self.file and not self.first:
            self[-1].write_log(self.file, True)


def categorize(log: LogEntry) -> str:
    CODE = "Coding"
    CHAT = "Chat"
    ASSIST = "Assistanat"
    MOOC = "MOOCs"
    CQFD = "CQFD"
    EPFL = "EPFL"
    AFK = "AFK"
    CHILL = "Chill"
    TIMETRACK = "Time tracking"
    NIXOS = "NixOs"
    WONTFIX = "Wont fix"
    ADMIN = "Administratif"

    # Categorizing vim uses
    if log.name == "nvim":
        return CODE
    if "NVIM" in log.name:
        mapping = {
            "app_watch.py": TIMETRACK,
            "nixos-conf": NIXOS,
        }
        for pattern, cat in mapping.items():
            if pattern in log.name:
                return cat

    name_contains_map = {
            "Telegram": CHAT,
            "Discord": CHAT,
            "WhatsApp": CHAT,
            "chat.lama-corp.space": CHAT,
            "Courrier": CHAT,
            "aerc": CHAT,

            "logement": ADMIN,
            "FMEL": ADMIN,

            "Mooc": MOOC,
            "Coursera": MOOC,
            "predproie.cc": MOOC,
            "biblio.cc": MOOC,

            "Google Drive": CQFD,
            "cqfd": CQFD,
            "Agepoly": CQFD,
            "Pulls": CQFD,
            "Outlook": CQFD,
            "Association des Etudiants en Mathématiques": CQFD,

            "app_watch.py": TIMETRACK,
            "ActivityWatch": TIMETRACK,
            "ARBTT": TIMETRACK,
            "Wakatime": TIMETRACK,

            "home-manager": NIXOS,
            "nixos-conf": NIXOS,
            "Nixos": NIXOS,
            "configuration.nix": NIXOS,

            "Stack Overflow": CODE,
            "Python": CODE,

            "zoom": EPFL,
            "moodle.epfl.ch": EPFL,
            "Ex_GT_Ch": EPFL,
            "Graph_Lec": EPFL,
            "Course: ": EPFL,
            "Moodle": EPFL,
            "Kuratowski.pdf": EPFL,
            "VSCodium": EPFL,
            "wikipedia": EPFL,
            "theorem": EPFL,
            "examen": EPFL,

            "diego@maple:": WONTFIX,

            "Reddit": CHILL,
            "Youtube": CHILL,
    }

    for pattern, cat in name_contains_map.items():
        if pattern.casefold() in log.name.casefold():
            return cat


    class_contains_map = {
            "Spotify": CHILL,
            "telegram": CHAT,
            # "terminator": CODE,
    }

    for pattern, cat in class_contains_map.items():
        if pattern in log.klass:
            return cat

    wontfix = [
            "/run/current-system/sw/bin/htop",
            "Mozilla Firefox",
        ]
    for w in wontfix:
        if log.name == w:
            return WONTFIX

    if log.name == log.klass == "":
        return AFK


def sec2str(sec: int) -> str:
    sec = int(sec)
    h = sec // 3600
    m = sec // 60 % 60
    s = sec % 60

    if h:
        return "{:02}h{:02}m{:02}s".format(h,m,s)
    elif m:
        return "{:02}m{:02}s".format(m,s)
    else:
        return "{:02}s".format(s)

def show_categ(categ: dict):
    tot_time = {}
    for cat, logs in categ.items():
        tot_time[cat] = sum([l.duration for l in logs])

    tot_time["None"] = tot_time[None]
    del tot_time[None]
    del tot_time["AFK"]

    total = sum(tot_time.values())
    lines = [ (str(cat), sec2str(s), str(100*s//total))
            for cat, s in sorted(tot_time.items(), key=itemgetter(1)) ]

    pad = [ max(map(len, col)) for col in zip(*lines) ]
    print(pad)

    print()
    print("Time tracked:", sec2str(total))
    for line in lines:
        print("{:>{pad[0]}} {:<{pad[1]}} {}%".format(*line, pad=pad))


def print_group_logs(logs, only_total=False):
    groups = defaultdict(int)

    for log in logs:
        groups[log.name, log.klass] += log.duration

    if not only_total:
        for (n, cl), dur in sorted(groups.items(), key=itemgetter(1)):
            print(sec2str(dur), n, "||", cl)

    print("Total:", sec2str(sum(groups.values())))



def group_category(logs):
    categ = defaultdict(list)
    for log in logs:
        cat = categorize(log)
        categ[cat].append(log)

    return categ

@click.group()
def app_watch():
    pass


@app_watch.command()
def compress():
    global LOG

    logs = Logs.load()

    LOG = LOG.with_suffix(".compressed")

    compressed = Logs()

    for log in logs:
        compressed.append(log)

@app_watch.command()
def start():

    logs = Logs.load()

    categ = group_category(logs)
    print_group_logs(categ[None])
    show_categ(categ)

    last = time()
    while True:
        log = LogEntry.get_log()
        logs.append(log)

        cat = categorize(log)
        if not cat:
            print(logs[-1])
        categ[cat].append(log)

        time_taken = time() - last
        if time_taken >= 1:  # for instance lid closed
            time_taken = 0
            last = time()
        else:
            last += 1

        sleep(1 - time_taken)

@app_watch.command()
@click.option("--day", "-d", default=-1, help="How many days ago")
@click.option("--category", "-c", help="Search only in this category")
@click.option("--pattern", "-p", help="Should contain this pattern")
@click.option("--by-category", "-b", default=False, is_flag=True, help="Whether to print results by category")
@click.option("--total", "-t", default=False, is_flag=True, help="Print only total values, not log entries")
def query(pattern, day, category, total, by_category):
    logs = Logs.load()

    if day >= 0:
        day = datetime.now() + timedelta(days=-day)
        logs = [l for l in logs if l.start.day == day.day]

    if pattern:
        logs = [l for l in logs if pattern in l.name]

    if category:
        logs = [l for l in logs if categorize(l) == category]

    if by_category:
        categ = group_category(logs)

        if total:
            show_categ(categ)
        else:
            for cat, ls in categ.items():
                print("----", cat, "----")
                print_group_logs(ls, total)
                print()
    else:
        print_group_logs(logs, total)

@app_watch.command("list-cat")
def list_cat():
    logs = Logs.load()

    cats = set()
    for l in logs:
        cats.add(categorize(l))

    print(*cats, sep="\n")


if __name__ == "__main__":
    app_watch()
