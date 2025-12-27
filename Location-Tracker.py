import os
import sys
import json
import time
import socket
import hashlib
import base64
import platform
import subprocess
import threading
import queue
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import urllib.request
import urllib.parse
import urllib.error

# Color support
try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False
    class Fore: BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Back: BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style: BRIGHT = DIM = NORMAL = RESET_ALL = ''

# Try to import optional libraries
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import folium
    from folium.plugins import HeatMap, MarkerCluster
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

# Configuration
VALID_LICENSE_KEY = "xai-6Kit0at2dCaQ8W4Z464Fe1lU6ZNyfzYVG1CbLywbHWjy25pmpmAgQelR9wZronOG8k4LndXmdAJJqcTe"
DEMO_MODE = False

class ColorPrinter:
    """Color output handler"""
    
    @staticmethod
    def print(text, color=Fore.WHITE, style=Style.NORMAL, end='\n'):
        if COLOR_AVAILABLE:
            print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)
        else:
            print(text, end=end)
    
    @staticmethod
    def print_banner():
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║               ADVANCED LOCATION TRACKER PRO v2.0                 ║
║               Multi-Source Geolocation Intelligence              ║
║                                                                  ║
║     ██╗      ██████╗  ██████╗ █████╗ ████████╗██╗ ██████╗        ║
║     ██║     ██╔═══██╗██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝        ║
║     ██║     ██║   ██║██║     ███████║   ██║   ██║██║             ║
║     ██║     ██║   ██║██║     ██╔══██║   ██║   ██║██║             ║
║     ███████╗╚██████╔╝╚██████╗██║  ██║   ██║   ██║╚██████╗        ║
║     ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝        ║
╚══════════════════════════════════════════════════════════════════╝
        """
        ColorPrinter.print(banner, Fore.CYAN, Style.BRIGHT)
    
    @staticmethod
    def print_status(msg):
        ColorPrinter.print(f"[*] {msg}", Fore.BLUE)
    
    @staticmethod
    def print_success(msg):
        ColorPrinter.print(f"[+] {msg}", Fore.GREEN)
    
    @staticmethod
    def print_warning(msg):
        ColorPrinter.print(f"[!] {msg}", Fore.YELLOW)
    
    @staticmethod
    def print_error(msg):
        ColorPrinter.print(f"[-] {msg}", Fore.RED)
    
    @staticmethod
    def print_critical(msg):
        ColorPrinter.print(f"[CRITICAL] {msg}", Fore.RED, Style.BRIGHT)

class SimpleLicenseManager:
    """Simple offline license manager"""
    
    def __init__(self):
        self.license_key = ""
        self.is_valid = False
        self.features = []
    
    def validate(self, license_key):
        """Validate license key - OFFLINE ONLY"""
        self.license_key = license_key.strip()
        
        # Direct comparison
        if self.license_key == VALID_LICENSE_KEY:
            ColorPrinter.print_success("License validated successfully!")
            self.is_valid = True
            self.features = ['full_access', 'all_methods', 'real_time', 'export', 'api_access']
            return True
        
        # Demo mode check
        elif DEMO_MODE and (self.license_key == "DEMO" or self.license_key.startswith("TRACKER-DEMO")):
            ColorPrinter.print_warning("Running in DEMO mode (limited features)")
            self.is_valid = True
            self.features = ['demo_mode', 'basic_tracking']
            return True
        
        # Invalid license
        else:
            ColorPrinter.print_error("Invalid license key!")
            self.is_valid = False
            return False
    
    def has_feature(self, feature):
        """Check if license has specific feature"""
        return feature in self.features or 'full_access' in self.features

class NetworkInfo:
    """Network information gathering"""
    
    @staticmethod
    def get_local_ip():
        """Get local IP address"""
        try:
            # Connect to Google DNS to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                return "127.0.0.1"
    
    @staticmethod
    def get_public_ip():
        """Get public IP address from multiple sources"""
        services = [
            "https://api.ipify.org",
            "https://ident.me",
            "https://checkip.amazonaws.com",
            "http://ifconfig.me/ip"
        ]
        
        for service in services:
            try:
                if REQUESTS_AVAILABLE:
                    response = requests.get(service, timeout=5)
                    ip = response.text.strip()
                    if ip and len(ip.split('.')) == 4:
                        return ip
                else:
                    # Use urllib as fallback
                    response = urllib.request.urlopen(service, timeout=5)
                    ip = response.read().decode('utf-8').strip()
                    if ip and len(ip.split('.')) == 4:
                        return ip
            except:
                continue
        
        return "Unknown"
    
    @staticmethod
    def get_network_info():
        """Get comprehensive network information"""
        info = {
            'local_ip': NetworkInfo.get_local_ip(),
            'public_ip': NetworkInfo.get_public_ip(),
            'hostname': socket.gethostname(),
            'mac_address': NetworkInfo._get_mac_address(),
            'network_interfaces': NetworkInfo._get_network_interfaces(),
            'dns_servers': NetworkInfo._get_dns_servers()
        }
        return info
    
    @staticmethod
    def _get_mac_address():
        """Get MAC address"""
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                          for elements in range(0, 8*6, 8)][::-1])
            return mac
        except:
            return "Unknown"
    
    @staticmethod
    def _get_network_interfaces():
        """Get network interfaces"""
        interfaces = []
        try:
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        interfaces.append({
                            'interface': iface,
                            'ip': addr_info.get('addr', ''),
                            'netmask': addr_info.get('netmask', ''),
                            'broadcast': addr_info.get('broadcast', '')
                        })
        except:
            # Fallback method
            try:
                if platform.system() == 'Windows':
                    result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    current_interface = None
                    for line in lines:
                        if 'Ethernet adapter' in line or 'Wireless LAN adapter' in line:
                            current_interface = line.split(':')[0].strip()
                        elif 'IPv4 Address' in line and current_interface:
                            ip = line.split(':')[-1].strip().split('(')[0].strip()
                            interfaces.append({'interface': current_interface, 'ip': ip})
            except:
                pass
        
        return interfaces
    
    @staticmethod
    def _get_dns_servers():
        """Get DNS servers"""
        dns_servers = []
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'DNS Servers' in line or 'DNS servers' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            dns = parts[1].strip().split('(')[0].strip()
                            if dns:
                                dns_servers.append(dns)
            elif platform.system() == 'Linux':
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
        except:
            pass
        
        return dns_servers

class GeolocationAPI:
    """Geolocation API integration"""
    
    APIS = {
        'ipapi': {
            'url': 'https://ipapi.co/{ip}/json/',
            'fields': {
                'ip': 'ip',
                'city': 'city',
                'region': 'region',
                'country': 'country_name',
                'lat': 'latitude',
                'lon': 'longitude',
                'isp': 'org',
                'timezone': 'timezone'
            }
        },
        'ipinfo': {
            'url': 'https://ipinfo.io/{ip}/json',
            'fields': {
                'ip': 'ip',
                'city': 'city',
                'region': 'region',
                'country': 'country',
                'lat': 'loc',
                'lon': 'loc',
                'isp': 'org'
            }
        },
        'geolocation': {
            'url': 'http://ip-api.com/json/{ip}',
            'fields': {
                'ip': 'query',
                'city': 'city',
                'region': 'regionName',
                'country': 'country',
                'lat': 'lat',
                'lon': 'lon',
                'isp': 'isp',
                'timezone': 'timezone'
            }
        }
    }
    
    @staticmethod
    def get_location_by_ip(ip_address, api_name='ipapi'):
        """Get location by IP address"""
        if api_name not in GeolocationAPI.APIS:
            api_name = 'ipapi'
        
        api_config = GeolocationAPI.APIS[api_name]
        url = api_config['url'].format(ip=ip_address)
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(url, timeout=10)
                data = response.json()
            else:
                # Use urllib as fallback
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req, timeout=10)
                data = json.loads(response.read().decode('utf-8'))
            
            # Parse response based on API
            result = {'ip': ip_address, 'source': api_name}
            
            for field, api_field in api_config['fields'].items():
                if api_field in data:
                    value = data[api_field]
                    
                    # Special handling for combined lat/lon
                    if field == 'lat' and isinstance(value, str) and ',' in value:
                        lat, lon = value.split(',')
                        result['lat'] = float(lat.strip())
                        result['lon'] = float(lon.strip())
                    elif field == 'lon' and 'lat' in result:
                        continue  # Already handled
                    elif field in ['lat', 'lon'] and isinstance(value, (int, float)):
                        result[field] = float(value)
                    else:
                        result[field] = value
            
            return result
            
        except Exception as e:
            ColorPrinter.print_warning(f"API {api_name} failed: {e}")
            return None
    
    @staticmethod
    def get_location_multi_source(ip_address):
        """Get location from multiple sources for accuracy"""
        results = []
        
        for api_name in GeolocationAPI.APIS.keys():
            result = GeolocationAPI.get_location_by_ip(ip_address, api_name)
            if result:
                results.append(result)
                time.sleep(0.5)  # Rate limiting
        
        if not results:
            return None
        
        # Average coordinates if multiple sources agree
        if len(results) > 1:
            try:
                lats = [r['lat'] for r in results if 'lat' in r]
                lons = [r['lon'] for r in results if 'lon' in r]
                
                if lats and lons:
                    avg_lat = sum(lats) / len(lats)
                    avg_lon = sum(lons) / len(lons)
                    
                    # Use first result as base
                    final_result = results[0].copy()
                    final_result['lat'] = avg_lat
                    final_result['lon'] = avg_lon
                    final_result['accuracy'] = 'high'
                    final_result['sources'] = len(results)
                    return final_result
            except:
                pass
        
        # Return first result with medium accuracy
        results[0]['accuracy'] = 'medium'
        results[0]['sources'] = len(results)
        return results[0]

class PhoneTracker:
    """Phone number tracking capabilities"""
    
    @staticmethod
    def track_phone_number(phone_number):
        """Track location by phone number"""
        if not PHONENUMBERS_AVAILABLE:
            ColorPrinter.print_error("phonenumbers library not installed!")
            ColorPrinter.print_status("Install with: pip install phonenumbers")
            return None
        
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone_number, None)
            
            # Get location information
            country = geocoder.country_name_for_number(parsed_number, "en")
            region = geocoder.description_for_number(parsed_number, "en")
            carrier_name = carrier.name_for_number(parsed_number, "en")
            timezones = timezone.time_zones_for_number(parsed_number)
            
            result = {
                'phone_number': phone_number,
                'country': country,
                'region': region,
                'carrier': carrier_name,
                'timezones': list(timezones),
                'valid': phonenumbers.is_valid_number(parsed_number),
                'type': phonenumbers.number_type(parsed_number)
            }
            
            return result
            
        except Exception as e:
            ColorPrinter.print_error(f"Phone tracking failed: {e}")
            return None

class SocialMediaTracker:
    """Social media username tracking"""
    
    @staticmethod
    def track_username(username, platforms=None):
        """Track username across social media platforms"""
        if platforms is None:
            platforms = ['instagram', 'twitter', 'facebook', 'github', 'linkedin']
        
        results = {}
        
        for platform in platforms:
            result = SocialMediaTracker._check_platform(username, platform)
            if result:
                results[platform] = result
        
        return results
    
    @staticmethod
    def _check_platform(username, platform):
        """Check if username exists on specific platform"""
        urls = {
            'instagram': f'https://www.instagram.com/{username}/',
            'twitter': f'https://twitter.com/{username}',
            'github': f'https://github.com/{username}',
            'facebook': f'https://www.facebook.com/{username}',
            'linkedin': f'https://www.linkedin.com/in/{username}/'
        }
        
        if platform not in urls:
            return None
        
        url = urls[platform]
        
        try:
            if REQUESTS_AVAILABLE:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    return {
                        'url': url,
                        'exists': True,
                        'platform': platform
                    }
            else:
                req = urllib.request.Request(url, method='HEAD')
                response = urllib.request.urlopen(req, timeout=5)
                if response.status == 200:
                    return {
                        'url': url,
                        'exists': True,
                        'platform': platform
                    }
        except:
            pass
        
        return {
            'url': url,
            'exists': False,
            'platform': platform
        }

class DatabaseManager:
    """Database for storing tracking results"""
    
    def __init__(self):
        self.db_path = Path.home() / ".location_tracker" / "tracking.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tracking history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracking_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT,
                    target_type TEXT,
                    latitude REAL,
                    longitude REAL,
                    city TEXT,
                    country TEXT,
                    isp TEXT,
                    timestamp DATETIME,
                    source TEXT,
                    accuracy TEXT,
                    notes TEXT
                )
            ''')
            
            # Create IP history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT,
                    city TEXT,
                    country TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp DATETIME,
                    is_tracked BOOLEAN
                )
            ''')
            
            conn.commit()
            conn.close()
            ColorPrinter.print_success("Database initialized")
            
        except Exception as e:
            ColorPrinter.print_error(f"Database initialization failed: {e}")
    
    def save_tracking_result(self, target, result, target_type='ip'):
        """Save tracking result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tracking_history 
                (target, target_type, latitude, longitude, city, country, isp, timestamp, source, accuracy, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                target,
                target_type,
                result.get('lat'),
                result.get('lon'),
                result.get('city'),
                result.get('country'),
                result.get('isp'),
                datetime.now().isoformat(),
                result.get('source', 'unknown'),
                result.get('accuracy', 'unknown'),
                json.dumps(result)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            ColorPrinter.print_error(f"Failed to save result: {e}")
            return False
    
    def get_tracking_history(self, limit=50):
        """Get tracking history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tracking_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            ColorPrinter.print_error(f"Failed to get history: {e}")
            return []
    
    def clear_history(self):
        """Clear all tracking history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tracking_history')
            cursor.execute('DELETE FROM ip_history')
            
            conn.commit()
            conn.close()
            
            ColorPrinter.print_success("Tracking history cleared")
            return True
            
        except Exception as e:
            ColorPrinter.print_error(f"Failed to clear history: {e}")
            return False

class MapGenerator:
    """Generate maps from location data"""
    
    @staticmethod
    def generate_map(locations, output_path="map.html"):
        """Generate interactive map from locations"""
        if not FOLIUM_AVAILABLE:
            ColorPrinter.print_error("Folium library not installed!")
            ColorPrinter.print_status("Install with: pip install folium")
            return None
        
        try:
            # Filter locations with coordinates
            valid_locations = [loc for loc in locations if 'lat' in loc and 'lon' in loc]
            
            if not valid_locations:
                ColorPrinter.print_warning("No valid coordinates for map generation")
                return None
            
            # Create map centered on average coordinates
            avg_lat = sum(loc['lat'] for loc in valid_locations) / len(valid_locations)
            avg_lon = sum(loc['lon'] for loc in valid_locations) / len(valid_locations)
            
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)
            
            # Add markers for each location
            for loc in valid_locations:
                popup_text = f"<b>{loc.get('ip', loc.get('target', 'Unknown'))}</b><br>"
                popup_text += f"City: {loc.get('city', 'Unknown')}<br>"
                popup_text += f"Country: {loc.get('country', 'Unknown')}<br>"
                popup_text += f"ISP: {loc.get('isp', 'Unknown')}"
                
                folium.Marker(
                    [loc['lat'], loc['lon']],
                    popup=popup_text,
                    tooltip=loc.get('ip', loc.get('target', 'Location'))
                ).add_to(m)
            
            # Add heatmap if multiple locations
            if len(valid_locations) > 1:
                heat_data = [[loc['lat'], loc['lon']] for loc in valid_locations]
                HeatMap(heat_data).add_to(m)
            
            # Save map
            m.save(output_path)
            ColorPrinter.print_success(f"Map generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            ColorPrinter.print_error(f"Map generation failed: {e}")
            return None

class AdvancedLocationTracker:
    """Main tracking application"""
    
    def __init__(self, license_manager):
        self.license = license_manager
        self.network_info = NetworkInfo()
        self.geolocation = GeolocationAPI()
        self.phone_tracker = PhoneTracker()
        self.social_tracker = SocialMediaTracker()
        self.database = DatabaseManager()
        self.tracking_history = []
    
    def get_own_location(self):
        """Get current location based on IP"""
        ColorPrinter.print_status("Getting your location...")
        
        # Get public IP
        public_ip = self.network_info.get_public_ip()
        
        if public_ip == "Unknown":
            ColorPrinter.print_error("Could not determine public IP")
            return None
        
        ColorPrinter.print_status(f"Public IP: {public_ip}")
        
        # Get location
        location = self.geolocation.get_location_multi_source(public_ip)
        
        if location:
            self._display_location_info(location)
            self.database.save_tracking_result(public_ip, location, 'self_ip')
            return location
        
        return None
    
    def track_ip(self, ip_address):
        """Track location by IP address"""
        ColorPrinter.print_status(f"Tracking IP: {ip_address}")
        
        # Validate IP format
        if not self._validate_ip(ip_address):
            ColorPrinter.print_error("Invalid IP address format")
            return None
        
        # Get location from multiple sources
        location = self.geolocation.get_location_multi_source(ip_address)
        
        if location:
            self._display_location_info(location)
            self.database.save_tracking_result(ip_address, location, 'ip')
            self.tracking_history.append(location)
            return location
        
        ColorPrinter.print_error("Failed to track IP")
        return None
    
    def track_phone(self, phone_number):
        """Track phone number"""
        ColorPrinter.print_status(f"Tracking phone: {phone_number}")
        
        result = self.phone_tracker.track_phone_number(phone_number)
        
        if result:
            self._display_phone_info(result)
            self.tracking_history.append(result)
            return result
        
        return None
    
    def track_username(self, username):
        """Track social media username"""
        ColorPrinter.print_status(f"Tracking username: @{username}")
        
        results = self.social_tracker.track_username(username)
        
        if results:
            self._display_social_info(username, results)
            self.tracking_history.append({'username': username, 'results': results})
            return results
        
        ColorPrinter.print_warning(f"No social media profiles found for @{username}")
        return None
    
    def bulk_track_ips(self, ip_list_file):
        """Track multiple IPs from file"""
        if not os.path.exists(ip_list_file):
            ColorPrinter.print_error("IP list file not found")
            return []
        
        try:
            with open(ip_list_file, 'r') as f:
                ips = [line.strip() for line in f if line.strip()]
            
            if not ips:
                ColorPrinter.print_error("No IPs found in file")
                return []
            
            ColorPrinter.print_status(f"Tracking {len(ips)} IP addresses...")
            
            results = []
            for i, ip in enumerate(ips, 1):
                if self._validate_ip(ip):
                    ColorPrinter.print_status(f"[{i}/{len(ips)}] Tracking {ip}")
                    result = self.track_ip(ip)
                    if result:
                        results.append(result)
                    time.sleep(1)  # Rate limiting
                else:
                    ColorPrinter.print_warning(f"Invalid IP: {ip}")
            
            ColorPrinter.print_success(f"Completed bulk tracking: {len(results)}/{len(ips)} successful")
            return results
            
        except Exception as e:
            ColorPrinter.print_error(f"Bulk tracking failed: {e}")
            return []
    
    def generate_report(self, output_format='txt', output_file=None):
        """Generate tracking report"""
        if not self.tracking_history:
            ColorPrinter.print_warning("No tracking data to report")
            return None
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tracking_report_{timestamp}.{output_format}"
        
        try:
            if output_format.lower() == 'json':
                with open(output_file, 'w') as f:
                    json.dump(self.tracking_history, f, indent=2)
            
            elif output_format.lower() == 'csv':
                with open(output_file, 'w', newline='') as f:
                    # Flatten data for CSV
                    rows = []
                    for item in self.tracking_history:
                        if 'ip' in item:  # IP location result
                            rows.append({
                                'Type': 'IP',
                                'Target': item.get('ip'),
                                'City': item.get('city', ''),
                                'Country': item.get('country', ''),
                                'Latitude': item.get('lat', ''),
                                'Longitude': item.get('lon', ''),
                                'ISP': item.get('isp', ''),
                                'Source': item.get('source', ''),
                                'Accuracy': item.get('accuracy', '')
                            })
                        elif 'phone_number' in item:  # Phone result
                            rows.append({
                                'Type': 'Phone',
                                'Target': item.get('phone_number'),
                                'Country': item.get('country', ''),
                                'Region': item.get('region', ''),
                                'Carrier': item.get('carrier', ''),
                                'Valid': item.get('valid', '')
                            })
                    
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
            
            elif output_format.lower() == 'html':
                self._generate_html_report(output_file)
            
            else:  # txt format
                with open(output_file, 'w') as f:
                    f.write(self._generate_text_report())
            
            ColorPrinter.print_success(f"Report saved: {output_file}")
            return output_file
            
        except Exception as e:
            ColorPrinter.print_error(f"Report generation failed: {e}")
            return None
    
    def generate_map(self, output_file="tracking_map.html"):
        """Generate map from tracking history"""
        if not self.tracking_history:
            ColorPrinter.print_warning("No location data for map")
            return None
        
        result = MapGenerator.generate_map(self.tracking_history, output_file)
        
        if result and os.path.exists(result):
            # Try to open in browser
            try:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(result)}")
            except:
                pass
        
        return result
    
    def _validate_ip(self, ip):
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def _display_location_info(self, location):
        """Display location information"""
        print("\n" + "="*60)
        ColorPrinter.print("LOCATION INFORMATION", Fore.CYAN, Style.BRIGHT)
        print("="*60)
        
        if 'ip' in location:
            print(f"IP Address: {location['ip']}")
        
        if 'city' in location and location['city']:
            print(f"City: {location['city']}")
        
        if 'region' in location and location['region']:
            print(f"Region: {location['region']}")
        
        if 'country' in location and location['country']:
            print(f"Country: {location['country']}")
        
        if 'lat' in location and 'lon' in location:
            print(f"Coordinates: {location['lat']:.4f}, {location['lon']:.4f}")
            print(f"Google Maps: https://maps.google.com/?q={location['lat']},{location['lon']}")
        
        if 'isp' in location and location['isp']:
            print(f"ISP: {location['isp']}")
        
        if 'timezone' in location and location['timezone']:
            print(f"Timezone: {location['timezone']}")
        
        if 'accuracy' in location:
            print(f"Accuracy: {location['accuracy']}")
        
        if 'sources' in location:
            print(f"Sources: {location['sources']}")
        
        print("="*60)
    
    def _display_phone_info(self, phone_info):
        """Display phone number information"""
        print("\n" + "="*60)
        ColorPrinter.print("PHONE NUMBER INFORMATION", Fore.CYAN, Style.BRIGHT)
        print("="*60)
        
        print(f"Phone Number: {phone_info['phone_number']}")
        print(f"Country: {phone_info['country']}")
        print(f"Region: {phone_info['region']}")
        
        if phone_info['carrier']:
            print(f"Carrier: {phone_info['carrier']}")
        
        if phone_info['timezones']:
            print(f"Timezones: {', '.join(phone_info['timezones'])}")
        
        print(f"Valid Number: {phone_info['valid']}")
        print("="*60)
    
    def _display_social_info(self, username, results):
        """Display social media information"""
        print("\n" + "="*60)
        ColorPrinter.print(f"SOCIAL MEDIA TRACKING: @{username}", Fore.CYAN, Style.BRIGHT)
        print("="*60)
        
        found = 0
        for platform, info in results.items():
            if info['exists']:
                ColorPrinter.print(f"[+] {platform.upper()}: Found", Fore.GREEN)
                print(f"    URL: {info['url']}")
                found += 1
            else:
                ColorPrinter.print(f"[-] {platform.upper()}: Not found", Fore.RED)
        
        print(f"\nTotal profiles found: {found}/{len(results)}")
        print("="*60)
    
    def _generate_text_report(self):
        """Generate text report"""
        report = []
        report.append("="*80)
        report.append("LOCATION TRACKING REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Entries: {len(self.tracking_history)}")
        report.append("="*80)
        
        for i, entry in enumerate(self.tracking_history, 1):
            report.append(f"\nENTRY {i}:")
            report.append("-"*40)
            
            if 'ip' in entry:
                report.append(f"Type: IP Address")
                report.append(f"IP: {entry.get('ip', 'N/A')}")
                report.append(f"Location: {entry.get('city', 'N/A')}, {entry.get('country', 'N/A')}")
                report.append(f"Coordinates: {entry.get('lat', 'N/A')}, {entry.get('lon', 'N/A')}")
                report.append(f"ISP: {entry.get('isp', 'N/A')}")
            
            elif 'phone_number' in entry:
                report.append(f"Type: Phone Number")
                report.append(f"Phone: {entry.get('phone_number', 'N/A')}")
                report.append(f"Location: {entry.get('country', 'N/A')}, {entry.get('region', 'N/A')}")
                report.append(f"Carrier: {entry.get('carrier', 'N/A')}")
            
            elif 'username' in entry:
                report.append(f"Type: Social Media")
                report.append(f"Username: {entry.get('username', 'N/A')}")
                for platform, info in entry.get('results', {}).items():
                    status = "Found" if info.get('exists') else "Not found"
                    report.append(f"  {platform}: {status}")
        
        report.append("\n" + "="*80)
        return "\n".join(report)
    
    def _generate_html_report(self, output_file):
        """Generate HTML report"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Location Tracking Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .entry { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; 
                 box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .ip-entry { border-left: 5px solid #4CAF50; }
        .phone-entry { border-left: 5px solid #2196F3; }
        .social-entry { border-left: 5px solid #FF9800; }
        .label { font-weight: bold; color: #666; }
        .value { margin-bottom: 10px; }
        .map-link { color: #2196F3; text-decoration: none; }
        .map-link:hover { text-decoration: underline; }
        .stats { display: flex; justify-content: space-between; background: white; 
                 padding: 15px; border-radius: 8px; margin: 10px 0; }
        .stat-box { text-align: center; padding: 10px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Location Tracking Report</h1>
        <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p>Advanced Location Tracker Pro v2.0</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">""" + str(len(self.tracking_history)) + """</div>
            <div class="stat-label">Total Entries</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(len([e for e in self.tracking_history if 'ip' in e])) + """</div>
            <div class="stat-label">IP Addresses</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">""" + str(len([e for e in self.tracking_history if 'phone_number' in e])) + """</div>
            <div class="stat-label">Phone Numbers</div>
        </div>
    </div>
"""
        
        for i, entry in enumerate(self.tracking_history, 1):
            if 'ip' in entry:
                html += f"""
    <div class="entry ip-entry">
        <h3>Entry {i}: IP Address</h3>
        <div class="value"><span class="label">IP:</span> {entry.get('ip', 'N/A')}</div>
        <div class="value"><span class="label">Location:</span> {entry.get('city', 'N/A')}, {entry.get('country', 'N/A')}</div>
"""
                if 'lat' in entry and 'lon' in entry:
                    html += f"""
        <div class="value"><span class="label">Coordinates:</span> {entry.get('lat', 'N/A')}, {entry.get('lon', 'N/A')}</div>
        <div class="value">
            <a class="map-link" href="https://maps.google.com/?q={entry.get('lat')},{entry.get('lon')}" target="_blank">
                View on Google Maps
            </a>
        </div>
"""
                html += f"""
        <div class="value"><span class="label">ISP:</span> {entry.get('isp', 'N/A')}</div>
        <div class="value"><span class="label">Source:</span> {entry.get('source', 'N/A')}</div>
    </div>
"""
            
            elif 'phone_number' in entry:
                html += f"""
    <div class="entry phone-entry">
        <h3>Entry {i}: Phone Number</h3>
        <div class="value"><span class="label">Phone:</span> {entry.get('phone_number', 'N/A')}</div>
        <div class="value"><span class="label">Country:</span> {entry.get('country', 'N/A')}</div>
        <div class="value"><span class="label">Region:</span> {entry.get('region', 'N/A')}</div>
        <div class="value"><span class="label">Carrier:</span> {entry.get('carrier', 'N/A')}</div>
    </div>
"""
            
            elif 'username' in entry:
                html += f"""
    <div class="entry social-entry">
        <h3>Entry {i}: Social Media - @{entry.get('username', 'N/A')}</h3>
"""
                for platform, info in entry.get('results', {}).items():
                    status = "✅ Found" if info.get('exists') else "❌ Not found"
                    html += f"""
        <div class="value">
            <span class="label">{platform.upper()}:</span> {status}
            {f'<br><a class="map-link" href="{info.get("url")}" target="_blank">Visit Profile</a>' if info.get('exists') else ''}
        </div>
"""
                html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

class LocationTrackerApp:
    """Main application class"""
    
    def __init__(self):
        self.license_manager = SimpleLicenseManager()
        self.tracker = None
    
    def check_license(self):
        """Check license - OFFLINE ONLY"""
        ColorPrinter.print_banner()
        
        print("\n" + "="*60)
        print("LICENSE REQUIREMENT")
        print("="*60)
        print("\nNote: This tool requires a valid license key to run.")
        
        license_key = input("\n[?] Enter license key: ").strip()
        
        if not self.license_manager.validate(license_key):
            return False
        
        print("="*60 + "\n")
        
        # Initialize tracker
        self.tracker = AdvancedLocationTracker(self.license_manager)
        
        return True
    
    def main_menu(self):
        """Display main menu"""
        while True:
            print("\n" + "="*60)
            ColorPrinter.print("ADVANCED LOCATION TRACKER PRO v2.0", Fore.CYAN, Style.BRIGHT)
            print("="*60)
            
            print("\n[MAIN MENU]")
            print("  1. Get My Location")
            print("  2. Track IP Address")
            print("  3. Track Phone Number")
            print("  4. Track Social Media Username")
            print("  5. Bulk Track IPs from File")
            print("  6. Generate Report")
            print("  7. Generate Map")
            print("  8. View Tracking History")
            print("  9. Network Information")
            print("  10. Clear History")
            print("  11. Exit")
            
            print("\n" + "-"*60)
            
            try:
                choice = input("\n[?] Select option (1-11): ").strip()
                
                if choice == '1':
                    self.get_my_location()
                elif choice == '2':
                    self.track_ip()
                elif choice == '3':
                    self.track_phone()
                elif choice == '4':
                    self.track_username()
                elif choice == '5':
                    self.bulk_track()
                elif choice == '6':
                    self.generate_report()
                elif choice == '7':
                    self.generate_map()
                elif choice == '8':
                    self.view_history()
                elif choice == '9':
                    self.network_info()
                elif choice == '10':
                    self.clear_history()
                elif choice == '11':
                    ColorPrinter.print_success("Goodbye!")
                    break
                else:
                    ColorPrinter.print_warning("Invalid choice!")
                    
            except KeyboardInterrupt:
                ColorPrinter.print_warning("\nInterrupted by user")
                break
            except Exception as e:
                ColorPrinter.print_error(f"Error: {e}")
    
    def get_my_location(self):
        """Get current location"""
        result = self.tracker.get_own_location()
        if result:
            input("\nPress Enter to continue...")
    
    def track_ip(self):
        """Track IP address"""
        ip = input("\n[?] Enter IP address to track: ").strip()
        
        if not ip:
            ColorPrinter.print_warning("No IP address provided!")
            return
        
        result = self.tracker.track_ip(ip)
        if result:
            input("\nPress Enter to continue...")
    
    def track_phone(self):
        """Track phone number"""
        if not self.license_manager.has_feature('full_access'):
            ColorPrinter.print_error("Full license required for phone tracking!")
            return
        
        phone = input("\n[?] Enter phone number (with country code): ").strip()
        
        if not phone:
            ColorPrinter.print_warning("No phone number provided!")
            return
        
        result = self.tracker.track_phone(phone)
        if result:
            input("\nPress Enter to continue...")
    
    def track_username(self):
        """Track social media username"""
        username = input("\n[?] Enter username to track: ").strip()
        
        if not username:
            ColorPrinter.print_warning("No username provided!")
            return
        
        result = self.tracker.track_username(username)
        if result:
            input("\nPress Enter to continue...")
    
    def bulk_track(self):
        """Bulk track IPs from file"""
        filename = input("\n[?] Enter path to IP list file: ").strip()
        
        if not filename or not os.path.exists(filename):
            ColorPrinter.print_error("File not found!")
            return
        
        results = self.tracker.bulk_track_ips(filename)
        
        if results:
            print(f"\nSuccessfully tracked {len(results)} IP addresses")
            input("\nPress Enter to continue...")
    
    def generate_report(self):
        """Generate tracking report"""
        if not self.tracker.tracking_history:
            ColorPrinter.print_warning("No tracking data to report!")
            return
        
        print("\nReport Formats:")
        print("  1. Text (.txt)")
        print("  2. JSON (.json)")
        print("  3. CSV (.csv)")
        print("  4. HTML (.html)")
        
        choice = input("\n[?] Select format (1-4): ").strip()
        
        formats = {'1': 'txt', '2': 'json', '3': 'csv', '4': 'html'}
        if choice in formats:
            output_file = input("[?] Output filename (optional): ").strip()
            self.tracker.generate_report(formats[choice], output_file)
        else:
            ColorPrinter.print_warning("Invalid format!")
    
    def generate_map(self):
        """Generate map from tracking data"""
        if not self.tracker.tracking_history:
            ColorPrinter.print_warning("No location data for map!")
            return
        
        output_file = input("\n[?] Map filename (optional): ").strip()
        if not output_file:
            output_file = "tracking_map.html"
        
        result = self.tracker.generate_map(output_file)
        if result:
            ColorPrinter.print_success(f"Map generated: {result}")
        
        input("\nPress Enter to continue...")
    
    def view_history(self):
        """View tracking history"""
        history = self.tracker.database.get_tracking_history()
        
        if not history:
            ColorPrinter.print_warning("No tracking history!")
            return
        
        print("\n" + "="*60)
        ColorPrinter.print("TRACKING HISTORY", Fore.CYAN, Style.BRIGHT)
        print("="*60)
        
        for entry in history[:20]:  # Show last 20 entries
            print(f"\nID: {entry[0]}")
            print(f"Target: {entry[1]} ({entry[2]})")
            print(f"Location: {entry[5]}, {entry[6]}")
            print(f"Time: {entry[8]}")
            print("-"*40)
        
        if len(history) > 20:
            ColorPrinter.print(f"\n... and {len(history) - 20} more entries", Fore.YELLOW)
        
        input("\nPress Enter to continue...")
    
    def network_info(self):
        """Display network information"""
        info = self.tracker.network_info.get_network_info()
        
        print("\n" + "="*60)
        ColorPrinter.print("NETWORK INFORMATION", Fore.CYAN, Style.BRIGHT)
        print("="*60)
        
        print(f"Local IP: {info['local_ip']}")
        print(f"Public IP: {info['public_ip']}")
        print(f"Hostname: {info['hostname']}")
        print(f"MAC Address: {info['mac_address']}")
        
        if info['network_interfaces']:
            print("\nNetwork Interfaces:")
            for iface in info['network_interfaces']:
                print(f"  {iface['interface']}: {iface['ip']}")
        
        if info['dns_servers']:
            print(f"\nDNS Servers: {', '.join(info['dns_servers'])}")
        
        print("="*60)
        input("\nPress Enter to continue...")
    
    def clear_history(self):
        """Clear tracking history"""
        confirm = input("\n[?] Are you sure you want to clear all history? (y/n): ").lower()
        
        if confirm == 'y':
            if self.tracker.database.clear_history():
                self.tracker.tracking_history = []
                ColorPrinter.print_success("History cleared!")

def check_dependencies():
    """Check and install dependencies"""
    required = ['colorama']
    optional = ['requests', 'folium', 'phonenumbers', 'netifaces']
    
    missing_required = []
    missing_optional = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print("\n[!] Missing required dependencies:")
        for dep in missing_required:
            print(f"  - {dep}")
        
        try:
            install = input("\n[?] Install now? (y/n): ").lower()
            if install == 'y':
                import subprocess
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_required)
                print("[+] Dependencies installed!")
        except:
            print("[!] Failed to install dependencies")
    
    if missing_optional:
        print("\n[!] Missing optional dependencies (some features limited):")
        for dep in missing_optional:
            print(f"  - {dep}")
        
        print("\n[!] Install with: pip install requests folium phonenumbers python-netifaces")

def main():
    """Main entry point"""
    # Check dependencies
    check_dependencies()
    
    # Create app
    app = LocationTrackerApp()
    
    # Check license
    if not app.check_license():
        return
    
    # Run main menu
    try:
        app.main_menu()
    except KeyboardInterrupt:
        ColorPrinter.print_warning("\nInterrupted by user")
    except Exception as e:
        ColorPrinter.print_error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()