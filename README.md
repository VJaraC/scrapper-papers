# Plantilla Base de Evaluación Asimétrica
## Asignatura: Estructuras de Datos Avanzadas (IC10D – EDA)
**Universidad Arturo Prat (UNAP)**  
**Semestre:** 2026-02  
**Docente:** Mauricio Andrés Oyarzún Silva (`moyarzunsil@unap.cl`)

---

## 🎯 Instrucciones para el Estudiante

Este repositorio es la plantilla oficial obligatoria para el desarrollo y entrega de los desafíos prácticos bajo el modelo de **Evaluación Asimétrica**.

### 📁 Estructura del Repositorio

Tu repositorio debe mantener estrictamente la siguiente jerarquía de directorios:

```text
├── .gitignore          <- Configuración para ignorar caches, .venv y temporales
├── README.md           <- Este documento con las instrucciones y datos del estudiante
├── AUDIT.md            <- [En Aula] Informe de auditoría matemática y deuda técnica
├── design/             <- [En Aula] Diagramas arquitectónicos (editable y vectorial)
│   ├── structure.drawio
│   └── structure.svg
└── src/                <- [En Casa] Código fuente funcional asistido por IA
    └── main.py
```

---

## ⏱️ Fases del Modelo Asimétrico

### 🏠 Fase 1: Trabajo en Casa (Asistido por IA)
1. Desarrolla la estructura de datos solicitada en la carpeta `src/`.
2. Puedes usar libremente herramientas de IA generativa (**GitHub Copilot**, ChatGPT, Claude, etc.).
3. Asegúrate de que el código sea modular, tipado con *type hints* y funcional.
4. **Condición Crítica de Entrada:** Debes realizar `git commit` y `git push` a tu repositorio **antes del inicio oficial del bloque presencial**.

### 🏛️ Fase 2: Auditoría en Aula (Presencial, Individual y Sin IA)
1. **Modelado en `design/`:**
   * Crea el diagrama estático UML de Clases (`structure.drawio`).
   * Crea el diagrama dinámico UML de Secuencia para el flujo principal.
   * Exporta ambos en formato vectorial a `design/structure.svg`.
2. **Informe en `AUDIT.md`:**
   * Completa la **Matriz de Complejidad** con la derivación matemática formal $\mathcal{O}$.
   * Identifica y documenta **Deuda Técnica y Alucinaciones** introducidas por la IA.
3. **Defensa Oral y Modificación en Vivo (25%):**
   * El docente revisará tus diagramas, informe y solicitará una modificación en caliente de tu código.

---

## 📊 Rúbrica de Calificación Presencial (100%)

| Criterio | Ponderación | Entregable Auditado |
| :--- | :---: | :--- |
| **Fidelidad Arquitectónica** | 25% | Correspondencia estricta entre `src/` y diagramas en `design/` |
| **Modelado Dinámico** | 25% | Diagrama de secuencia con llamadas, tiempos y retornos en `design/` |
| **Análisis de Complejidad** | 25% | Deducción analítica del orden $\mathcal{O}$ en `AUDIT.md` |
| **Defensa Oral y Dominio** | 25% | Respuestas técnicas y modificación de código en vivo |

---

## 👤 Datos del Estudiante (Completar antes de entregar)
* **Nombre Completo:** ______________________________________
* **RUT:** ___________________
* **Correo Institucional:** __________________________________
* **Fecha del Taller:** ___________________
