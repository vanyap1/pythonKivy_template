import socket
import subprocess

def get_active_ip_addresses():
    """Повертає IP адреси активних мережевих інтерфейсів у форматі '192.168.1.1\\n192.168.1.2'"""
    ip_addresses = []
    
    try:
        # Спробуємо імпортувати netifaces
        import netifaces
        
        # Метод 1: Через netifaces (найкращий)
        for interface in netifaces.interfaces():
            if interface == 'lo':  # Пропускаємо loopback
                continue
            
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info['addr']
                        if ip != '127.0.0.1':  # Пропускаємо localhost
                            ip_addresses.append(ip)
            except:
                continue
                
    except ImportError:
        print("netifaces not installed, using alternative methods...")
        # Метод 2: Через subprocess (якщо netifaces не встановлено)
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                ip_addresses.extend([ip for ip in ips if ip != '127.0.0.1'])
        except Exception as e:
            print(f"hostname -I failed: {e}")
            # Метод 3: Через socket (запасний варіант)
            try:
                # Підключаємося до зовнішнього хоста щоб дізнатися локальний IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                if local_ip != '127.0.0.1':
                    ip_addresses.append(local_ip)
            except Exception as e:
                print(f"Socket method failed: {e}")
    
    # Видаляємо дублікати та повертаємо у потрібному форматі
    unique_ips = list(set(ip_addresses))
    return '\\n'.join(unique_ips) if unique_ips else '127.0.0.1'


def get_active_ip_addresses_simple():
    """Проста версія без netifaces"""
    ip_addresses = []
    
    try:
        # Через hostname -I
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            ip_addresses.extend([ip for ip in ips if ip != '127.0.0.1'])
    except Exception as e:
        print(f"hostname method failed: {e}")
        try:
            # Через ip route
            result = subprocess.run(['ip', 'route', 'get', '1.1.1.1'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\\n'):
                    if 'src' in line:
                        parts = line.split()
                        if 'src' in parts:
                            src_index = parts.index('src')
                            if src_index + 1 < len(parts):
                                ip_addresses.append(parts[src_index + 1])
                                break
        except Exception as e:
            print(f"ip route method failed: {e}")
            # Запасний варіант
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                ip_addresses.append(local_ip)
            except Exception as e:
                print(f"Socket fallback failed: {e}")
                ip_addresses.append('No Network')
    
    unique_ips = list(set(ip_addresses))
    var = '\n'.join(unique_ips) if unique_ips else 'No Network'
    print(var)


def get_detailed_network_info():
    """Детальна інформація про мережеві інтерфейси"""
    info = {}
    
    try:
        import netifaces
        
        for interface in netifaces.interfaces():
            if interface == 'lo':
                continue
                
            try:
                addrs = netifaces.ifaddresses(interface)
                interface_info = {
                    'ipv4': [],
                    'ipv6': [],
                    'mac': None
                }
                
                # IPv4 адреси
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        interface_info['ipv4'].append({
                            'addr': addr.get('addr'),
                            'netmask': addr.get('netmask'),
                            'broadcast': addr.get('broadcast')
                        })
                
                # MAC адреса
                if netifaces.AF_LINK in addrs:
                    interface_info['mac'] = addrs[netifaces.AF_LINK][0].get('addr')
                
                info[interface] = interface_info
                
            except Exception as e:
                print(f"Error processing interface {interface}: {e}")
                
    except ImportError:
        print("netifaces not available for detailed info")
        
    return info


def test_all_methods():
    """Тестування всіх методів"""
    print("=== Testing IP Address Detection Methods ===\\n")
    
    print("1. Method with netifaces:")
    try:
        result1 = get_active_ip_addresses()
        print(f"   Result: {result1}")
        #print(f"   Formatted: {result1.replace('\\n', ', ')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\\n2. Simple method:")
    try:
        result2 = get_active_ip_addresses_simple()
        print(f"   Result: {result2}")
        #print(f"   Formatted: {result2.replace('\\n', ', ')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\\n3. Detailed network info:")
    try:
        detailed = get_detailed_network_info()
        for interface, info in detailed.items():
            print(f"   {interface}:")
            print(f"     IPv4: {info['ipv4']}")
            print(f"     MAC: {info['mac']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\\n4. Manual commands test:")
    try:
        # hostname -I
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        print(f"   hostname -I: {result.stdout.strip()}")
        
        # ip addr show
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\\n')
        ips = []
        for line in lines:
            if 'inet ' in line and '127.0.0.1' not in line:
                parts = line.strip().split()
                if len(parts) > 1 and '/' in parts[1]:
                    ip = parts[1].split('/')[0]
                    ips.append(ip)
        print(f"   ip addr parsed: {', '.join(ips)}")
        
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    # Запуск тестів
    test_all_methods()
    
    print("\\n=== Quick Usage Example ===")
    print("For Kivy ActionBar:")
    ip_string = get_active_ip_addresses_simple()
    print(f"self.action_bar.sysIp = '{ip_string}'")
    
    print("\\nTo install netifaces (optional):")
    print("pip install netifaces")