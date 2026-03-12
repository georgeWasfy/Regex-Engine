import pytest
import sys
sys.path.insert(0, 'src')

from regex_engine.parser import (
    getPresedence,
    implicitConcat,
    plus_to_star,
    infix2Postfix,
    pre_process_regex,
)


class TestPrecedence:
    def test_operators_have_correct_precedence(self):
        assert getPresedence('(') < getPresedence('|')
        assert getPresedence('|') < getPresedence('#')
        assert getPresedence('#') < getPresedence('*')
        assert getPresedence('*') == getPresedence('+') == getPresedence('?')

    def test_unknown_operator_gets_highest_precendence(self):
        assert getPresedence('x') > getPresedence('*')


class TestImplicitConcat:
    def test_simple_concatenation(self):
        assert implicitConcat('ab') == 'a#b'

    def test_concat_after_paren(self):
        assert implicitConcat('(a)b') == '(a)#b'

    def test_concat_after_alternation(self):
        assert implicitConcat('a|b') == 'a|b'

    def test_no_concat_after_operators(self):
        assert implicitConcat('a*') == 'a*'
        assert implicitConcat('a+') == 'a+'
        assert implicitConcat('a?') == 'a?'

    def test_parens_no_extra_concat(self):
        assert implicitConcat('(ab)') == '(a#b)'

    def test_complex_expression(self):
        assert implicitConcat('abc') == 'a#b#c'


class TestPlusToStar:
    def test_plus_becomes_star_with_self(self):
        assert plus_to_star('a+') == 'aa*'

    def test_plus_in_paren(self):
        assert plus_to_star('(a)+') == '(a)(a)*'

    def test_plus_complex_paren(self):
        assert plus_to_star('(ab)+') == '(ab)(ab)*'


class TestInfix2Postfix:
    def test_simple_alternation(self):
        assert infix2Postfix('a|b') == 'ab|'

    def test_simple_concatenation(self):
        assert infix2Postfix('a#b') == 'ab#'

    def test_kleene_star(self):
        assert infix2Postfix('a*') == 'a*'

    def test_optional(self):
        assert infix2Postfix('a?') == 'a?'

    def test_complex_expression(self):
        assert infix2Postfix('(a|b)*') == 'ab|*'

    def test_precedence_alternation_lower_than_concat(self):
        assert infix2Postfix('a|b#c') == 'abc#|'

    def test_left_associativity(self):
        assert infix2Postfix('a|b|c') == 'ab|c|'

    def test_concat_higher_than_alternation(self):
        assert infix2Postfix('a#b|c#d') == 'ab#cd#|'


class TestPreProcessRegex:
    def test_full_pipeline_simple(self):
        assert pre_process_regex('a|b') == 'ab|'

    def test_full_pipeline_concat(self):
        assert pre_process_regex('ab') == 'ab#'

    def test_full_pipeline_star(self):
        assert pre_process_regex('a*') == 'a*'

    def test_full_pipeline_plus(self):
        assert pre_process_regex('a+') == 'aa*#'

    def test_full_pipeline_optional(self):
        assert pre_process_regex('a?') == 'a?'

    def test_full_pipeline_complex(self):
        assert pre_process_regex('(a|b)*c') == 'ab|*c#'

    def test_wildcard(self):
        assert pre_process_regex('a.b') == 'a.#b#'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
