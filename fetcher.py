import requests
import ipaddress
import json
from pathlib import Path

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
║    │ █▄▄▄▄▄▄▄▄▄ █▄▄▄█ █▄▄▄▄ █▄▄▄█ █▄▄▄▄ █▄▄▄▄ │ IPv4 Range Collector    │    ║
║    └────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║    [✓] Author   : Shadow Ghost                                               ║
║    [✓] Telegram : https://t.me/shadow_ghost_yt                               ║
║    [✓] GitHub   : https://github.com/0xdeadgh0st7a5                          ║
║    [✓] Purpose  : Extract IPv4 ranges by country from RIR databases          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    # Print banner with green color for hacker vibe
    print('\033[92m' + banner + '\033[0m')

def fetch_rir_data():
    """Fetch data from all RIRs"""
    rir_urls = {
        'arin': 'https://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest',
        'ripe': 'https://ftp.ripe.net/ripe/stats/delegated-ripencc-extended-latest',
        'apnic': 'https://ftp.apnic.net/stats/apnic/delegated-apnic-extended-latest',
        'lacnic': 'https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-extended-latest',
        'afrinic': 'https://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-extended-latest'
    }
    
    all_entries = []
    
    for rir, url in rir_urls.items():
        try:
            print(f"Fetching data from {rir.upper()}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the data
            for line in response.text.splitlines():
                if line.startswith('#') or not line.strip():
                    continue
                
                parts = line.strip().split('|')
                if len(parts) >= 7:
                    registry, country, type, start, value, date, status = parts[:7]
                    if type == 'ipv4' and status == 'allocated':
                        all_entries.append({
                            'rir': registry,
                            'country': country,
                            'type': type,
                            'start': start,
                            'value': int(value),
                            'date': date
                        })
        except Exception as e:
            print(f"Error fetching from {rir}: {e}")
    
    return all_entries

def calculate_ipv4_ranges(entries, country_code):
    """Calculate CIDR ranges from entries for a specific country"""
    country_code = country_code.upper()
    ranges = []
    
    for entry in entries:
        if entry['country'] == country_code:
            start_ip = entry['start']
            num_addresses = entry['value']
            
            # Calculate network address and CIDR
            network = ipaddress.IPv4Network(f"{start_ip}/{32 - (num_addresses - 1).bit_length()}", strict=False)
            ranges.append(str(network))
    
    return sorted(set(ranges))  # Remove duplicates and sort

def save_ranges(country_code, ranges, output_dir='ip_ranges'):
    """Save ranges to files"""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Save as plain text (CIDR list)
    txt_file = Path(output_dir) / f'{country_code}_ip_ranges.txt'
    with open(txt_file, 'w') as f:
        f.write('\n'.join(ranges))
    
    print(f"Saved {len(ranges)} ranges to:")
    print(f"  Text: {txt_file}")

def main():
    display_banner()
    """Main function"""
    # Get user input
    country_code = input("Enter country code (e.g., US, CN, JP, GB): ").strip().upper()
    
    if len(country_code) != 2:
        print("Please enter a valid 2-letter country code")
        return
    
    print(f"\nFetching IPv4 ranges for {country_code}...")
    
    # Fetch data from RIRs
    entries = fetch_rir_data()
    
    if not entries:
        print("No data fetched. Check your internet connection.")
        return
    
    print(f"Total IPv4 entries fetched: {len(entries)}")
    
    # Calculate ranges for the country
    ranges = calculate_ipv4_ranges(entries, country_code)
    
    if not ranges:
        print(f"No IPv4 ranges found for country code: {country_code}")
        return
    
    print(f"\nFound {len(ranges)} unique IPv4 ranges for {country_code}")
    
    # Display first 5 ranges as preview
    print("\nFirst 5 ranges (preview):")
    for r in ranges[:5]:
        print(f"  {r}")
    if len(ranges) > 5:
        print(f"  ... and {len(ranges) - 5} more")
    
    # Calculate total addresses
    total_addresses = sum(ipaddress.IPv4Network(r).num_addresses for r in ranges)
    print(f"\nTotal IPv4 addresses: {total_addresses:,}")
    
    # Save to files
    save_ranges(country_code, ranges)
    
    # Display summary
    print(f"\nSummary for {country_code}:")
    print(f"  Total CIDR ranges: {len(ranges)}")
    print(f"  Total IP addresses: {total_addresses:,}")

def quick_fetch(country_code):
    """Quick fetch function for programmatic use"""
    print(f"Fetching IPv4 ranges for {country_code}...")
    entries = fetch_rir_data()
    ranges = calculate_ipv4_ranges(entries, country_code)
    save_ranges(country_code, ranges)
    return ranges

if __name__ == "__main__":
    main()
    
    # Example for programmatic use:
    # ranges = quick_fetch("US")
