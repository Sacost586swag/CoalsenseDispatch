import coalsense_common


def test_package_imports() -> None:
    # Evita el falso verde: pytest sin pruebas sale con código 5, y esto
    # comprueba además que el paquete está instalado en el entorno.
    assert coalsense_common.__name__ == "coalsense_common"
