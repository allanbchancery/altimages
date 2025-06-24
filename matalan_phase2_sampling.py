import requests
import urllib3
from urllib.parse import urlparse
import time
import json
from bs4 import BeautifulSoup
import re
from collections import defaultdict

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MatalanPhase2Sampling:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AccessibilityAnalyzer/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        self.crawl_delay = 2
        self.analysis_results = {}
        
    def analyze_page_accessibility(self, url, page_type):
        """Analyze a single page for accessibility and widgets"""
        print(f"🔍 Analyzing {page_type}: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {'error': f'HTTP {response.status_code}'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Image accessibility analysis
            images_data = self.analyze_images(soup)
            
            # Widget analysis
            widgets_data = self.analyze_widgets(soup, page_type)
            
            # Page structure analysis
            structure_data = self.analyze_page_structure(soup)
            
            # Accessibility features
            accessibility_data = self.analyze_accessibility_features(soup)
            
            return {
                'url': url,
                'page_type': page_type,
                'status': 'success',
                'images': images_data,
                'widgets': widgets_data,
                'structure': structure_data,
                'accessibility': accessibility_data,
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {url}: {e}")
            return {'error': str(e), 'url': url, 'page_type': page_type}
    
    def analyze_images(self, soup):
        """Analyze image accessibility"""
        images = soup.find_all('img')
        
        image_stats = {
            'total_images': len(images),
            'with_alt': 0,
            'missing_alt': 0,
            'empty_alt': 0,
            'long_alt': 0,
            'decorative': 0,
            'issues': []
        }
        
        for i, img in enumerate(images):
            alt_text = img.get('alt')
            src = img.get('src', '')
            
            if alt_text is None:
                image_stats['missing_alt'] += 1
                image_stats['issues'].append(f"Image {i+1}: Missing alt attribute")
            elif alt_text == '':
                image_stats['empty_alt'] += 1
                image_stats['decorative'] += 1
            elif len(alt_text) > 125:
                image_stats['long_alt'] += 1
                image_stats['with_alt'] += 1
                image_stats['issues'].append(f"Image {i+1}: Alt text too long ({len(alt_text)} chars)")
            else:
                image_stats['with_alt'] += 1
        
        # Calculate accessibility score
        accessible_images = image_stats['with_alt'] + image_stats['decorative']
        image_stats['accessibility_score'] = (accessible_images / image_stats['total_images'] * 100) if image_stats['total_images'] > 0 else 0
        
        return image_stats
    
    def analyze_widgets(self, soup, page_type):
        """Analyze widgets based on page type"""
        widgets = {}
        
        if page_type == 'homepage':
            widgets.update(self.analyze_homepage_widgets(soup))
        elif page_type == 'category':
            widgets.update(self.analyze_category_widgets(soup))
        elif page_type == 'product':
            widgets.update(self.analyze_product_widgets(soup))
        elif page_type == 'static':
            widgets.update(self.analyze_static_widgets(soup))
        
        # Common widgets for all pages
        widgets.update(self.analyze_common_widgets(soup))
        
        return widgets
    
    def analyze_homepage_widgets(self, soup):
        """Analyze homepage-specific widgets"""
        widgets = {}
        
        # Hero banner
        hero_sections = soup.find_all(['section', 'div'], class_=re.compile(r'hero|banner|carousel', re.I))
        widgets['hero_banner'] = {
            'found': len(hero_sections) > 0,
            'count': len(hero_sections),
            'has_images': any(section.find('img') for section in hero_sections)
        }
        
        # Featured categories
        category_sections = soup.find_all(['section', 'div'], class_=re.compile(r'category|featured|grid', re.I))
        widgets['featured_categories'] = {
            'found': len(category_sections) > 0,
            'count': len(category_sections)
        }
        
        return widgets
    
    def analyze_category_widgets(self, soup):
        """Analyze category page widgets"""
        widgets = {}
        
        # Product grid
        product_items = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|card', re.I))
        widgets['product_grid'] = {
            'found': len(product_items) > 0,
            'product_count': len(product_items)
        }
        
        # Filters
        filter_elements = soup.find_all(['div', 'section'], class_=re.compile(r'filter|facet|sidebar', re.I))
        widgets['filters'] = {
            'found': len(filter_elements) > 0,
            'filter_sections': len(filter_elements)
        }
        
        # Pagination
        pagination = soup.find_all(['nav', 'div'], class_=re.compile(r'pag', re.I))
        widgets['pagination'] = {
            'found': len(pagination) > 0
        }
        
        return widgets
    
    def analyze_product_widgets(self, soup):
        """Analyze product page widgets"""
        widgets = {}
        
        # Product gallery
        gallery_images = soup.find_all('img', src=re.compile(r'productimg|product', re.I))
        widgets['product_gallery'] = {
            'found': len(gallery_images) > 0,
            'image_count': len(gallery_images)
        }
        
        # Product info
        price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'price', re.I))
        widgets['product_info'] = {
            'price_found': len(price_elements) > 0,
            'price_elements': len(price_elements)
        }
        
        # Add to cart
        cart_buttons = soup.find_all(['button', 'input'], attrs={'type': 'submit'})
        cart_buttons.extend(soup.find_all('button', class_=re.compile(r'cart|bag|buy', re.I)))
        widgets['add_to_cart'] = {
            'found': len(cart_buttons) > 0,
            'button_count': len(cart_buttons)
        }
        
        # Recommendations
        rec_sections = soup.find_all(['section', 'div'], string=re.compile(r'you may also|recommend|similar', re.I))
        widgets['recommendations'] = {
            'found': len(rec_sections) > 0
        }
        
        return widgets
    
    def analyze_static_widgets(self, soup):
        """Analyze static page widgets"""
        widgets = {}
        
        # Forms
        forms = soup.find_all('form')
        widgets['forms'] = {
            'found': len(forms) > 0,
            'form_count': len(forms)
        }
        
        # Maps (for store locator)
        map_elements = soup.find_all(['div', 'iframe'], class_=re.compile(r'map', re.I))
        widgets['maps'] = {
            'found': len(map_elements) > 0
        }
        
        return widgets
    
    def analyze_common_widgets(self, soup):
        """Analyze widgets common to all pages"""
        widgets = {}
        
        # Navigation
        nav_elements = soup.find_all(['nav', 'header'])
        widgets['navigation'] = {
            'found': len(nav_elements) > 0,
            'nav_count': len(nav_elements)
        }
        
        # Footer
        footer_elements = soup.find_all('footer')
        widgets['footer'] = {
            'found': len(footer_elements) > 0
        }
        
        # Search
        search_inputs = soup.find_all('input', attrs={'type': 'search'})
        search_inputs.extend(soup.find_all('input', class_=re.compile(r'search', re.I)))
        widgets['search'] = {
            'found': len(search_inputs) > 0
        }
        
        return widgets
    
    def analyze_page_structure(self, soup):
        """Analyze overall page structure"""
        structure = {
            'total_elements': len(soup.find_all()),
            'headings': {
                'h1': len(soup.find_all('h1')),
                'h2': len(soup.find_all('h2')),
                'h3': len(soup.find_all('h3')),
                'h4': len(soup.find_all('h4')),
                'h5': len(soup.find_all('h5')),
                'h6': len(soup.find_all('h6'))
            },
            'interactive_elements': {
                'buttons': len(soup.find_all('button')),
                'links': len(soup.find_all('a')),
                'inputs': len(soup.find_all('input')),
                'selects': len(soup.find_all('select'))
            },
            'media_elements': {
                'images': len(soup.find_all('img')),
                'videos': len(soup.find_all('video')),
                'iframes': len(soup.find_all('iframe'))
            }
        }
        
        return structure
    
    def analyze_accessibility_features(self, soup):
        """Analyze accessibility features"""
        accessibility = {}
        
        # ARIA attributes
        aria_elements = soup.find_all(attrs={'aria-label': True})
        aria_elements.extend(soup.find_all(attrs={'aria-labelledby': True}))
        aria_elements.extend(soup.find_all(attrs={'aria-describedby': True}))
        
        accessibility['aria_usage'] = {
            'elements_with_aria': len(aria_elements),
            'aria_labels': len(soup.find_all(attrs={'aria-label': True})),
            'aria_labelledby': len(soup.find_all(attrs={'aria-labelledby': True})),
            'aria_describedby': len(soup.find_all(attrs={'aria-describedby': True}))
        }
        
        # Skip links
        skip_links = soup.find_all('a', href=re.compile(r'#.*content|#.*main', re.I))
        accessibility['skip_links'] = {
            'found': len(skip_links) > 0,
            'count': len(skip_links)
        }
        
        # Form labels
        labels = soup.find_all('label')
        inputs = soup.find_all('input')
        accessibility['form_accessibility'] = {
            'labels': len(labels),
            'inputs': len(inputs),
            'label_ratio': len(labels) / len(inputs) if inputs else 0
        }
        
        return accessibility
    
    def run_phase2_analysis(self):
        """Run Phase 2 sampling analysis"""
        print("🚀 Starting Matalan Phase 2: Sampling Analysis")
        print("=" * 60)
        
        # Load Phase 1 discovery results
        try:
            with open('matalan_quick_discovery.json', 'r') as f:
                discovery_data = json.load(f)
        except FileNotFoundError:
            print("❌ Phase 1 discovery data not found!")
            return None
        
        # Get recommended samples
        samples = discovery_data['recommended_samples']
        
        # Analyze each sample
        all_results = {}
        total_samples = sum(len(urls) for urls in samples.values())
        current_sample = 0
        
        for priority, urls in samples.items():
            print(f"\n📊 Analyzing {priority.upper()} priority pages...")
            
            for url_data in urls:
                current_sample += 1
                url = url_data['url']
                
                # Determine page type
                if url.endswith('/'):
                    page_type = 'homepage'
                elif '.list' in url or any(cat in url for cat in ['/womens', '/mens', '/kids', '/home', '/sale', '/baby']):
                    page_type = 'category'
                elif url.endswith('.html'):
                    page_type = 'product'
                else:
                    page_type = 'static'
                
                print(f"   [{current_sample}/{total_samples}] {page_type.title()}: {url}")
                
                # Analyze the page
                result = self.analyze_page_accessibility(url, page_type)
                all_results[url] = result
                
                # Respectful delay
                if current_sample < total_samples:
                    print(f"   ⏱️ Waiting {self.crawl_delay} seconds...")
                    time.sleep(self.crawl_delay)
        
        # Generate comprehensive report
        report = self.generate_phase2_report(discovery_data, all_results)
        
        print(f"\n✅ Phase 2 Analysis Complete!")
        print(f"📊 Analyzed {len(all_results)} pages")
        print(f"⏱️ Total analysis time: ~{len(all_results) * self.crawl_delay} seconds")
        
        return report
    
    def generate_phase2_report(self, discovery_data, analysis_results):
        """Generate comprehensive Phase 2 report"""
        
        # Aggregate statistics
        total_images = sum(result.get('images', {}).get('total_images', 0) for result in analysis_results.values() if 'images' in result)
        total_accessible_images = sum(result.get('images', {}).get('with_alt', 0) + result.get('images', {}).get('decorative', 0) for result in analysis_results.values() if 'images' in result)
        
        # Calculate overall accessibility score
        overall_accessibility = (total_accessible_images / total_images * 100) if total_images > 0 else 0
        
        # Widget analysis summary
        widget_summary = defaultdict(int)
        for result in analysis_results.values():
            if 'widgets' in result:
                for widget_type, widget_data in result['widgets'].items():
                    if isinstance(widget_data, dict) and widget_data.get('found'):
                        widget_summary[widget_type] += 1
        
        report = {
            'phase2_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'discovery_data': discovery_data,
            'analysis_summary': {
                'pages_analyzed': len(analysis_results),
                'successful_analyses': len([r for r in analysis_results.values() if 'error' not in r]),
                'total_images': total_images,
                'accessible_images': total_accessible_images,
                'overall_accessibility_score': round(overall_accessibility, 1)
            },
            'widget_summary': dict(widget_summary),
            'detailed_results': analysis_results,
            'recommendations': self.generate_recommendations(analysis_results)
        }
        
        return report
    
    def generate_recommendations(self, analysis_results):
        """Generate specific recommendations based on analysis"""
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # Analyze results for recommendations
        for url, result in analysis_results.items():
            if 'error' in result:
                continue
                
            images = result.get('images', {})
            if images.get('missing_alt', 0) > 0:
                recommendations['high_priority'].append(f"Add alt text to {images['missing_alt']} images on {result['page_type']} pages")
            
            if images.get('long_alt', 0) > 0:
                recommendations['medium_priority'].append(f"Shorten {images['long_alt']} overly long alt texts on {result['page_type']} pages")
            
            accessibility = result.get('accessibility', {})
            if accessibility.get('skip_links', {}).get('found') == False:
                recommendations['high_priority'].append(f"Add skip links to {result['page_type']} pages")
        
        return recommendations

def save_phase2_report(report, filename='matalan_phase2_report.json'):
    """Save Phase 2 report to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Phase 2 report saved to: {filename}")

if __name__ == "__main__":
    # Run Phase 2 analysis
    analyzer = MatalanPhase2Sampling()
    report = analyzer.run_phase2_analysis()
    
    if report:
        # Save report
        save_phase2_report(report)
        
        # Print summary
        print(f"\n📋 PHASE 2 ANALYSIS SUMMARY:")
        print(f"   📊 Pages analyzed: {report['analysis_summary']['pages_analyzed']}")
        print(f"   🖼️ Total images: {report['analysis_summary']['total_images']}")
        print(f"   ✅ Accessibility score: {report['analysis_summary']['overall_accessibility_score']}%")
        print(f"   🧩 Widgets found: {len(report['widget_summary'])}")
        print(f"\n🎯 Ready for Phase 3: Comprehensive Reporting")
