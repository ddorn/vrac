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
EMPTY = "%"


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


def bifurcations(occ):
    if isinstance(occ[next(iter(occ))], float):  # depth 0
        return len(occ) - 1
    else:
        return sum(bifurcations(o) for o in occ.values())

def valid_word(word):
    for c in word:
        if 0xa0 > ord(c) > ord("z") \
            or SEP in word \
            or not c.isalpha() and not c in ".,-'’!?;: ":
            return False
    return True


def preproc(expressions, depth=2):
    # occ[first token][second token][third token] = prob of 3rd token after 1st and 2nd
    occ = empty_occ(depth)
    for count, expr in expressions:
        w = [EMPTY] * depth
        for c in expr:
            probas = get(occ, *w)
            probas[c] += count
            w.pop(0)
            w.append(c)
        # End of word
        probas = get(occ, *w)
        probas[EMPTY] += count

    return occ



def preproc_words(file_, depth=2, verbose=False):
    # occ[first token][second token][third token] = prob of 3rd token after 1st and 2nd
    ignored = 0
    expressions = []
    for line in file_:
        count, _, word = line.partition(" ")
        count = float(count)
        word = word.strip()
        if valid_word(word):
            expressions.append((count, word))
        else:
            if verbose:
                print("×", word)
            ignored += 1

    print("Ignored:", ignored)
    print("Used:", len(expressions))
    return preproc(expressions, depth)


def preproc_sentences(file_, depth, verbose=False):
    ignored = 0
    expressions = []
    for line in file_:
        count, _, sentence = line.partition(" ")
        count = float(count)
        words = sentence.strip().split()
        for word in words:
            if not valid_word(word):
                ignored += 1
                if verbose:
                    print("×", sentence.strip(), "=>", word)
                break
        else:
            expressions.append((count, words))

    print("Ignored:", ignored)
    print("Used:", len(expressions))
    return preproc(expressions, depth)


def save_occ(occ, file, *_prefix):
    """Save a multi-dimensional occurence table to an open file.

    Return the number of lines written."""

    lines = 0
    for token, oc in occ.items():
        if isinstance(oc, float):
            print(*_prefix, token, oc, file=file, sep=SEP)
            lines += 1
        else:
            lines += save_occ(oc, file, *_prefix, token)

    return lines


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

    word = [EMPTY] * depth
    while word[-1] != EMPTY or len(word) == depth:
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
@click.option("-d", "--depth", default=2, help="Number of previous tokens that influence the next.")
@click.option("-S", "--sentences", is_flag=True, default=False, help="Generate sentences instead of words")
@click.option('-v', '--verbose', is_flag=True)
def proc(input, output, depth, sentences, verbose):
    """Process a file with word frequencies for the generate command.

    Each line must be in the format 'FREQUENCY WORD'.
    The frequency the ponderation for a given word."""

    if sentences:
        occ = preproc_sentences(input, depth, verbose)
    else:
        occ = preproc_words(input, depth, verbose)
    print("Generated with", bifurcations(occ), "bifurcations.")

    lines = save_occ(occ, output)
    print(lines, "lines written.")


@cli.command("gen")
@click.argument("probas", type=click.File("r"))
@click.option("-n", "--count", default=1, help="Number of words to generate")
def gen_cmd(probas, count):
    """Generate random words/sentences from a proc file."""

    occ = load_preproc(probas)
    for i in range(count):
        w = gen(occ)
        if all(len(t) == 1 for t in w):
            sep = ""
        else:
            sep = " "
        print(sep.join(w).capitalize())


if __name__ == "__main__":
    cli()
