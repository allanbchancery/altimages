import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
import time
import re
from collections import defaultdict
import json

class MatalanSiteDiscovery:
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
        self.discovered_urls = []
        self.url_categories = defaultdict(list)
        self.page_templates = {}
        self.crawl_delay = 2  # 2 seconds between requests
        
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
                    'content': robots_content
                }
            else:
                print("⚠️ robots.txt not found, using default settings")
                return None
        except Exception as e:
            print(f"❌ Error checking robots.txt: {e}")
            return None
    
    def fetch_sitemap(self):
        """Fetch and parse sitemap.xml"""
        print("🗺️ Fetching sitemap...")
        sitemaps_to_check = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemaps/sitemap.xml"
        ]
        
        for sitemap_url in sitemaps_to_check:
            try:
                print(f"   Trying: {sitemap_url}")
                time.sleep(self.crawl_delay)
                response = self.session.get(sitemap_url, timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ Found sitemap at: {sitemap_url}")
                    return self.parse_sitemap(response.content, sitemap_url)
                    
            except Exception as e:
                print(f"   ❌ Failed to fetch {sitemap_url}: {e}")
                continue
        
        print("⚠️ No sitemap found, will use alternative discovery methods")
        return []
    
    def parse_sitemap(self, xml_content, sitemap_url):
        """Parse sitemap XML and extract URLs"""
        try:
            root = ET.fromstring(xml_content)
            urls = []
            
            # Handle sitemap index (contains links to other sitemaps)
            if 'sitemapindex' in root.tag:
                print("📋 Found sitemap index, fetching individual sitemaps...")
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                    loc_elem = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc_elem is not None:
                        sub_sitemap_url = loc_elem.text
                        print(f"   Fetching sub-sitemap: {sub_sitemap_url}")
                        time.sleep(self.crawl_delay)
                        try:
                            sub_response = self.session.get(sub_sitemap_url, timeout=15)
                            if sub_response.status_code == 200:
                                sub_urls = self.parse_sitemap(sub_response.content, sub_sitemap_url)
                                urls.extend(sub_urls)
                        except Exception as e:
                            print(f"   ❌ Failed to fetch sub-sitemap: {e}")
            
            # Handle regular sitemap (contains URLs)
            else:
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc_elem is not None:
                        url = loc_elem.text
                        
                        # Get additional metadata if available
                        lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                        priority_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
                        
                        url_data = {
                            'url': url,
                            'lastmod': lastmod_elem.text if lastmod_elem is not None else None,
                            'priority': priority_elem.text if priority_elem is not None else None
                        }
                        urls.append(url_data)
            
            print(f"✅ Extracted {len(urls)} URLs from sitemap")
            return urls
            
        except ET.ParseError as e:
            print(f"❌ Error parsing sitemap XML: {e}")
            return []
    
    def categorize_urls(self, urls):
        """Categorize URLs by type and purpose"""
        print("📂 Categorizing URLs...")
        
        categories = {
            'product_pages': [],
            'category_pages': [],
            'brand_pages': [],
            'static_pages': [],
            'utility_pages': [],
            'other': []
        }
        
        patterns = {
            'product_pages': [
                r'/clothing/.+/\d+\.html$',
                r'/home/.+/\d+\.html$',
                r'/baby/.+/\d+\.html$',
                r'/accessories/.+/\d+\.html$'
            ],
            'category_pages': [
                r'/clothing/?$',
                r'/clothing/[^/]+/?$',
                r'/home/?$',
                r'/baby/?$',
                r'/accessories/?$'
            ],
            'brand_pages': [
                r'/brands/',
                r'/designer/'
            ],
            'static_pages': [
                r'/$',  # Homepage
                r'/about',
                r'/help',
                r'/contact',
                r'/stores',
                r'/size-guide'
            ],
            'utility_pages': [
                r'/search',
                r'/account',
                r'/basket',
                r'/checkout',
                r'/login'
            ]
        }
        
        for url_data in urls:
            url = url_data['url'] if isinstance(url_data, dict) else url_data
            path = urlparse(url).path
            categorized = False
            
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, path, re.IGNORECASE):
                        categories[category].append(url_data)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                categories['other'].append(url_data)
        
        # Print summary
        for category, urls_list in categories.items():
            print(f"   {category}: {len(urls_list)} URLs")
        
        return categories
    
    def select_representative_samples(self, categorized_urls):
        """Select representative pages for analysis"""
        print("🎯 Selecting representative samples...")
        
        samples = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # High priority: Homepage and main category pages
        if categorized_urls['static_pages']:
            homepage = [url for url in categorized_urls['static_pages'] 
                       if urlparse(url['url'] if isinstance(url, dict) else url).path == '/']
            if homepage:
                samples['high_priority'].extend(homepage[:1])
        
        # High priority: Main category pages
        main_categories = [url for url in categorized_urls['category_pages']
                          if len(urlparse(url['url'] if isinstance(url, dict) else url).path.strip('/').split('/')) <= 1]
        samples['high_priority'].extend(main_categories[:5])
        
        # Medium priority: Product pages (sample from different categories)
        product_samples = self.sample_products_by_category(categorized_urls['product_pages'])
        samples['medium_priority'].extend(product_samples)
        
        # Low priority: Other pages
        samples['low_priority'].extend(categorized_urls['brand_pages'][:3])
        samples['low_priority'].extend(categorized_urls['utility_pages'][:2])
        
        total_samples = sum(len(urls) for urls in samples.values())
        print(f"✅ Selected {total_samples} representative pages for analysis")
        
        return samples
    
    def sample_products_by_category(self, product_urls, max_per_category=3):
        """Sample products from different categories"""
        category_products = defaultdict(list)
        
        for url_data in product_urls:
            url = url_data['url'] if isinstance(url_data, dict) else url_data
            path = urlparse(url).path
            
            # Extract category from URL path
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2:
                category = path_parts[0]  # e.g., 'clothing', 'home', 'baby'
                subcategory = path_parts[1] if len(path_parts) > 2 else 'general'
                category_key = f"{category}/{subcategory}"
                category_products[category_key].append(url_data)
        
        # Sample from each category
        samples = []
        for category, products in category_products.items():
            # Take up to max_per_category products from each category
            sampled = products[:max_per_category]
            samples.extend(sampled)
            print(f"   {category}: {len(sampled)} samples selected")
        
        return samples
    
    def generate_discovery_report(self, robots_data, sitemap_urls, categorized_urls, samples):
        """Generate comprehensive discovery report"""
        report = {
            'discovery_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'robots_txt': robots_data,
            'sitemap_analysis': {
                'total_urls_found': len(sitemap_urls),
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
                'user_agent': self.session.headers['User-Agent']
            }
        }
        
        return report
    
    def run_discovery(self):
        """Run the complete discovery phase"""
        print("🚀 Starting Matalan Site Discovery - Phase 1")
        print("=" * 60)
        
        # Step 1: Check robots.txt
        robots_data = self.check_robots_txt()
        
        # Step 2: Fetch sitemap
        sitemap_urls = self.fetch_sitemap()
        
        # Step 3: Categorize URLs
        categorized_urls = self.categorize_urls(sitemap_urls)
        
        # Step 4: Select samples
        samples = self.select_representative_samples(categorized_urls)
        
        # Step 5: Generate report
        report = self.generate_discovery_report(robots_data, sitemap_urls, categorized_urls, samples)
        
        print("\n" + "=" * 60)
        print("✅ Discovery Phase 1 Complete!")
        print(f"📊 Total URLs discovered: {len(sitemap_urls)}")
        print(f"🎯 Representative samples selected: {report['sampling_strategy']['total_selected']}")
        print(f"⏱️ Recommended crawl delay: {self.crawl_delay} seconds")
        
        return report

def save_discovery_report(report, filename='matalan_discovery_report.json'):
    """Save discovery report to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Discovery report saved to: {filename}")

if __name__ == "__main__":
    # Run discovery
    discovery = MatalanSiteDiscovery()
    report = discovery.run_discovery()
    
    # Save report
    save_discovery_report(report)
    
    # Print summary
    print("\n📋 DISCOVERY SUMMARY:")
    print(f"   🏠 Homepage: Included")
    print(f"   📂 Category pages: {report['sitemap_analysis']['categories']['category_pages']}")
    print(f"   🛍️ Product pages: {report['sitemap_analysis']['categories']['product_pages']}")
    print(f"   📄 Static pages: {report['sitemap_analysis']['categories']['static_pages']}")
    print(f"   🔧 Utility pages: {report['sitemap_analysis']['categories']['utility_pages']}")
    print(f"\n🎯 Ready for Phase 2: Sampling Analysis")
