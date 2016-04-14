#!/usr/bin/env python3
#
# module purpose: check a password strength
# usage: ./check_pswd.py %yourpassword%
# author: mbogomaz
#

import sys
import os
from STree import STree
from str_func import *
from tokens_func import *


#
#  Configuration
#
MIN_L = 8      # min. password length
MAX_L = 32     # max. password lenght
BR_CHR = "\n"  # a word end symbol for a suffix tree, without it
               # the tree for [panama,pan] and [panama] will be the same
MIN_ENTROPY = 40
MIN_WORD_LEN_MTCH = 3
DICT_FILENAME = 'dictionary.txt'
#
# Calculate an entropy:
# 1. find tokens, assess them
# 2. assess the chars, left outside that tokens
#
# returns response code and optionally an entropy
# as a tuple:  (code, entropy)
#
def check_pass(p,          # password
               dct=None):  # dictionary (STree)

    print('Checking password: %s' % p)

    # check that we are in printable ascii:
    error = None
    char_out_of_rng = [c for c in p if 32 > ord(c) or ord(c) > 126]
    if char_out_of_rng:
        print('Characters outside the printable ascii range:',
              *char_out_of_rng)
        error = 4

    if len(p) < MIN_L:
        print('Password is too short (%s chars), \
              at least %s characters are required' % (len(p), MIN_L))
        error = 3

    if len(p) > MAX_L:
        print('Password is too long (%s chars), maximum\
               allowed are %s characters' % (len(p), MAX_L))
        error = 3

    if error:
        return error,

    #
    # starting the main logic of the password assessment:
    #
    p_tokens_nums = list(p)  # chars which are in tokens will be replaced
                             # to a number with a weight
    process_tokens('Repeats',
                   search_repeats(p, 1),   p, p_tokens_nums)
    process_tokens('Keyboard sequence',
                   search_keyboard_seq(p), p, p_tokens_nums)
    process_tokens('Sequences',
                   search_sequences(p),    p, p_tokens_nums)
    if not dct:
        dct = STree.load_dict(DICT_FILENAME, "\n")
    # case insensitive dictionary match
    process_tokens('Commonly used words',
                   search_dictionary(pswd=p.lower(),
                                     tr_dict=dct,
                                     min_l=MIN_WORD_LEN_MTCH),
                   p, p_tokens_nums)
    #
    # uncomment to find the parts with len == 5
    #
    # process_tokens('Commonly used words parts',
    #                search_dictionary(pswd = p.lower(),
    #                                  tr_dict = dct,
    #                                  min_l = 5,
    #                                  permissive = True),
    #                p, p_tokens_nums) #todo: substract the res from prev test

    e = round(calc_entropy(p_tokens_nums), 2)
    # e /= a_func(p,self_repeat(p)
    if e > MIN_ENTROPY:
        print('Password is OK, score: %.2f' % e)
        return 0, e
    else:
        print('Password is weak, score: %.2f the required is at least: %s'
              % (e, MIN_ENTROPY))
        return 2, e


class TestPasswordCheck(unittest.TestCase):

    def setUp(self):
        self.d = STree.load_dict(DICT_FILENAME, "\n")

    def test_weak_psw(self):
        with open('./psdws_weak.txt', encoding='latin-1') as lines:
            for line in lines:
                res = check_pass(line.strip(), self.d)[1]
                self.assertTrue(res < MIN_ENTROPY)

    def test_ok_psw(self):
        with open('./pswds_ok.txt', encoding='latin-1') as lines:
            for line in lines:
                res = check_pass(line.strip(), self.d)[1]
                self.assertTrue(res >= MIN_ENTROPY)


if "__main__" == __name__:
    # unittest.main()
    if(len(sys.argv) != 2):
        print('Specify a password as a one command line argument')
        exit(1)
    exit(check_pass(sys.argv[1])[0])
