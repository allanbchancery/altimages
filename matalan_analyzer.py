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
    time.sleep(7)

    # --- PART 1: EXTRACT ALT TAGS ---
    print("Extracting image alt tags...")
    images_data = []
    # Note: These selectors are based on inspection of the page structure.
    # They might change if Matalan updates their site.
    all_images = driver.find_elements(By.CSS_SELECTOR, 'img[data-testid="pdp-gallery-image"], .carousel__item img')
    
    for img in all_images:
        alt_text = img.get_attribute('alt')
        status = ''
        if not alt_text: # Checks for None or empty string
            status = '❌ MISSING / EMPTY'
        elif len(alt_text) > 125:
            status = '⚠️ POTENTIALLY TOO LONG'
        else:
            status = '✅ PRESENT'
            
        images_data.append({
            'image_src': img.get_attribute('src'),
            'alt_text': alt_text,
            'status': status
        })

    # --- PART 2: EXTRACT WIDGETS ---
    print("Extracting widget data...")
    widgets_data = {}

    # Widget 1: The Purchase Widget
    try:
        purchase_widget = driver.find_element(By.CSS_SELECTOR, '[data-e2e="pdp-add-to-bag-container"]')
        price = purchase_widget.find_element(By.CSS_SELECTOR, '.price__value').text
        title = purchase_widget.find_element(By.CSS_SELECTOR, 'h1').text
        sizes_elements = purchase_widget.find_elements(By.CSS_SELECTOR, '[data-testid="size-button-label"]')
        available_sizes = [size.text for size in sizes_elements]
        
        widgets_data['purchase_widget'] = {
            'Product Name': title,
            'Price': price,
            'Available Sizes': ', '.join(available_sizes) if available_sizes else "No sizes found/listed"
        }
    except NoSuchElementException:
        widgets_data['purchase_widget'] = {'Error': 'Could not find the purchase widget.'}

    # Widget 2: Product Information Accordion
    try:
        info_widget = driver.find_element(By.CSS_SELECTOR, '[data-testid="pdp-accordion-group"]')
        headings = info_widget.find_elements(By.CSS_SELECTOR, '[data-testid="accordion-button"]')
        info_accordion = {heading.text: "Content available" for heading in headings} # simplified for clarity
        widgets_data['product_info_widget'] = info_accordion
    except NoSuchElementException:
        widgets_data['product_info_widget'] = {'Error': 'Could not find the product info accordion.'}

    # Widget 3: "You may also like" Recommendations
    try:
        recs_widget = driver.find_element(By.XPATH, "//*[contains(text(), 'You may also like')]/ancestor::section")
        products = recs_widget.find_elements(By.CSS_SELECTOR, '.product-image__container')
        recommended_products = []
        for product in products:
            try:
                name = product.find_element(By.CSS_SELECTOR, '.product-card__name').text
                price = product.find_element(By.CSS_SELECTOR, '.product-card__price').text
                recommended_products.append(f"{name} - {price}")
            except NoSuchElementException:
                continue # Skip if a product card is incomplete
        widgets_data['recommendations_widget'] = recommended_products
    except NoSuchElementException:
        widgets_data['recommendations_widget'] = {'Error': 'Could not find the recommendations widget.'}

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
