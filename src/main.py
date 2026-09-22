"""
Plantilla Base - Estructuras de Datos Avanzadas (IC10D - EDA)
Fase 1: Trabajo Autónomo en Casa (Asistido por IA)

Instrucciones:
1. Implementa aquí la estructura de datos requerida para el taller.
2. Mantén tipado estricto (type hints) y docstrings descriptivos.
3. Asegura que el código sea ejecutable con pruebas de muestra en el bloque __main__.
"""

from typing import Any, Optional, List


class NodoBase:
    """Nodo elemental para estructuras enlazadas (ejemplo referencial)."""
    def __init__(self, valor: Any, prioridad: float = 0.0) -> None:
        self.valor: Any = valor
        self.prioridad: float = prioridad
        self.siguiente: Optional['NodoBase'] = None

    def __repr__(self) -> str:
        return f"Nodo(valor={self.valor}, prioridad={self.prioridad})"


class EstructuraDatosBase:
    """
    Estructura de datos principal.
    Define las operaciones públicas y atributos privados requeridos.
    """
    def __init__(self) -> None:
        self._tamano: int = 0
        self._cabeza: Optional[NodoBase] = None

    @property
    def tamano(self) -> int:
        """Retorna el número de elementos almacenados."""
        return self._tamano

    def esta_vacia(self) -> bool:
        """Verifica si la estructura no contiene elementos."""
        return self._tamano == 0

    def insertar(self, valor: Any, prioridad: float = 0.0) -> None:
        """
        Inserta un nuevo elemento en la estructura.
        Precondición: valor != None.
        Postcondición: tamano se incrementa en 1.
        """
        nuevo_nodo = NodoBase(valor, prioridad)
        nuevo_nodo.siguiente = self._cabeza
        self._cabeza = nuevo_nodo
        self._tamano += 1

    def buscar(self, valor: Any) -> bool:
        """
        Busca si un elemento existe en la estructura.
        Retorna True si fue encontrado, False en caso contrario.
        """
        actual = self._cabeza
        while actual is not None:
            if actual.valor == valor:
                return True
            actual = actual.siguiente
        return False


def main() -> None:
    """Punto de entrada para pruebas locales rápidas."""
    print("=== Inicializando Estructura de Datos (Prueba Local) ===")
    estructura = EstructuraDatosBase()
    
    # Inserciones de prueba
    estructura.insertar("Elemento_A", prioridad=10.0)
    estructura.insertar("Elemento_B", prioridad=20.0)
    
    print(f"Tamaño actual: {estructura.tamano}")
    print(f"¿Existe 'Elemento_A'?: {estructura.buscar('Elemento_A')}")
    print(f"¿Existe 'Elemento_Z'?: {estructura.buscar('Elemento_Z')}")
    print("=== Ejecución completada exitosamente ===")


if __name__ == "__main__":
    main()
