#!/usr/bin/env python3

# a tree (like a suffix tree) structure:
# # 0--AT--1
# \--B--2--'ANANA'
#       \--'Z'
#
# represented as:
# 0:[[1,2],['AT','B']]
# 2:[[3,4],['ANANA','Z']]
#
# vertex:[[vertexes],[edges]]
#
# note: 1.compress (classical suffix tree compression)
#       2.add a counter, how much the node (ngram) was matched while
#       filling the tree  (will help to calculate next char probability
#       in a markov chain) The nodes can be used to build a database
#       with ngrams and treir probabilities

import pickle
import unittest
import os
import sys
from str_func import str_slices
#from bisect import bisect, insort


class STree(dict):  # a unidirectional tree
    # a class variables, "constants":
    vertex_index = 0  # vertex
    edge_index = 1    # value on edge

    # object variables:
    _max_idx = 0
    _tolerance = 0
    _strict = False  # strict matching
                     # False: report a match when the first part of the word
                     # is matched
                     # True: when the whole word is matched
                     # while filling is set to False

    _updating = True  # the mode to fill a tree (populate)
                      # else - for search
    _cmp_chr = None

    @staticmethod
    def _cmp_chr_simple(chr1, chr2, i_char=None):
        return chr1 == chr2

    def __init__(self):
        dict.__init__(self)
        self._cmp_chr = STree._cmp_chr_simple
    # self[0] =[[],[]]
    # self._addNewVertex(0, strs[0])
    # for s in strs[1:]:
    #     [a for a in self.travel(s, 0, 0, 0, 0)]


    #
    # fn - a file name, without an '.txt' extension to load values from.
    # file should be located in cwd,
    # and words should be newline ("\n") separated
    # load a serialized fn +'.pickle' if exists or in contrary is saves
    # an seriazed object
    #
    @staticmethod
    def load_dict(fn, br_chr="\n", max_l=None):
        if os.path.isfile('./%s.pickle' % fn):
            with open('./%s.pickle' % fn, 'rb') as f:
                t = pickle.load(f)
        else:
            t = STree()
            print('Preparing dictionary cache')
            sys.stdout.flush()
            with open('./%s' % fn) as lines:
                # the dictionary elements are limited with max password length
                [t.add_str(line.strip() + br_chr) for line in lines
                    if max_l is None or len(line.strip()) <= max_l]

            # attempt to save the serialized object
            with open('./%s.pickle' % fn, 'wb') as f:
                pickle.dump(t, f, pickle.HIGHEST_PROTOCOL)
            # note: among the pickle store a hash for consistency check
            print('Done.')
        return t  # a tree object

    #
    # frequenlty used patterns in passwords:
    # 1. first char is capitalised
    # 2. substitution @ -> a, etc
    pswd_chr_subst = {'$': 's',  # popular substitutions in passwords  1:N
                      '@': 'a',
                      '6': 'b',
                      '3': 'e',
                      '5': 's',
                      '!': 'i',
                      '0': 'o'}
                    # '2':'to', '4':'for', suitable for phrases

    @staticmethod
    def passwd_cmp(chr_dict,    # from dictionary
                   chr_passwd,  # from a password
                   i_char):     # chr positional index in a password

        if(chr_passwd == chr_dict):
            res = True
        elif chr_passwd in STree.pswd_chr_subst:
            res = STree.pswd_chr_subst[chr_passwd] == chr_dict
        elif i_char == 0:
            res = chr_passwd.lower() == chr_dict.lower()
        else:
            res = False
        return res

    #
    # returns first N chars matched as a list
    #
    def add_str(self, s):
        self._updating = True
        self._strict = False
        if len(self) == 0:
            self[0] = [[], []]
            self._addNewVertex(0, s)
            return [0]
        else:
            self.tolerance = 0
            return list(self.travel(s, 0, 0, 0, 0))
    #
    # returns a generator with matched lenghts (for tolerance == 0 only
    # one match should be reported)
    # only full matches are returned when strict == True
    #
    def match_str(self,
                  s,
                  strict=True,
                  cmp_func=None,
                  tolerance=0):
        if len(self) == 0:
            raise ValueError('Tree is not filled issue #4')
        self._tolerance = tolerance  # an object "constant" for comparison
        self._updating = False
        self._strict = strict
        if cmp_func:
            self._cmp_chr = cmp_func
        return self.travel(s, 0, 0, 0, tolerance)

    #
    # returns a list of a offsets[0] and matches_length[1]
    #
    def match_str_slices(self,
                         slices,
                         sequence=False,
                         strict=True,
                         cmp_func=None):
        res = []
        ignore_same_match_c = 0
        minl = min([len(sl) for sl in slices])  # min. match accepted
        for i, s in enumerate(slices):  # i is an offset in a password
            m = list(self.match_str(s, strict, cmp_func))[0]
            if ignore_same_match_c > 0:
                ignore_same_match_c += -1  # next slice will match ,
                                           # when the sequence was matched
            if m >= minl:
                if sequence:
                    if m != ignore_same_match_c:
                        res += [(i, m)]
                        ignore_same_match_c = m
                        continue
                else:
                    res += [(i, m)]
        return res

    ##
    ##  returns a list of a matches and offsets
    ##
    #  def match_str_slices_t(self, slices):
    #      res = []
    #      minl = min([len(sl) for sl in slices]) # min. match accepted
    #      for i,s in enumerate(slices): # i is an offset in a password
    #          m =  max(self.match_str(s, 1)) # ideally is to process each
    #                                         # possible match separately
    #          #print('#'*13 , m,maxl)
    #          if m >= minl:
    #              res += [i, s[:m]]
    #      return res


    #
    # just a counter, should be unique and atomic in a one object
    #
    def _newVrtx(self):
        self._max_idx += 1
        return self._max_idx

    def vrtx_cnt(self):
        return self._max_idx

    # vrtx - a vertex to which add to (index)
    # value  - a char or a str

    def _addNewVertex(self,
                      vrtx,
                      value):
        nvi = self._newVrtx()  # new vertex index
        childs_vx, childs_vl = self._getVrtxAndEdges(vrtx)
        if vrtx in self:
            childs_vx.append(nvi)
            childs_vl.append(value)
        else:  # in case when a vertex has no subnodes, the vertex
               # is not in a main tree set
            s_elf[vrtx] = [[nvi], [value]]

    def _getVrtxAndEdges(self, vrtx):
        VRTX = STree.vertex_index
        EDG = STree.edge_index
        childs_vx = self[vrtx][VRTX]  # a link to a childs vertexes array
        childs_vl = self[vrtx][EDG]  # a link to a childs values array
        return childs_vx, childs_vl

    def _putNewVertexInStr(self,
                           vrtx,    # "from" vertex
                           i_chld,  # "to" child vertex index
                           i_char,  # a character index, from which it is
                                    # required to branch, should be > 0,
                                    # because a case when a fisrt char is not
                                    # equal is already covered
                           value):
        childs_vx, childs_vl = self._getVrtxAndEdges(vrtx)
        if 0 == i_char:
            raise IndexError('Main logic ussue #1')  # case should be covered
                                                     # in "travel" function

        if len(childs_vl[i_chld]) < 2:
            raise IndexError('Main logic ussue #2')  # chr should not be here

        str_left, str_right = childs_vl[i_chld][:i_char],\
                              childs_vl[i_chld][i_char:]
        childs_vl[i_chld] = str_left  # replaced the str with a left part
        chld_vx = childs_vx[i_chld]
        nvi = self._newVrtx()  # new vertex index
        childs_vx[i_chld] = nvi  # broken end looks at a new vertex
        # if str_right[0] < value:  #keep it sorted
        #    self[nvi] = [[chld_vx, self._newVrtx()],[str_right,value]]
        # else:
        self[nvi] = [[self._newVrtx(), chld_vx], [value, str_right]]
    #
    # this func settles a character or the part of the str from str[i_char:]
    # or the whole str, when nothing matched in a single iteration
    # in a whole recursive cycle it settles a whole string to a tree
    # in non-updating mode(self._updating) , just gathers matching info
    # (without a tolerance it should return exactly one match)
    #
    # word matched not fully - report matches count
    # filling a tree: tree matched not to a branch end: report matches amount
    # matching a tree:tr.matched not to a branch end: report zero match amount
    def travel(self,
               inp_str,  # an input string
               i_char,   # an index of a chr in "inp_str"
               vrtx,
               matches,
               tolerance_left):  # will be different for each recursion path

        if i_char > len(inp_str) - 1:
            raise IndexError('Main logic ussue #3')

        childs_vx, childs_vl = self._getVrtxAndEdges(vrtx)
        ch_current = inp_str[i_char]  # a character being processed
        for i, chld_val in enumerate(childs_vl):  # looking child nodes and
                                                # deeper recursive. they can
                                                # be a chr or str, better is
                                                # to store them ordered and
                                                # to use binary search
            #
            # a single char (edge)
            #
            if len(chld_val) == 1:
                if self._cmp_chr(chld_val, ch_current, i_char)\
                        or tolerance_left > 0:
                    matches += 1  # one match fixed
                    # end of the inp. string not reached
                    if childs_vx[i] in self\
                            and i_char + 1 <= len(inp_str) - 1:
                        yield from self.travel(inp_str,
                                               i_char + 1,
                                               childs_vx[i],
                                               matches,
                                               tolerance_left -
                                               (chld_val != ch_current))
                    else:  # this is the last vertex in tree
                        if self._updating:
                            childs_vl[i] += inp_str[i_char + 1:]  # safe
                        if self._strict and i_char != len(inp_str) - 1:
                        # no mismatch, but end of the inp. string not reached
                            yield 0
                            return
                        yield matches
                    if self._tolerance:
                        matches -= 1
                        continue
                    else:
                        return
            #
            # a string (edge)
            #
            if len(chld_val) > 1:
                i_vrtx_c = 0  # a local pointer to the current chr in an edge
                while i_char < len(inp_str)\
                        and (self._cmp_chr(chld_val[i_vrtx_c],
                                           inp_str[i_char],
                                           i_char))\
                        or tolerance_left > 0:

                    # when equal - go next
                    # chld_str cometh to an end, do append a str or travel,
                    # when possible
                    # not equal - is time to brach

                    matches += 1  # one match fixed

                    # it is possible to go further though a node
                    # edge string part left is more or equal a str. part left
                    if (len(chld_val) - 1) > i_vrtx_c:
                        if self._strict:
                            if len(inp_str) - 1 == i_char:  # no mismatch,
                            # but end of the string reached
                                yield 0
                                return
                        i_char += 1
                        i_vrtx_c += 1
                        tolerance_left -= (chld_val != ch_current)
                        continue  # a string is like a branch,
                                  # so we scroll the string
                    else:
                        if childs_vx[i] in self \
                                and i_char + 1 <= len(inp_str) - 1:
                            if self._strict:
                                if len(inp_str) - 1 == i_char:  # no mismatch
                                # but end of the string reached
                                    yield 0
                                    return
                            # a string come to an end we travel to childs
                            yield from self.travel(inp_str,
                                                   i_char + 1,
                                                   childs_vx[i],
                                                   matches,
                                                   tolerance_left -
                                                   (chld_val != ch_current))
                        else:
                            if self._updating:  # it it requered to append the
                                                # rest part of the str
                                childs_vl[i] += inp_str[i_char+1:]
                            yield matches
                        return
                # it is required to break a string, and do a new branch
                if i_vrtx_c > 0:
                    if self._updating:
                        if i_char > len(inp_str) - 1:
                            # end of the str. reached
                            yield matches
                            return
                        self._putNewVertexInStr(vrtx,
                                                i,
                                                i_vrtx_c,
                                                inp_str[i_char:])
                    if self._strict:
                        yield 0  # inp_str not fully matched
                    else:
                        yield matches
                    return
        #
        # nothing matching found:
        #
        if self._updating:
            self._addNewVertex(vrtx,
                               inp_str[i_char:])
        if self._tolerance:  # note: not an elegant way
            return
        if self._strict:
            yield 0
        else:
            yield matches

#
# not every case is commented, but it is easy
# to imagine which tree shoul be built and which str shoul match
#

class TestTreeMethods(unittest.TestCase):
    #
    # test correct branching
    #
    def test_tree_1(self):
      #  return
        t = STree()
        s = 'abcdefgh'
        l = len(s)
        self.assertEqual(t.add_str(s)[0], 0)  # no match
        self.assertEqual(t.vrtx_cnt(), 1)  # one vertex
        for a in range(1, 7):
        #   self.assertEqual(t.vrtx_cnt(), a)
            was_vrtx = t.vrtx_cnt()

            matches = t.add_str(s[:-a]+'z')  # the tail is cropped and replacd
                                             # with a symbol, which requires
                                             # to branch
            self.assertEqual(was_vrtx + 2, t.vrtx_cnt())  # branching happened

            self.assertEqual(len(matches), 1)  # one match
            t.add_str(s)  # intentionally, string was added before,
                          # so it should not change anything
            self.assertEqual(matches[0],
                             len(s[:-a]))  # str part matched fully
    #
    # test immutable vtrx cnt in some case
    #
    def test_tree_2(self):
        t = STree()
        s = 'abc'
        l = len(s)
        t.add_str(s)
        for a in range(1, 7):
            s += str(a)
            t.add_str(s)
        self.assertEqual(t.vrtx_cnt(), 1)  # should not branch
        self.assertEqual(t[0][1][0], s)  # checked the value

    #
    #  test correct str end checks, and some usual matches
    #
    def test_tree_3(self):
    #  a str, and expected matches amount
        str_matches = [['z', 0],
                       ['na1', 0],
                       ['na', 2],
                       ['abc', 0],
                       ['abcd', 3],
                       ['abz', 2],
                       ['abzaaa', 3],
                       ['abzaaz', 5]]
        t = STree()
        for i, s in enumerate(str_matches):
            m = t.add_str(s[0])
            self.assertEqual(m, [s[1]])  # at the same time, the length
                                         # of the matched list is checked
            if 2 == i:
                self.assertEqual(t, {0: [[1, 2], ['z', 'na1']]})
        t_expected = {0: [[1, 2, 4], ['z', 'na1', 'ab']], 4: [[6, 3],
                         ['zaa', 'cd']], 6: [[7, 5], ['z', 'a']]}
        self.assertEqual(t, t_expected)
        strict_matches = [1, 3, 0, 0, 4, 0, 6, 6]
        for i, s in enumerate(str_matches):
            m = list(t.add_str(s[0]))
            m = list(t.add_str(s[0]))
            self.assertEqual(m, [len(s[0])])  # test matches
            m = list(t.match_str(s[0]))
            self.assertEqual(m, [strict_matches[i]])  # test matches
            m = list(t.match_str(s[0], 0, False))
            self.assertEqual(m, [len(s[0])])  # test matches

        m = t.match_str('zzzzzzz', False)
        self.assertEqual(list(m)[0], 1)  # test matches
        m = t.match_str('abzaazzzz')
        self.assertEqual(list(m)[0], 0)  # test matches
        m = t.match_str('abzaazzzz', False)
        self.assertEqual(list(m)[0], 6)  # test matches

        self.assertEqual(
            list(t.match_str('abzaay'))[0], 0)  # the check in a chr node
        self.assertEqual(
            list(t.add_str('abza'))[0], 4)
        self.assertEqual(
            list(t.match_str('abza'))[0], 0)  # the check in a str node
    #
    #  test correctness of the different logic branches
    #  (some of them was tested in test#3)
    #
    def test_match_str(self):
        t = STree()
        t.add_str('a')
        self.assertEqual(list(t.match_str('a'))[0], 1)  # single
        self.assertEqual(list(t.match_str('aa'))[0], 0)  # #2 should not
        t = STree()
        t.add_str('abcde')
        self.assertEqual(list(t.match_str('abcA'))[0], 0)  # no match
        self.assertEqual(list(t.match_str('abc'))[0], 0)   # a part
        self.assertEqual(list(t.match_str('abcd'))[0], 0)  # end
        self.assertEqual(list(t.match_str('ab'))[0], 0)    # begin b
        self.assertEqual(list(t.match_str('a'))[0], 0)     # begin

    def test_chars(self):  # some special test for len
        t = STree()
        t.add_str('e')
        t.add_str('eaz')
        t.add_str('e')
        t.add_str('evv')
        t.add_str('a')
        # note: not too much flexible, the tree structure may grow
        t_expected = {0: [[2, 4], ['e', 'a']], 2: [[1, 3], ['az', 'vv']]}

        t = STree()
        t.add_str('rerere')
        self.assertEqual(list(t.match_str('reret'))[0], 0)

    def test_tolerance_chr(self):
        t = STree()
        t.add_str('a')
        expected_matches = [1]
        self.assertEqual(list(t.match_str('a', False, tolerance=1)),
                         expected_matches)

        t = STree()
        t.add_str('ab')
        t.add_str('av')
        expected_matches = [2, 2]
        self.assertEqual(list(t.match_str('as', False, tolerance=1)),
                         expected_matches)
        t = STree()
        t.add_str('abc')
        t.add_str('acd')
        t.add_str('acv')
        t.add_str('abz')
        expected_matches = [2, 2]
        self.assertEqual(list(t.match_str('as', False, tolerance=2)),
                         expected_matches)
        expected_matches = [3, 3, 3, 3]
        self.assertEqual(list(t.match_str('abc', False, tolerance=2)),
                         expected_matches)

    def test_tolerance_str(self):
        # questionable thing, then it is required to report the word,
        # found in a dictionary  then, it is required to store the word line
        # num in a dict. txt, or collect this
        # word, travelling the tree
        # t = STree()
        # t.add_str('abc')
        # print(list(t.match_str('vbc',1,False)))
        pass

    def test__passwd_cmp(self):
        str_dict = 'password'
        str_pass = 'P@$$w0rd'
        for i, ch_d in enumerate(str_dict):
            self.assertTrue(STree.passwd_cmp(ch_d, str_pass[i], i))

    @unittest.skip("excessive testing skipped")
    def test_a_tree_excessive(self):
        from random import shuffle
        with open('dictionary.txt') as lines:
            words_list = list(lines)
        shuffle(words_list)
        self.assertEqual(
            len(words_list), len(set(words_list)))  # dictionary has dupes
        t = STree()
        for i, w in enumerate(words_list):
            t.add_str(w)
            for j, w_m in enumerate(words_list):
                if j > i + 144:
                    break
                strict_m = list(t.match_str(w_m))
                non_strict_match = list(t.match_str(w_m, False))
                l = len(w_m)
                if j <= i:  # should match
                    self.assertEqual([l], strict_m,
                                     (w, w_m, i, j, t))  # wrd.should match
                    self.assertEqual([l],
                                     non_strict_match)  # should match once
                else:  # should not match
                    self.assertEqual([0], strict_m)  # word not added


if '__main__' == __name__:
    unittest.main()
