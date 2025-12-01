"""Сервис валидации входного контроля."""
from typing import Dict, Any, Callable

from common.models import ValidationResult, ControlType
from client.src.config import get_config


class ValidatorService:
    """Сервис для выполнения различных типов контроля."""

    def __init__(self):
        self.validators: Dict[ControlType, Callable] = {
            ControlType.WEIGHT_CHECK: self._validate_weight,
            ControlType.QUANTITY_CHECK: self._validate_quantity,
            ControlType.DIMENSION_CHECK: self._validate_dimension,
            ControlType.VISUAL_CHECK: self._validate_visual,
        }

    def validate(
        self,
        control_type: ControlType,
        params: Dict[str, Any],
        actual_values: Dict[str, Any]
    ) -> ValidationResult:
        """Выполнить валидацию по типу контроля."""
        validator = self.validators.get(control_type)
        if not validator:
            return ValidationResult(
                passed=False,
                message=f"Неизвестный тип контроля: {control_type}",
                details={}
            )
        return validator(params, actual_values)

    def get_instructions(self, control_type: ControlType, params: Dict[str, Any]) -> str:
        """Получить инструкции для оператора."""
        config = get_config()
        control_config = config["validation"]["control_types"].get(control_type.value, {})
        description = control_config.get("description", control_type.value)

        if control_type == ControlType.WEIGHT_CHECK:
            target = params.get("target_weight", "?")
            tolerance = params.get("tolerance", "?")
            return f"{description}\nОжидаемый вес: {target} кг (±{tolerance} кг)"

        elif control_type == ControlType.QUANTITY_CHECK:
            expected = params.get("expected_count", "?")
            return f"{description}\nОжидаемое количество: {expected}"

        elif control_type == ControlType.DIMENSION_CHECK:
            dims = []
            for d in ["length", "width", "height"]:
                if d in params:
                    dims.append(f"{d}: {params[d]}")
            tolerance = params.get("tolerance", "?")
            return f"{description}\nРазмеры: {', '.join(dims)} (±{tolerance})"

        elif control_type == ControlType.VISUAL_CHECK:
            checklist = params.get("checklist", [])
            items = "\n".join(f"• {item}" for item in checklist)
            return f"{description}\nЧек-лист:\n{items}"

        return description

    def _validate_weight(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка веса."""
        target = params.get("target_weight", 0)
        tolerance = params.get("tolerance", 0)
        measured = actual.get("measured_weight", 0)

        diff = abs(measured - target)
        passed = diff <= tolerance

        return ValidationResult(
            passed=passed,
            message="Вес в норме" if passed else f"Отклонение веса: {diff:.2f} кг",
            details={
                "target_weight": target,
                "tolerance": tolerance,
                "measured_weight": measured,
                "difference": diff
            }
        )

    def _validate_quantity(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка количества."""
        expected = params.get("expected_count", 0)
        counted = actual.get("counted", 0)

        passed = counted == expected

        return ValidationResult(
            passed=passed,
            message="Количество совпадает" if passed else f"Расхождение: {counted - expected}",
            details={
                "expected_count": expected,
                "counted": counted,
                "difference": counted - expected
            }
        )

    def _validate_dimension(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка размеров."""
        tolerance = params.get("tolerance", 0)
        issues = []

        for dim in ["length", "width", "height"]:
            if dim in params and dim in actual:
                expected = params[dim]
                measured = actual[dim]
                if abs(measured - expected) > tolerance:
                    issues.append(f"{dim}: {measured} (ожид. {expected})")

        passed = len(issues) == 0

        return ValidationResult(
            passed=passed,
            message="Размеры в норме" if passed else f"Отклонения: {', '.join(issues)}",
            details={
                "expected": {k: v for k, v in params.items() if k != "tolerance"},
                "measured": actual,
                "tolerance": tolerance
            }
        )

    def _validate_visual(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Визуальный осмотр (всегда на усмотрение оператора)."""
        passed = actual.get("passed", False)
        notes = actual.get("notes", "")

        return ValidationResult(
            passed=passed,
            message="Визуальный осмотр пройден" if passed else "Обнаружены дефекты",
            details={
                "checklist": params.get("checklist", []),
                "operator_notes": notes,
                "operator_decision": passed
            }
        )
