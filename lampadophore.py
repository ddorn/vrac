#!/usr/bin/env python

import random
from pprint import pprint
from pathlib import Path
from collections import defaultdict, Counter

import click

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


def preproc_freq_words(file_, depth=2):
    # occ[first token][second token][third token] = prob of 3rd token after 1st and 2nd
    occ = empty_occ(depth)
    for line in file_:
        count, _, word = line.partition(" ")
        count = float(count)
        word = word.strip()
        for c in word:
            if 0xa0 > ord(c) > ord("z") \
                or SEP in word \
                or not c.isalpha() and not c in "-'":
                print("×", word)
                break
        else:
            w = [" "] * depth
            for c in word.lower() + " ":
                probas = get(occ, *w)
                probas[c] += count
                w.pop(0)
                w.append(c)

    return occ


def preproc_prov(path):
    occ = empty_occ(1)


def save_occ(occ, file, *_prefix):
    """Save a multi-dimensional occurence table to an open file."""

    for token, oc in occ.items():
        if isinstance(oc, float):
            print(*_prefix, token, oc, file=file, sep=SEP)
        else:
            save_occ(oc, file, *_prefix, token)


def load_preproc(file):
    """Load a occurence table from an open file."""
    depth = file.readline().count("#") - 1
    file.seek(0)

    occ = empty_occ(depth)
    for line in file:
        *prefix, freq = line.strip("\n").split(SEP)
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



@click.group()
def cli():
    pass


@cli.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("w"))
@click.option("-d", "--depth", default=2)
def proc(input, output, depth):
    """Process a file with word frequencies for the generate command.

    Each line must be in the format 'FREQUENCY WORD'.
    The frequency the ponderation for a given word."""

    occ = preproc_freq_words(input, depth)
    save_occ(occ, output)


@cli.command("gen")
@click.argument("probas", type=click.File("r"))
@click.option("-n", "--count", default=1, help="Number of words to generate")
def gen_cmd(probas, count):
    """Generate random words/sentences from a proc file."""

    occ = load_preproc(probas)
    for i in range(count):
        w = gen(occ)
        print("".join(w).title())


if __name__ == "__main__":
    cli()
