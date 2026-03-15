"""
Comprehensive test suite for NFABuilder (Thompson's Construction).

Uses only the real API from nfa.py:
  - State.transitions  : list[int | tuple], indexed by alphabet position
  - State.is_accept    : bool
  - State.is_epsilon   : bool
  - EngineNFA.transitions_table : list[State]
  - EngineNFA.alphabet          : dict[str, int]
  - EngineNFA.is_match(str)     : bool

The shared ALPHABET passed to NFABuilder includes EPSILON so callers never
have to worry about it; NFABuilder strips it internally before constructing
EngineNFA (which appends EPSILON itself at max(values)+1 = index 4).

NOTE: patterns whose *-body can be traversed entirely by epsilon transitions
(e.g. (a?)*, (a*)* ) create pure epsilon cycles in the NFA graph. The
original is_match has no cycle guard, so these patterns loop forever and are
intentionally excluded from this suite.

Run with:  pytest test_nfa_builder.py -v
"""

import pytest

from regex_engine.builder import NFABuilder
from regex_engine.nfa import EPSILON, EngineNFA


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

ALPHABET = {'a': 0, 'b': 1, 'c': 2, 'd': 3, EPSILON: 4}


def build(postfix: str) -> EngineNFA:
    return NFABuilder(ALPHABET, postfix).build_nfa()


def accepts(postfix: str, string: str) -> bool:
    return build(postfix).is_match(string)


def eps_idx(nfa: EngineNFA) -> int:
    return nfa.alphabet[EPSILON]


def char_trans(state, nfa: EngineNFA, char: str):
    return state.transitions[nfa.alphabet[char]]


def eps_trans(state, nfa: EngineNFA):
    return state.transitions[eps_idx(nfa)]


def all_targets(value) -> list:
    """Normalise a raw transition value (int or tuple) to a list of non-zero targets."""
    if isinstance(value, tuple):
        return [v for v in value if v != 0]
    return [value] if value != 0 else []


# ===========================================================================
# 1.  STRUCTURAL TESTS — white-box inspection of the transition table
# ===========================================================================

class TestAtomicNFA:
    """_atomic(['x']): minimal 2-state NFA that consumes exactly one character."""

    def test_exactly_two_states(self):
        assert len(build('a').transitions_table) == 2

    def test_first_state_not_accept(self):
        assert not build('a').transitions_table[0].is_accept

    def test_last_state_is_accept(self):
        assert build('a').transitions_table[-1].is_accept

    def test_first_state_not_epsilon(self):
        assert not build('a').transitions_table[0].is_epsilon

    def test_accept_state_all_zero_transitions(self):
        nfa = build('a')
        assert all(t == 0 for t in nfa.transitions_table[-1].transitions)

    def test_s0_fires_on_correct_char(self):
        nfa = build('a')
        assert all_targets(char_trans(nfa.transitions_table[0], nfa, 'a')) == [1]

    def test_s0_does_not_fire_on_other_char(self):
        nfa = build('a')
        assert char_trans(nfa.transitions_table[0], nfa, 'b') == 0

    def test_s0_has_no_epsilon_transition(self):
        nfa = build('a')
        assert eps_trans(nfa.transitions_table[0], nfa) == 0

    def test_epsilon_atomic_marks_is_epsilon(self):
        nfa = NFABuilder(ALPHABET, '')._atomic([EPSILON])
        assert nfa.transitions_table[0].is_epsilon

    def test_epsilon_atomic_transitions_on_epsilon_slot(self):
        nfa = NFABuilder(ALPHABET, '')._atomic([EPSILON])
        assert all_targets(eps_trans(nfa.transitions_table[0], nfa)) == [1]

    def test_each_char_has_independent_atomic(self):
        for ch in 'abcd':
            nfa = build(ch)
            for other in 'abcd':
                if other != ch:
                    assert char_trans(nfa.transitions_table[0], nfa, other) == 0


class TestWildcardNFA:
    """_wildcard(): 2-state NFA matching any single non-epsilon symbol."""

    def test_exactly_two_states(self):
        assert len(build('.').transitions_table) == 2

    def test_first_state_not_accept(self):
        assert not build('.').transitions_table[0].is_accept

    def test_last_state_is_accept(self):
        assert build('.').transitions_table[-1].is_accept

    def test_covers_every_real_symbol_index(self):
        nfa = build('.')
        ei = eps_idx(nfa)
        s0 = nfa.transitions_table[0]
        for i in range(0, ei):
            assert all_targets(s0.transitions[i]) == [1], (
                f"Wildcard must fire at alphabet index {i}"
            )

    def test_does_not_fire_on_epsilon_slot(self):
        nfa = build('.')
        assert eps_trans(nfa.transitions_table[0], nfa) == 0

    def test_transitions_vector_length_equals_alphabet_size(self):
        nfa = build('.')
        assert len(nfa.transitions_table[0].transitions) == len(nfa.alphabet)


class TestConcatenationNFA:
    """_concatination: ab# — two atomics joined by an explicit epsilon bridge."""

    def test_exactly_four_states(self):
        # left body(1) + eps_join(1) + right body(1) + accept(1) = 4
        assert len(build('ab#').transitions_table) == 4

    def test_exactly_one_accept_state(self):
        nfa = build('ab#')
        assert sum(1 for s in nfa.transitions_table if s.is_accept) == 1

    def test_accept_is_last_state(self):
        assert build('ab#').transitions_table[-1].is_accept

    def test_s0_consumes_left_operand_not_right(self):
        """State 0 must fire on 'a' (left) and be silent on 'b' (right)."""
        nfa = build('ab#')
        assert all_targets(char_trans(nfa.transitions_table[0], nfa, 'a')) != []
        assert char_trans(nfa.transitions_table[0], nfa, 'b') == 0

    def test_epsilon_bridge_at_state_1(self):
        """State 1 is the epsilon bridge; must be epsilon and point to state 2."""
        nfa = build('ab#')
        s1 = nfa.transitions_table[1]
        assert s1.is_epsilon
        assert all_targets(eps_trans(s1, nfa)) == [2]

    def test_state_2_consumes_right_operand(self):
        nfa = build('ab#')
        assert all_targets(char_trans(nfa.transitions_table[2], nfa, 'b')) != []
        assert char_trans(nfa.transitions_table[2], nfa, 'a') == 0

    def test_three_char_concat_six_states(self):
        assert len(build('ab#c#').transitions_table) == 6

    def test_three_char_concat_one_accept(self):
        assert sum(1 for s in build('ab#c#').transitions_table if s.is_accept) == 1


class TestAlternationNFA:
    """_alternate: ab| — Thompson split/merge structure."""

    def test_exactly_six_states(self):
        # split(1) + a_body(1) + a_merge(1) + b_body(1) + b_merge(1) + final(1) = 6
        assert len(build('ab|').transitions_table) == 6

    def test_exactly_one_accept_state(self):
        assert sum(1 for s in build('ab|').transitions_table if s.is_accept) == 1

    def test_start_state_is_epsilon(self):
        assert build('ab|').transitions_table[0].is_epsilon

    def test_start_branches_to_two_distinct_targets(self):
        nfa = build('ab|')
        targets = all_targets(eps_trans(nfa.transitions_table[0], nfa))
        assert len(targets) == 2
        assert targets[0] != targets[1]

    def test_both_branch_targets_are_not_accept(self):
        nfa = build('ab|')
        for t in all_targets(eps_trans(nfa.transitions_table[0], nfa)):
            assert not nfa.transitions_table[t].is_accept

    def test_exactly_two_merge_states_point_to_final(self):
        nfa = build('ab|')
        fi = len(nfa.transitions_table) - 1
        merges = [s for s in nfa.transitions_table[:-1]
                  if s.is_epsilon and all_targets(eps_trans(s, nfa)) == [fi]]
        assert len(merges) == 2

    def test_nested_alternation_one_accept(self):
        assert sum(1 for s in build('ab|c|').transitions_table if s.is_accept) == 1


class TestStarNFA:
    """_star: a* — Thompson Kleene-star structure."""

    def test_exactly_four_states(self):
        # start_eps(1) + body(1) + loop_eps(1) + final(1) = 4
        assert len(build('a*').transitions_table) == 4

    def test_exactly_one_accept_state(self):
        assert sum(1 for s in build('a*').transitions_table if s.is_accept) == 1

    def test_start_state_is_epsilon(self):
        assert build('a*').transitions_table[0].is_epsilon

    def test_start_can_enter_body_and_skip_to_final(self):
        nfa = build('a*')
        fi = len(nfa.transitions_table) - 1
        targets = all_targets(eps_trans(nfa.transitions_table[0], nfa))
        assert 1 in targets, "Start must reach body at index 1"
        assert fi in targets, "Start must reach final directly (zero repetitions)"

    def test_loop_eps_state_points_back_to_body(self):
        nfa = build('a*')
        s2 = nfa.transitions_table[2]
        assert s2.is_epsilon
        assert 1 in all_targets(eps_trans(s2, nfa))

    def test_loop_eps_state_also_exits_to_final(self):
        nfa = build('a*')
        fi = len(nfa.transitions_table) - 1
        assert fi in all_targets(eps_trans(nfa.transitions_table[2], nfa))


class TestOptionalNFA:
    """a? is built as _alternate(epsilon_nfa, a_nfa)."""

    def test_exactly_one_accept_state(self):
        assert sum(1 for s in build('a?').transitions_table if s.is_accept) == 1

    def test_start_state_is_epsilon(self):
        assert build('a?').transitions_table[0].is_epsilon

    def test_start_has_exactly_two_branches(self):
        nfa = build('a?')
        assert len(all_targets(eps_trans(nfa.transitions_table[0], nfa))) == 2


# ===========================================================================
# 2.  SEMANTIC TESTS — does is_match return the right answer?
# ===========================================================================

class TestAtomicAcceptance:
    def test_accepts_matching_char(self):       assert accepts('a', 'a')
    def test_rejects_wrong_char(self):          assert not accepts('a', 'b')
    def test_rejects_empty(self):               assert not accepts('a', '')
    def test_rejects_two_chars(self):           assert not accepts('a', 'aa')

    def test_each_char_accepted_by_its_nfa(self):
        for ch in 'abcd':
            assert accepts(ch, ch)

    def test_no_char_accepted_by_wrong_nfa(self):
        for ch in 'abcd':
            for other in 'abcd':
                if other != ch:
                    assert not accepts(ch, other)


class TestConcatenationAcceptance:
    def test_accepts_correct_pair(self):        assert accepts('ab#', 'ab')
    def test_rejects_reversed(self):            assert not accepts('ab#', 'ba')
    def test_rejects_left_only(self):           assert not accepts('ab#', 'a')
    def test_rejects_right_only(self):          assert not accepts('ab#', 'b')
    def test_rejects_empty(self):               assert not accepts('ab#', '')
    def test_rejects_extra_char(self):          assert not accepts('ab#', 'abc')

    def test_three_chars_correct_order(self):   assert accepts('ab#c#', 'abc')
    def test_three_chars_rotation(self):        assert not accepts('ab#c#', 'bca')
    def test_three_chars_reverse(self):         assert not accepts('ab#c#', 'cba')
    def test_three_chars_partial(self):         assert not accepts('ab#c#', 'ab')

    def test_four_chars(self):                  assert accepts('ab#c#d#', 'abcd')
    def test_four_chars_wrong_order(self):      assert not accepts('ab#c#d#', 'abdc')


class TestAlternationAcceptance:
    def test_accepts_left(self):                assert accepts('ab|', 'a')
    def test_accepts_right(self):               assert accepts('ab|', 'b')
    def test_rejects_neither(self):             assert not accepts('ab|', 'c')
    def test_rejects_empty(self):               assert not accepts('ab|', '')
    def test_rejects_concatenation(self):       assert not accepts('ab|', 'ab')

    def test_three_way_a(self):                 assert accepts('ab|c|', 'a')
    def test_three_way_b(self):                 assert accepts('ab|c|', 'b')
    def test_three_way_c(self):                 assert accepts('ab|c|', 'c')
    def test_three_way_d(self):                 assert not accepts('ab|c|', 'd')


class TestStarAcceptance:
    def test_accepts_empty(self):               assert accepts('a*', '')
    def test_accepts_one(self):                 assert accepts('a*', 'a')
    def test_accepts_two(self):                 assert accepts('a*', 'aa')
    def test_accepts_many(self):                assert accepts('a*', 'aaaaaa')
    def test_rejects_wrong_char(self):          assert not accepts('a*', 'b')
    def test_rejects_mixed(self):               assert not accepts('a*', 'ab')
    def test_rejects_trailing_wrong(self):      assert not accepts('a*', 'aab')


class TestOptionalAcceptance:
    def test_accepts_empty(self):               assert accepts('a?', '')
    def test_accepts_one(self):                 assert accepts('a?', 'a')
    def test_rejects_two(self):                 assert not accepts('a?', 'aa')
    def test_rejects_wrong_char(self):          assert not accepts('a?', 'b')


class TestWildcardAcceptance:
    def test_accepts_a(self):                   assert accepts('.', 'a')
    def test_accepts_b(self):                   assert accepts('.', 'b')
    def test_accepts_c(self):                   assert accepts('.', 'c')
    def test_accepts_d(self):                   assert accepts('.', 'd')
    def test_rejects_empty(self):               assert not accepts('.', '')
    def test_rejects_two_chars(self):           assert not accepts('.', 'ab')


# ===========================================================================
# 3.  COMPOUND EXPRESSION TESTS
# ===========================================================================

class TestConcatWithStar:
    """ab* — 'a' then zero-or-more 'b'."""
    def test_just_a(self):          assert accepts('ab*#', 'a')
    def test_ab(self):              assert accepts('ab*#', 'ab')
    def test_abbb(self):            assert accepts('ab*#', 'abbb')
    def test_rejects_empty(self):   assert not accepts('ab*#', '')
    def test_rejects_b_only(self):  assert not accepts('ab*#', 'b')
    def test_rejects_ba(self):      assert not accepts('ab*#', 'ba')


class TestStarOfConcat:
    """(ab)* — zero or more exact 'ab' repetitions."""
    def test_empty(self):                   assert accepts('ab#*', '')
    def test_one(self):                     assert accepts('ab#*', 'ab')
    def test_two(self):                     assert accepts('ab#*', 'abab')
    def test_three(self):                   assert accepts('ab#*', 'ababab')
    def test_rejects_a(self):               assert not accepts('ab#*', 'a')
    def test_rejects_b(self):               assert not accepts('ab#*', 'b')
    def test_rejects_partial(self):         assert not accepts('ab#*', 'aba')
    def test_rejects_wrong_char(self):      assert not accepts('ab#*', 'c')


class TestStarOfAlternation:
    """(a|b)* — zero or more chars each 'a' or 'b'."""
    def test_empty(self):                   assert accepts('ab|*', '')
    def test_a(self):                       assert accepts('ab|*', 'a')
    def test_b(self):                       assert accepts('ab|*', 'b')
    def test_ab(self):                      assert accepts('ab|*', 'ab')
    def test_ba(self):                      assert accepts('ab|*', 'ba')
    def test_long_mixed(self):              assert accepts('ab|*', 'aabb')
    def test_very_long(self):               assert accepts('ab|*', 'aabbba')
    def test_rejects_c(self):               assert not accepts('ab|*', 'c')
    def test_rejects_string_with_c(self):   assert not accepts('ab|*', 'abc')


class TestOptionalInConcat:
    """a?b — optional 'a' then mandatory 'b'."""
    def test_just_b(self):          assert accepts('a?b#', 'b')
    def test_ab(self):              assert accepts('a?b#', 'ab')
    def test_rejects_a_only(self):  assert not accepts('a?b#', 'a')
    def test_rejects_empty(self):   assert not accepts('a?b#', '')
    def test_rejects_aab(self):     assert not accepts('a?b#', 'aab')


class TestOptionalAtEnd:
    """ab? — mandatory 'a' then optional 'b'."""
    def test_a_only(self):          assert accepts('ab?#', 'a')
    def test_ab(self):              assert accepts('ab?#', 'ab')
    def test_rejects_b_only(self):  assert not accepts('ab?#', 'b')
    def test_rejects_empty(self):   assert not accepts('ab?#', '')
    def test_rejects_abb(self):     assert not accepts('ab?#', 'abb')


class TestWildcardCombinations:
    def test_wildcard_star_empty(self):         assert accepts('.*', '')
    def test_wildcard_star_single(self):        assert accepts('.*', 'a')
    def test_wildcard_star_long(self):          assert accepts('.*', 'abcd')

    def test_a_dot_b_middle_a(self):            assert accepts('a.#b#', 'aab')
    def test_a_dot_b_middle_c(self):            assert accepts('a.#b#', 'acb')
    def test_a_dot_b_rejects_too_short(self):   assert not accepts('a.#b#', 'ab')
    def test_a_dot_b_rejects_empty(self):       assert not accepts('a.#b#', '')


class TestAlternationOfConcats:
    """(ab)|(cd)."""
    def test_accepts_ab(self):          assert accepts('ab#cd#|', 'ab')
    def test_accepts_cd(self):          assert accepts('ab#cd#|', 'cd')
    def test_rejects_ac(self):          assert not accepts('ab#cd#|', 'ac')
    def test_rejects_empty(self):       assert not accepts('ab#cd#|', '')
    def test_rejects_abcd(self):        assert not accepts('ab#cd#|', 'abcd')


class TestAlternationWithOptionals:
    """a?|b? — accepts '', 'a', or 'b'."""
    def test_empty(self):               assert accepts('a?b?|', '')
    def test_a(self):                   assert accepts('a?b?|', 'a')
    def test_b(self):                   assert accepts('a?b?|', 'b')
    def test_rejects_ab(self):          assert not accepts('a?b?|', 'ab')
    def test_rejects_c(self):           assert not accepts('a?b?|', 'c')


class TestComplexPattern:
    """(a|b)*(c|d)(a|b) — word-boundary-like pattern."""
    P = 'ab|*cd|#ab|#'

    def test_ca(self):          assert accepts(self.P, 'ca')
    def test_cb(self):          assert accepts(self.P, 'cb')
    def test_da(self):          assert accepts(self.P, 'da')
    def test_db(self):          assert accepts(self.P, 'db')
    def test_aaca(self):        assert accepts(self.P, 'aaca')
    def test_bbdb(self):        assert accepts(self.P, 'bbdb')
    def test_rejects_c(self):   assert not accepts(self.P, 'c')
    def test_rejects_ab(self):  assert not accepts(self.P, 'ab')
    def test_rejects_empty(self): assert not accepts(self.P, '')


# ===========================================================================
# 4.  EDGE CASES
# ===========================================================================

class TestEdgeCases:
    def test_build_returns_nfa(self):
        assert build('a') is not None

    def test_self_alternation(self):
        assert accepts('aa|', 'a')
        assert not accepts('aa|', '')
        assert not accepts('aa|', 'b')

    def test_triple_same_concat(self):
        assert accepts('aa#a#', 'aaa')
        assert not accepts('aa#a#', 'aa')
        assert not accepts('aa#a#', 'aaaa')

    def test_star_accepts_empty(self):
        """a* is NOT the empty language."""
        assert accepts('a*', '')

    def test_wildcard_star_accepts_any(self):
        assert accepts('.*', 'abcd')
        assert accepts('.*', '')

    def test_star_then_char(self):
        """a*b — zero-or-more 'a' then exactly one 'b'."""
        assert accepts('a*b#', 'b')
        assert accepts('a*b#', 'ab')
        assert accepts('a*b#', 'aaab')
        assert not accepts('a*b#', '')
        assert not accepts('a*b#', 'a')

    def test_three_way_alternation_in_star(self):
        """(a|b|c)* — any combination of a, b, c."""
        assert accepts('ab|c|*', 'acbc')
        assert accepts('ab|c|*', '')
        assert not accepts('ab|c|*', 'd')


# ===========================================================================
# 5.  ERROR HANDLING
# ===========================================================================

class TestErrorHandling:
    def test_concat_operator_needs_two_operands(self):
        with pytest.raises(ValueError, match="Append symbol"):
            build('#')

    def test_alternation_operator_needs_two_operands(self):
        with pytest.raises(ValueError, match="Alternation symbol"):
            build('|')

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError, match="Unkown operator"):
            build('a+')

    def test_invalid_input_char_raises(self):
        with pytest.raises(ValueError):
            build('a').is_match('!')

    def test_two_operands_no_operator_does_not_crash(self):
        """Leaving two NFAs on the stack is malformed but must not hard-crash."""
        try:
            result = build('ab')
            assert result is not None
        except (ValueError, IndexError):
            pass


# ===========================================================================
# 6.  REGRESSION TESTS — one test class per identified bug
# ===========================================================================

class TestRegressionOperandOrder:
    """Bug: _concatination had nfa1/nfa2 swapped, producing reversed output."""

    def test_ab_not_ba(self):
        assert accepts('ab#', 'ab')
        assert not accepts('ab#', 'ba')

    def test_abc_preserves_order(self):
        assert accepts('ab#c#', 'abc')
        assert not accepts('ab#c#', 'cba')
        assert not accepts('ab#c#', 'bca')
        assert not accepts('ab#c#', 'bac')

    def test_ab_and_ba_are_distinct_languages(self):
        assert accepts('ab#', 'ab') and not accepts('ab#', 'ba')
        assert accepts('ba#', 'ba') and not accepts('ba#', 'ab')


class TestRegressionShiftOffset:
    """Bug: offset was `len(nfa2) + i` (growing each iteration) instead of
    a fixed snapshot captured before the insertion loop."""

    def test_three_concat_lands_at_correct_index(self):
        assert accepts('ab#c#', 'abc')
        assert not accepts('ab#c#', 'ab')
        assert not accepts('ab#c#', 'abcc')

    def test_four_concat_correct(self):
        assert accepts('ab#c#d#', 'abcd')
        assert not accepts('ab#c#d#', 'abdc')


class TestRegressionTupleIncrement:
    """Bug: engine's increment_state_by only shifted x[0] of a 2-tuple,
    leaving x[1] at its old value. This silently broke any pattern where
    an alternation NFA (whose start state holds a two-target eps tuple) is
    passed into _star. The builder's _shift_state helper fixes all elements."""

    def test_star_of_alternation_empty(self):
        assert accepts('ab|*', '')

    def test_star_of_alternation_single_a(self):
        assert accepts('ab|*', 'a')

    def test_star_of_alternation_single_b(self):
        assert accepts('ab|*', 'b')

    def test_star_of_alternation_multi(self):
        assert accepts('ab|*', 'abba')
        assert accepts('ab|*', 'aabb')

    def test_star_of_alternation_rejects_other(self):
        assert not accepts('ab|*', 'c')
        assert not accepts('ab|*', 'abc')

    def test_star_of_three_way_alternation(self):
        assert accepts('ab|c|*', 'acbc')
        assert not accepts('ab|c|*', 'd')

    def test_concat_of_two_stars_of_alternation(self):
        """(a|b)*(c|d)* — any mix of {a,b} followed by any mix of {c,d}."""
        assert accepts('ab|*cd|*#', '')
        assert accepts('ab|*cd|*#', 'ab')
        assert accepts('ab|*cd|*#', 'cd')
        assert accepts('ab|*cd|*#', 'abcd')
        assert not accepts('ab|*cd|*#', 'ca')


class TestRegressionEpsilonAlphabet:
    """Bug: if EPSILON was already in the caller's alphabet dict, EngineNFA
    would overwrite it at index max+1, shifting the epsilon slot and making
    wildcard ranges cover one extra (wrong) index. NFABuilder now strips
    EPSILON before constructing EngineNFA."""

    def test_epsilon_index_is_4_inside_nfa(self):
        assert build('a').alphabet[EPSILON] == 4

    def test_wildcard_epsilon_slot_is_zero(self):
        nfa = build('.')
        ei = eps_idx(nfa)
        assert nfa.transitions_table[0].transitions[ei] == 0

    def test_wildcard_transition_vector_length(self):
        nfa = build('.')
        assert len(nfa.transitions_table[0].transitions) == len(nfa.alphabet)


class TestRegressionStarLoopIndex:
    """Bug: _star used the engine's increment_state_by which only shifts
    the first element of a tuple transition. For a multi-state inner NFA
    (such as a concat or alternation), the loop-back index would be wrong
    and the star would fail to match repeated occurrences."""

    def test_star_of_concat_empty(self):
        assert accepts('ab#*', '')

    def test_star_of_concat_one_rep(self):
        assert accepts('ab#*', 'ab')

    def test_star_of_concat_two_reps(self):
        assert accepts('ab#*', 'abab')

    def test_star_of_concat_rejects_partial(self):
        assert not accepts('ab#*', 'a')
        assert not accepts('ab#*', 'aba')

    def test_star_of_6state_alternation(self):
        """Inner NFA has 6 states; loop-back index must still resolve correctly."""
        assert accepts('ab|*', '')
        assert accepts('ab|*', 'abba')
        assert not accepts('ab|*', 'c')