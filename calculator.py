"""
Модуль калькулятора с использованием обратной польской нотации.
Поддерживает операции: +, -, *, /, ^ и скобки.
"""

from typing import List, Union, Dict, Optional


class CalculatorError(Exception):
    """Исключение для ошибок калькулятора."""
    pass


class Token:
    """Базовый класс для всех токенов."""
    pass


class Number(Token):
    """Класс для числовых токенов."""

    def __init__(self, value: float):
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"


class Operator(Token):
    """Класс для операторов."""

    # Приоритеты операторов (чем больше число, тем выше приоритет)
    PRECEDENCE = {
        '+': 1,
        '-': 1,
        '*': 2,
        '/': 2,
        '^': 3,
    }

    # Ассоциативность операторов (True - правоассоциативный, False - левоассоциативный)
    RIGHT_ASSOCIATIVE = {'^'}

    def __init__(self, symbol: str):
        if symbol not in self.PRECEDENCE:
            raise CalculatorError(f"Неподдерживаемый оператор: {symbol}")
        self.symbol = symbol

    @property
    def precedence(self) -> int:
        """Возвращает приоритет оператора."""
        return self.PRECEDENCE[self.symbol]

    @property
    def is_right_associative(self) -> bool:
        """Проверяет, является ли оператор правоассоциативным."""
        return self.symbol in self.RIGHT_ASSOCIATIVE

    def apply(self, left: float, right: float) -> float:
        """Применяет оператор к двум операндам."""
        if self.symbol == '+':
            return left + right
        if self.symbol == '-':
            return left - right
        if self.symbol == '*':
            return left * right
        if self.symbol == '/':
            if right == 0:
                raise CalculatorError("Деление на ноль")
            return left / right
        if self.symbol == '^':
            return left ** right
        raise CalculatorError(f"Неизвестный оператор: {self.symbol}")

    def __repr__(self):
        return f"Operator('{self.symbol}')"


class LeftParen(Token):
    """Класс для левой скобки."""

    def __repr__(self):
        return "LeftParen()"


class RightParen(Token):
    """Класс для правой скобки."""

    def __repr__(self):
        return "RightParen()"


class UnaryMinus(Token):
    """Класс для унарного минуса."""
    
    def __repr__(self):
        return "UnaryMinus()"


class Tokenizer:
    """Класс для разбора входной строки в токены."""

    def __init__(self, expression: str):
        self.expression = expression.replace(' ', '')  # Удаляем пробелы
        self.position = 0

    def get_tokens(self) -> List[Token]:
        """Разбирает выражение и возвращает список токенов."""
        tokens = []
        unary_context = True  # В начале выражения ожидается унарный оператор

        while self.position < len(self.expression):
            char = self.expression[self.position]

            if char.isdigit() or char == '.':  # Число
                tokens.append(self._parse_number())
                unary_context = False
            elif char in '+-*/^':  # Оператор
                # Проверяем, является ли минус унарным
                if char == '-' and unary_context:
                    tokens.append(UnaryMinus())
                else:
                    tokens.append(Operator(char))
                unary_context = True
                self.position += 1
            elif char == '(':  # Левая скобка
                tokens.append(LeftParen())
                self.position += 1
                unary_context = True
            elif char == ')':  # Правая скобка
                tokens.append(RightParen())
                self.position += 1
                unary_context = False
            else:
                raise CalculatorError(f"Недопустимый символ: {char}")

        return tokens

    def _parse_number(self) -> Number:
        """Парсит число из текущей позиции."""
        start = self.position
        has_decimal = False

        while self.position < len(self.expression):
            char = self.expression[self.position]
            if char.isdigit():
                self.position += 1
            elif char == '.':
                if has_decimal:
                    raise CalculatorError("Некорректное число: несколько десятичных точек")
                has_decimal = True
                self.position += 1
            else:
                break

        number_str = self.expression[start:self.position]
        try:
            value = float(number_str)
            return Number(value)
        except ValueError as exc:
            raise CalculatorError(f"Некорректное число: {number_str}") from exc


class ShuntingYard:
    """Алгоритм сортировочной станции для преобразования в ОПН."""

    @staticmethod
    def to_rpn(tokens: List[Token]) -> List[Union[Number, Operator]]:
        """
        Преобразует список токенов в обратную польскую нотацию.
        Использует алгоритм сортировочной станции Дейкстры.
        """
        output = []
        stack = []

        for token in tokens:
            if isinstance(token, Number):
                output.append(token)

            elif isinstance(token, UnaryMinus):
                # Обрабатываем унарный минус как специальный оператор
                # В ОПН унарный минус можно представить как оператор с одним операндом
                # Для простоты, преобразуем в умножение на -1
                output.append(Number(-1))
                output.append(Operator('*'))
                
            elif isinstance(token, Operator):
                while (stack and isinstance(stack[-1], Operator) and
                       ShuntingYard._should_pop_operator(token, stack[-1])):
                    output.append(stack.pop())
                stack.append(token)

            elif isinstance(token, LeftParen):
                stack.append(token)

            elif isinstance(token, RightParen):
                while stack and not isinstance(stack[-1], LeftParen):
                    output.append(stack.pop())

                if not stack:
                    raise CalculatorError("Несоответствие скобок: не найдена открывающая скобка")

                stack.pop()  # Удаляем левую скобку

        # Выталкиваем оставшиеся операторы из стека
        while stack:
            if isinstance(stack[-1], LeftParen):
                raise CalculatorError("Несоответствие скобок: незакрытая скобка")
            output.append(stack.pop())

        return output

    @staticmethod
    def _should_pop_operator(current: Operator, top: Operator) -> bool:
        """
        Определяет, нужно ли вытолкнуть оператор из стека.

        Правила:
        - Если текущий оператор левоассоциативный и его приоритет <= приоритета верхнего
        - Если текущий оператор правоассоциативный и его приоритет < приоритета верхнего
        """
        if current.is_right_associative:
            return current.precedence < top.precedence
        return current.precedence <= top.precedence


class RPNEvaluator:
    """Класс для вычисления выражений в ОПН."""

    @staticmethod
    def evaluate(rpn_tokens: List[Union[Number, Operator]], 
                 variables: Optional[Dict[str, float]] = None) -> float:
        """
        Вычисляет значение выражения в обратной польской нотации.
        
        Args:
            rpn_tokens: Список токенов в ОПН
            variables: Словарь переменных (имя -> значение)
        """
        stack = []
        variables = variables or {}

        for token in rpn_tokens:
            if isinstance(token, Number):
                stack.append(token.value)

            elif isinstance(token, Operator):
                if len(stack) < 2:
                    raise CalculatorError("Недостаточно операндов для операции")

                right = stack.pop()
                left = stack.pop()
                result = token.apply(left, right)
                stack.append(result)

        if len(stack) != 1:
            raise CalculatorError("Некорректное выражение")

        return stack[0]


class Calculator:
    """Основной класс калькулятора."""

    def __init__(self):
        self.tokenizer = Tokenizer
        self.shunting_yard = ShuntingYard()
        self.evaluator = RPNEvaluator()
        self.rpn = None
        self.expression = None

    def start_calculator(self, expression: str):
        """Подготавливает калькулятор к вычислению."""
        self.expression = expression
        return self.rpn

    def calculate(self, expression: Optional[str] = None, 
                  variables: Optional[Dict[str, float]] = None) -> float:
        """
        Вычисляет значение математического выражения.

        Args:
            expression: Строка с выражением (например, "3 + 4 * 2")
            variables: Словарь переменных (имя -> значение)

        Returns:
            Результат вычисления

        Raises:
            CalculatorError: При ошибках в выражении
        """
        # Если выражение не передано, используем сохраненное
        if expression is not None:
            self.expression = expression
        
        if not self.expression or not str(self.expression).strip():
            raise ValueError("Пустое выражение")
        
        # Проверка типа входных данных
        if not isinstance(self.expression, str):
            raise ValueError("Введено не строчное выражение")
        
        # Поддержка переменных
        expr = self.expression
        if variables:
            for var_name, var_value in variables.items():
                expr = expr.replace(var_name, str(var_value))

        try:
            # Токенизация
            tokenizer = self.tokenizer(expr)
            tokens = tokenizer.get_tokens()

            # Преобразование в ОПН
            rpn_tokens = self.shunting_yard.to_rpn(tokens)
            self.rpn = rpn_tokens

            # Вычисление
            result = self.evaluator.evaluate(rpn_tokens, variables)
            
            return result

        except CalculatorError as e:
            raise ValueError(str(e)) from e
        except Exception as e:
            raise ValueError(str(e)) from e


def main():
    """Интерактивный режим калькулятора."""
    calculator = Calculator()
    print("Калькулятор с обратной польской нотацией")
    print("Поддерживаемые операции: +, -, *, /, ^ (степень)")
    print("Используйте скобки для изменения приоритета")
    print("Введите 'exit' для выхода\n")

    while True:
        try:
            expression = input("Выражение: ").strip()

            if expression.lower() in ('exit', 'quit', 'q'):
                break

            if not expression:
                continue

            result = calculator.calculate(expression)
            print(f"Результат: {result}\n")

        except (CalculatorError, ValueError) as err:
            print(f"Ошибка: {err}\n")
        except Exception as err:
            print(f"Неожиданная ошибка: {err}\n")


if __name__ == "__main__":
    main()