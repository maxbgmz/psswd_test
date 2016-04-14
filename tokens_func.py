#!/usr/bin/env python3

import unittest
from operator import itemgetter
from STree import STree
from str_func import str_slices

TOKEN_CHR0_WEIGHT = 2   # first char weight todo: should be adaptive
TOKEN_CHR_WEIGHT = 1.2  # all others chars weight

#
# 1. inform a user, what was found and where
# 2. fill p_tokens_markers with numbers
#
# todo: add a possibility to process p[::2], p[1::2]
#
def process_tokens(name,               # the token name
                   lst,                # a list of where found and its length
                   pswd,               # a password
                   p_tokens_markers):  # a list to replace chrs to weights
    if len(lst) == 0:
        return
    print(name)
    spaces = ' '*4  # identation
    lst = sorted(lst, key=itemgetter(1))  # note: this sorting is done to make
                                          # larger tokens overlap smaller,that
                                          # is better than nothing, but better
                                          # is to consider a smaller as some
                                          # v. substraction
    for l in lst:
        offset, length = l[0], l[1]
        for i, v in enumerate(p_tokens_markers):
            if i >= offset and i < (offset + length):
                if i == offset:
                    p_tokens_markers[i] = TOKEN_CHR0_WEIGHT
                if i > offset:
                    p_tokens_markers[i] = TOKEN_CHR_WEIGHT
        print('%sAt place:%s found: %s'
             % (spaces,
                offset + 1,  # offset, human readable
                pswd[offset:offset + length]))  # value
#
# returns [[offset,length],..]
#
def search_dictionary(pswd,       # a password
                      tr_dict,    # STree dictionary
                      min_l=3,  # minimum word len, to consider
                      stop_chr="\n",  # tail chr (terminator)
                      permissive=False):  # report a partial matches
    sls = str_slices(pswd.lower(), min_l)
    dict_result = tr_dict.match_str_slices(sls,
                                           sequence=False,
                                           strict=False,
                                           cmp_func=STree.passwd_cmp)
    if permissive:
        return dict_result
    dict_full_matches = []
    for s in dict_result:
        wrd_matched = pswd[s[0]:s[0] + s[1]]
        for l in range(len(wrd_matched), min_l - 1, -1):
            wrd = wrd_matched[0:l] + stop_chr
            if list(tr_dict.match_str(wrd,
                                      strict=True,
                                      cmp_func=STree.passwd_cmp))[0] > 0:
                dict_full_matches += [(s[0], l)]
                break  # a match with a max len found
    return dict_full_matches
#
# should return all self-repeats
# returns [[offset,length],..]
# for example:
#   for 12nnn3az4nn56nn78az
#       0  3 5   9     5
# return [[3,2],[9,2],[13,2],[17,2]]
# actually, returns tuples
#
def search_repeats(pswd, min_repeat_len):
    tr = STree()
    l = len(pswd)
    mi = []  # contains tuples of the matched index and it length
    ignore_same_match_c = 0  # todo: not DRY with match_str_slices

    for i in range(l):
        p_part = pswd[i:]
        match = tr.add_str(p_part)[0]
        if ignore_same_match_c > 0:
            ignore_same_match_c += -1  # next slice will match
                                       # when the sequence was matched
        if match >= min_repeat_len:
            if match != ignore_same_match_c:
                mi += [(i, match)]
                ignore_same_match_c = match
    return mi

#
# two sequences func use this constant:
# note: to a congig:
MIN_SEQ_LEN = 3  # minimal sequence length that will match
#
# each keyboard row (r1 = qwert.. , r2 = asdf.. ...)
# and a column (c0 = qaz c1 = wsx ..)
# returns [[offset,length],..]
#
def search_keyboard_seq(pswd):
    # target is to calc three continued steps on a one graph,
    # 'q':['w'], 'w':['q','e'], 'e':['w','r'], ......
    #def process_str_to_graph(s):
    #    l = len(s)
    #    g = {}
    #    for i, k in enumerate(s):
    #        if 0 == i:
    #            g[k]=[s[i+1]]
    #        elif i == l - 1:
    #            g[k]=[s[i-1]]
    #        else:
    #            g[k]=[s[i-1], s[i+1]]
    #    return g

    # todo: add other layouts
    # numbers are already covered, zero not
    # in place, but it does not make great difference
    rows = ['!@#$%^&*()_+',
            'qwertyuiop[]',
            'asdfghjkl;\'\\',
            'zxcvbnm,./']
    cols = []
    for i in range(len(rows[0])):
        s = ''
        for r in rows:
            if i < len(r) - 1:
                s += r[i]
        cols += [s] + [s[::-1]]  # note: probably among qaz,
                                 # zsw or zse is also suitable
    rows += [r[::-1] for r in rows]  # + reversed
    tr = STree()
    for seq in rows + cols:  # an "set" sum
        slices = str_slices(seq, MIN_SEQ_LEN)
        [tr.add_str(s) for s in slices]
    return tr.match_str_slices(str_slices(pswd.lower(), MIN_SEQ_LEN),
                               True,  # sequence
                               False) # strict
#
# searches for a  a-z, A-Z, 0-9 sequences
# returns [[offset,length],..]
#
def search_sequences(pswd):
    seqs = [''.join([chr(a) for a in range(ord('a'), ord('z') + 1)]),
            ''.join([chr(a) for a in range(ord('A'), ord('Z') + 1)]),
            ''.join([chr(a) for a in range(ord('0'), ord('9') + 1)])]
    tr = STree()
    for seq in seqs:
        slices = str_slices(seq, MIN_SEQ_LEN)
        slices_reverted = str_slices(seq[::-1], MIN_SEQ_LEN)
        [tr.add_str(s) for s in slices + slices_reverted]
    return tr.match_str_slices(str_slices(pswd, MIN_SEQ_LEN),
                               True,   # sequence
                               False)  # strict

#
# works ok with l > 8 , but does not appreciate completely the self-match %
#
#def self_matches(p):
#    t = STree()
#    l = len(p)
#    n_all = (l / 2) * (l - 1) # a progression sum, except the first
#    n_matched = 0
#    matches_idxs = []
#    for i in range(l):
#        p_part = p[i:]
#        matches = t.add_str(p_part)[0]
#        if matches > 0 :
#            n_matched += matches
#            matches_idxs += [i]
#
#    percent = n_matched / n_all
#    return percent, matches_idxs

#
# good passwors has lower and upper case letters,
#  numbers and a special symbols
#
# MIN_PERCENT_ACCEPTED = .25  # a percent of chars from certain range in
#                             # a password
#                             # for simplification, is same for each range.
#
#def check_range(p):
#      r_name = ['lower case letters',
#             'upper case letters',
#             'numbers',
#             'special characters']
#   def rng(c):
#       if   ord('a') <= ord(c) <= ord('z'): return 0;
#       elif ord('A') <= ord(c) <= ord('Z'): return 1;
#       elif ord('0') <= ord(c) <= ord('9'): return 2
#       else: return 3
#   rc = [0,0,0,0] # ranges counters
#   for c in p:
#       rc[rng(c)] += 1
#   for i, v in enumerate(rc):
#       if v/check_pass.MIN_L < MIN_PERCENT_ACCEPTED:
# note: I am not asked to suggest
#           yield '%s %s(%.2f%%) \
#               try to add some' % (('No', 'Not enough')[v>0],
#                               r_name[i],
#                               v/check_pass.MIN_L *100) # percents per ranges


class Test__tokens_func(unittest.TestCase):

    def test_search_sequences(self):
        r = search_sequences('rtz123456789')
        self.assertEqual(r, [(3, 9)])
        r = search_sequences('23456789')
        self.assertEqual(r, [(0, 8)])

    def test_search_keyb(self):
        r = search_keyboard_seq('ghjkl')
        self.assertEqual(r, [(0, 5)])
        r = search_keyboard_seq('8ghjkl')
        self.assertEqual(r, [(1, 5)])

    def test_search_repeats(self):
        r = search_repeats('ophrr', 1)
        self.assertEqual(r, [(4, 1)])
        r = search_repeats('olivelive', 1)
        self.assertEqual(r, [(5, 4)])

    def test_search_dict(self):
        apasswd = 'abracadabra'
        dict_words = ['abracad', 'cadabra']
        t = STree()
        t.add_str(dict_words[0])
        t.add_str(dict_words[1])

        r = search_dictionary(apasswd, t)
        self.assertEqual(r, [(0, 7), (4, 7)])


if '__main__' == __name__:
    unittest.main()
