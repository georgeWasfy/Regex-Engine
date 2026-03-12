from .nfa import EngineNFA
from .parser import pre_process_regex
from .builder import NFABuilder


class Regex:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.alphabet = {}
        self.nfa = None
    
    def _build_alphabet(self, input_str: str) -> dict:
        charset = set(self.pattern) | set(input_str)
        alphabet = {}
        idx = 0
        for char in sorted(charset):
            if char not in alphabet and char not in ('(', ')', '*', '+', '?', '|', '#', '.', '^', '$'):
                alphabet[char] = idx
                idx += 1
        return alphabet
    
    def match(self, input: str) -> bool:
        self.alphabet = self._build_alphabet(input)
        postfix_regex = pre_process_regex(self.pattern)
        builder = NFABuilder(self.alphabet, postfix_regex)
        self.nfa = builder.build_nfa()
        return self.nfa.is_match(list(input))
    
    def dump(self):
        self.nfa.dump()
