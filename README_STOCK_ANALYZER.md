# Sistema de Análisis Bursátil - NYSE

Sistema de análisis de acciones bursátiles en terminal, similar a Lightspeed pero en consola.

## Características

- **Visualización en tiempo real** de cotizaciones de la bolsa de Nueva York (NYSE)
- **Gráficos de precios** que se actualizan automáticamente
- **Indicadores técnicos**:
  - RSI (Relative Strength Index)
  - Alligator (Bill Williams)
  - Volumen con medias móviles
  - SMA (Simple Moving Average)
  - EMA (Exponential Moving Average)
- **Panel lateral** con lista de acciones y cambios de precio
- **Colores diferenciados**: 
  - 🟢 Verde: Precio sube respecto al cierre anterior
  - 🔴 Rojo: Precio baja respecto al cierre anterior
- **Múltiples ventanas** de visualización simultánea
- **Datos en tiempo real** desde Yahoo Finance

## Acciones por defecto

- **SBUX** - Starbucks Corporation
- **AAL** - American Airlines Group Inc.

## Requisitos

- Python 3.8+
- Terminal compatible con curses (Linux, macOS, WSL en Windows)

## Instalación de dependencias

```bash
pip install yfinance numpy pandas matplotlib rich
```

## Ejecución

```bash
python stock_analyzer.py
```

## Controles

| Tecla | Acción |
|-------|--------|
| ↑ / ↓ | Cambiar entre acciones |
| + | Agregar nueva acción |
| - | Remover acción actual |
| i | Mostrar/ocultar indicadores |
| q | Salir del programa |

## Estructura de la interfaz

```
┌─────────────────────────────────────────────────────────────┐
│        SISTEMA DE ANÁLISIS BURSÁTIL - NYSE    2024-01-01   │
├──────────────────────────────┬──────────────────────────────┤
│                              │  COTIZACIONES                │
│   GRÁFICO DE PRECIOS         │                              │
│   (con líneas Alligator)     │  SBUX  $95.22  +0.45  +0.47% │
│                              │  AAL   $10.81  -0.12  -1.10% │
│                              │                              │
├──────────────┬───────────────┤  CONTROLES                   │
│   VOLUMEN    │     RSI       │  ↑/↓: Cambiar acción         │
│              │               │  +: Agregar acción           │
│              │  [30]──[70]   │  -: Remover acción           │
│              │               │  i: Toggle indicadores       │
└──────────────┴───────────────┘  q: Salir                    │
└─────────────────────────────────────────────────────────────┘
```

## Arquitectura del código

### Clases principales

1. **StockData**: Gestiona los datos de cada acción
   - Almacena historial de precios, volúmenes, highs, lows
   - Calcula cambios porcentuales
   - Se actualiza automáticamente desde Yahoo Finance

2. **TechnicalIndicators**: Calcula indicadores técnicos
   - `calculate_rsi()`: Índice de Fuerza Relativa
   - `calculate_alligator()`: Indicador de Bill Williams
   - `calculate_sma()`: Media Móvil Simple
   - `calculate_ema()`: Media Móvil Exponencial

3. **ChartRenderer**: Renderiza gráficos en terminal
   - `draw_price_chart()`: Gráfico de precios principal
   - `draw_volume_chart()`: Barras de volumen
   - `draw_rsi_chart()`: Gráfico de RSI con niveles

4. **StockTerminal**: Clase principal de la aplicación
   - Gestiona la interfaz curses
   - Coordina ventanas y actualizaciones
   - Maneja input del usuario

## Personalización

### Agregar más acciones

Puede agregar acciones durante la ejecución presionando `+` e ingresando el símbolo (ej: AAPL, GOOGL, MSFT, TSLA).

También puede modificar la lista inicial en el código:

```python
app = StockTerminal(stdscr, ['SBUX', 'AAL', 'AAPL', 'TSLA'])
```

### Cambiar intervalo de actualización

Modifique `self.update_interval` en la clase `StockTerminal`:

```python
self.update_interval = 5  # segundos entre actualizaciones
```

### Modificar períodos de indicadores

En la clase `TechnicalIndicators`, ajuste los parámetros:

```python
# RSI con período personalizado
rsi = TechnicalIndicators.calculate_rsi(prices, period=14)

# SMA con diferente período
sma = TechnicalIndicators.calculate_sma(prices, period=50)
```

## Notas importantes

1. **Horario de mercado**: El sistema detecta si el mercado NYSE está abierto (9:30 AM - 4:00 PM ET, Lunes-Viernes)

2. **Datos históricos**: Durante el cierre del mercado, se muestran los últimos datos disponibles

3. **Requisitos de terminal**: 
   - Tamaño mínimo recomendado: 120x40 caracteres
   - Soporte para colores y caracteres Unicode

4. **Fuente de datos**: Yahoo Finance (gratuito, puede tener delay de 15 minutos)

## Troubleshooting

### Error: "terminal too small"
Aumente el tamaño de su terminal a al menos 120x40 caracteres.

### Error: "no data available"
Verifique su conexión a internet. Los datos pueden no estar disponibles fuera del horario de mercado.

### Error: "curses not supported"
En Windows, use WSL (Windows Subsystem for Linux) o una terminal compatible como Cmder con ANSI habilitado.

## Licencia

Código de ejemplo para fines educativos.

## Autor

Asistente de Código - 2024
