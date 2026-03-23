"""
Модуль тестирования калькулятора.
Тестирует каждый этап работы: токенизацию, преобразование в ОПН и вычисление.
"""

import pytest
from calculator import (
    Calculator, CalculatorError, Tokenizer, ShuntingYard, RPNEvaluator,
    Number, Operator, LeftParen, RightParen, UnaryMinus
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
    
    def test_unary_minus(self):
        """Тест унарного минуса."""
        tokenizer = Tokenizer("-5")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 1
        assert isinstance(tokens[0], UnaryMinus)
    
    def test_complex_expression(self):
        """Тест сложного выражения."""
        tokenizer = Tokenizer("3 + 4 * (2 - 1)")
        tokens = tokenizer.get_tokens()
        assert len(tokens) == 7  # Унарных минусов нет, поэтому 7 токенов
        
        # Проверяем типы токенов
        assert isinstance(tokens[0], Number)  # 3
        assert isinstance(tokens[1], Operator)  # +
        assert isinstance(tokens[2], Number)  # 4
        assert isinstance(tokens[3], Operator)  # *
        assert isinstance(tokens[4], LeftParen)  # (
        assert isinstance(tokens[5], Number)  # 2
        assert isinstance(tokens[6], Operator)  # -
        assert isinstance(tokens[7], Number)  # 1
        assert isinstance(tokens[8], RightParen)  # )
    
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
    
    def test_basic_addition(self):
        """Тест сложения."""
        assert self.calc.calculate("2+3") == 5.0
    
    def test_basic_subtraction(self):
        """Тест вычитания."""
        assert self.calc.calculate("10-4") == 6.0
    
    def test_basic_multiplication(self):
        """Тест умножения."""
        assert self.calc.calculate("6*7") == 42.0
    
    def test_basic_division(self):
        """Тест деления."""
        assert self.calc.calculate("15/3") == 5.0
    
    def test_multiple_operations(self):
        """Тест нескольких операций."""
        assert self.calc.calculate("2+3*4") == 14.0
    
    def test_parentheses(self):
        """Тест скобок."""
        assert self.calc.calculate("(2+3)*4") == 20.0
    
    def test_nested_parentheses(self):
        """Тест вложенных скобок."""
        assert self.calc.calculate("2*(3+(4-2))") == 10.0
    
    def test_unary_minus(self):
        """Тест унарного минуса."""
        assert self.calc.calculate("-5+3") == -2.0
    
    def test_unary_minus_with_parentheses(self):
        """Тест унарного минуса со скобками."""
        assert self.calc.calculate("-(3+2)") == -5.0
    
    def test_double_unary_minus(self):
        """Тест двойного унарного минуса."""
        assert self.calc.calculate("--5") == 5.0
    
    def test_division_by_zero(self):
        """Тест деления на ноль."""
        with pytest.raises(ValueError):
            self.calc.calculate("10/0")
    
    def test_complex_expression(self):
        """Тест сложного выражения."""
        result = self.calc.calculate("18+18-2*(13+6-3/5)-64")
        assert abs(result - (-64.8)) < 0.0001
    
    def test_floating_point(self):
        """Тест чисел с плавающей точкой."""
        assert self.calc.calculate("3.5+2.5") == 6.0
    
    def test_negative_numbers(self):
        """Тест отрицательных чисел."""
        assert self.calc.calculate("-3*4") == -12.0
    
    def test_expression_with_spaces(self):
        """Тест выражения с пробелами."""
        assert self.calc.calculate(" 2 + 3 * 4 ") == 14.0
    
    def test_empty_expression(self):
        """Тест пустого выражения."""
        with pytest.raises(ValueError, match="Пустое выражение"):
            self.calc.calculate("")
    
    def test_non_string_input(self):
        """Тест нестрокового ввода."""
        with pytest.raises(ValueError, match="Введено не строчное выражение"):
            self.calc.calculate(123)
    
    def test_invalid_operator(self):
        """Тест неверного оператора."""
        with pytest.raises(ValueError):
            self.calc.calculate("2^3")
    
    def test_missing_operand(self):
        """Тест отсутствующего операнда."""
        with pytest.raises(ValueError):
            self.calc.calculate("2+")
    
    def test_variables(self):
        """Тест переменных."""
        variables = {'x': 5, 'y': 3}
        result = self.calc.calculate("x*y+2", variables)
        assert result == 17.0
    
    def test_undefined_variable(self):
        """Тест неопределенной переменной."""
        with pytest.raises(ValueError):
            self.calc.calculate("x+2")
    
    def test_variable_with_expression(self):
        """Тест выражения с переменными."""
        variables = {'a': 10, 'b': 2}
        result = self.calc.calculate("(a+b)*3", variables)
        assert result == 36.0
    
    def test_unary_minus_with_multiplication(self):
        """Тест унарного минуса с умножением."""
        assert self.calc.calculate("-2*-3") == 6.0
    
    def test_complex_with_unary(self):
        """Тест сложного выражения с унарным минусом."""
        assert self.calc.calculate("-(-2+3)*4") == -4.0
    
    def test_operator_precedence(self):
        """Тест приоритета операторов."""
        assert self.calc.calculate("2+3*4-6/2") == 11.0
    
    def test_parentheses_precedence(self):
        """Тест приоритета скобок."""
        assert self.calc.calculate("(2+3)*(4-1)") == 15.0
    
    def test_division_result_type(self):
        """Тест типа результата деления."""
        result = self.calc.calculate("5/2")
        assert result == 2.5
        assert isinstance(result, float)
    
    def test_large_numbers(self):
        """Тест больших чисел."""
        assert self.calc.calculate("1000000*1000000") == 1000000000000.0
    
    def test_decimal_precision(self):
        """Тест точности десятичных дробей."""
        result = self.calc.calculate("1/3")
        assert abs(result - 0.3333333333333333) < 0.0000000000001
    
    def test_multiple_parentheses(self):
        """Тест множественных скобок."""
        assert self.calc.calculate("(1+2)*(3+4)*(5+6)") == 231.0
    
    def test_chain_operations(self):
        """Тест цепочки операций."""
        assert self.calc.calculate("1+2+3+4+5") == 15.0
    
    def test_recalculate_same_instance(self):
        """Тест переиспользования экземпляра."""
        self.calc.calculate("2+3")
        result = self.calc.calculate("5*6")
        assert result == 30.0
    
    def test_calculate_without_expression(self):
        """Тест вычисления без выражения."""
        self.calc.start_calculator("2+3")
        result = self.calc.calculate()
        assert result == 5.0


class TestCalculatorEdgeCases:
    """Тесты для граничных случаев."""
    
    def setup_method(self):
        """Подготовка перед каждым тестом."""
        self.calc = Calculator()
    
    def test_single_number(self):
        """Тест одного числа."""
        assert self.calc.calculate("42") == 42.0
    
    def test_single_negative_number(self):
        """Тест одного отрицательного числа."""
        assert self.calc.calculate("-42") == -42.0
    
    def test_decimal_numbers(self):
        """Тест некорректных десятичных чисел."""
        with pytest.raises(ValueError):
            self.calc.calculate("3.14.15")
    
    def test_leading_zeros(self):
        """Тест ведущих нулей."""
        assert self.calc.calculate("002+003") == 5.0
    
    def test_trailing_operator(self):
        """Тест оператора в конце."""
        with pytest.raises(ValueError):
            self.calc.calculate("2+3+")
    
    def test_leading_operator(self):
        """Тест оператора в начале."""
        with pytest.raises(ValueError):
            self.calc.calculate("+2+3")
    
    def test_empty_parentheses(self):
        """Тест пустых скобок."""
        with pytest.raises(ValueError):
            self.calc.calculate("()")
    
    def test_unmatched_parentheses(self):
        """Тест несогласованных скобок."""
        with pytest.raises(ValueError):
            self.calc.calculate("(2+3")
    
    def test_variable_with_undefined_variable(self):
        """Тест с неопределенной переменной."""
        with pytest.raises(ValueError):
            self.calc.calculate("x+y", {'x': 5})
    
    def test_whitespace_only(self):
        """Тест только пробелов."""
        with pytest.raises(ValueError, match="Пустое выражение"):
            self.calc.calculate("   ")
            