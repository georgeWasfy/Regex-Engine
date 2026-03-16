from typing import List, Tuple, Union


EPSILON_TRANSITION = None
EPSILON = 'ε'


class State:
    def __init__(self, size, name, is_accept, is_epsilon=False):
        self.transitions = [0] * size
        self.name = name
        self.is_accept = is_accept
        self.is_epsilon = is_epsilon
        
    def set_transition_vec(self, range: range, nextStateIdx: int) -> None:
        for i in range:
            self.transitions[i] = nextStateIdx 
    def __repr__(self):
        return f"State(name='{self.name}', is_accept={self.is_accept}, transitions={self.transitions})"
        
class EngineNFA:
    def __init__(self, alphabet):
        self.transitions_table = [] 
        self.alphabet = alphabet.copy()
        self.alphabet[EPSILON] = (max(alphabet.values()) if len(alphabet) > 0 else 0) + 1

    def add_state(self, name, transition: range, nextStatesIdx: Tuple[int, ...], is_accept=False, is_epsilon=False) -> None:
        new_state = State(len(self.alphabet.keys()), name, is_accept, is_epsilon)
        new_state.set_transition_vec(transition, nextStatesIdx)
        self.transitions_table.append(new_state)  
            
    def remove_accept_state(self):
        del self.transitions_table[-1]
        
    
    def insert_state(self, state: State):
        self.transitions_table.append(state)   
                

    def is_match(self, input: Union[str, List[str]]) -> bool:
        stack = [(0, self.transitions_table[0])]  # (input_index, state)
        visited = set()
        while stack:
            idx, state = stack.pop()
            key = (idx, id(state))
            if key in visited:
                continue
            visited.add(key)
            # Check if this state is accepting
            if state.is_accept and idx == len(input):
                return True

            # Determine next characters to process
            if idx < len(input):
                char = input[idx]
                if char not in self.alphabet:
                    raise ValueError(f"Invalid character: {char} is not a valid character in the defined alphabet")
                transitions = state.transitions[self.alphabet[char]]
                if isinstance(transitions, int):
                    transitions = (transitions,)
                for next_state_idx in reversed(transitions):
                    if next_state_idx != 0:
                        stack.append((idx + 1, self.transitions_table[next_state_idx]))

            # Always process epsilon transitions (do not advance idx)
            epsilon_transitions = state.transitions[self.alphabet[EPSILON]]
            print("ep trans",epsilon_transitions)
            if isinstance(epsilon_transitions, int):
                epsilon_transitions = (epsilon_transitions,)
            for next_state_idx in reversed(epsilon_transitions):
                print("next state idx", next_state_idx)
                if next_state_idx != 0:
                    stack.append((idx, self.transitions_table[next_state_idx]))

        return False
    
    def dump(self):
        max_len = 0
        for row in self.transitions_table:
            for element in row.transitions:
                element_str = str(element)
                max_len = max(max_len, len(element_str))
                
        print( ' ' * 5, end=" ")
        for i in range(len(self.transitions_table)):
            padding = ' ' * (max_len - len(str(i)))
            print(str(i) + padding, end=" ")
        print('\n')
        
        for symbol in self.alphabet.keys():
            print(f"{symbol} => ", end=" ")
            for state in self.transitions_table:
                element = str(state.transitions[self.alphabet[symbol]])
                padding = ' ' * (max_len - len(element))
                print(element + padding, end=" ")
            print('\n')
