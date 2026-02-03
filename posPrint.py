# add user privileges to access /dev/usb/lp0
# sudo usermod -a -G lp username

class POSPrinter:
    """Class for working with thermal POS printer via /dev/usb/lp0"""
    
    # ESC/POS commands
    ESC = b'\x1b'
    GS = b'\x1d'
    
    # Initialization
    INIT = ESC + b'@'
    
    # Alignment
    ALIGN_LEFT = ESC + b'a\x00'
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_RIGHT = ESC + b'a\x02'
    
    # Font sizes (ESC ! n)
    FONT_NORMAL = ESC + b'!\x00'
    FONT_BOLD = ESC + b'!\x08'
    FONT_DOUBLE_HEIGHT = ESC + b'!\x10'
    FONT_DOUBLE_WIDTH = ESC + b'!\x20'
    FONT_LARGE = ESC + b'!\x30'  # Double width + height
    
    # Underline
    UNDERLINE_OFF = ESC + b'\x2d\x00'
    UNDERLINE_ON = ESC + b'\x2d\x01'
    UNDERLINE_THICK = ESC + b'\x2d\x02'
    
    # Inverse (white text on black)
    INVERSE_ON = GS + b'B\x01'
    INVERSE_OFF = GS + b'B\x00'
    
    # Paper cut
    CUT_PAPER = GS + b'V\x00'
    
    def __init__(self, device='/dev/usb/lp0'):
        self.device = device
    
    def sanitize_text(self, text):
        """Replace Ukrainian symbols for cp866"""
        replacements = {
            'і': 'i', 'І': 'I',
            'ї': 'i', 'Ї': 'I',
            'є': 'e', 'Є': 'E',
            'ґ': 'g', 'Ґ': 'G'
        }
        for ukr, lat in replacements.items():
            text = text.replace(ukr, lat)
        return text
    
    def print_raw(self, data):
        """Print raw bytes"""
        try:
            with open(self.device, 'wb') as f:
                f.write(data)
        except FileNotFoundError:
            print(f"Device {self.device} not found. Check printer connection.")
        except PermissionError:
            print(f"No access permission to {self.device}. Run: sudo usermod -a -G lp $USER")
    
    def print_text(self, text, encoding='cp866'):
        """Print text with automatic character replacement"""
        safe_text = self.sanitize_text(text)
        self.print_raw(safe_text.encode(encoding, errors='replace'))
    
    def print_line(self, text='', align='left', bold=False, underline=False, large=False):
        """Print line with formatting"""
        commands = [self.INIT]
        
        # Вирівнювання
        if align == 'center':
            commands.append(self.ALIGN_CENTER)
        elif align == 'right':
            commands.append(self.ALIGN_RIGHT)
        else:
            commands.append(self.ALIGN_LEFT)
        
        # Розмір та стиль
        if large:
            commands.append(self.FONT_LARGE)
        elif bold:
            commands.append(self.FONT_BOLD)
        else:
            commands.append(self.FONT_NORMAL)
        
        # Підкреслення
        if underline:
            commands.append(self.UNDERLINE_ON)
        
        # Друк
        for cmd in commands:
            self.print_raw(cmd)
        
        self.print_text(text + '\n')
        
        # Reset
        self.print_raw(self.UNDERLINE_OFF)
        self.print_raw(self.FONT_NORMAL)
    
    def print_separator(self, char='=', width=32):
        """Print separator line"""
        self.print_text(char * width + '\n')
    
    def draw_box(self, text, width=32):
        """Draw box around text"""
        # Pseudographics symbols for cp866
        lines = text.split('\n')
        top = '┌' + '─' * (width - 2) + '┐'
        bottom = '└' + '─' * (width - 2) + '┘'
        
        self.print_text(top + '\n')
        for line in lines:
            padded = line.ljust(width - 4)
            self.print_text(f'│ {padded} │\n')
        self.print_text(bottom + '\n')
    
    def plot_graph(self, data, width=32, height=10, title="Graph"):
        """Draw graph from array of points"""
        if not data:
            return
        
        # Normalize data
        min_val = min(data)
        max_val = max(data)
        value_range = max_val - min_val if max_val != min_val else 1
        
        self.print_line(title, align='center', bold=True)
        self.print_separator('─')
        
        # Create graph grid
        for row in range(height, -1, -1):
            line = ''
            threshold = min_val + (value_range * row / height)
            
            for i, value in enumerate(data):
                if len(line) >= width - 5:
                    break
                if value >= threshold:
                    line += '█'
                else:
                    line += ' '
            
            # Scale value
            label = f"{threshold:5.1f}"
            self.print_text(f'{label}|{line}\n')
        
        # X axis
        self.print_text('     +' + '─' * min(len(data), width - 6) + '\n')
        self.print_separator()
    
    def plot_bar_chart(self, labels, values, width=32):
        """Draw bar chart"""
        if not labels or not values or len(labels) != len(values):
            return
        
        max_val = max(values) if values else 1
        max_label_len = max(len(str(l)) for l in labels)
        bar_width = width - max_label_len - 8
        
        self.print_line("Bar Chart", align='center', bold=True)
        self.print_separator('=')
        
        for label, value in zip(labels, values):
            bar_len = int((value / max_val) * bar_width) if max_val > 0 else 0
            bar = '█' * bar_len
            label_str = str(label).ljust(max_label_len)
            self.print_text(f'{label_str} {value:5.1f} |{bar}\n')
        
        self.print_separator()
    
    def print_ascii_art(self, art):
        """Print ASCII art"""
        self.print_raw(self.ALIGN_CENTER)
        self.print_text(art + '\n')
        self.print_raw(self.ALIGN_LEFT)
    
    def print_table(self, headers, rows, col_widths=None):
        """Print table"""
        if not headers or not rows:
            return
        
        # Автоматичне визначення ширини колонок
        if col_widths is None:
            col_widths = [max(len(str(h)), max(len(str(row[i])) for row in rows if i < len(row))) 
                         for i, h in enumerate(headers)]
        
        # Table header
        header_line = ' | '.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        self.print_text(header_line + '\n')
        self.print_separator('-', sum(col_widths) + len(headers) * 3 - 1)
        
        # Table rows
        for row in rows:
            row_line = ' | '.join(str(row[i]).ljust(col_widths[i]) if i < len(row) else ' ' * col_widths[i] 
                                 for i in range(len(headers)))
            self.print_text(row_line + '\n')
    
    def print_qr_placeholder(self, text):
        """QR code placeholder (requires additional commands)"""
        self.print_line("[ QR Code ]", align='center')
        self.print_line(f"Data: {text}", align='center')
    
    def feed_and_cut(self, lines=3):
        """Feed paper and cut (if supported)"""
        # Paper feed command: ESC d n
        self.print_raw(self.ESC + b'd' + bytes([lines]))
        self.print_raw(self.CUT_PAPER)


# ========== USAGE EXAMPLES ==========

def example_basic():
    """Basic printing example"""
    printer = POSPrinter()
    
    printer.print_line("=" * 32)
    printer.print_line("BASIC EXAMPLE", align='center', large=True)
    printer.print_line("=" * 32)
    printer.print_text("\n")
    
    printer.print_line("Normal text")
    printer.print_line("Bold text", bold=True)
    printer.print_line("Underlined text", underline=True)
    printer.print_line("Large text", large=True)
    printer.print_text("\n")
    
    printer.print_line("Left aligned", align='left')
    printer.print_line("Center aligned", align='center')
    printer.print_line("Right aligned", align='right')
    
    printer.feed_and_cut()


def example_graph():
    """Graph printing example"""
    import math
    
    printer = POSPrinter()
    
    # Sine wave
    data1 = [math.sin(x * 0.5) * 5 + 5 for x in range(30)]
    printer.plot_graph(data1, title="Sine Wave", height=8)
    
    # Random data
    import random
    data2 = [random.randint(10, 100) for _ in range(25)]
    printer.plot_graph(data2, title="Random Data", height=10)
    
    printer.feed_and_cut()


def example_bar_chart():
    """Bar chart example"""
    printer = POSPrinter()
    
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    values = [120, 85, 150, 95, 180]
    
    printer.plot_bar_chart(labels, values)
    printer.feed_and_cut()


def example_ascii_art():
    """ASCII art example"""
    printer = POSPrinter()
    
    coffee = """
       (  )   (   )  )
        ) (   )  (  (
        ( )  (    ) )
        _____________
       <_____________> ___
       |             |/ _ \\
       |   COFFEE    | | | |
       |   [_]  [_]  |_| | |
    ___|_____________|\\___/
    """
    
    robot = """
    ┌─────────┐
    │ O     O │
    │    ▼    │
    │  ─────  │
    └─────────┘
       │   │
      ─┴─ ─┴─
    """
    
    printer.print_line("ASCII ART", align='center', large=True)
    printer.print_separator('=')
    printer.print_ascii_art(coffee)
    printer.print_text("\n")
    printer.print_ascii_art(robot)
    
    printer.feed_and_cut()


def example_box():
    """Box example"""
    printer = POSPrinter()
    
    printer.draw_box("ATTENTION!\nImportant message\nFor all users", width=32)
    printer.print_text("\n")
    printer.draw_box("Price: 150 UAH", width=32)
    
    printer.feed_and_cut()


def example_table():
    """Table example"""
    printer = POSPrinter()
    
    printer.print_line("SALES TABLE", align='center', bold=True)
    printer.print_separator('=')
    
    headers = ['Item', 'Qty', 'Price']
    rows = [
        ['Bread', '2', '25'],
        ['Milk', '1', '35'],
        ['Eggs', '10', '45'],
        ['Butter', '1', '120']
    ]
    
    printer.print_table(headers, rows, col_widths=[15, 5, 8])
    
    printer.print_separator('-')
    printer.print_line("Total: 225 UAH", align='right', bold=True)
    
    printer.feed_and_cut()


def example_receipt():
    """Full receipt example"""
    printer = POSPrinter()
    
    # Header
    printer.print_line("STORE 'PRODUCTS'", align='center', large=True)
    printer.print_line("123 Main Street", align='center')
    printer.print_line("Tel: +380 12 345 6789", align='center')
    printer.print_separator('=')
    
    # Date and number
    printer.print_line("Receipt #12345", align='left')
    printer.print_line("Date: 03.02.2026 14:35", align='left')
    printer.print_separator('-')
    
    # Items
    items = [
        ('White Bread', 2, 25.00),
        ('Milk 2.5%', 1, 35.50),
        ('Eggs C1 (10pcs)', 1, 45.00),
        ('Butter', 1, 120.00),
        ('Hard Cheese', 0.3, 180.00)
    ]
    
    total = 0
    for name, qty, price in items:
        subtotal = qty * price
        total += subtotal
        printer.print_text(f"{name}\n")
        printer.print_text(f"  {qty} x {price:.2f} = {subtotal:.2f} UAH\n")
    
    printer.print_separator('=')
    printer.print_line(f"TOTAL: {total:.2f} UAH", align='right', large=True)
    printer.print_separator('=')
    
    # Footer
    printer.print_text("\n")
    printer.print_line("Thank you for shopping!", align='center')
    printer.print_line("Come again!", align='center')
    printer.print_text("\n")
    
    # Barcode (placeholder)
    printer.print_qr_placeholder("CHK12345-03022026")
    
    printer.feed_and_cut(4)


def example_comprehensive():
    """Comprehensive example - demonstration of all features"""
    printer = POSPrinter()
    
    printer.print_line("╔═══════════════════════════╗", align='center')
    printer.print_line("║   ALL FEATURES DEMO      ║", align='center', bold=True)
    printer.print_line("╚═══════════════════════════╝", align='center')
    printer.print_text("\n")
    
    # Section 1: Fonts
    printer.print_line("1. DIFFERENT FONTS", bold=True, underline=True)
    printer.print_line("Normal text")
    printer.print_line("Bold text", bold=True)
    printer.print_line("Large text", large=True)
    printer.print_text("\n")
    
    # Section 2: Graph
    printer.print_line("2. GRAPH", bold=True, underline=True)
    data = [3, 5, 4, 8, 12, 15, 14, 16, 18, 20, 19, 17, 15, 10, 8, 6]
    printer.plot_graph(data, title="Temperature (C)", height=6)
    printer.print_text("\n")
    
    # Section 3: Bar Chart
    printer.print_line("3. BAR CHART", bold=True, underline=True)
    printer.plot_bar_chart(['A', 'B', 'C', 'D'], [75, 120, 95, 150])
    printer.print_text("\n")
    
    # Section 4: Pseudographics
    printer.print_line("4. PSEUDOGRAPHICS", bold=True, underline=True)
    pattern = """
    ░░▒▒▓▓██▓▓▒▒░░
    ◄═══════════►
    ╔═╦═╗ ┌─┬─┐
    ║ ║ ║ │ │ │
    ╠═╬═╣ ├─┼─┤
    ╚═╩═╝ └─┴─┘
    """
    printer.print_ascii_art(pattern)
    
    printer.feed_and_cut(5)


# Run examples
if __name__ == "__main__":
    examples = {
        '1': example_basic,
        '2': example_graph,
        '3': example_bar_chart,
        '4': example_ascii_art,
        '5': example_box,
        '6': example_table,
        '7': example_receipt,
        '8': example_comprehensive
    }
    
    print("\n" + "="*50)
    print("POS PRINTER EXAMPLES")
    print("="*50)
    
    while True:
        print("\nChoose an example:")
        print("1 - Basic formatting")
        print("2 - Graph")
        print("3 - Bar chart")
        print("4 - ASCII art")
        print("5 - Boxes")
        print("6 - Table")
        print("7 - Receipt")
        print("8 - All features")
        print("9 - All examples in sequence")
        print("0 - Exit")
        
        choice = input("\nYour choice (0-9): ").strip()
        
        if choice == '0':
            print("\nExiting. Goodbye!")
            break
        elif choice == '9':
            for name, func in examples.items():
                print(f"\n{'='*50}")
                print(f"Running example {name}: {func.__name__}")
                print('='*50)
                func()
                input("\nPress Enter to continue to next example...")
        elif choice in examples:
            print(f"\nRunning {examples[choice].__name__}...")
            examples[choice]()
            print("\nDone!")
        else:
            print("\nInvalid choice! Please try again.")