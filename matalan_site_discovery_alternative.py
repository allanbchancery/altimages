import requests
import urllib3
from urllib.parse import urlparse, urljoin
import time
import re
from collections import defaultdict
import json
from bs4 import BeautifulSoup

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MatalanSiteDiscoveryAlternative:
    def __init__(self):
        self.base_url = "https://www.matalan.co.uk"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AccessibilityAnalyzer/1.0; +https://example.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        # Disable SSL verification
        self.session.verify = False
        self.discovered_urls = []
        self.crawl_delay = 2
        
    def check_robots_txt(self):
        """Check robots.txt for crawling guidelines"""
        print("🤖 Checking robots.txt...")
        try:
            response = self.session.get(f"{self.base_url}/robots.txt", timeout=10)
            if response.status_code == 200:
                robots_content = response.text
                print("✅ robots.txt found")
                
                # Look for crawl delay
                crawl_delay_match = re.search(r'Crawl-delay:\s*(\d+)', robots_content, re.IGNORECASE)
                if crawl_delay_match:
                    suggested_delay = int(crawl_delay_match.group(1))
                    self.crawl_delay = max(self.crawl_delay, suggested_delay)
                    print(f"📋 Crawl delay set to {self.crawl_delay} seconds")
                
                # Check for disallowed paths
                disallowed = re.findall(r'Disallow:\s*(.+)', robots_content, re.IGNORECASE)
                print(f"🚫 Found {len(disallowed)} disallowed paths")
                
                return {
                    'crawl_delay': self.crawl_delay,
                    'disallowed_paths': disallowed,
                    'content': robots_content[:500] + "..." if len(robots_content) > 500 else robots_content
                }
            else:
                print("⚠️ robots.txt not found, using default settings")
                return None
        except Exception as e:
            print(f"❌ Error checking robots.txt: {e}")
            return None
    
    def discover_from_homepage(self):
        """Discover site structure from homepage navigation"""
        print("🏠 Analyzing homepage for site structure...")
        try:
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find navigation links
                nav_links = []
                
                # Common navigation selectors
                nav_selectors = [
                    'nav a',
                    '.navigation a',
                    '.nav a',
                    '.menu a',
                    'header a',
                    '.main-nav a'
                ]
                
                for selector in nav_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href and href.startswith('/'):
                            full_url = urljoin(self.base_url, href)
                            nav_links.append({
                                'url': full_url,
                                'text': link.get_text(strip=True),
                                'source': 'navigation'
                            })
                
                print(f"✅ Found {len(nav_links)} navigation links")
                return nav_links
                
        except Exception as e:
            print(f"❌ Error analyzing homepage: {e}")
            return []
    
    def generate_known_urls(self):
        """Generate URLs based on common e-commerce patterns"""
        print("🔍 Generating URLs based on common patterns...")
        
        known_urls = []
        
        # Main category pages
        categories = [
            '/clothing',
            '/clothing/womens',
            '/clothing/mens', 
            '/clothing/dresses',
            '/clothing/tops',
            '/clothing/jeans',
            '/home',
            '/home/bedding',
            '/home/furniture',
            '/baby',
            '/accessories',
            '/shoes'
        ]
        
        for category in categories:
            known_urls.append({
                'url': f"{self.base_url}{category}",
                'type': 'category',
                'source': 'pattern_generation'
            })
        
        # Static pages
        static_pages = [
            '/',
            '/about',
            '/help',
            '/contact',
            '/stores',
            '/size-guide',
            '/delivery',
            '/returns'
        ]
        
        for page in static_pages:
            known_urls.append({
                'url': f"{self.base_url}{page}",
                'type': 'static',
                'source': 'pattern_generation'
            })
        
        # Sample product URLs (based on the pattern we know works)
        sample_products = [
            '/clothing/brown-leaf-print-tunic-midaxi-dress/15824638.html',
            '/clothing/black-basic-t-shirt/12345678.html',
            '/clothing/blue-denim-jeans/87654321.html'
        ]
        
        for product in sample_products:
            known_urls.append({
                'url': f"{self.base_url}{product}",
                'type': 'product',
                'source': 'known_pattern'
            })
        
        print(f"✅ Generated {len(known_urls)} URLs from patterns")
        return known_urls
    
    def validate_urls(self, urls):
        """Validate which URLs actually exist"""
        print("✅ Validating URL accessibility...")
        valid_urls = []
        
        for i, url_data in enumerate(urls[:20]):  # Limit to first 20 for discovery
            try:
                url = url_data['url']
                print(f"   Checking {i+1}/{min(len(urls), 20)}: {url}")
                
                # Use HEAD request to check if URL exists
                response = self.session.head(url, timeout=10, allow_redirects=True)
                
                if response.status_code in [200, 301, 302]:
                    url_data['status'] = response.status_code
                    url_data['accessible'] = True
                    valid_urls.append(url_data)
                    print(f"      ✅ Accessible (Status: {response.status_code})")
                else:
                    print(f"      ❌ Not accessible (Status: {response.status_code})")
                
                time.sleep(self.crawl_delay)
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:50]}...")
                continue
        
        print(f"✅ Found {len(valid_urls)} accessible URLs")
        return valid_urls
    
    def categorize_discovered_urls(self, urls):
        """Categorize discovered URLs"""
        print("📂 Categorizing discovered URLs...")
        
        categories = {
            'homepage': [],
            'category_pages': [],
            'product_pages': [],
            'static_pages': [],
            'other': []
        }
        
        for url_data in urls:
            url = url_data['url']
            path = urlparse(url).path
            
            if path == '/':
                categories['homepage'].append(url_data)
            elif re.search(r'/clothing/.+/\d+\.html$', path):
                categories['product_pages'].append(url_data)
            elif re.search(r'/clothing/?$|/home/?$|/baby/?$', path):
                categories['category_pages'].append(url_data)
            elif path in ['/about', '/help', '/contact', '/stores', '/size-guide', '/delivery', '/returns']:
                categories['static_pages'].append(url_data)
            else:
                categories['other'].append(url_data)
        
        # Print summary
        for category, urls_list in categories.items():
            print(f"   {category}: {len(urls_list)} URLs")
        
        return categories
    
    def select_analysis_samples(self, categorized_urls):
        """Select representative samples for analysis"""
        print("🎯 Selecting samples for analysis...")
        
        samples = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # High priority: Homepage
        samples['high_priority'].extend(categorized_urls['homepage'])
        
        # High priority: Main category pages
        samples['high_priority'].extend(categorized_urls['category_pages'][:3])
        
        # Medium priority: Product pages
        samples['medium_priority'].extend(categorized_urls['product_pages'][:5])
        
        # Low priority: Static pages
        samples['low_priority'].extend(categorized_urls['static_pages'][:3])
        
        total_samples = sum(len(urls) for urls in samples.values())
        print(f"✅ Selected {total_samples} samples for analysis")
        
        return samples
    
    def generate_discovery_report(self, robots_data, nav_links, generated_urls, valid_urls, categorized_urls, samples):
        """Generate comprehensive discovery report"""
        report = {
            'discovery_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'discovery_method': 'Alternative (Homepage + Pattern Generation)',
            'robots_txt': robots_data,
            'navigation_analysis': {
                'nav_links_found': len(nav_links),
                'sample_nav_links': nav_links[:5]  # First 5 for reference
            },
            'url_generation': {
                'total_generated': len(generated_urls),
                'total_validated': len(valid_urls),
                'validation_success_rate': f"{len(valid_urls)/len(generated_urls)*100:.1f}%" if generated_urls else "0%"
            },
            'categorization': {
                'categories': {k: len(v) for k, v in categorized_urls.items()}
            },
            'sampling_strategy': {
                'high_priority_pages': len(samples['high_priority']),
                'medium_priority_pages': len(samples['medium_priority']),
                'low_priority_pages': len(samples['low_priority']),
                'total_selected': sum(len(urls) for urls in samples.values())
            },
            'selected_urls': samples,
            'crawl_settings': {
                'crawl_delay': self.crawl_delay,
                'user_agent': self.session.headers['User-Agent'],
                'ssl_verification': False
            }
        }
        
        return report
    
    def run_discovery(self):
        """Run the complete alternative discovery phase"""
        print("🚀 Starting Matalan Site Discovery - Phase 1 (Alternative Method)")
        print("=" * 70)
        
        # Step 1: Check robots.txt
        robots_data = self.check_robots_txt()
        
        # Step 2: Analyze homepage navigation
        nav_links = self.discover_from_homepage()
        
        # Step 3: Generate known URL patterns
        generated_urls = self.generate_known_urls()
        
        # Step 4: Validate URLs
        valid_urls = self.validate_urls(generated_urls)
        
        # Step 5: Categorize URLs
        categorized_urls = self.categorize_discovered_urls(valid_urls)
        
        # Step 6: Select samples
        samples = self.select_analysis_samples(categorized_urls)
        
        # Step 7: Generate report
        report = self.generate_discovery_report(robots_data, nav_links, generated_urls, valid_urls, categorized_urls, samples)
        
        print("\n" + "=" * 70)
        print("✅ Alternative Discovery Phase 1 Complete!")
        print(f"📊 Total URLs validated: {len(valid_urls)}")
        print(f"🎯 Representative samples selected: {report['sampling_strategy']['total_selected']}")
        print(f"⏱️ Recommended crawl delay: {self.crawl_delay} seconds")
        
        return report

def save_discovery_report(report, filename='matalan_discovery_report_alternative.json'):
    """Save discovery report to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Discovery report saved to: {filename}")

if __name__ == "__main__":
    # Run alternative discovery
    discovery = MatalanSiteDiscoveryAlternative()
    report = discovery.run_discovery()
    
    # Save report
    save_discovery_report(report)
    
    # Print summary
    print("\n📋 ALTERNATIVE DISCOVERY SUMMARY:")
    print(f"   🏠 Homepage: {'✅' if report['categorization']['categories']['homepage'] > 0 else '❌'}")
    print(f"   📂 Category pages: {report['categorization']['categories']['category_pages']}")
    print(f"   🛍️ Product pages: {report['categorization']['categories']['product_pages']}")
    print(f"   📄 Static pages: {report['categorization']['categories']['static_pages']}")
    print(f"   🔧 Other pages: {report['categorization']['categories']['other']}")
    print(f"\n🎯 Ready for Phase 2: Sampling Analysis")
    print(f"📈 Success Rate: {report['url_generation']['validation_success_rate']}")
