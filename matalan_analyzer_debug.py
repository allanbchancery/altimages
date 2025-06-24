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
    
    # Wait for the dynamic content to load. This is crucial.
    # We'll wait a bit longer to ensure carousels and reviews appear.
    print("Waiting for page to load dynamic content...")
    time.sleep(10)

    # Debug: Check page title and basic info
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    
    # Debug: Save page source to see what we're working with
    page_source = driver.page_source
    print(f"Page source length: {len(page_source)} characters")
    
    # Check if we can find any images at all
    all_images = driver.find_elements(By.TAG_NAME, 'img')
    print(f"Total images found on page: {len(all_images)}")
    
    # --- PART 1: EXTRACT ALT TAGS (with broader search) ---
    print("Extracting image alt tags...")
    images_data = []
    
    # Try multiple selectors
    selectors_to_try = [
        'img[data-testid="pdp-gallery-image"]',
        '.carousel__item img',
        'img',  # All images as fallback
    ]
    
    for selector in selectors_to_try:
        images = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"Found {len(images)} images with selector: {selector}")
        if images:
            break
    
    # Take first 10 images to avoid overwhelming output
    for i, img in enumerate(images[:10]):
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
            'image_src': src[:100] + '...' if src and len(src) > 100 else src,  # Truncate long URLs
            'alt_text': alt_text,
            'status': status
        })

    # --- PART 2: EXTRACT WIDGETS (with debugging) ---
    print("Extracting widget data...")
    widgets_data = {}

    # Widget 1: The Purchase Widget (try multiple selectors)
    purchase_selectors = [
        '[data-e2e="pdp-add-to-bag-container"]',
        '[data-testid*="add-to-bag"]',
        '.add-to-bag',
        '.purchase-widget',
        'button[data-testid*="add"]'
    ]
    
    purchase_found = False
    for selector in purchase_selectors:
        try:
            purchase_widget = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"Found purchase widget with selector: {selector}")
            purchase_found = True
            break
        except NoSuchElementException:
            continue
    
    if purchase_found:
        try:
            # Try to find price and title with multiple selectors
            price_selectors = ['.price__value', '.price', '[data-testid*="price"]', '.product-price']
            title_selectors = ['h1', '.product-title', '[data-testid*="title"]']
            
            price = "Not found"
            for p_sel in price_selectors:
                try:
                    price = purchase_widget.find_element(By.CSS_SELECTOR, p_sel).text
                    break
                except NoSuchElementException:
                    continue
            
            title = "Not found"
            for t_sel in title_selectors:
                try:
                    title = purchase_widget.find_element(By.CSS_SELECTOR, t_sel).text
                    break
                except NoSuchElementException:
                    continue
            
            widgets_data['purchase_widget'] = {
                'Product Name': title,
                'Price': price,
                'Widget Found': 'Yes'
            }
        except Exception as e:
            widgets_data['purchase_widget'] = {'Error': f'Found widget but extraction failed: {str(e)}'}
    else:
        widgets_data['purchase_widget'] = {'Error': 'Could not find the purchase widget with any selector.'}

    # Widget 2: Product Information (try multiple selectors)
    info_selectors = [
        '[data-testid="pdp-accordion-group"]',
        '.accordion',
        '.product-info',
        '.product-details'
    ]
    
    info_found = False
    for selector in info_selectors:
        try:
            info_widget = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"Found info widget with selector: {selector}")
            info_found = True
            break
        except NoSuchElementException:
            continue
    
    if info_found:
        widgets_data['product_info_widget'] = {'Status': 'Found but content extraction simplified for debugging'}
    else:
        widgets_data['product_info_widget'] = {'Error': 'Could not find the product info widget with any selector.'}

    # Widget 3: Check for any recommendation sections
    rec_selectors = [
        "//*[contains(text(), 'You may also like')]/ancestor::section",
        "//*[contains(text(), 'recommended')]/ancestor::section",
        ".recommendations",
        ".related-products"
    ]
    
    rec_found = False
    for selector in rec_selectors:
        try:
            if selector.startswith("//"):
                recs_widget = driver.find_element(By.XPATH, selector)
            else:
                recs_widget = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"Found recommendations widget with selector: {selector}")
            rec_found = True
            break
        except NoSuchElementException:
            continue
    
    if rec_found:
        widgets_data['recommendations_widget'] = {'Status': 'Found but content extraction simplified for debugging'}
    else:
        widgets_data['recommendations_widget'] = {'Error': 'Could not find the recommendations widget with any selector.'}

    # Debug: Check what elements we can find
    print("\nDebugging - Looking for common elements:")
    common_elements = ['h1', 'h2', 'button', '.price', '.product']
    for element in common_elements:
        try:
            found = driver.find_elements(By.CSS_SELECTOR, element)
            print(f"  {element}: {len(found)} found")
        except:
            print(f"  {element}: Error searching")

    driver.quit()
    print("Extraction complete.")
    return images_data, widgets_data

# --- RUN THE ANALYSIS ---
target_url = "https://www.matalan.co.uk/clothing/brown-leaf-print-tunic-midaxi-dress/15824638.html"
images, widgets = analyze_matalan_product_page(target_url)

# --- DISPLAY THE RESULTS ---
print("\n" + "="*50)
print("             EXTRACTION RESULTS FOR MATALAN PAGE")
print("="*50 + "\n")

print("\n--- 🖼️ Image Alt Tag Accessibility Report ---")
if images:
    df_images = pd.DataFrame(images)
    print(df_images.to_string())
else:
    print("No images found with the specified selectors.")

print("\n\n--- 🧩 Widget Data Report ---")
if widgets:
    for widget_name, data in widgets.items():
        print(f"\n--- Widget: {widget_name} ---")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                print(f"  Item {i}: {item}")
else:
    print("No widget data was extracted.")
