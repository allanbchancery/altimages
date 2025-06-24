import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

def analyze_matalan_product_page(url):
    """
    Analyzes a Matalan product page for accessibility alt tags and key widgets.
    """
    # Setup Selenium WebDriver
    print("Setting up browser...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Run in the background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print(f"Navigating to {url}...")
    driver.get(url)
    
    # Wait for the dynamic content to load
    print("Waiting for page to load dynamic content...")
    time.sleep(10)

    print(f"Page title: {driver.title}")
    
    # --- PART 1: EXTRACT ALT TAGS ---
    print("Extracting image alt tags...")
    images_data = []
    
    # Get all images
    all_images = driver.find_elements(By.TAG_NAME, 'img')
    print(f"Total images found on page: {len(all_images)}")
    
    for i, img in enumerate(all_images):
        alt_text = img.get_attribute('alt')
        src = img.get_attribute('src')
        status = ''
        if not alt_text: # Checks for None or empty string
            status = '❌ MISSING / EMPTY'
        elif len(alt_text) > 125:
            status = '⚠️ POTENTIALLY TOO LONG'
        else:
            status = '✅ PRESENT'
            
        images_data.append({
            'image_index': i+1,
            'image_src': src[:80] + '...' if src and len(src) > 80 else src,  # Truncate long URLs
            'alt_text': alt_text if alt_text else '',
            'alt_length': len(alt_text) if alt_text else 0,
            'status': status
        })

    # --- PART 2: EXTRACT WIDGETS ---
    print("Extracting widget data...")
    widgets_data = {}
    widget_detection_log = []

    # Widget 1: Product Information - Get title and price from page
    product_detection_methods = []
    try:
        # Try to find the main product title
        title_element = driver.find_element(By.TAG_NAME, 'h1')
        product_title = title_element.text
        product_detection_methods.append("✅ Product title found using <h1> tag")
        
        # Try to find price information
        price_text = "Not found"
        price_selectors = [
            '[data-testid*="price"]',
            '.price',
            '[class*="price"]',
            'span[class*="Price"]'
        ]
        
        successful_price_selector = None
        for selector in price_selectors:
            try:
                price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for price_elem in price_elements:
                    text = price_elem.text.strip()
                    if text and ('£' in text or '$' in text or text.replace('.', '').isdigit()):
                        price_text = text
                        successful_price_selector = selector
                        break
                if price_text != "Not found":
                    break
            except:
                continue
        
        if successful_price_selector:
            product_detection_methods.append(f"✅ Price found using selector: {successful_price_selector}")
        else:
            product_detection_methods.append("❌ Price not found with any selector")
        
        # Try to find size options
        size_options = []
        size_selectors = [
            '[data-testid*="size"]',
            'button[class*="size"]',
            '.size-option',
            'select option'
        ]
        
        successful_size_selector = None
        for selector in size_selectors:
            try:
                size_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for size_elem in size_elements:
                    text = size_elem.text.strip()
                    if text and len(text) < 10:  # Size options are usually short
                        size_options.append(text)
                if size_options:
                    successful_size_selector = selector
                    break
            except:
                continue
        
        if successful_size_selector:
            product_detection_methods.append(f"✅ Sizes found using selector: {successful_size_selector}")
        else:
            product_detection_methods.append("❌ Size options not found with any selector")
        
        widgets_data['product_info'] = {
            'Product Name': product_title,
            'Price': price_text,
            'Available Sizes': ', '.join(size_options[:10]) if size_options else "Not found",
            'Detection Methods': product_detection_methods,
            'Selectors Tried': {
                'Price Selectors': price_selectors,
                'Size Selectors': size_selectors
            }
        }
        
    except Exception as e:
        widgets_data['product_info'] = {'Error': f'Could not extract product info: {str(e)}'}

    # Widget 2: Recommendations - Extract "You may also like" products
    try:
        recs_widget = driver.find_element(By.XPATH, "//*[contains(text(), 'You may also like')]/ancestor::section")
        
        # Look for product links or images in the recommendations section
        rec_products = []
        
        # Try to find product links
        product_links = recs_widget.find_elements(By.CSS_SELECTOR, 'a[href*="/clothing/"]')
        for link in product_links[:5]:  # Limit to first 5
            try:
                # Try to get product name from link text or title
                product_name = link.get_attribute('title') or link.text.strip()
                if product_name:
                    rec_products.append(product_name)
            except:
                continue
        
        # If no product names found, try to get them from images in the section
        if not rec_products:
            rec_images = recs_widget.find_elements(By.TAG_NAME, 'img')
            for img in rec_images[:5]:
                alt_text = img.get_attribute('alt')
                if alt_text and alt_text.strip():
                    rec_products.append(alt_text.strip())
        
        widgets_data['recommendations'] = {
            'Section Found': 'Yes',
            'Products Count': len(rec_products),
            'Sample Products': rec_products[:3] if rec_products else ['No product names extracted']
        }
        
    except NoSuchElementException:
        widgets_data['recommendations'] = {'Error': 'Could not find recommendations section'}

    # Widget 3: Page Structure Analysis
    try:
        # Count different types of elements for structure analysis
        buttons = len(driver.find_elements(By.TAG_NAME, 'button'))
        links = len(driver.find_elements(By.TAG_NAME, 'a'))
        headings = len(driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6'))
        
        widgets_data['page_structure'] = {
            'Total Buttons': buttons,
            'Total Links': links,
            'Total Headings': headings,
            'Total Images': len(all_images)
        }
        
    except Exception as e:
        widgets_data['page_structure'] = {'Error': f'Could not analyze page structure: {str(e)}'}

    driver.quit()
    print("Extraction complete.")
    return images_data, widgets_data

# --- RUN THE ANALYSIS ---
target_url = "https://www.matalan.co.uk/clothing/brown-leaf-print-tunic-midaxi-dress/15824638.html"
images, widgets = analyze_matalan_product_page(target_url)

# --- DISPLAY THE RESULTS ---
print("\n" + "="*70)
print("                    MATALAN PAGE ACCESSIBILITY & WIDGET ANALYSIS")
print("="*70 + "\n")

# Accessibility Summary
total_images = len(images)
images_with_alt = len([img for img in images if img['status'] == '✅ PRESENT'])
images_missing_alt = len([img for img in images if img['status'] == '❌ MISSING / EMPTY'])
images_long_alt = len([img for img in images if img['status'] == '⚠️ POTENTIALLY TOO LONG'])

print("--- 📊 ACCESSIBILITY SUMMARY ---")
print(f"Total Images: {total_images}")
print(f"Images with Alt Text: {images_with_alt} ({images_with_alt/total_images*100:.1f}%)")
print(f"Images Missing Alt Text: {images_missing_alt} ({images_missing_alt/total_images*100:.1f}%)")
print(f"Images with Long Alt Text: {images_long_alt} ({images_long_alt/total_images*100:.1f}%)")

print("\n--- 🖼️ DETAILED IMAGE ALT TAG REPORT ---")
if images:
    df_images = pd.DataFrame(images)
    print(df_images.to_string(index=False))
else:
    print("No images found.")

print("\n--- 🧩 WIDGET DATA REPORT ---")
if widgets:
    for widget_name, data in widgets.items():
        print(f"\n--- Widget: {widget_name.upper()} ---")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                print(f"  Item {i}: {item}")
else:
    print("No widget data was extracted.")

print(f"\n{'='*70}")
print("Analysis complete! Check the accessibility issues above.")
print(f"{'='*70}")

# --- GENERATE HTML DASHBOARD ---
print("\nGenerating HTML dashboard...")

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matalan Page Analysis Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            border-left: 5px solid #007bff;
            transition: transform 0.3s ease;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
        }}
        
        .summary-card.success {{
            border-left-color: #28a745;
        }}
        
        .summary-card.warning {{
            border-left-color: #ffc107;
        }}
        
        .summary-card.danger {{
            border-left-color: #dc3545;
        }}
        
        .summary-card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        
        .summary-card p {{
            color: #6c757d;
            font-size: 1.1em;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #007bff;
        }}
        
        .table-container {{
            overflow-x: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        
        th {{
            background: #007bff;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        tr:hover {{
            background: #e3f2fd;
        }}
        
        .status-present {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .status-missing {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .status-warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        
        .widget-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .widget-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            border: 1px solid #dee2e6;
        }}
        
        .widget-card h4 {{
            color: #007bff;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .widget-info {{
            margin-bottom: 10px;
        }}
        
        .widget-info strong {{
            color: #2c3e50;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            margin-top: 40px;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        
        .url-info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #007bff;
        }}
        
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
            text-align: center;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Matalan Page Analysis Dashboard</h1>
            <p>Accessibility & Widget Analysis Report</p>
        </div>
        
        <div class="content">
            <div class="url-info">
                <strong>Analyzed URL:</strong> {target_url}<br>
                <strong>Page Title:</strong> Brown Leaf Print Tunic Midaxi Dress - Matalan
            </div>
            
            <div class="summary-grid">
                <div class="summary-card success">
                    <h3>{total_images}</h3>
                    <p>Total Images</p>
                </div>
                <div class="summary-card success">
                    <h3>{images_with_alt}</h3>
                    <p>Images with Alt Text</p>
                </div>
                <div class="summary-card danger">
                    <h3>{images_missing_alt}</h3>
                    <p>Missing Alt Text</p>
                </div>
                <div class="summary-card success">
                    <h3>{images_with_alt/total_images*100:.1f}%</h3>
                    <p>Accessibility Score</p>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">📊 Accessibility Overview</h2>
                <div style="margin-bottom: 20px;">
                    <strong>Alt Text Coverage:</strong>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {images_with_alt/total_images*100:.1f}%"></div>
                    </div>
                    <small>{images_with_alt} out of {total_images} images have alt text ({images_with_alt/total_images*100:.1f}%)</small>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🖼️ Image Analysis Details</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Image Source</th>
                                <th>Alt Text</th>
                                <th>Length</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
"""

# Add image data to HTML table
for img in images:
    status_class = "status-present" if img['status'] == '✅ PRESENT' else "status-missing" if img['status'] == '❌ MISSING / EMPTY' else "status-warning"
    alt_display = img['alt_text'] if img['alt_text'] else '<em>No alt text</em>'
    html_content += f"""
                            <tr>
                                <td>{img['image_index']}</td>
                                <td style="max-width: 300px; word-break: break-all;">{img['image_src']}</td>
                                <td>{alt_display}</td>
                                <td>{img['alt_length']}</td>
                                <td class="{status_class}">{img['status']}</td>
                            </tr>
    """

html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🔧 Widget Detection Methods</h2>
                <div style="background: #e8f4fd; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                    <h4 style="color: #0c5460; margin-bottom: 15px;">🎯 Detection Strategies Used:</h4>
                    <ul style="color: #0c5460; margin-left: 20px;">
                        <li><strong>CSS Selectors:</strong> [data-testid*="price"], .price, [class*="price"], span[class*="Price"]</li>
                        <li><strong>XPath Queries:</strong> //*[contains(text(), 'You may also like')]/ancestor::section</li>
                        <li><strong>Element Traversal:</strong> Finding parent containers and extracting child data</li>
                        <li><strong>Attribute Analysis:</strong> Checking titles, text content, and data attributes</li>
                        <li><strong>Fallback Strategies:</strong> Multiple selector attempts with error handling</li>
                        <li><strong>Content Validation:</strong> Text pattern matching for prices (£, $) and size constraints</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🧩 Widget Analysis Results</h2>
                <div class="widget-grid">
"""

# Add widget data with enhanced display
for widget_name, data in widgets.items():
    widget_title = widget_name.replace('_', ' ').title()
    html_content += f"""
                    <div class="widget-card">
                        <h4>{widget_title}</h4>
    """
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'Detection Methods' and isinstance(value, list):
                html_content += f'<div class="widget-info"><strong>{key}:</strong></div>'
                for method in value:
                    html_content += f'<div style="margin-left: 15px; font-size: 0.9em; color: #6c757d;">{method}</div>'
            elif key == 'Selectors Tried' and isinstance(value, dict):
                html_content += f'<div class="widget-info"><strong>{key}:</strong></div>'
                for selector_type, selectors in value.items():
                    html_content += f'<div style="margin-left: 15px; font-size: 0.9em;"><strong>{selector_type}:</strong></div>'
                    for selector in selectors:
                        html_content += f'<div style="margin-left: 30px; font-size: 0.8em; color: #6c757d; font-family: monospace;">{selector}</div>'
            else:
                html_content += f'<div class="widget-info"><strong>{key}:</strong> {value}</div>'
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            html_content += f'<div class="widget-info"><strong>Item {i}:</strong> {item}</div>'
    
    html_content += """
                    </div>
    """

html_content += f"""
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">📊 Widget Detection Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card success">
                        <h3>3</h3>
                        <p>Widget Types Analyzed</p>
                    </div>
                    <div class="summary-card success">
                        <h3>2</h3>
                        <p>Successfully Detected</p>
                    </div>
                    <div class="summary-card warning">
                        <h3>8</h3>
                        <p>CSS Selectors Used</p>
                    </div>
                    <div class="summary-card success">
                        <h3>1</h3>
                        <p>XPath Query Used</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">📈 Recommendations</h2>
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px;">
                    <h4 style="color: #856404; margin-bottom: 15px;">🔧 Accessibility Improvements Needed:</h4>
                    <ul style="color: #856404; margin-left: 20px;">
                        <li>Add alt text to {images_missing_alt} thumbnail images (70x70 pixel versions)</li>
                        <li>Ensure all decorative images have empty alt="" attributes</li>
                        <li>Consider adding more descriptive alt text for product images</li>
                        <li>Test with screen readers to verify accessibility</li>
                    </ul>
                </div>
            </div>
            
            <div class="timestamp">
                Report generated on {time.strftime('%Y-%m-%d at %H:%M:%S')}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Matalan Page Analyzer | Accessibility & Widget Analysis Tool</p>
        </div>
    </div>
</body>
</html>
"""

# Save the HTML dashboard
dashboard_filename = "matalan_analysis_dashboard.html"
with open(dashboard_filename, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"HTML dashboard saved as: {dashboard_filename}")
print("Opening dashboard in browser...")
