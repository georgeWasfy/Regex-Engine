from .nfa import EngineNFA, EPSILON


class NFABuilder:
    def __init__(self, alphabet, postfix_regex):
        self.postfix_regex = postfix_regex
        self.alphabet = {k: v for k, v in alphabet.items() if k != EPSILON}

    def _make_nfa(self) -> EngineNFA:
        return EngineNFA(self.alphabet)

    @staticmethod
    def _shift_state(state, inc: int) -> None:
        """
        Increment every non-zero index in state.transitions by inc.
        """
        state.transitions = [
            tuple(v + inc if v != 0 else 0 for v in x)
            if isinstance(x, tuple) and len(x) > 0
            else x
            for x in state.transitions
        ]

    def _atomic(self, events):
        NFA = self._make_nfa()
        for idx, e in enumerate(events):
            NFA.add_state(f"S{idx}", range(NFA.alphabet[e], NFA.alphabet[e] + 1), (len(
                NFA.transitions_table) + 1,), False, e == EPSILON)
        NFA.add_state(f"S_final", range(0), 0, True, False)
        return NFA

    def _wildcard(self):
        NFA = self._make_nfa()
        eps_idx = NFA.alphabet[EPSILON]
        NFA.add_state("S0", range(0, eps_idx), (1,), False, False)
        NFA.add_state("S_final", range(0), 0, True, False)
        return NFA

    def _concatination(self, nfa1: EngineNFA, nfa2: EngineNFA) -> EngineNFA:
        """
        Concatenate nfa2 followed by nfa1.
        nfa1 is the right/later operand (popped from the stack first).

        Layout (two 2-state atomics → 4 states):
          [0]     S0_nfa2  (unchanged, the start)
          [1]     epsilon join state  →  nfa1_start
          [2]     S0_nfa1  (shifted by offset)
          [3]     S_final  (accept)
        """
        result = nfa2
        result.remove_accept_state()

        eps_idx = result.alphabet[EPSILON]
        nfa1_start = len(result.transitions_table) + 1

        result.add_state(
            f"S{len(result.transitions_table)}",
            range(eps_idx, eps_idx + 1),
            (nfa1_start,),
            False, True,
        )

        offset = len(result.transitions_table)

        for state in nfa1.transitions_table:
            if not state.is_accept:
                self._shift_state(state, offset)
                result.insert_state(state)

        result.add_state("S_final", range(0), 0, True, False)
        return result

    def _alternate(self, nfa1: EngineNFA, nfa2: EngineNFA) -> EngineNFA:
        """
        Alternation: nfa2 | nfa1  (nfa2 = left, nfa1 = right operand).

        Layout:
          [0]                       epsilon start → (nfa2_start, nfa1_start)
          [1 .. len(nfa2)-1]        nfa2 non-accept states  (shifted +1)
          [len(nfa2)]               nfa2 merge  →  final
          [len(nfa2)+1 ..]          nfa1 non-accept states  (shifted +nfa1_start)
          [len(nfa2)+len(nfa1)]     nfa1 merge  →  final
          [len(nfa2)+len(nfa1)+1]   S_final (accept)
        """
        union_nfa = self._make_nfa()
        eps_idx = union_nfa.alphabet[EPSILON]

        final_state_idx = len(nfa1.transitions_table) + len(nfa2.transitions_table) + 1
        nfa2_start_idx = 1
        nfa1_start_idx = len(nfa2.transitions_table) + 1

        union_nfa.add_state(
            "S0",
            range(eps_idx, eps_idx + 1),
            (nfa2_start_idx, nfa1_start_idx),
            False, True,
        )

        for state in nfa2.transitions_table:
            if not state.is_accept:
                self._shift_state(state, 1)
                union_nfa.insert_state(state)

        union_nfa.add_state(
            f"S{len(union_nfa.transitions_table)}",
            range(eps_idx, eps_idx + 1),
            (final_state_idx,),
            False, True,
        )

        for state in nfa1.transitions_table:
            if not state.is_accept:
                self._shift_state(state, nfa1_start_idx)
                union_nfa.insert_state(state)

        union_nfa.add_state(
            f"S{len(union_nfa.transitions_table)}",
            range(eps_idx, eps_idx + 1),
            (final_state_idx,),
            False, True,
        )

        union_nfa.add_state("S_final", range(0), 0, True, False)
        return union_nfa

    def _star(self, nfa: EngineNFA) -> EngineNFA:
        """
        Kleene star.

        Layout (2-state inner NFA → 4 states):
          [0]       epsilon start  →  (1, final_idx)   [enter or skip]
          [1..]     nfa body states  (shifted +1)
          [N-1]     epsilon loop   →  (1, final_idx)   [repeat or exit]
          [N]       S_final (accept)
        """
        star_nfa = self._make_nfa()
        eps_idx = star_nfa.alphabet[EPSILON]
        final_idx = len(nfa.transitions_table) + 1

        star_nfa.add_state(
            "S0",
            range(eps_idx, eps_idx + 1),
            (1, final_idx),
            False, True,
        )

        for state in nfa.transitions_table:
            if not state.is_accept:
                self._shift_state(state, 1)
                star_nfa.insert_state(state)
            else:
                star_nfa.add_state(
                    f"S{len(star_nfa.transitions_table)}",
                    range(eps_idx, eps_idx + 1),
                    (1, final_idx),
                    False, True,
                )

        star_nfa.add_state("S_final", range(0), 0, True, False)
        return star_nfa

    def build_nfa(self):
        nfas = []
        for char in self.postfix_regex:
            match char:
                case char if char.isalnum():
                    nfas.append(self._atomic([char]))

                case '#':
                    if(len(nfas) < 2):
                        raise ValueError("Append symbol must be preceded with atleast 2 symbols")
                    nfa1 = nfas.pop()  # right op
                    nfa2 = nfas.pop()  # left op
                    nfas.append(self._concatination(nfa1, nfa2))
                             
                case '|': 
                    if(len(nfas) < 2):
                        raise ValueError("Alternation symbol must be preceded with atleast 2 symbols")
                    nfa1, nfa2 = nfas.pop(), nfas.pop()
                    nfas.append(self._alternate(nfa1, nfa2))
                    
                case '*': 
                    nfa = nfas.pop()
                    nfas.append(self._star(nfa))
                    
                case '?':
                    nfa = nfas.pop()
                    nothing_nfa = self._atomic([EPSILON])
                    nfas.append(self._alternate(nfa, nothing_nfa))
                    
                case '.':
                    wildcard_nfa = self._wildcard()
                    nfas.append(wildcard_nfa)

                case _:
                    raise ValueError(f"Unkown operator: {char}")
        return nfas[0]