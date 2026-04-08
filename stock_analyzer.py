#!/usr/bin/env python3
"""
Sistema de Análisis Bursátil en Terminal - NYSE
Similar a Lightspeed pero en consola
Autor: Asistente de Código
"""

import curses
import time
import threading
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Tuple
import math


class StockData:
    """Clase para almacenar y gestionar datos de una acción"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.prices: deque = deque(maxlen=200)  # Últimos 200 precios
        self.volumes: deque = deque(maxlen=200)
        self.highs: deque = deque(maxlen=200)
        self.lows: deque = deque(maxlen=200)
        self.opens: deque = deque(maxlen=200)
        self.closes: deque = deque(maxlen=200)
        self.timestamps: deque = deque(maxlen=200)
        self.current_price: float = 0.0
        self.previous_close: float = 0.0
        self.change: float = 0.0
        self.change_percent: float = 0.0
        self.last_update: datetime = None
        self.ticker = None
        
    def initialize(self):
        """Inicializar datos históricos"""
        try:
            self.ticker = yf.Ticker(self.symbol)
            hist = self.ticker.history(period="5d", interval="1m")
            
            if not hist.empty:
                self.previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[0]
                
                for idx, row in hist.iterrows():
                    self.prices.append(row['Close'])
                    self.volumes.append(row['Volume'])
                    self.highs.append(row['High'])
                    self.lows.append(row['Low'])
                    self.opens.append(row['Open'])
                    self.closes.append(row['Close'])
                    self.timestamps.append(idx)
                
                if self.prices:
                    self.current_price = self.prices[-1]
                    self.change = self.current_price - self.previous_close
                    self.change_percent = (self.change / self.previous_close) * 100
                    self.last_update = datetime.now()
                    
            return True
        except Exception as e:
            print(f"Error inicializando {self.symbol}: {e}")
            return False
    
    def update(self):
        """Actualizar con el último precio"""
        try:
            if self.ticker:
                data = self.ticker.history(period="1d", interval="1m")
                if not data.empty:
                    latest = data.iloc[-1]
                    self.prices.append(latest['Close'])
                    self.volumes.append(latest['Volume'])
                    self.highs.append(latest['High'])
                    self.lows.append(latest['Low'])
                    self.opens.append(latest['Open'])
                    self.closes.append(latest['Close'])
                    self.timestamps.append(data.index[-1])
                    
                    self.current_price = latest['Close']
                    self.change = self.current_price - self.previous_close
                    self.change_percent = (self.change / self.previous_close) * 100
                    self.last_update = datetime.now()
                    return True
        except Exception as e:
            pass
        return False


class TechnicalIndicators:
    """Cálculo de indicadores técnicos"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calcular RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        prices = list(prices)[-period-1:]
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(list(prices)[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        prices = list(prices)[-period:]
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    @staticmethod
    def calculate_alligator(prices: List[float]) -> Dict[str, Optional[float]]:
        """
        Calcula el indicador Alligator de Bill Williams
        - Jaw (Mandíbula): SMA 13, desplazado 8 períodos
        - Teeth (Dientes): SMA 8, desplazado 5 períodos
        - Lips (Labios): SMA 5, desplazado 3 períodos
        """
        result = {
            'jaw': None,
            'teeth': None,
            'lips': None
        }
        
        if len(prices) < 21:  # Necesitamos al menos 13 + 8
            return result
        
        prices_list = list(prices)
        
        # Jaw: SMA 13 desplazado 8
        if len(prices_list) >= 21:
            jaw_prices = prices_list[-21:-8]
            if len(jaw_prices) >= 13:
                result['jaw'] = sum(jaw_prices[-13:]) / 13
        
        # Teeth: SMA 8 desplazado 5
        if len(prices_list) >= 13:
            teeth_prices = prices_list[-13:-5]
            if len(teeth_prices) >= 8:
                result['teeth'] = sum(teeth_prices[-8:]) / 8
        
        # Lips: SMA 5 desplazado 3
        if len(prices_list) >= 8:
            lips_prices = prices_list[-8:-3]
            if len(lips_prices) >= 5:
                result['lips'] = sum(lips_prices[-5:]) / 5
        
        return result
    
    @staticmethod
    def calculate_volume_sma(volumes: List[int], period: int = 20) -> Optional[float]:
        """Volume Simple Moving Average"""
        if len(volumes) < period:
            return None
        return sum(list(volumes)[-period:]) / period


class ChartRenderer:
    """Renderizado de gráficos en terminal"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.chars = {
            'candle_up': '│',
            'candle_down': '│',
            'line': '─',
            'axis': '┼',
            'grid': '·'
        }
    
    def draw_price_chart(self, win, prices: List[float], 
                         indicators: Dict, height: int, width: int,
                         title: str):
        """Dibujar gráfico de precios con velas/líneas"""
        if not prices or len(prices) < 2:
            win.addstr(0, 0, "Datos insuficientes")
            return
        
        win.clear()
        win.border()
        
        # Título
        win.addstr(0, 2, f" {title} ", curses.A_BOLD)
        
        # Calcular rango de precios
        min_price = min(prices[-width+10:]) if len(prices) > width-10 else min(prices)
        max_price = max(prices[-width+10:]) if len(prices) > width-10 else max(prices)
        price_range = max_price - min_price
        
        if price_range == 0:
            price_range = 1
        
        # Dibujar eje Y con etiquetas de precio
        label_width = 8
        chart_start_x = label_width
        
        for i in range(height - 2):
            y_pos = height - 3 - i
            price_level = min_price + (i / (height - 3)) * price_range
            label = f"${price_level:.2f}"
            try:
                win.addstr(y_pos, 0, label[:label_width])
            except:
                pass
        
        # Dibujar gráfico de líneas
        visible_prices = prices[-(width - label_width - 5):] if len(prices) > width - label_width - 5 else prices
        
        prev_y = None
        for i, price in enumerate(visible_prices):
            x_pos = chart_start_x + i
            if x_pos >= width - 1:
                break
            
            # Normalizar precio a posición Y
            normalized = (price - min_price) / price_range
            y_pos = height - 3 - int(normalized * (height - 3))
            y_pos = max(1, min(y_pos, height - 2))
            
            if prev_y is not None:
                # Dibujar línea conectando puntos
                try:
                    win.addch(y_pos, x_pos, '·')
                except:
                    pass
            prev_y = y_pos
        
        # Dibujar indicadores si existen
        self._draw_indicators(win, indicators, height, width, chart_start_x, min_price, price_range)
        
        # Información adicional
        info_y = height - 1
        if len(prices) > 0:
            current = prices[-1]
            info = f"Actual: ${current:.2f} | Min: ${min_price:.2f} | Max: ${max_price:.2f}"
            try:
                win.addstr(info_y, 1, info[:width-2])
            except:
                pass
        
        win.refresh()
    
    def _draw_indicators(self, win, indicators: Dict, height: int, width: int,
                        start_x: int, min_price: float, price_range: float):
        """Dibujar indicadores en el gráfico"""
        # Alligator lines
        if 'alligator' in indicators and indicators['alligator']:
            alligator = indicators['alligator']
            colors = [
                ('jaw', 4),    # Azul
                ('teeth', 2),  # Rojo
                ('lips', 1)    # Verde
            ]
            
            for name, color in colors:
                if alligator.get(name):
                    try:
                        normalized = (alligator[name] - min_price) / price_range
                        y_pos = height - 3 - int(normalized * (height - 3))
                        y_pos = max(1, min(y_pos, height - 2))
                        
                        # Usar diferentes caracteres para cada línea
                        char = {'jaw': '-', 'teeth': '=', 'lips': '.'}[name]
                        for x in range(start_x, width - 1):
                            try:
                                win.addch(y_pos, x, char, curses.color_pair(color))
                            except:
                                pass
                    except:
                        pass
    
    def draw_volume_chart(self, win, volumes: List[int], prices: List[float],
                         height: int, width: int):
        """Dibujar gráfico de volumen"""
        if not volumes:
            return
        
        win.clear()
        win.border()
        win.addstr(0, 2, " Volumen ", curses.A_BOLD)
        
        max_vol = max(volumes[-width+10:]) if len(volumes) > width-10 else max(volumes)
        if max_vol == 0:
            max_vol = 1
        
        visible_volumes = volumes[-(width - 10):] if len(volumes) > width - 10 else volumes
        visible_prices = prices[-(width - 10):] if len(prices) > width - 10 else prices
        
        bar_width = max(1, (width - 10) // len(visible_volumes))
        
        for i, (vol, price) in enumerate(zip(visible_volumes, visible_prices)):
            x_pos = 5 + i * bar_width
            if x_pos >= width - 5:
                break
            
            bar_height = int((vol / max_vol) * (height - 3))
            bar_height = max(1, min(bar_height, height - 3))
            
            # Color según si el precio subió o bajó
            color = 2 if i > 0 and price >= visible_prices[i-1] else 3
            
            for h in range(bar_height):
                try:
                    win.addch(height - 2 - h, x_pos, '█', curses.color_pair(color))
                except:
                    pass
        
        win.refresh()
    
    def draw_rsi_chart(self, win, rsi_values: List[float], height: int, width: int):
        """Dibujar gráfico de RSI"""
        if not rsi_values:
            return
        
        win.clear()
        win.border()
        win.addstr(0, 2, " RSI (14) ", curses.A_BOLD)
        
        # Líneas de sobrecompra/sobreventa
        overbought_y = height - 3 - int(0.7 * (height - 3))
        oversold_y = height - 3 - int(0.3 * (height - 3))
        
        try:
            for x in range(5, width - 5):
                win.addch(overbought_y, x, '─', curses.color_pair(8))
                win.addch(oversold_y, x, '─', curses.color_pair(8))
        except:
            pass
        
        try:
            win.addstr(overbought_y, width - 10, "70", curses.color_pair(8))
            win.addstr(oversold_y, width - 10, "30", curses.color_pair(8))
        except:
            pass
        
        # Dibujar línea RSI
        visible_rsi = rsi_values[-(width - 10):] if len(rsi_values) > width - 10 else rsi_values
        
        prev_y = None
        for i, rsi in enumerate(visible_rsi):
            x_pos = 5 + i
            if x_pos >= width - 5:
                break
            
            normalized = rsi / 100
            y_pos = height - 3 - int(normalized * (height - 3))
            y_pos = max(1, min(y_pos, height - 2))
            
            # Color según nivel
            color = 2 if rsi < 30 else (3 if rsi > 70 else 0)
            
            try:
                win.addch(y_pos, x_pos, '·', curses.color_pair(color))
            except:
                pass
        
        # Valor actual de RSI
        if rsi_values:
            current_rsi = rsi_values[-1]
            try:
                win.addstr(height - 1, 1, f"RSI: {current_rsi:.2f}", curses.A_BOLD)
            except:
                pass
        
        win.refresh()


class StockTerminal:
    """Clase principal del sistema"""
    
    def __init__(self, stdscr, symbols: List[str] = None):
        self.stdscr = stdscr
        self.symbols = symbols if symbols else ['SBUX', 'AAL']
        self.stocks: Dict[str, StockData] = {}
        self.running = True
        self.update_interval = 5  # segundos
        self.selected_stock = 0
        self.show_indicators = True
        self.chart_renderer = ChartRenderer(stdscr)
        
        # Layout
        self.main_win = None
        self.side_panel = None
        self.indicator_win = None
        self.volume_win = None
        self.rsi_win = None
        
        # Datos históricos para indicadores
        self.rsi_history: Dict[str, deque] = {}
        
    def setup_colors(self):
        """Configurar colores de la terminal"""
        curses.start_color()
        curses.use_default_colors()
        
        # Pares de colores
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Verde - suba
        curses.init_pair(2, curses.COLOR_RED, -1)     # Rojo - baja
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Amarillo
        curses.init_pair(4, curses.COLOR_BLUE, -1)    # Azul
        curses.init_pair(5, curses.COLOR_CYAN, -1)    # Cyan
        curses.init_pair(6, curses.COLOR_MAGENTA, -1) # Magenta
        curses.init_pair(7, curses.COLOR_WHITE, -1)   # Blanco
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Negro sobre blanco
    
    def initialize_stocks(self):
        """Inicializar todas las acciones"""
        for symbol in self.symbols:
            stock = StockData(symbol)
            if stock.initialize():
                self.stocks[symbol] = stock
                self.rsi_history[symbol] = deque(maxlen=100)
                # Calcular RSI inicial
                rsi = TechnicalIndicators.calculate_rsi(list(stock.prices))
                if rsi:
                    self.rsi_history[symbol].append(rsi)
    
    def create_windows(self):
        """Crear ventanas de la interfaz"""
        height, width = self.stdscr.getmaxyx()
        
        # Ventana principal de gráficos (60% del ancho)
        chart_width = int(width * 0.6)
        self.main_win = curses.newwin(height - 8, chart_width, 0, 0)
        
        # Panel lateral (40% del ancho)
        side_width = width - chart_width
        self.side_panel = curses.newwin(height - 8, side_width, 0, chart_width)
        
        # Ventana de indicadores (mitad inferior izquierda)
        indicator_height = (height - 8) // 2
        self.indicator_win = curses.newwin(indicator_height, chart_width, 
                                           height - 8 - indicator_height, 0)
        
        # Ventana de volumen
        self.volume_win = curses.newwin(indicator_height, chart_width // 2,
                                        height - 8 - indicator_height, 0)
        
        # Ventana de RSI
        self.rsi_win = curses.newwin(indicator_height, chart_width // 2,
                                     height - 8 - indicator_height, chart_width // 2)
    
    def draw_side_panel(self):
        """Dibujar panel lateral con información de acciones"""
        if not self.side_panel:
            return
        
        self.side_panel.clear()
        self.side_panel.border()
        self.side_panel.addstr(0, 2, " COTIZACIONES ", curses.A_BOLD)
        
        height, width = self.side_panel.getmaxyx()
        
        # Encabezados
        header = f"{'Símbolo':<8} {'Precio':>10} {'Cambio':>10} {'%':>8}"
        try:
            self.side_panel.addstr(2, 1, header[:width-2])
        except:
            pass
        
        # Lista de acciones
        y_pos = 4
        for i, symbol in enumerate(self.stocks.keys()):
            stock = self.stocks[symbol]
            
            # Formato de precio
            price_str = f"${stock.current_price:.2f}"
            
            # Formato de cambio con color
            change = stock.change
            change_pct = stock.change_percent
            
            if change >= 0:
                change_str = f"+{change:.2f}"
                pct_str = f"+{change_pct:.2f}%"
                color = curses.color_pair(1)  # Verde
            else:
                change_str = f"{change:.2f}"
                pct_str = f"{change_pct:.2f}%"
                color = curses.color_pair(2)  # Rojo
            
            # Resaltar acción seleccionada
            attr = curses.A_REVERSE if i == self.selected_stock else curses.A_NORMAL
            
            try:
                line = f"{symbol:<8} {price_str:>10} {change_str:>10} {pct_str:>8}"
                self.side_panel.addstr(y_pos, 1, line[:width-2], color | attr)
                
                # Última actualización
                if stock.last_update:
                    update_str = f"Actualizado: {stock.last_update.strftime('%H:%M:%S')}"
                    self.side_panel.addstr(y_pos + 1, 1, update_str[:width-2], curses.A_DIM)
                
                y_pos += 3
            except:
                pass
        
        # Instrucciones
        instructions_y = height - 8
        try:
            self.side_panel.addstr(instructions_y, 1, " CONTROLES ", curses.A_BOLD)
            self.side_panel.addstr(instructions_y + 1, 1, "↑/↓: Cambiar acción")
            self.side_panel.addstr(instructions_y + 2, 1, "+: Agregar acción")
            self.side_panel.addstr(instructions_y + 3, 1, "-: Remover acción")
            self.side_panel.addstr(instructions_y + 4, 1, "i: Toggle indicadores")
            self.side_panel.addstr(instructions_y + 5, 1, "q: Salir")
        except:
            pass
        
        self.side_panel.refresh()
    
    def draw_header(self):
        """Dibujar encabezado superior"""
        height, width = self.stdscr.getmaxyx()
        
        title = " SISTEMA DE ANÁLISIS BURSÁTIL - NYSE "
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD | curses.A_REVERSE)
            self.stdscr.addstr(0, width - len(timestamp) - 1, timestamp)
        except:
            pass
    
    def draw_footer(self):
        """Dibujar pie de página"""
        height, width = self.stdscr.getmaxyx()
        
        market_status = "MERCADO ABIERTO" if self.is_market_open() else "MERCADO CERRADO"
        status_color = curses.color_pair(1) if self.is_market_open() else curses.color_pair(3)
        
        try:
            self.stdscr.addstr(height - 1, 1, f" Estado: {market_status}", status_color)
            self.stdscr.addstr(height - 1, width - 20, "v1.0")
        except:
            pass
    
    def is_market_open(self) -> bool:
        """Verificar si el mercado NYSE está abierto"""
        now = datetime.now()
        
        # Horario NYSE: 9:30 AM - 4:00 PM ET (Lunes a Viernes)
        if now.weekday() >= 5:  # Fin de semana
            return False
        
        hour = now.hour
        minute = now.minute
        
        # Convertir a ET (aproximado, asumiendo UTC-5)
        et_hour = (hour - 5) % 24
        
        if et_hour < 9 or (et_hour == 9 and minute < 30):
            return False
        if et_hour >= 16:
            return False
        
        return True
    
    def update_data(self):
        """Actualizar datos de todas las acciones"""
        for symbol, stock in self.stocks.items():
            stock.update()
            
            # Actualizar RSI
            rsi = TechnicalIndicators.calculate_rsi(list(stock.prices))
            if rsi:
                self.rsi_history[symbol].append(rsi)
    
    def add_stock(self, symbol: str):
        """Agregar nueva acción"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            stock = StockData(symbol)
            if stock.initialize():
                self.stocks[symbol] = stock
                self.rsi_history[symbol] = deque(maxlen=100)
                rsi = TechnicalIndicators.calculate_rsi(list(stock.prices))
                if rsi:
                    self.rsi_history[symbol].append(rsi)
                self.symbols.append(symbol)
    
    def remove_stock(self, symbol: str):
        """Remover acción"""
        symbol = symbol.upper()
        if symbol in self.stocks and len(self.stocks) > 1:
            del self.stocks[symbol]
            del self.rsi_history[symbol]
            self.symbols.remove(symbol)
            if self.selected_stock >= len(self.symbols):
                self.selected_stock = len(self.symbols) - 1
    
    def get_current_stock(self) -> Optional[StockData]:
        """Obtener acción actualmente seleccionada"""
        if not self.stocks:
            return None
        
        symbol = list(self.stocks.keys())[self.selected_stock]
        return self.stocks[symbol]
    
    def run(self):
        """Bucle principal"""
        self.setup_colors()
        self.initialize_stocks()
        
        last_update = 0
        
        while self.running:
            try:
                # Crear/redimensionar ventanas
                self.create_windows()
                
                # Dibujar interfaz
                self.draw_header()
                
                # Obtener acción actual
                current_stock = self.get_current_stock()
                
                if current_stock:
                    # Calcular indicadores
                    indicators = {
                        'rsi': TechnicalIndicators.calculate_rsi(list(current_stock.prices)),
                        'alligator': TechnicalIndicators.calculate_alligator(list(current_stock.prices)),
                        'sma_20': TechnicalIndicators.calculate_sma(list(current_stock.prices), 20),
                        'ema_12': TechnicalIndicators.calculate_ema(list(current_stock.prices), 12),
                    }
                    
                    # Dibujar gráfico principal
                    height, width = self.main_win.getmaxyx()
                    self.chart_renderer.draw_price_chart(
                        self.main_win,
                        list(current_stock.prices),
                        indicators,
                        height,
                        width,
                        f" {current_stock.symbol} - Precio "
                    )
                    
                    # Dibujar panel lateral
                    self.draw_side_panel()
                    
                    # Dibujar RSI
                    if current_stock.symbol in self.rsi_history and self.rsi_history[current_stock.symbol]:
                        height, width = self.rsi_win.getmaxyx()
                        self.chart_renderer.draw_rsi_chart(
                            self.rsi_win,
                            list(self.rsi_history[current_stock.symbol]),
                            height,
                            width
                        )
                    
                    # Dibujar volumen
                    height, width = self.volume_win.getmaxyx()
                    self.chart_renderer.draw_volume_chart(
                        self.volume_win,
                        list(current_stock.volumes),
                        list(current_stock.prices),
                        height,
                        width
                    )
                
                # Dibujar footer
                self.draw_footer()
                
                self.stdscr.refresh()
                
                # Actualizar datos periódicamente
                current_time = time.time()
                if current_time - last_update >= self.update_interval:
                    self.update_data()
                    last_update = current_time
                
                # Pequeña pausa para no saturar CPU
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                # En caso de error, continuar ejecutando
                try:
                    self.stdscr.addstr(1, 1, f"Error: {str(e)[:50]}")
                except:
                    pass
                time.sleep(1)


def main(stdscr):
    """Función principal para curses"""
    # Configuración de la pantalla
    curses.curs_set(0)  # Ocultar cursor
    stdscr.nodelay(True)  # No bloquear en input
    stdscr.timeout(100)  # Timeout para refresh
    
    # Crear aplicación
    app = StockTerminal(stdscr, ['SBUX', 'AAL'])
    
    # Bucle de eventos
    while app.running:
        app.run()
        
        # Manejar input del usuario
        try:
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                app.running = False
            elif key == curses.KEY_UP:
                app.selected_stock = max(0, app.selected_stock - 1)
            elif key == curses.KEY_DOWN:
                app.selected_stock = min(len(app.stocks) - 1, app.selected_stock + 1)
            elif key == ord('+') or key == ord('='):
                # Pedir símbolo para agregar
                curses.echo()
                curses.curs_set(1)
                stdscr.nodelay(False)
                
                stdscr.addstr(curses.LINES - 2, 1, "Ingrese símbolo (ej: AAPL): ")
                stdscr.refresh()
                
                try:
                    symbol = stdscr.getstr(curses.LINES - 2, 30, 10).decode('utf-8').strip()
                    if symbol:
                        app.add_stock(symbol)
                except:
                    pass
                
                curses.noecho()
                curses.curs_set(0)
                stdscr.nodelay(True)
                stdscr.timeout(100)
            elif key == ord('-'):
                # Remover acción actual
                current_symbol = list(app.stocks.keys())[app.selected_stock]
                app.remove_stock(current_symbol)
            elif key == ord('i') or key == ord('I'):
                app.show_indicators = not app.show_indicators
                
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE ANÁLISIS BURSÁTIL - NYSE")
    print("=" * 60)
    print("\nIniciando aplicación...")
    print("\nAcciones cargadas: SBUX, AAL")
    print("\nControles:")
    print("  ↑/↓ : Cambiar entre acciones")
    print("  +   : Agregar nueva acción")
    print("  -   : Remover acción actual")
    print("  i   : Mostrar/ocultar indicadores")
    print("  q   : Salir")
    print("\nPresione Ctrl+C para salir en cualquier momento\n")
    print("=" * 60)
    
    time.sleep(2)
    
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n\nAplicación terminada por el usuario.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("Asegúrese de tener una terminal compatible con curses.")
