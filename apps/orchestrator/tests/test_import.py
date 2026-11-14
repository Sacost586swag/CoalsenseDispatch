import coalsense_orchestrator


def test_package_imports() -> None:
    # Evita el falso verde: pytest sin pruebas sale con código 5, y esto
    # comprueba además que el paquete está instalado en el entorno.
    assert coalsense_orchestrator.__name__ == "coalsense_orchestrator"
