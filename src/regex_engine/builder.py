from .nfa import EngineNFA, EPSILON


class NFABuilder:
    def __init__(self, alphabet, postfix_regex):
        self.postfix_regex = postfix_regex      
        self.alphabet = alphabet
        
    def _atomic(self,events):
        NFA = EngineNFA(self.alphabet)
        for idx, e in enumerate(events):
            NFA.add_state(f"S{idx}", range(NFA.alphabet[e], NFA.alphabet[e] + 1), (len(
                NFA.transitions_table) + 1,), False, e == EPSILON)
        NFA.add_state(f"S_final", range(0), 0, True, False)
        return NFA
    
    def _wildcard(self):
        NFA = EngineNFA(self.alphabet)
        NFA.add_state(f"S{0}", range(0, len(NFA.alphabet.keys())), (len(
                NFA.transitions_table) + 1,), False, False)
        NFA.add_state(f"S_final", range(0), 0, True, False)
        return NFA
    
    def _concatination(self, nfa1: EngineNFA, nfa2: EngineNFA) -> EngineNFA:
        nfa2.remove_accept_state()
        for i in range(len(nfa1.transitions_table)):
            if not nfa1.transitions_table[i].is_accept:
                new_state = nfa2.increment_state_by(nfa1.transitions_table[i], len(nfa2.transitions_table) + i)
                nfa2.insert_state(new_state)
        nfa2.add_state(f"S_final", range(0), 0, True, False)
        return nfa2
    
    def _alternate(self, nfa1: EngineNFA, nfa2: EngineNFA) -> EngineNFA:
        union_nfa = EngineNFA(self.alphabet)
        final_state_idx = len(nfa1.transitions_table) + len(nfa2.transitions_table) + 1
        expsilon_idx = union_nfa.alphabet[EPSILON]
        nfa1_start_idx, nfa2_start_idx = len(nfa2.transitions_table) + 1, 1
        
        union_nfa.add_state(f"S{0}", range(expsilon_idx, expsilon_idx + 1), 
                            (nfa2_start_idx, nfa1_start_idx), False, True)
        
        for i in range(len(nfa2.transitions_table)):
            if not nfa2.transitions_table[i].is_accept:
                new_state = union_nfa.increment_state_by(nfa2.transitions_table[i],1)
                union_nfa.insert_state(new_state)
            
        union_nfa.add_state(f"S{len(union_nfa.transitions_table)}", range(expsilon_idx, expsilon_idx + 1), 
                            (final_state_idx,), False, True)
        
        for i in range(len(nfa1.transitions_table)):
            if not nfa1.transitions_table[i].is_accept:
                new_state = union_nfa.increment_state_by(nfa1.transitions_table[i], nfa1_start_idx)
                union_nfa.insert_state(new_state)
                
        union_nfa.add_state(f"S{len(union_nfa.transitions_table)}", range(expsilon_idx, expsilon_idx + 1), 
                            (final_state_idx,), False, True)
            
        union_nfa.add_state(f"S_final", range(0), 0, True, False)
        return union_nfa
    
    def _star(self, nfa: EngineNFA) -> EngineNFA:
        star_nfa = EngineNFA(self.alphabet)
        expsilon_idx = star_nfa.alphabet[EPSILON]
        star_nfa.add_state(f"S{0}", range(expsilon_idx, expsilon_idx + 1), 
                            (1,len(nfa.transitions_table) + 1), False, True)
        for i in range(len(nfa.transitions_table)):
            if not nfa.transitions_table[i].is_accept:
                new_state = star_nfa.increment_state_by(nfa.transitions_table[i],1)
                star_nfa.insert_state(new_state)
            else:
                star_nfa.add_state(f"S{i}", range(expsilon_idx, expsilon_idx + 1), 
                            (1,len(nfa.transitions_table) + 1), False, True)
        star_nfa.add_state(f"S_final", range(0), 0, True, False)
        return star_nfa
    
    def build_nfa(self):
        nfas = []
        for char in self.postfix_regex:
            match char:
                case char if char.isalnum():
                    char_nfa = self._atomic([char])
                    nfas.append(char_nfa)
                    
                case '#':
                    if(len(nfas) < 2):
                        raise ValueError("Append symbol must be preceded with atleast 2 symbols")
                    nfa1 = nfas.pop()
                    nfa2 = nfas.pop()
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
