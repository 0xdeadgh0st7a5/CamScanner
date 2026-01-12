#!/usr/bin/env python3

import ipaddress
import socket
import threading
import ssl
import re
from termcolor import colored
import time
import os

OUTPUT_FILE = "Camera_Founds.txt"

def display_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗██╗  ██╗ █████╗ ██████╗ ██████╗  ██████╗ ██╗  ██╗███████╗████████╗ ║
║   ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝╚══██╔══╝ ║
║   ███████╗███████║███████║██║  ██║██║  ██║██║   ██║█████╔╝ █████╗     ██║    ║
║   ╚════██║██╔══██║██╔══██║██║  ██║██║  ██║██║   ██║██╔═██╗ ██╔══╝     ██║    ║
║   ███████║██║  ██║██║  ██║██████╔╝██████╔╝╚██████╔╝██║  ██╗███████╗   ██║    ║
║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝    ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║    ┌────────────────────────────────────────────────────────────────────┐    ║
║    │ █▀▀▀▀▀▀▀▀▀ █▀▀▀█ █▀▀▀▀ █▀▀▀█ █▀▀▀▀ █▀▀▀▀ │ SHADOW GHOST v1.0       │    ║
║    │ █▄▄▄▄▄▄▄▄▄ █▄▄▄█ █▄▄▄▄ █▄▄▄█ █▄▄▄▄ █▄▄▄▄ │ Camera Scanner          │    ║
║    └────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║    [✓] Author   : Shadow Ghost                                               ║
║    [✓] Telegram : https://t.me/shadow_ghost_yt                               ║
║    [✓] GitHub   : https://github.com/0xdeadgh0st7a5                          ║
║    [✓] Purpose  : CCTV & IP Camera Scanner                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    # Print banner with green color for hacker vibe
    print('\033[92m' + banner + '\033[0m')

def read_ips_from_file(filename):
    ips = []
    try:
        if not os.path.exists(filename):
            print(colored(f"[x] File Not Found!", "red"))
            return ips  # Return empty list instead of []
            
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ips.append(line)

        if not ips:
            print(colored(f"[x] No valid IPs Found in {filename}", "red"))
        
        return ips
    except Exception as e:
        print(colored(f"[x] Error Reading File: {e}", "red"))
        return []
        
def cidr_to_ips(cidr):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        print(colored(f"[x] Invalid CIDR Range : {e}", "red"))
        return []
    except Exception as e:
        print(colored(f"[x] Error Parsing CIDR : {e}", "red"))
        return []

def save_results(ip, port, device_type):
    entry = f"{device_type} - {ip}:{port}"
    try:
        # Check if entry already exists
        entry_exists = False
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if f"{ip}:{port}" in line:
                            entry_exists = True
                            break
            except Exception:
                pass  # If we can't read the file, we'll overwrite it
        
        if not entry_exists:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
            return True
        return False
    except Exception as e:
        print(colored(f"[!] Save error: {e}", "yellow"))
        return False

def get_title(ip, port, timeout=0.25):
    try:
        if port == 443 or port == 8443:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(timeout)
            raw_sock.connect((ip, port))
            sock = context.wrap_socket(raw_sock, server_hostname=ip)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
        request = f"GET / HTTP/1.1\r\nHost: {ip}\r\n\r\n"
        sock.send(request.encode())
        
        response = b""
        try:
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
        except (socket.timeout, socket.error):
            pass
        finally:
            sock.close()
            
        response_str = response.decode('utf-8', errors='ignore')
        return response_str
    except Exception:
        return ""

def scan_ports(ip, port, timeout=0.25):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            # Check if already in output file
            already_found = False
            if os.path.exists(OUTPUT_FILE):
                try:
                    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                        for line in f:
                            if f"{ip}:{port}" in line:
                                already_found = True
                                break
                except Exception:
                    pass
            
            if not already_found:
                # Check specific ports first
                if port == 37777 or port == 37778:
                    print(colored(f"[+] Found Dahua Camera - {ip}:{port}", "green", attrs=['bold']))
                    save_results(ip, port, "Dahua Camera")
                    return True
                elif port == 554:
                    print(colored(f"[+] Found Hikvision Camera - {ip}:{port}", "cyan", attrs=['bold']))
                    save_results(ip, port, "Hikvision Camera")
                    return True
                else:
                    response_str = get_title(ip, port)
                    if response_str:
                        # Check for Hikvision FIRST (before title check)
                        if "/doc/page/login.asp" in response_str.lower():
                            print(colored(f"[+] Found Hikvision Camera - {ip}:{port}", "cyan", attrs=['bold']))
                            save_results(ip, port, "Hikvision Camera")
                            return True
                        
                        title_match = re.search(r'<title[^>]*>(.*?)</title>', response_str, re.IGNORECASE)
                        title = ""
                        if title_match:
                            title = title_match.group(1).strip()
                        
                        # STRICT MATCHING: Only exact "WEB" or "WEB SERVICE"
                        if title:
                            title_lower = title.lower()
                            
                            # EXACT match only (no extra spaces, no other words)
                            if title_lower == "web":
                                print(colored(f"[+] Found Dahua Camera - {ip}:{port}", "green", attrs=['bold']))
                                save_results(ip, port, "Dahua Camera")
                                return True
                            elif title_lower == "web service":
                                print(colored(f"[+] Found Dahua Camera - {ip}:{port}", "green", attrs=['bold']))
                                save_results(ip, port, "Dahua Camera")
                                return True
                            # Check for other camera brands in title
                            elif any(keyword in title_lower for keyword in ["dahua", "dmss"]):
                                print(colored(f"[+] Found Dahua Camera - {ip}:{port}", "green", attrs=['bold']))
                                save_results(ip, port, "Dahua Camera")
                                return True
                            elif any(keyword in title_lower for keyword in ["hikvision", "hik"]):
                                print(colored(f"[+] Found Hikvision Camera - {ip}:{port}", "cyan", attrs=['bold']))
                                save_results(ip, port, "Hikvision Camera")
                                return True
                            elif any(keyword in title_lower for keyword in ["ip camera", "web camera", "web cam", "ip cam", "cctv", "surveillance"]):
                                print(colored(f"[+] Found Generic Camera - {ip}:{port}", "blue", attrs=['bold']))
                                save_results(ip, port, "Generic Camera")
                                return True
                        
                        # Also check response body for other camera indicators
                        response_lower = response_str.lower()
                        if any(indicator in response_lower for indicator in ["hikvision", "hik-connect", "/doc/page/"]):
                            print(colored(f"[+] Found Hikvision Camera - {ip}:{port}", "cyan", attrs=['bold']))
                            save_results(ip, port, "Hikvision Camera")
                            return True
                        elif any(indicator in response_lower for indicator in ["dahua", "dmss", "dhi-"]):
                            print(colored(f"[+] Found Dahua Camera - {ip}:{port}", "green", attrs=['bold']))
                            save_results(ip, port, "Dahua Camera")
                            return True
                        elif any(indicator in response_lower for indicator in ["camera", "cctv", "surveillance", "ipcam"]):
                            print(colored(f"[+] Found Generic Camera - {ip}:{port}", "blue", attrs=['bold']))
                            save_results(ip, port, "Generic Camera")
                            return True
        return False
    except Exception as e:
        # Only show errors for debugging if needed
        # print(colored(f"Error scanning {ip}:{port}: {e}", "red"))
        return False
            
def parse_ports(ports_input):
    ports = []
    if not ports_input:
        print(colored(f"[!] No Ports Defined Using Default 80 and 8080", "yellow"))
        ports_input = "80,8080"
    
    ports_input = ports_input.strip()
    
    if "," in ports_input:
        try:
            ports = [int(p.strip()) for p in ports_input.split(",")]
            ports = [p for p in ports if 1 <= p <= 65535]
            if len(ports) != len(set(ports)):
                print(colored(f"[!] Duplicate Ports Removed!", "yellow"))
                ports = list(set(ports))
        except ValueError:
            print(colored(f"[x] Invalid Ports List", "red"))
            return []
    else:
        try:
            port = int(ports_input)
            if 1 <= port <= 65535:
                ports = [port]
            else:
                print(colored(f"[x] Port must be between 1-65535", "red"))
                return []
        except ValueError:
            print(colored(f"[x] Invalid Port!", "red"))
            return []
    
    return ports
    
def main():
    display_banner()
    
    print(colored("[+] IP Input Options:", "cyan"))
    print(colored("    1. Manual IP/CIDR input", "cyan"))
    print(colored("    2. Read from text file", "cyan"))
    
    choice = input(colored("\n[+] Select option (1 or 2): ", "cyan")).strip()
    ip_range = []
    
    if choice == "2":
        filename = input(colored("[+] Enter filename with IPs/CIDRs: ", "cyan")).strip()
        ip_inputs = read_ips_from_file(filename)
        
        if not ip_inputs:
            return
            
        for ip_input in ip_inputs:
            if "/" in ip_input:
                ips = cidr_to_ips(ip_input)
                ip_range.extend(ips)
            else:
                try:
                    ipaddress.ip_address(ip_input)
                    ip_range.append(ip_input)
                except ValueError:
                    print(colored(f"[!] Skipping invalid IP: {ip_input}", "yellow"))
    
    else:
        ip_cidr = input(colored("[+] Enter IP Address or IP Range: ", "cyan")).strip()
        
        if not ip_cidr:
            print(colored("[x] No IP address provided", "red"))
            return
        
        if "/" in ip_cidr:
            ip_range = cidr_to_ips(ip_cidr)
        else:
            try:
                ipaddress.ip_address(ip_cidr)
                ip_range = [ip_cidr]
            except ValueError:
                print(colored(f"[x] Invalid IP/CIDR: {ip_cidr}", "red"))
                return
    
    if not ip_range:
        print(colored("[x] No valid IP addresses to scan", "red"))
        return
        
    ports_input = input(colored(f"[+] Enter Ports Separated by commas: ", "cyan"))
    
    ports = parse_ports(ports_input)
    if not ports:
        return
            
    # Calculate total targets
    total_targets = len(ip_range) * len(ports)
    
    # Adjust max threads based on system capability
    max_concurrent = 1000  # Reduced from 1000 for stability
    max_threads = max_concurrent
    
    print(colored(f"\n[+] Starting Scan", "yellow"))
    print(colored(f"[+] Total Targets : {total_targets}", "yellow"))
    print(colored(f"[+] Using {max_threads} max concurrent threads", "yellow"))
    print(colored(f"[+] Scanning...\n", "yellow"))
    
    start_time = time.time()
    open_ports = []
    
    # Use a semaphore to limit concurrent threads
    thread_semaphore = threading.Semaphore(max_threads)
    
    def scan_with_limits(ip, port):
        with thread_semaphore:
            is_open = scan_ports(ip, port)
            if is_open:
                open_ports.append((ip, port))
    
    # Thread management
    threads = []
    scanned_targets = 0
    
    for ip in ip_range:
        for port in ports:
            # Create thread
            thread = threading.Thread(target=scan_with_limits, args=(ip, port))
            thread.start()
            threads.append(thread)
            scanned_targets += 1
            
            # Small delay to prevent overwhelming the system
            if len(threads) >= max_threads * 2:
                # Clean up finished threads periodically
                threads = [t for t in threads if t.is_alive()]
                time.sleep(0.01)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
        
    end_time = time.time()
    scan_duration = end_time - start_time
    
    print(colored(f"\n\n{'='*70}", "cyan"))
    print(colored(f"SCAN COMPLETED", "cyan", attrs=['bold']))
    print(colored(f"Duration : {scan_duration:.2f} seconds", "cyan"))
    print(colored(f"Total Targets Scanned : {scanned_targets}", "cyan"))
    print(colored(f"Total Cameras Found : {len(open_ports)}", "cyan"))
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            total_cameras = len(f.readlines())
        print(colored(f"Total in Output File : {total_cameras}", "cyan"))
    print(colored(f"{'='*70}", "cyan"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored(f"\n\n[x] Interrupted by User!", "red"))
    except Exception as e:
        print(colored(f"\n\n[x] Unexpected Error : {e}", "red"))
