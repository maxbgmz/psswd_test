#!/usr/bin/env python3
#
# some functions to work with strings
#
import operator
import functools
import unittest
from math import log2

#
# returns a list with all the string parts from s[0:] to s[len(s) -a:]
# like a suffix array, but sorted by length
#
def str_slices(astr,          # a source str
               min_l=1,       # minimal slice length, will be added
                              # without a end_symb
               end_symb=''):  # a tail mark symbol
    res_list = []
    l = len(astr)
    for i in range(l-min_l + 1):
        res_list.append(astr[i:] + end_symb)
    return res_list

#
# returns a characters' range id
# as a tuple (range_id variations)
# if chr is outside the printable ascii returns -1
# note: to improve performance it is possible to create a list where ord_c
# is an index, and fill it once
# str.isalpha and etc are questionable, because they passes unicode
#
def chr_range(c):
    ord_c = ord(c)
    if ord('a') <= ord_c <= ord('z'):
        return 0 # lower case letters
    if ord('A') <= ord_c <= ord('Z'):
        return 1 # upper case letters
    if ord('0') <= ord_c <= ord('9'):
        return 2 # numbers
    if (ord(' ') <= ord_c <= ord('/')
     or ord(':') <= ord_c <= ord('@')
     or ord('[') <= ord_c <= ord('`')
     or ord('{') <= ord_c <= ord('~')):
        return 3  # special printable
                  # (punctuation) characters
    return -1
#
# variations count of the given range_id (range_id from chr_range)
#
rng_cnts = (26, 26, 10, 33)

def range_vrs_cnt(range_id):
    return rng_cnts[range_id]
#
# variations for a chr's range
#
def chr_rng_cnt(achr):
    return range_vrs_cnt(chr_range(achr))
#
# p_nt is a password without tokens, tokens are replaced with a float num
# is a list where can be character or float num which means the weight
#
def calc_entropy(p_nt):
    RPT_LIM_VAL = 15  # a constant used to fade the estimated variability
    p_ranges_nt = [0] * len(p_nt)  # additional array for calculations
    e_cnt = 1  # entropy multiplication based counter
    r_cnt = {}  # index is a count of chrs, value is a list with ranges
                # ids with that count
                # when ranges has same cnt, they shares the same entropy
    rc = [0, 0, 0, 0]  # ranges counts, index is a range id. range id is
                       # in accordance with chr_range
                       # then, updates to a
    rc_e = list(rc) # additional array for estimated counts calculus
    def est_rng_cnt(achr):
        return rc_e[chr_range(achr)]

    for el in p_nt:
        if type(el) in (float, int):
           # e_cnt * = el  # accumulating entropy
            pass
        else:
            rc[chr_range(el)] += 1  # accumulating range counters

    #
    #  initial version >
    #
    #  grouping ranges by chars count
    # for i, v in enumerate(rc):
    #     if v == 0:
    #         continue
    #     if v in r_cnt:
    #         r_cnt[v].append(i)
    #     else:
    #         r_cnt[v]=[i]
    # # r_cnt[cnt]=[1,2,3]
    # ranges_set = set()  # will grow from largest groups to lowest
    # for cnt in reversed(sorted(r_cnt)): # cnt is a count of certain chr range
    #     ranges_set.update(r_cnt[cnt])
    #     var_cnt = sum([range_vrs_cnt(v) for v in ranges_set ])# a Vn function
    #    #                                                 #(readme, section 5)
    #     for i, r in enumerate(rc):
    #         if r == cnt:
    #            rc_e[i] = var_cnt
    #
    #    #this multiplication is for the case when some ranges have same count
    #      m_all *= var_cnt  \
    #                (cnt * len(r_cnt[cnt]))
    #
    #  < initial version
    #


    #
    #  calculating estimated V for each chr range
    #      c V
    #    -------------------------------
    # id=0|a 62| a 62|     |      |     |
    # id=1|A 62| A 62| A 36|      |     |
    # id=2|1 62| 1 62| 1 36| 1 10 | 1 10|
    #    --------------------------------
    #        62    62    36    10     10  #sums
    #   62 == 26 + 26 + 10
    #   36 == 26 + 10
    #  V(id_0) = 62
    #  V(id_1) = (62 + 62 + 36 ) / 3
    #  V(id_2) = (62 + 62 + 36 + 10 + 10) / 5
    #
    #  for the case, stated upper tbl_rcs structure:
    #  [[62, 62],
    #   [62, 62, 36],
    #   [62, 62, 36, 10, 10],
    #   []]
    tbl_rcs = [[], [], [], []]
    rc_tmp = list(rc)
    for i in range(0, max(rc)):
        col_sum = 0  # sum
        ranges_involved = []
        for chr_id, cnt in enumerate(rc_tmp):
          # if c >= i:
            if cnt != 0:
                col_sum += range_vrs_cnt(chr_id)
                rc_tmp[chr_id] -= 1
                ranges_involved += [chr_id]
        for chr_id in ranges_involved:
           tbl_rcs[chr_id] += [col_sum]
    for chr_id, row in enumerate(tbl_rcs):
        if row:
            rc_ev = sum(row) / len(row)
        else:
            rc_ev = 0
        rc_e[chr_id] = rc_ev
    chr_was = 0  # for the first step will evaluate to False, so it is safe
    #
    #  v alignment, according to a position,
    #  for chrs, in the same range appearing one by one the "v" fill fade
    #
    for i, achr in enumerate(p_nt):
        if type(p_nt[i]) in (float, int):
            p_ranges_nt[i] = p_nt[i]
        else:
            v = rc_e[chr_range(achr)]
            # a repeat found, "v" will equal the mean of the "v" of the prev
            # and the v of the char itself
            if type(chr_was) not in (float, int)\
                    and chr_range(chr_was) == chr_range(achr):
                chr_rng_itself = chr_rng_cnt(achr)  # that leads to ovepricing
                                                    # for a passwords which
                                                    # are from one and only
                                                    # range, do I introduced
                                                    # RPT_LIM_VAL
                chr_rng_itself = min(chr_rng_itself, RPT_LIM_VAL)
                v = (p_ranges_nt[i - 1] - chr_rng_itself) / 2 +chr_rng_itself
                RPT_LIM_VAL
                # p_ranges_nt = e
            p_ranges_nt[i] = v
        chr_was = achr
    v_all = functools.reduce(operator.mul, p_ranges_nt, 1)
    return log2(v_all)


def self_repeat(p):
    return len(p) - len(set(p))


class Test__str_func(unittest.TestCase):

    def test__str_slices(self):

        s = '012345678'
        slices = str_slices(s, 3)
        sls_expected = ['012345678', '12345678', '2345678',
                        '345678', '45678', '5678', '678']
        self.assertEqual(slices, sls_expected)
        s = '012345678'
        slices = str_slices(s, 1, '#')
        sls_expected = ['012345678#', '12345678#', '2345678#',
                        '345678#', '45678#', '5678#', '678#', '78#', '8#']
        self.assertEqual(slices, sls_expected)

    def test__chr_range(self):

        astr = "\x07\xF0aaTB90!~"
        l_expected = [-1, -1, 0, 0, 1, 1, 2, 2, 3, 3]
        self.assertEqual(l_expected, [chr_range(s) for s in astr])

    @unittest.skip("should be updated, for a letest version with alignment")
    def test__calc_entropy(self):
        p_nt = [3.0, 3, 3, 1, 1]
        self.assertEqual(log2(27), calc_entropy(p_nt))
        # [1] addition should not change the result
        r = calc_entropy(list('12345678') + [1])
        self.assertEqual(26.58, round(r, 2))

        r = calc_entropy(list('6783zgth'))
        self.assertEqual(41.36, round(r, 2))

        r = calc_entropy(list("56cgHJ#("))
        self.assertEqual(52.56, round(r, 2))

        r = calc_entropy(list("abZZZAAAZZZFFFDDD"))
        self.assertEqual(81.91, round(r, 2))

        r = calc_entropy(list("abcZZZZ0101"))
        r_expected = log2((36 ** 4) * (36 ** 4) * (62 ** 3))
        self.assertEqual(round(r_expected, 7), round(r, 7))

if '__main__' == __name__:
    unittest.main()
