import pytest
from regex_engine.nfa import State, EngineNFA, EPSILON

# NOTE: The Epsilon always have index greater than last alphabet by one
class TestState:
    def test_state_creation(self):
        alphabet_size = 3
        state = State(alphabet_size, "S0", is_accept=False)
        assert state.name == "S0"
        assert state.is_accept is False
        assert len(state.transitions) == alphabet_size

    def test_state_with_epsilon_flag(self):
        state = State(3, "S0", is_accept=False, is_epsilon=True)
        assert state.is_epsilon is True

    def test_set_transition_vec(self):
        alphabet = {'a': 0, 'b': 1, EPSILON: 2}
        state = State(len(alphabet), "S0", is_accept=False)
        state.set_transition_vec(range(0, 1), (1,))
        # transitions should be exactly what set_transition_vec sets
        assert state.transitions[0] == (1,)


class TestEngineNFA:
    def test_nfa_creation(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        assert len(nfa.transitions_table) == 0
        assert EPSILON in nfa.alphabet

    def test_add_state(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        assert len(nfa.transitions_table) == 1

    def test_add_accept_state(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,), is_accept=True)
        assert nfa.transitions_table[0].is_accept is True

    def test_remove_accept_state(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(0, 1), (2,), is_accept=True)
        assert len(nfa.transitions_table) == 2
        nfa.remove_accept_state()
        assert len(nfa.transitions_table) == 1

    def test_increment_state_name(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        state = State(len(alphabet), "S5", is_accept=False)
        incremented = nfa.increment_state_by(state, 2)
        assert incremented.name == "S7"

    def test_increment_state_transitions(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        state = State(len(alphabet), "S0", is_accept=False)
        state.set_transition_vec(range(0, 1), (1,))
        incremented = nfa.increment_state_by(state, 2)
        assert incremented.transitions[0] == (3,)


class TestEngineNFAIsMatch:
    def test_exact_match(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        # NFA: a -> b -> accept
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(1, 2), (2,))
        nfa.add_state("S2", range(0), 0, is_accept=True)
        assert nfa.is_match(['a', 'b']) is True

    def test_no_match(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(1, 2), (2,))
        nfa.add_state("S2", range(0), 0, is_accept=True)
        assert nfa.is_match(['a', 'a']) is False

    def test_empty_input_no_accept(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        # NFA with accept only after consuming 'a'
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(0), 0, is_accept=True)
        assert nfa.is_match([]) is False

    def test_empty_string_accept(self):
        alphabet = {}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0), 0, is_accept=True)
        assert nfa.is_match([]) is True

    def test_invalid_character_raises(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(0), 0, is_accept=True)
        with pytest.raises(ValueError, match="Invalid character"):
            nfa.is_match(['b'])

    def test_partial_match_not_accepted(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        # NFA: a -> a -> accept
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(0, 1), (2,))
        nfa.add_state("S2", range(0), 0, is_accept=True)
        assert nfa.is_match(['a']) is False

    def test_epsilon_transition_accept(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        # S0 --ε--> S1 (accept)
        nfa.add_state("S0", range(1, 2), (1,), is_epsilon=True)
        nfa.add_state("S1", range(0), 0, is_accept=True)
        assert nfa.is_match([]) is True

    def test_alternation(self):
        alphabet = {'a': 0, 'b': 1, 'c': 2}
        nfa = EngineNFA(alphabet)
        # Simulate a|b NFA manually
        # S0 --a--> S1
        # S0 --b--> S1
        # S1 accept
        nfa.add_state("S0", range(0, 2), (1,))
        nfa.add_state("S1", range(0, 0), 0, is_accept=True)

        assert nfa.is_match(['a']) is True
        assert nfa.is_match(['b']) is True
        assert nfa.is_match(['c']) is False

    def test_concatenation(self):
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        # NFA: a -> b -> accept
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(1, 2), (2,))
        nfa.add_state("S2", range(0), 0, is_accept=True)
        assert nfa.is_match(['a', 'b']) is True
        assert nfa.is_match(['b', 'a']) is False

    def test_plus_simulation(self):
        alphabet = {'a': 0}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(0, 1), (1,), is_accept=True)
        assert nfa.is_match(['a']) is True
        assert nfa.is_match(['a', 'a', 'a']) is True

    def test_complex_epsilon_and_concat(self):
        # NFA: a -> ε -> b -> accept
        alphabet = {'a': 0, 'b': 1}
        nfa = EngineNFA(alphabet)
        nfa.add_state("S0", range(0, 1), (1,))
        nfa.add_state("S1", range(2), (2,), is_epsilon=True)
        nfa.add_state("S2", range(0), 0, is_accept=True)
        assert nfa.is_match(['a', 'b']) is True
        assert nfa.is_match(['a']) is False