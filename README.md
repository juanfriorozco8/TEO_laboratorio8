Universidad del Valle de Guatemala

Facultad de Ingeniería

Teoría de la Computación

Laboratorio 8: análisis de complejidad y tiempos de ejecución

Juan Francisco Orozco Mijangos (24647)

## Descripción del proyecto

En este laboratorio implementamos tres programas en C++ para estudiar cómo cambia el tiempo de ejecución cuando aumenta el tamaño de la entrada. Analizamos ciclos anidados, el efecto de un `break` y un ciclo que avanza de cuatro en cuatro. Calculamos la complejidad de cada programa y la comparamos con los tiempos que obtenemos al ejecutarlo.

Para automatizar las mediciones usamos un script en Python que compila los programas, los ejecuta con distintos valores de `n` y guarda los resultados en tablas CSV y gráficas. También resolvemos a mano los procedimientos de los tres programas, los casos de búsqueda lineal, búsqueda binaria y Quicksort, y las propiedades de notación asintótica del problema 5. Con esto relacionamos el análisis teórico con el comportamiento de nuestras implementaciones.

## Contenido del laboratorio

| Problema | Qué analizamos | Complejidad | Código |
| --- | --- | --- | --- |
| 1 | Tres ciclos anidados, con un índice que se duplica en el ciclo interno. | O(n² log n) | [Contador anidado](problema1_contador_anidado/main.cpp) |
| 2 | Un `break` que limita el ciclo interno a una iteración por cada vuelta del externo. | O(n) | [Secuencia con break](problema2_secuencia_break/main.cpp) |
| 3 | Un ciclo externo hasta `n/3` y un ciclo interno que avanza de cuatro en cuatro. | O(n²) | [Secuencia con paso de cuatro](problema3_secuencia_paso4/main.cpp) |

En el problema 4 determinamos el mejor caso, el caso promedio y el peor caso de búsqueda lineal, búsqueda binaria y Quicksort. En el problema 5 justificamos propiedades de la notación asintótica y analizamos el costo de crear subtuplas e insertarlas en un conjunto de Python. Incluimos estos ejercicios y los procedimientos de los problemas 1 a 3 en las [respuestas a mano](ejercicios_a_mano/respuestas.pdf).

## Instalación

Para ejecutar el proyecto utilizamos Python 3.10 o superior y un compilador GCC o Clang con soporte para C++17, disponible mediante el comando `c++`. Usamos Matplotlib para generar las gráficas.

Desde la carpeta del proyecto, creamos un entorno virtual, lo activamos e instalamos la dependencia. Estos comandos corresponden a macOS y Linux.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install matplotlib
```

Comprobamos las herramientas disponibles antes de ejecutar el laboratorio.

```bash
python --version
c++ --version
```

## Ejecución

El script compila automáticamente cada programa con C++17 y guarda los ejecutables en una carpeta temporal. Para ejecutar un problema y mostrar su salida, indicamos el número del problema y un valor de `n` entre 1 y 1000000.

```bash
python profiling.py --problema 1 --ejecutar 100
```

Podemos seleccionar los problemas 1, 2 o 3. El primero muestra el valor de `counter` y los otros dos imprimen `Sequence` según sus respectivos ciclos.

### Medición de tiempos

Para procesar los tres programas y generar sus tablas y gráficas ejecutamos el siguiente comando.

```bash
python profiling.py
```

Trabajamos con los tamaños `1`, `10`, `100`, `1000`, `10000`, `100000` y `1000000`. El script conserva las mediciones que ya están completas y vuelve a intentar las que excedieron el límite. Por defecto, usamos una muestra por tamaño y un límite de cinco segundos por proceso.

Para volver a medir un problema completo con tres muestras por tamaño usamos `--repetir` y `--muestras`. Guardamos la mediana de las muestras terminadas.

```bash
python profiling.py --problema 2 --repetir --muestras 3
```

Podemos ajustar el límite de tiempo por proceso o ejecutar las mediciones hasta que terminen.

```bash
python profiling.py --problema 3 --limite 30
python profiling.py --problema 1 --sin-limite
```

Medimos el tiempo dentro de cada programa de C++ con `steady_clock`. Durante el profiling, Python descarta la salida estándar de los programas para evitar que las impresiones llenen la terminal.

## Resultados

| Problema | Tabla de tiempos | Gráfica |
| --- | --- | --- |
| 1 | [Tabla CSV](problema1_contador_anidado/tabla.csv) | [Tamaño de entrada y tiempo](problema1_contador_anidado/grafica.png) |
| 2 | [Tabla CSV](problema2_secuencia_break/tabla.csv) | [Tamaño de entrada y tiempo](problema2_secuencia_break/grafica.png) |
| 3 | [Tabla CSV](problema3_secuencia_paso4/tabla.csv) | [Tamaño de entrada y tiempo](problema3_secuencia_paso4/grafica.png) |

En las tablas registramos `n`, el tiempo en segundos, el estado de la medición, las repeticiones por muestra, la cantidad de muestras y el límite utilizado. Cuando un proceso supera ese límite sin completar una muestra, guardamos `limite_excedido` y dejamos vacío el tiempo. Las gráficas incluyen una vista lineal y otra logarítmica.

## Pruebas de funcionamiento

Comprobamos los tres programas con una entrada pequeña para poder revisar sus resultados directamente.

```bash
python profiling.py --problema 1 --ejecutar 10
python profiling.py --problema 2 --ejecutar 10
python profiling.py --problema 3 --ejecutar 10
```

| Problema | Resultado esperado para `n = 10` | Comprobación |
| --- | --- | --- |
| 1 | `counter = 120` | 6 iteraciones externas × 5 intermedias × 4 internas. |
| 2 | 10 líneas con `Sequence`. | Una impresión por cada iteración externa. |
| 3 | 9 líneas con `Sequence`. | 3 iteraciones externas × 3 internas. |

También comprobamos el caso `n = 1` de los problemas 2 y 3, que termina sin imprimir secuencias.

```bash
python profiling.py --problema 2 --ejecutar 1
python profiling.py --problema 3 --ejecutar 1
```

Para revisar los argumentos disponibles consultamos la ayuda del script.

```bash
python profiling.py --help
```
