# Informe de Auditoría Técnica (AUDIT.md)

**Asignatura:** Estructuras de Datos Avanzadas (IC10D – EDA)  
**Estudiante:** [Nombre del Alumno]  
**RUT:** [RUT]  
**Fecha de Auditoría:** [AAAA-MM-DD]  
**Desafío / Estructura:** [Ej. Cola de Prioridad / Árbol AVL / Skip List]  

---

## 1. Matriz de Complejidad Asintótica

| Operación / Método | Complejidad Temporal (Peor Caso) | Complejidad Temporal (Mejor Caso) | Complejidad Espacial ($\mathcal{O}$) |
| :--- | :---: | :---: | :---: |
| `insertar(elemento, clave)` | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ |
| `buscar(clave)`             | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ |
| `eliminar(clave)`           | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ |
| `extraer_extremo()`         | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ | $\mathcal{O}(\dots)$ |

### 📐 Justificación y Derivación Matemática Formal
*(Desglosar el conteo exacto de instrucciones elementales $T(n)$ o relaciones de recurrencia aplicadas al código de `src/`)*:

* **Operación `[Nombre Operación 1]`:**
  $$T(n) = c_1 \cdot n + c_2 \implies \mathcal{O}(n)$$
  *Justificación verbal:* ...

* **Operación `[Nombre Operación 2]`:**
  $$T(n) = \dots$$
  *Justificación verbal:* ...

---

## 2. Auditoría de Deuda Técnica y Alucinaciones de la IA

*(Analizar críticamente el código generado por IA en casa. Identificar ineficiencias ocultas, sobrecostos de memoria o malas prácticas).*

### 🔍 Hallazgo 1: Ineficiencia Algorítmica / Trampa de Complejidad
* **Ubicación en código:** `src/main.py` (Líneas X a Y).
* **Descripción del problema:** [Ej. La IA utilizó un arreglo desordenado con búsqueda lineal $\mathcal{O}(n)$ más desplazamiento `pop()`, generando un cuello de botella cuadrático $\mathcal{O}(n^2)$ ante ráfagas de datos.]
* **Impacto técnico:** [Pérdida de rendimiento / consumo excesivo de memoria / fugas de punteros].

### 💡 Propuesta de Optimización Arquitectónica
* **Solución propuesta:** [Ej. Reemplazar el arreglo plano por un Montículo Binario (*Binary Heap*) para reducir la extracción a $\mathcal{O}(\log n)$].
* **Ganancia Teórica Asintótica:** De $\mathcal{O}(\dots)$ a $\mathcal{O}(\dots)$.

---

## 3. Registro de Modificación en Vivo (Defensa Presencial)
*(Espacio reservado para anotar la modificación solicitada por el docente durante la defensa oral).*

* **Requisito solicitado por el docente:** 
* **Estrategia de resolución aplicada:**
