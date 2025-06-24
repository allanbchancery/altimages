import requests
import urllib3
from urllib.parse import urlparse
import time
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def quick_matalan_discovery():
    """Quick discovery of Matalan site structure"""
    print("🚀 Quick Matalan Site Discovery - Phase 1")
    print("=" * 50)
    
    base_url = "https://www.matalan.co.uk"
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; AccessibilityAnalyzer/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    
    # Test known working URLs and common patterns
    test_urls = [
        # Known working
        f"{base_url}/",
        f"{base_url}/clothing/brown-leaf-print-tunic-midaxi-dress/15824638.html",
        
        # Common category patterns
        f"{base_url}/womens",
        f"{base_url}/mens", 
        f"{base_url}/kids",
        f"{base_url}/home",
        f"{base_url}/sale",
        
        # Alternative patterns
        f"{base_url}/women",
        f"{base_url}/men",
        f"{base_url}/children",
        f"{base_url}/baby",
        
        # Static pages
        f"{base_url}/help",
        f"{base_url}/stores",
        f"{base_url}/size-guide"
    ]
    
    valid_urls = []
    
    print("🔍 Testing URL patterns...")
    for i, url in enumerate(test_urls):
        try:
            print(f"   {i+1}/{len(test_urls)}: Testing {url}")
            response = session.head(url, timeout=5, allow_redirects=True)
            
            if response.status_code in [200, 301, 302]:
                valid_urls.append({
                    'url': url,
                    'status': response.status_code,
                    'final_url': response.url
                })
                print(f"      ✅ Accessible (Status: {response.status_code})")
            else:
                print(f"      ❌ Not accessible (Status: {response.status_code})")
                
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:30]}...")
        
        time.sleep(1)  # Be respectful
    
    # Categorize found URLs
    categories = {
        'homepage': [],
        'product_pages': [],
        'category_pages': [],
        'static_pages': []
    }
    
    for url_data in valid_urls:
        url = url_data['url']
        path = urlparse(url).path
        
        if path == '/':
            categories['homepage'].append(url_data)
        elif '/clothing/' in path and path.endswith('.html'):
            categories['product_pages'].append(url_data)
        elif path in ['/womens', '/mens', '/kids', '/home', '/sale', '/women', '/men', '/children', '/baby']:
            categories['category_pages'].append(url_data)
        else:
            categories['static_pages'].append(url_data)
    
    # Generate report
    report = {
        'discovery_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'base_url': base_url,
        'method': 'Quick Pattern Testing',
        'total_tested': len(test_urls),
        'total_accessible': len(valid_urls),
        'success_rate': f"{len(valid_urls)/len(test_urls)*100:.1f}%",
        'categories': {k: len(v) for k, v in categories.items()},
        'accessible_urls': valid_urls,
        'categorized_urls': categories,
        'recommended_samples': {
            'high_priority': categories['homepage'] + categories['category_pages'][:3],
            'medium_priority': categories['product_pages'][:2],
            'low_priority': categories['static_pages'][:2]
        }
    }
    
    # Save report
    with open('matalan_quick_discovery.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Quick Discovery Complete!")
    print(f"📊 Tested: {report['total_tested']} URLs")
    print(f"✅ Accessible: {report['total_accessible']} URLs")
    print(f"📈 Success Rate: {report['success_rate']}")
    print(f"\n📂 Categories found:")
    for category, count in report['categories'].items():
        print(f"   {category}: {count}")
    
    total_samples = sum(len(urls) for urls in report['recommended_samples'].values())
    print(f"\n🎯 Recommended samples for analysis: {total_samples}")
    
    return report

if __name__ == "__main__":
    report = quick_matalan_discovery()
    
    print(f"\n💾 Report saved to: matalan_quick_discovery.json")
    print(f"🎯 Ready for Phase 2: Detailed Analysis")
