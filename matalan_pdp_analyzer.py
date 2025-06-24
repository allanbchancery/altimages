import requests
import urllib3
from urllib.parse import urlparse, urljoin
import time
import json
from bs4 import BeautifulSoup
import re
from collections import defaultdict, Counter
import hashlib

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MatalanPDPAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PDPAnalyzer/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        self.crawl_delay = 2
        self.discovered_pdps = []
        self.analyzed_pdps = {}
        
    def discover_pdps_from_categories(self):
        """Discover PDP URLs from category pages and known patterns"""
        print("🔍 Discovering PDPs from multiple sources...")
        
        all_pdp_urls = set()
        
        # Method 1: Use known working PDP and try to find similar patterns
        known_pdp = "https://www.matalan.co.uk/clothing/brown-leaf-print-tunic-midaxi-dress/15824638.html"
        all_pdp_urls.add(known_pdp)
        print(f"   Added known working PDP: {known_pdp}")
        
        # Method 2: Try category pages with different approaches
        category_urls = [
            "https://www.matalan.co.uk/womens.list",
            "https://www.matalan.co.uk/mens.list", 
            "https://www.matalan.co.uk/kids.list",
            "https://www.matalan.co.uk/homeware.list",
            "https://www.matalan.co.uk/baby.list"
        ]
        
        for category_url in category_urls:
            try:
                print(f"   Scanning: {category_url}")
                response = self.session.get(category_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # More comprehensive link discovery
                    all_links = soup.find_all('a', href=True)
                    category_pdps = set()
                    
                    for link in all_links:
                        href = link.get('href')
                        if href:
                            if href.startswith('/'):
                                full_url = urljoin("https://www.matalan.co.uk", href)
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                continue
                            
                            # Filter for actual product pages with more patterns
                            if self.is_likely_pdp(full_url):
                                category_pdps.add(full_url)
                    
                    print(f"      Found {len(category_pdps)} potential PDPs")
                    all_pdp_urls.update(category_pdps)
                    
                    # Debug: Show some example links found
                    if len(category_pdps) == 0:
                        sample_links = [link.get('href') for link in all_links[:10] if link.get('href')]
                        print(f"      Sample links found: {sample_links}")
                    
                time.sleep(self.crawl_delay)
                
            except Exception as e:
                print(f"   ❌ Error scanning {category_url}: {e}")
                continue
        
        # Method 3: Generate potential PDPs based on known patterns
        if len(all_pdp_urls) < 5:
            print("   🔄 Generating additional PDPs based on known patterns...")
            base_ids = ['15824638', '15824639', '15824640', '15824641', '15824642', 
                       '15824643', '15824644', '15824645', '15824646', '15824647']
            
            categories = ['clothing', 'home', 'baby']
            sample_names = [
                'black-basic-t-shirt',
                'blue-denim-jeans', 
                'white-cotton-shirt',
                'red-summer-dress',
                'grey-hoodie',
                'navy-trousers',
                'pink-blouse',
                'green-cardigan'
            ]
            
            for i, product_id in enumerate(base_ids):
                if i < len(sample_names):
                    category = categories[i % len(categories)]
                    name = sample_names[i]
                    potential_url = f"https://www.matalan.co.uk/{category}/{name}/{product_id}.html"
                    all_pdp_urls.add(potential_url)
        
        # Convert to list and limit for analysis
        self.discovered_pdps = list(all_pdp_urls)[:20]  # Limit to 20 for thorough analysis
        print(f"✅ Discovered {len(self.discovered_pdps)} unique PDPs for analysis")
        
        return self.discovered_pdps
    
    def is_likely_pdp(self, url):
        """Check if URL is likely a product detail page"""
        # Common PDP patterns
        pdp_patterns = [
            r'/clothing/.+/\d+\.html$',
            r'/home/.+/\d+\.html$', 
            r'/baby/.+/\d+\.html$',
            r'/accessories/.+/\d+\.html$',
            r'/product/.+',
            r'/p/\d+',
            r'/.+/\d{6,}\.html$'  # 6+ digit product IDs
        ]
        
        for pattern in pdp_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def analyze_pdp_images(self, soup, url):
        """Analyze all images on a PDP for alt tag compliance"""
        images = soup.find_all('img')
        
        image_analysis = {
            'total_images': len(images),
            'with_alt': 0,
            'missing_alt': 0,
            'empty_alt': 0,
            'good_alt': 0,
            'long_alt': 0,
            'images_detail': [],
            'issues': []
        }
        
        for i, img in enumerate(images):
            src = img.get('src', '')
            alt_text = img.get('alt')
            
            # Determine image type based on src or context
            image_type = self.classify_image_type(img, src)
            
            image_detail = {
                'index': i + 1,
                'src': src[:100] + '...' if len(src) > 100 else src,
                'alt_text': alt_text,
                'type': image_type,
                'status': '',
                'issue': ''
            }
            
            if alt_text is None:
                image_analysis['missing_alt'] += 1
                image_detail['status'] = 'missing'
                image_detail['issue'] = 'No alt attribute'
                image_analysis['issues'].append(f"Image {i+1} ({image_type}): Missing alt attribute")
            elif alt_text == '':
                image_analysis['empty_alt'] += 1
                image_detail['status'] = 'empty'
                image_detail['issue'] = 'Empty alt text'
            elif len(alt_text) > 125:
                image_analysis['long_alt'] += 1
                image_analysis['with_alt'] += 1
                image_detail['status'] = 'long'
                image_detail['issue'] = f'Alt text too long ({len(alt_text)} chars)'
                image_analysis['issues'].append(f"Image {i+1} ({image_type}): Alt text too long")
            else:
                image_analysis['good_alt'] += 1
                image_analysis['with_alt'] += 1
                image_detail['status'] = 'good'
            
            image_analysis['images_detail'].append(image_detail)
        
        # Calculate compliance score
        compliant_images = image_analysis['good_alt'] + image_analysis['empty_alt']  # Empty alt is OK for decorative
        image_analysis['compliance_score'] = (compliant_images / image_analysis['total_images'] * 100) if image_analysis['total_images'] > 0 else 0
        
        return image_analysis
    
    def classify_image_type(self, img_element, src):
        """Classify image type based on context and src"""
        # Check parent elements and classes for context
        parent_classes = []
        parent = img_element.parent
        for _ in range(3):  # Check up to 3 levels up
            if parent and parent.get('class'):
                parent_classes.extend(parent.get('class'))
            if parent:
                parent = parent.parent
            else:
                break
        
        img_classes = img_element.get('class', [])
        all_classes = ' '.join(parent_classes + img_classes).lower()
        
        # Classify based on patterns
        if any(term in all_classes for term in ['product', 'gallery', 'main', 'hero']):
            return 'product_image'
        elif any(term in all_classes for term in ['thumb', 'thumbnail', 'small']):
            return 'thumbnail'
        elif any(term in all_classes for term in ['logo', 'brand']):
            return 'logo'
        elif any(term in all_classes for term in ['icon', 'ui', 'button']):
            return 'ui_element'
        elif any(term in src.lower() for term in ['logo', 'icon', 'sprite']):
            return 'ui_element'
        elif any(term in src.lower() for term in ['product', 'item']):
            return 'product_image'
        else:
            return 'other'
    
    def detect_widgets_dynamically(self, soup, url):
        """Dynamically detect widgets based on HTML structure"""
        widgets = {}
        
        # 1. Image Gallery/Carousel Detection
        gallery_indicators = [
            soup.find_all(['div', 'section'], class_=re.compile(r'gallery|carousel|slider|swiper', re.I)),
            soup.find_all(['div'], attrs={'data-role': re.compile(r'gallery|carousel', re.I)}),
            soup.find_all(['div'], id=re.compile(r'gallery|carousel|slider', re.I))
        ]
        
        gallery_found = any(len(indicators) > 0 for indicators in gallery_indicators)
        if gallery_found:
            widgets['image_gallery'] = {
                'found': True,
                'type': 'Image Gallery/Carousel',
                'implementation': self.analyze_gallery_implementation(soup)
            }
        
        # 2. Size Selector Detection
        size_selectors = soup.find_all(['select', 'div'], attrs={
            'class': re.compile(r'size|variant', re.I),
            'data-attribute': re.compile(r'size', re.I)
        })
        size_buttons = soup.find_all('button', class_=re.compile(r'size', re.I))
        
        if size_selectors or size_buttons:
            widgets['size_selector'] = {
                'found': True,
                'type': 'Size Selector',
                'implementation': 'dropdown' if size_selectors else 'buttons',
                'count': len(size_selectors) + len(size_buttons)
            }
        
        # 3. Color/Variant Picker Detection
        color_elements = soup.find_all(['div', 'button', 'input'], class_=re.compile(r'color|colour|variant|swatch', re.I))
        if color_elements:
            widgets['color_picker'] = {
                'found': True,
                'type': 'Color/Variant Picker',
                'count': len(color_elements)
            }
        
        # 4. Quantity Selector Detection
        quantity_inputs = soup.find_all(['input'], attrs={'type': 'number'})
        quantity_selectors = soup.find_all(['select'], class_=re.compile(r'quantity|qty', re.I))
        
        if quantity_inputs or quantity_selectors:
            widgets['quantity_selector'] = {
                'found': True,
                'type': 'Quantity Selector',
                'implementation': 'input' if quantity_inputs else 'dropdown'
            }
        
        # 5. Add to Cart/Bag Detection
        add_to_cart = soup.find_all(['button', 'input'], attrs={
            'class': re.compile(r'add.*cart|add.*bag|buy', re.I),
            'data-action': re.compile(r'add.*cart|add.*bag', re.I)
        })
        
        if add_to_cart:
            widgets['add_to_cart'] = {
                'found': True,
                'type': 'Add to Cart/Bag',
                'count': len(add_to_cart)
            }
        
        # 6. Product Tabs/Accordion Detection
        tabs = soup.find_all(['div', 'ul'], class_=re.compile(r'tab|accordion', re.I))
        tab_panels = soup.find_all(['div'], attrs={'role': 'tabpanel'})
        
        if tabs or tab_panels:
            widgets['product_tabs'] = {
                'found': True,
                'type': 'Product Information Tabs/Accordion',
                'count': len(tabs) + len(tab_panels)
            }
        
        # 7. Reviews/Ratings Detection
        reviews = soup.find_all(['div', 'section'], class_=re.compile(r'review|rating|star', re.I))
        if reviews:
            widgets['reviews'] = {
                'found': True,
                'type': 'Reviews/Ratings',
                'count': len(reviews)
            }
        
        # 8. Recommendations Detection
        recommendations = soup.find_all(['div', 'section'], string=re.compile(r'you may also|recommend|similar|related', re.I))
        rec_containers = soup.find_all(['div', 'section'], class_=re.compile(r'recommend|similar|related|cross.sell', re.I))
        
        if recommendations or rec_containers:
            widgets['recommendations'] = {
                'found': True,
                'type': 'Product Recommendations',
                'count': len(recommendations) + len(rec_containers)
            }
        
        # 9. Breadcrumb Detection
        breadcrumbs = soup.find_all(['nav', 'div', 'ol'], class_=re.compile(r'breadcrumb', re.I))
        breadcrumb_schema = soup.find_all(['div'], attrs={'itemtype': re.compile(r'BreadcrumbList', re.I)})
        
        if breadcrumbs or breadcrumb_schema:
            widgets['breadcrumbs'] = {
                'found': True,
                'type': 'Breadcrumb Navigation'
            }
        
        # 10. Social Sharing Detection
        social = soup.find_all(['div', 'a', 'button'], class_=re.compile(r'share|social|facebook|twitter|pinterest', re.I))
        if social:
            widgets['social_sharing'] = {
                'found': True,
                'type': 'Social Sharing',
                'count': len(social)
            }
        
        # 11. Wishlist Detection
        wishlist = soup.find_all(['button', 'a'], class_=re.compile(r'wishlist|favourite|favorite|heart', re.I))
        if wishlist:
            widgets['wishlist'] = {
                'found': True,
                'type': 'Wishlist/Favorites',
                'count': len(wishlist)
            }
        
        # 12. Size Guide Detection
        size_guide = soup.find_all(['a', 'button'], string=re.compile(r'size guide|size chart|sizing', re.I))
        if size_guide:
            widgets['size_guide'] = {
                'found': True,
                'type': 'Size Guide',
                'count': len(size_guide)
            }
        
        return widgets
    
    def analyze_gallery_implementation(self, soup):
        """Analyze how the image gallery is implemented"""
        # Check for common carousel libraries
        if soup.find_all(class_=re.compile(r'swiper', re.I)):
            return 'Swiper.js'
        elif soup.find_all(class_=re.compile(r'slick', re.I)):
            return 'Slick Carousel'
        elif soup.find_all(class_=re.compile(r'owl', re.I)):
            return 'Owl Carousel'
        elif soup.find_all(class_=re.compile(r'glide', re.I)):
            return 'Glide.js'
        else:
            return 'Custom Implementation'
    
    def analyze_single_pdp(self, url):
        """Analyze a single PDP for images and widgets"""
        print(f"   Analyzing: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {'error': f'HTTP {response.status_code}', 'url': url}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic product info
            product_info = self.extract_product_info(soup, url)
            
            # Analyze images
            image_analysis = self.analyze_pdp_images(soup, url)
            
            # Detect widgets dynamically
            widgets = self.detect_widgets_dynamically(soup, url)
            
            # Page structure analysis
            structure = self.analyze_page_structure(soup)
            
            analysis_result = {
                'url': url,
                'product_info': product_info,
                'image_analysis': image_analysis,
                'widgets': widgets,
                'structure': structure,
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return {'error': str(e), 'url': url, 'status': 'failed'}
    
    def extract_product_info(self, soup, url):
        """Extract basic product information"""
        info = {
            'title': '',
            'category': '',
            'price': '',
            'product_id': ''
        }
        
        # Extract title
        title_selectors = ['h1', '.product-title', '.product-name', '[data-testid="product-title"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                info['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract category from URL or breadcrumbs
        path_parts = urlparse(url).path.strip('/').split('/')
        if len(path_parts) > 0:
            info['category'] = path_parts[0]
        
        # Extract product ID from URL
        id_match = re.search(r'/(\d+)\.html$', url)
        if id_match:
            info['product_id'] = id_match.group(1)
        
        # Extract price
        price_selectors = ['.price', '.product-price', '[data-testid="price"]', '.price-current']
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                info['price'] = price_elem.get_text(strip=True)
                break
        
        return info
    
    def analyze_page_structure(self, soup):
        """Analyze overall page structure"""
        return {
            'total_elements': len(soup.find_all()),
            'images': len(soup.find_all('img')),
            'buttons': len(soup.find_all('button')),
            'forms': len(soup.find_all('form')),
            'inputs': len(soup.find_all('input')),
            'selects': len(soup.find_all('select')),
            'links': len(soup.find_all('a'))
        }
    
    def run_pdp_analysis(self):
        """Run complete PDP analysis"""
        print("🚀 Starting Matalan PDP Analysis")
        print("=" * 50)
        
        # Step 1: Discover PDPs
        pdps = self.discover_pdps_from_categories()
        
        if not pdps:
            print("❌ No PDPs discovered")
            return None
        
        # Step 2: Analyze each PDP
        print(f"\n📊 Analyzing {len(pdps)} PDPs...")
        
        for i, pdp_url in enumerate(pdps):
            print(f"[{i+1}/{len(pdps)}] {pdp_url}")
            
            result = self.analyze_single_pdp(pdp_url)
            self.analyzed_pdps[pdp_url] = result
            
            # Respectful delay
            if i < len(pdps) - 1:
                time.sleep(self.crawl_delay)
        
        # Step 3: Generate summary
        summary = self.generate_analysis_summary()
        
        print(f"\n✅ PDP Analysis Complete!")
        print(f"📊 Analyzed: {len([r for r in self.analyzed_pdps.values() if r.get('status') == 'success'])} PDPs")
        print(f"❌ Failed: {len([r for r in self.analyzed_pdps.values() if r.get('status') == 'failed'])} PDPs")
        
        return {
            'summary': summary,
            'detailed_results': self.analyzed_pdps,
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_analysis_summary(self):
        """Generate summary statistics"""
        successful_analyses = [r for r in self.analyzed_pdps.values() if r.get('status') == 'success']
        
        if not successful_analyses:
            return {'error': 'No successful analyses'}
        
        # Image analysis summary
        total_images = sum(r['image_analysis']['total_images'] for r in successful_analyses)
        total_missing_alt = sum(r['image_analysis']['missing_alt'] for r in successful_analyses)
        total_good_alt = sum(r['image_analysis']['good_alt'] for r in successful_analyses)
        
        # Widget analysis summary
        widget_frequency = Counter()
        for result in successful_analyses:
            for widget_name in result['widgets'].keys():
                widget_frequency[widget_name] += 1
        
        # Category breakdown
        category_breakdown = Counter()
        for result in successful_analyses:
            category = result['product_info']['category']
            category_breakdown[category] += 1
        
        summary = {
            'total_pdps_analyzed': len(successful_analyses),
            'total_images': total_images,
            'alt_tag_compliance': {
                'total_missing': total_missing_alt,
                'total_good': total_good_alt,
                'compliance_rate': (total_good_alt / total_images * 100) if total_images > 0 else 0
            },
            'widget_frequency': dict(widget_frequency),
            'category_breakdown': dict(category_breakdown),
            'most_common_widgets': widget_frequency.most_common(10)
        }
        
        return summary

def save_pdp_analysis(results, filename='matalan_pdp_analysis.json'):
    """Save PDP analysis results"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 PDP analysis saved to: {filename}")

if __name__ == "__main__":
    analyzer = MatalanPDPAnalyzer()
    results = analyzer.run_pdp_analysis()
    
    if results:
        save_pdp_analysis(results)
        
        print(f"\n📋 ANALYSIS SUMMARY:")
        summary = results['summary']
        print(f"   📊 PDPs Analyzed: {summary['total_pdps_analyzed']}")
        print(f"   🖼️ Total Images: {summary['total_images']}")
        print(f"   ✅ Alt Tag Compliance: {summary['alt_tag_compliance']['compliance_rate']:.1f}%")
        print(f"   🧩 Unique Widgets Found: {len(summary['widget_frequency'])}")
        print(f"   📂 Categories: {list(summary['category_breakdown'].keys())}")
