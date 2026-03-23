"""
Модуль тестирования калькулятора.
Тестирует каждый этап работы: токенизацию, преобразование в ОПН и вычисление.
"""

import pytest
from calculator import (
    Calculator, CalculatorError, Tokenizer, ShuntingYard, RPNEvaluator,
    Number, Operator, LeftParen, RightParen
)


class TestTokenizer:
    """Тесты для токенизатора."""

    def test_simple_numbers(self):
        """Тест простых чисел."""
        tokenizer = Tokenizer("123")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 1
        assert isinstance(tokens[0], Number)
        assert tokens[0].value == 123.0

    def test_decimal_numbers(self):
        """Тест десятичных чисел."""
        tokenizer = Tokenizer("3.14")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 1
        assert isinstance(tokens[0], Number)
        assert tokens[0].value == 3.14

    def test_operators(self):
        """Тест операторов."""
        tokenizer = Tokenizer("+ - * / ^")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 5
        symbols = ['+', '-', '*', '/', '^']
        for i, token in enumerate(tokens):
            assert isinstance(token, Operator)
            assert token.symbol == symbols[i]

    def test_parentheses(self):
        """Тест скобок."""
        tokenizer = Tokenizer("( )")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 2
        assert isinstance(tokens[0], LeftParen)
        assert isinstance(tokens[1], RightParen)

    def test_complex_expression(self):
        """Тест сложного выражения."""
        tokenizer = Tokenizer("3 + 4 * (2 - 1)")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 9

        # Проверяем типы токенов
        assert isinstance(tokens[0], Number)     # 3
        assert tokens[0].value == 3.0
        assert isinstance(tokens[1], Operator)   # +
        assert tokens[1].symbol == '+'
        assert isinstance(tokens[2], Number)     # 4
        assert tokens[2].value == 4.0
        assert isinstance(tokens[3], Operator)   # *
        assert tokens[3].symbol == '*'
        assert isinstance(tokens[4], LeftParen)  # (
        assert isinstance(tokens[5], Number)     # 2
        assert tokens[5].value == 2.0
        assert isinstance(tokens[6], Operator)   # -
        assert tokens[6].symbol == '-'
        assert isinstance(tokens[7], Number)     # 1
        assert tokens[7].value == 1.0
        assert isinstance(tokens[8], RightParen) # )

    def test_invalid_character(self):
        """Тест недопустимого символа."""
        tokenizer = Tokenizer("3 + a")
        with pytest.raises(CalculatorError, match="Недопустимый символ"):
            tokenizer.get_tokens()

    def test_invalid_number(self):
        """Тест некорректного числа."""
        tokenizer = Tokenizer("3.14.15")
        with pytest.raises(CalculatorError, match="Некорректное число"):
            tokenizer.get_tokens()


class TestShuntingYard:
    """Тесты для алгоритма сортировочной станции."""

    def test_simple_expression(self):
        """Тест простого выражения: 3 + 4 -> 3 4 +"""
        tokens = [Number(3), Operator('+'), Number(4)]
        rpn = ShuntingYard.to_rpn(tokens)

        assert len(rpn) == 3
        assert isinstance(rpn[0], Number)
        assert rpn[0].value == 3
        assert isinstance(rpn[1], Number)
        assert rpn[1].value == 4
        assert isinstance(rpn[2], Operator)
        assert rpn[2].symbol == '+'

    def test_precedence(self):
        """Тест приоритета операций: 3 + 4 * 2 -> 3 4 2 * +"""
        tokens = [Number(3), Operator('+'), Number(4), Operator('*'), Number(2)]
        rpn = ShuntingYard.to_rpn(tokens)

        assert len(rpn) == 5
        assert rpn[0].value == 3
        assert rpn[1].value == 4
        assert rpn[2].value == 2
        assert rpn[3].symbol == '*'
        assert rpn[4].symbol == '+'

    def test_parentheses(self):
        """Тест скобок: (3 + 4) * 2 -> 3 4 + 2 *"""
        tokens = [
            LeftParen(), Number(3), Operator('+'), Number(4), RightParen(),
            Operator('*'), Number(2)
        ]
        rpn = ShuntingYard.to_rpn(tokens)

        assert len(rpn) == 5
        assert rpn[0].value == 3
        assert rpn[1].value == 4
        assert rpn[2].symbol == '+'
        assert rpn[3].value == 2
        assert rpn[4].symbol == '*'

    def test_right_associative(self):
        """Тест правоассоциативности: 2 ^ 3 ^ 2 -> 2 3 2 ^ ^"""
        tokens = [Number(2), Operator('^'), Number(3), Operator('^'), Number(2)]
        rpn = ShuntingYard.to_rpn(tokens)

        assert len(rpn) == 5
        assert rpn[0].value == 2
        assert rpn[1].value == 3
        assert rpn[2].value == 2
        assert rpn[3].symbol == '^'
        assert rpn[4].symbol == '^'

    def test_mismatched_parentheses(self):
        """Тест несоответствия скобок."""
        tokens = [LeftParen(), Number(3), Operator('+'), Number(4)]
        with pytest.raises(CalculatorError, match="Несоответствие скобок"):
            ShuntingYard.to_rpn(tokens)


class TestRPNEvaluator:
    """Тесты для вычисления ОПН."""

    def test_simple_addition(self):
        """Тест сложения."""
        rpn = [Number(3), Number(4), Operator('+')]
        result = RPNEvaluator.evaluate(rpn)
        assert result == 7

    def test_complex_expression(self):
        """Тест сложного выражения: 3 4 2 * + -> 3 + 4 * 2 = 11"""
        rpn = [Number(3), Number(4), Number(2), Operator('*'), Operator('+')]
        result = RPNEvaluator.evaluate(rpn)
        assert result == 11

    def test_division(self):
        """Тест деления."""
        rpn = [Number(10), Number(3), Operator('/')]
        result = RPNEvaluator.evaluate(rpn)
        assert result == pytest.approx(3.333333, 0.0001)

    def test_division_by_zero(self):
        """Тест деления на ноль."""
        rpn = [Number(5), Number(0), Operator('/')]
        with pytest.raises(CalculatorError, match="Деление на ноль"):
            RPNEvaluator.evaluate(rpn)

    def test_power(self):
        """Тест возведения в степень."""
        rpn = [Number(2), Number(3), Operator('^')]
        result = RPNEvaluator.evaluate(rpn)
        assert result == 8

    def test_insufficient_operands(self):
        """Тест недостаточного количества операндов."""
        rpn = [Number(5), Operator('+')]
        with pytest.raises(CalculatorError, match="Недостаточно операндов"):
            RPNEvaluator.evaluate(rpn)

    def test_invalid_expression(self):
        """Тест некорректного выражения."""
        rpn = [Number(5), Number(3)]
        with pytest.raises(CalculatorError, match="Некорректное выражение"):
            RPNEvaluator.evaluate(rpn)


class TestCalculator:
    """Интеграционные тесты для калькулятора."""

    def setup_method(self):
        """Подготовка перед каждым тестом."""
        self.calc = Calculator()

    def test_simple_calculation(self):
        """Тест простых вычислений."""
        assert self.calc.calculate("3 + 4") == 7
        assert self.calc.calculate("10 - 3") == 7
        assert self.calc.calculate("5 * 6") == 30
        assert self.calc.calculate("15 / 3") == 5
        assert self.calc.calculate("2 ^ 3") == 8

    def test_precedence(self):
        """Тест приоритета операций."""
        assert self.calc.calculate("3 + 4 * 2") == 11
        assert self.calc.calculate("10 - 6 / 3") == 8
        assert self.calc.calculate("2 ^ 3 * 4") == 32

    def test_parentheses(self):
        """Тест скобок."""
        assert self.calc.calculate("(3 + 4) * 2") == 14
        assert self.calc.calculate("10 / (5 - 3)") == 5
        assert self.calc.calculate("(2 ^ 3) * (4 - 1)") == 24

    def test_complex_expressions(self):
        """Тест сложных выражений."""
        assert self.calc.calculate("3 + 4 * 2 - 6 / 3") == 3 + 4*2 - 6/3
        assert self.calc.calculate("(3 + 4) * (2 - 6) / 3") == (3+4)*(2-6)/3
        assert self.calc.calculate("2 ^ (3 + 1) - 10") == 2**4 - 10

    def test_empty_expression(self):
        """Тест пустого выражения."""
        with pytest.raises(CalculatorError, match="Пустое выражение"):
            self.calc.calculate("")
        with pytest.raises(CalculatorError, match="Пустое выражение"):
            self.calc.calculate("   ")

    def test_invalid_syntax(self):
        """Тест неверного синтаксиса."""
        with pytest.raises(CalculatorError):
            self.calc.calculate("3 + + 4")
            