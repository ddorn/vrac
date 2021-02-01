#!/usr/bin/env python

import random
from pprint import pprint
from pathlib import Path
from collections import defaultdict, Counter

DATA = Path(__file__).parent / "data"
FR_FREQ_WORD_FILE = DATA / "fr-freq-words"
ALSA_RAW = DATA / "villages-alsaciens.txt"
PROC_ALSA = DATA / "proc-alsa"
PROC_FR = DATA / "proc-fr-letter"
SEP = "#"


def empty_occ(depth=2):
    def r(d):
        return (lambda: defaultdict(d))
    d = float
    for i in range(depth):
        d = r(d)
    return defaultdict(d)


def get(occ, *indices):
    """Get the value in the occurence table recursively"""
    for i in indices:
        occ = occ[i]
    return occ

def set(occ, value, *indices):
    """Set a value in the occurence table recursively"""
    if len(indices) == 1:
        occ[indices[0]] = value
        return

    *rest, last = indices
    d = get(occ, *rest)
    d[last] = value

def get_depth(occ):
    if isinstance(occ, float):
        return -1
    return 1 + get_depth(occ[next(iter(occ))])


def preproc_freq_words(path):
    # occ[first token][second token][third token] = prob of 3rd token after 1st and 2nd
    occ = empty_occ()
    text = path.read_text()
    lines = text.splitlines()
    for line in lines:
        count, _, word = line.partition(" ")
        count = float(count)

        for c in word:
            if 0xa0 > ord(c) > ord("z"):
                break
            if SEP in word:
                print(word)
                break
            if not c.isalpha() and not c in "-'":
                print(word)
                break
        else:
            a = b = " "
            for c in word.lower() + " ":
                occ[a][b][c] += count
                a, b = b, c

    return occ


def preproc_prov(path):
    occ = empty_occ(1)



def save_occ(occ, path):
    """Save a multi-dimensional occurence table to a file."""
    with open(path, "w") as f:
        _save_occ(occ, f)

def _save_occ(occ, f, *prefix):
    """Recursive helper function to write to the file."""
    for token, oc in occ.items():
        if isinstance(oc, float):
            print(*prefix, token, oc, file=f, sep=SEP)
        else:
            _save_occ(oc, f, *prefix, token)


def load_preproc(path):
    """Load a occurence table from a file."""
    lines = path.read_text().splitlines()
    depth = lines[0].count("#") - 1
    occ = empty_occ(depth)
    for line in lines:
        *prefix, freq = line.split(SEP)
        freq = float(freq)
        set(occ, freq, *prefix)

    return occ


def gen(occ):
    depth = get_depth(occ)

    word = [" "] * depth
    while word[-1] != " " or len(word) == depth:
        probas = get(occ, *word[-depth:])
        occ_total = sum(probas.values())
        occ_cum = 0
        cutoff = random.random() * occ_total
        for w, p in probas.items():
            occ_cum += p
            if occ_cum >= cutoff:
                word.append(w)
                break

    word = word[depth:-1]

    return word


def main():
    occ = preproc_freq_words(ALSA_RAW)
    save_occ(occ, PROC_ALSA)


    o = load_preproc(PROC_ALSA)
    w = gen(occ)
    print("".join(w))


if __name__ == "__main__":
    main()
