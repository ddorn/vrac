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


class Occurences:
    def __init__(self, depth=2):
        self.depth = depth
        self.occ = self._empty(depth)

    def __str__(self):
        return self._str(self.occ, 0)

    def _str(self,  occ, depth):
        s = ""
        for k, v in occ.items():
            s += "\t"*depth + k 
            if isinstance(v, (float, int)):
                s += f" {v}\n"
            else:
                s += "\n" + self._str(v, depth+1)
        return s

    @staticmethod
    def _empty(depth):
        def r(d):
            return (lambda: defaultdict(d))
        d = float
        for i in range(depth):
            d = r(d)
        return defaultdict(d)

    def __getitem__(self, key):
        """Get the value in the occurence table recursively"""
        occ = self.occ
        for i in key:
            occ = occ[i]
        return occ

    def __setitem__(self, key, value):
        """Set a value in the occurence table recursively"""
        if len(key) == 1:
            self.occ[key[0]] = value
            return

        *rest, last = key
        d = self[rest]
        d[last] = value

    def __delitem__(self, key):
        if len(key) == 1:
            del self.occ[key[0]]
        else:
            *start, last = key
            del self[start][last]
            all_empty = True
            for i in range(len(start), 1, -1):
                s = key[:i]
                if all_empty and len(self[s]) == 0:
                    *a, b = s
                    del self[a][b]
                else:
                    all_empty = False
            if all_empty and len(self[key[0],]) == 0:
                del self.occ[key[0]]

    def __iter__(self):
        return self._iter(self.occ)

    @staticmethod
    def _iter(occ, *start):
        if isinstance(occ, (float, int)):
            yield start
        else:
            for k, v in occ.items():
                yield from Occurences._iter(v, *start, k)

    def bifurcations(self, _occ=None):
        if _occ is None:
            _occ = self.occ
        if isinstance(_occ[next(iter(_occ))], float):  # depth 0
            return len(_occ) - 1
        else:
            return sum(self.bifurcations(o) for o in _occ.values())


    def save(self, file):
        """Save a multi-dimensional occurence table to an open file.

        Return the number of lines written."""

        lines = 0
        for oc in self:
            print(*oc, self[oc], file=file, sep=SEP)
            lines += 1

        return lines

    @classmethod
    def from_expressions(cls, expressions, depth=2):
        """Create an occ from a list of pair (count, expr)."""

        occ = cls(depth)
        for count, expr in expressions:
            w = [EMPTY] * depth
            for c in expr:
                occ[w][c] += count
                w.pop(0)
                w.append(c)
            # End of word
            occ[w][EMPTY] += count

        # Remove all expression that did not create branches

        for count, expr in expressions:
            w = [EMPTY] * depth
            path = [w[:]]
            for i, c in enumerate(expr):
                w.pop(0)
                w.append(c)
                path.append(w[:])
                if len(occ[w]) > 1 and i >= depth:
                    break
            else:
                for i, w in enumerate(path):
                    c = next(iter(occ[w]))
                    occ[w][c] -= count

        to_remove = []
        for k in occ:
            if occ[k] < 0.00001:
                to_remove.append(k)
        for k in to_remove:
            del occ[k]

        return occ

    @classmethod
    def load(cls, file):
        """Load a occurence table from an open file."""
        depth = file.readline().count("#") - 1
        file.seek(0)

        occ = cls(depth)
        for line in file:
            *prefix, freq = line.strip("\n").split(SEP)
            occ[prefix] = float(freq)

        return occ

    def gen(self):
        word = [EMPTY] * self.depth
        while word[-1] != EMPTY or len(word) == self.depth:
            probas = self[word[-self.depth:]]
            occ_total = sum(probas.values())
            occ_cum = 0
            cutoff = random.random() * occ_total
            for w, p in probas.items():
                occ_cum += p
                if occ_cum >= cutoff:
                    word.append(w)
                    break

        word = word[self.depth:-1]  # Remove the EMPTYs

        if all(len(t) == 1 for t in word):
            sep = ""
        else:
            sep = " "
        return sep.join(word).capitalize()


def valid_word(word):
    for c in word:
        if 0xa0 > ord(c) > ord("z") \
            or SEP in word \
            or not c.isalpha() and not c in ".,-'’!?;: ":
            return False
    return True


def preproc_words(file_, depth=2, verbose=False):
    """Create an OCC from a file with 'count word' on each line."""

    ignored = 0
    expressions = []
    for line in file_:
        count, _, word = line.partition(" ")
        count = float(count)
        word = word.strip().lower()
        if valid_word(word):
            expressions.append((count, word))
        else:
            if verbose:
                print("×", word)
            ignored += 1

    print("Ignored:", ignored)
    print("Used:", len(expressions))
    return Occurences.from_expressions(expressions, depth)


def preproc_sentences(file_, depth, verbose=False):
    """Create an OCC from a file with 'count sentence' on each line."""

    ignored = 0
    expressions = []
    for line in file_:
        count, _, sentence = line.partition(" ")
        count = float(count)
        words = sentence.lower().strip().split()
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
    return Occurences.from_expressions(expressions, depth)


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
    print("Generated with", occ.bifurcations(), "bifurcations.")

    lines = occ.save(output)
    print(lines, "lines written.")


@cli.command("gen")
@click.argument("probas", type=click.File("r"))
@click.option("-n", "--count", default=1, help="Number of words to generate")
def gen_cmd(probas, count):
    """Generate random words/sentences from a proc file."""

    occ = Occurences.load(probas)
    for i in range(count):
        print(occ.gen())


if __name__ == "__main__":
    cli()
