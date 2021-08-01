# Author: Hayk Aleksanyan
# read file and tokenize into words

import os
import re

import file_reader


class SimpleTokenizer:
    def __init__(self, stop_words_file=""):
        self.file_reader = file_reader.FileReaderFromBinary()

        self.stop_words_file = stop_words_file
        self.stop_words = set()
        self.load_stop_words()

    @property
    def name(self):
        return type(self).__name__

    def load_stop_words(self):
        if self.stop_words_file != "" and os.path.exists(self.stop_words_file):
            stop_words_list = self.file_reader.read_file_into_list_of_row(self.stop_words_file)
            self.stop_words = set([w.strip() for w in stop_words_list])

    def tokenize_file(self, file_path, token_min_length=2, verbose=0):
        file_row_list = self.file_reader.read_file_into_list_of_row(file_path, verbose=verbose)

        if not file_row_list:
            return []

        str_data = " ".join(file_row_list)

        for c in {'\a', '\b', '\f', '\n', '\r', '\t'}:
            str_data = str_data.replace(c, ' ')

        reg_exp_spaces = re.compile(' {2,}')  # strips off the extra white-spaces
        reg_exp_alphanum = re.compile(r'[^\w -]')  # everything except non-alphanumeric, non-space, non-hyphen

        str_data = re.sub(reg_exp_alphanum, '', str_data)
        str_data = re.sub(reg_exp_spaces, ' ', str_data)

        str_data = str_data.strip()

        tokens = []  # the final list of Tokens to be returned
        for w in str_data.split(' '):
            w = w.strip('-')
            if len(w) >= token_min_length:
                tokens.append(w)

        if verbose:
            print('[{}] the number of tokens equals {}'.format(self.name, len(tokens)), flush=True)

        return tokens

    def group_heuristics(self, tokens, drop_stop_words=True, verbose=0):
        """
           given a raw (unprocessed) list of tokens, we apply a few crude heuristics to group some tokens together
        """

        grouped_tokens = []

        for token in tokens:
            if drop_stop_words:
                if token.lower() not in self.stop_words:
                    grouped_tokens.append(token)
            else:
                grouped_tokens.append(token)

        # 1. if a token appears both lower case and upper case, we replace the upper case version with lowercase
        token_set = set(grouped_tokens)
        for t in token_set:
            if t[0].lower() + t[1:] in token_set and t[0].upper() + t[1:] in token_set:
                w = t[0].upper() + t[1:]
                w_rep = t[0].lower() + t[1:]

                for i, token in enumerate(grouped_tokens):
                    if token == w:
                        grouped_tokens[i] = w_rep

        # 2. replacement of plurals
        token_set = set(grouped_tokens)
        for t in token_set:
            if t[-1] == 's' and t[:-1] in token_set:
                w_rep = t[:-1]
                for i, token in enumerate(grouped_tokens):
                    if token == t:
                        grouped_tokens[i] = w_rep

        if verbose:
            print("[{}] number of original tokens={}, unique={}, unique tokens after stop words check and grouping={}".
                  format(self.name, len(tokens), len(set(tokens)), len(set(grouped_tokens)), flush=True))

        return grouped_tokens

    def get_token_to_freq_sorted(self, tokens, drop_stop_words=True):
        """
          gets a list of raw tokens (strings) and returns 2 lists
          where the 1st is the grouped (unique) list of the original tokens, and the 2nd is their frequency
          returns the sorted (according to decreasing frequencies) lists
        """

        grouped_tokens = self.group_heuristics(tokens, drop_stop_words=drop_stop_words)

        token_to_freq = dict()
        for token in grouped_tokens:
            if token not in token_to_freq:
                token_to_freq[token] = 0
            token_to_freq[token] += 1

        token_to_freq_sorted = sorted(token_to_freq.items(), key=lambda p: (-p[1], p[0]))

        return {token: freq for (token, freq) in token_to_freq_sorted}
