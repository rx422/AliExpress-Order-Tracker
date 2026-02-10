"""
AliExpress Order Tracker - HTML Generator

Extracts orders from a saved AliExpress orders page and generates
a standalone HTML file with sorting, filtering, and state persistence.
"""

import re
import os
import json
import base64
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
ACTIVE_DIR = BASE_DIR / 'active'
ARCHIVE_DIR = BASE_DIR / 'archive'

# Output settings
OUTPUT_FILENAME = 'AliExpress_Orders.html'

# Exchange rate cache
EXCHANGE_RATE_CACHE = BASE_DIR / 'exchange_rate_cache.json'
DEFAULT_EXCHANGE_RATE = 0.92


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Order:
    """Represents an AliExpress order."""
    order_number: str
    status: str
    delivery_info: str
    delivery_date: str
    description: str
    is_delayed: bool
    price: float
    local_image: str
    is_archived: bool = False


# =============================================================================
# Exchange Rate
# =============================================================================

def get_usd_to_eur_rate() -> float:
    """Fetch current USD to EUR exchange rate with caching."""
    try:
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            rate = data['rates']['EUR']
            
            # Cache the rate
            with open(EXCHANGE_RATE_CACHE, 'w') as f:
                json.dump({'rate': rate}, f)
            
            print(f"USD to EUR rate: {rate} (live)")
            return rate
    except Exception as e:
        print(f"Could not fetch exchange rate: {e}")
        
        # Try cached rate
        try:
            with open(EXCHANGE_RATE_CACHE, 'r') as f:
                cached = json.load(f)
                rate = cached['rate']
                print(f"USD to EUR rate: {rate} (cached)")
                return rate
        except:
            print(f"USD to EUR rate: {DEFAULT_EXCHANGE_RATE} (default)")
            return DEFAULT_EXCHANGE_RATE


# =============================================================================
# Source File Discovery
# =============================================================================

def find_source_files(directory: Path):
    """Find the HTML file and corresponding _files folder in a directory."""
    if not directory.exists():
        return None, None
    html_files = list(directory.glob('*.html'))
    if not html_files:
        return None, None
    html_file = html_files[0]
    # Browser saves companion folder as <name>_files
    files_folder = directory / (html_file.stem + '_files')
    if not files_folder.exists():
        # Fallback: find any _files folder
        files_folders = [d for d in directory.iterdir() if d.is_dir() and d.name.endswith('_files')]
        files_folder = files_folders[0] if files_folders else None
    return html_file, files_folder


# =============================================================================
# Order Parsing
# =============================================================================

def parse_price(price_str: str, usd_to_eur: float) -> float:
    """Parse price string and convert to EUR if needed."""
    is_usd = '$' in price_str
    price_num = re.sub(r'[$€\s]', '', price_str).replace(',', '.')
    try:
        price = float(price_num)
        if is_usd:
            price = round(price * usd_to_eur, 2)
        return price
    except:
        return 0.0


def parse_delivery_date(delivery_info: str) -> str:
    """Extract delivery date from delivery info string."""
    date_match = re.search(
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)',
        delivery_info, re.IGNORECASE
    )
    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2).capitalize()
        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = months.get(month_name, 1)
        year = 2026 if month >= 1 else 2025
        return f'{year}-{month:02d}-{day:02d}'
    return ''


def parse_orders(html_content: str, usd_to_eur: float, is_archived: bool = False) -> List[Order]:
    """Parse orders from AliExpress HTML content."""
    order_blocks = re.split(r'RedOrderList_OrderList__item__a2315', html_content)
    orders = []
    
    for block in order_blocks[1:]:
        # Order number
        order_match = re.search(
            r'RedOrderList_OrderItem__number__1tjf5">(\d{2,4}\s\d{4}\s\d{4}\s\d{4})</div>',
            block
        )
        if not order_match:
            continue
        order_number = order_match.group(1).strip()
        
        # Status
        status_match = re.search(r'RedOrderList_OrderItem__tag__1tjf5[^"]*">([^<]+)</div>', block)
        status = status_match.group(1).strip() if status_match else "Unknown"
        
        # Delivery info
        delivery_match = re.search(r'RedOrderList_OrderItem__title__1tjf5">([^<]+)</h4>', block)
        delivery_info = delivery_match.group(1).strip() if delivery_match else "N/A"
        
        # Description
        desc_match = re.search(r'RedOrderList_OrderItem__description__1tjf5[^"]*">([^<]+)</div>', block)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Check if delayed
        is_delayed = 'descriptionDangerous' in block and bool(description)
        
        # Price
        price_match = re.search(r'totalPrice__1tjf5">([^<]+)</div>', block)
        price = parse_price(price_match.group(1), usd_to_eur) if price_match else 0.0
        
        # Image
        image_match = re.search(r'src="[^"]*_files/([^"]+\.jpg)"', block)
        local_image = image_match.group(1) if image_match else ""
        
        # Delivery date
        delivery_date = parse_delivery_date(delivery_info)
        
        orders.append(Order(
            order_number=order_number,
            status=status,
            delivery_info=delivery_info,
            delivery_date=delivery_date,
            description=description,
            is_delayed=is_delayed,
            price=price,
            local_image=local_image,
            is_archived=is_archived,
        ))
    
    return orders


# =============================================================================
# Image Processing
# =============================================================================

def get_image_base64(image_filename: str, images_folder: Path) -> Optional[str]:
    """Load image and convert to base64 data URL."""
    if not image_filename:
        return None
    
    image_path = images_folder / image_filename
    try:
        with open(image_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
            return f'data:image/jpeg;base64,{img_data}'
    except:
        return None


def create_image_html(image_filename: str, images_folder: Path) -> str:
    """Create HTML for order image."""
    base64_src = get_image_base64(image_filename, images_folder)
    if base64_src:
        return f'<img src="{base64_src}" alt="Product" class="product-image">'
    return '<div class="product-image" style="background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#ccc;font-size:12px;">No image</div>'


# =============================================================================
# Template Rendering
# =============================================================================

def load_template(name: str) -> str:
    """Load template from templates directory."""
    template_path = TEMPLATES_DIR / name
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template: str, **kwargs) -> str:
    """Simple template rendering with {{variable}} syntax."""
    result = template
    for key, value in kwargs.items():
        result = result.replace('{{' + key + '}}', str(value))
    return result


def get_status_class(status: str) -> str:
    """Determine CSS class for order status."""
    status_upper = status.upper()
    if 'READY' in status_upper or 'PICKUP' in status_upper:
        return 'status-ready'
    elif 'TRANSIT' in status_upper:
        return 'status-transit'
    return 'status-unknown'


def render_order_card(order: Order, images_folder: Optional[Path]) -> str:
    """Render a single order card."""
    template = load_template('order_card.html')

    order_id = order.order_number.replace(' ', '')
    order_url = f"https://aliexpress.ru/order-list/{order_id}"

    return render_template(
        template,
        price=order.price,
        order_number=order.order_number,
        delivery_date=order.delivery_date,
        order_url=order_url,
        img_html=create_image_html(order.local_image, images_folder) if images_folder else '',
        status_class='status-ready' if order.is_archived else get_status_class(order.status),
        status='Received' if order.is_archived else order.status,
        delivery_info=order.delivery_info,
        desc_class='delivery-desc delayed' if order.is_delayed else 'delivery-desc',
        description=order.description,
        price_formatted=f'{order.price:.2f}',
        card_extra_class=' archived' if order.is_archived else '',
        checkbox_attrs=' checked disabled' if order.is_archived else '',
    )


def generate_html(orders: List[Order], images_map: dict) -> str:
    """Generate complete HTML document."""
    # Load templates
    base_template = load_template('base.html')
    styles = load_template('styles.css')
    script = load_template('script.js')

    # Render order cards
    order_cards = '\n'.join(
        render_order_card(order, images_map.get(order.order_number))
        for order in orders
    )
    
    # Calculate totals
    total_price = sum(o.price for o in orders)
    total_formatted = f'{total_price:.2f}'.replace('.', ',')
    
    # Render final HTML
    return render_template(
        base_template,
        styles=styles,
        script=script,
        order_count=len(orders),
        total_price=total_formatted,
        order_cards=order_cards
    )


# =============================================================================
# Main
# =============================================================================

def load_orders_from_dir(directory: Path, usd_to_eur: float, is_archived: bool = False):
    """Load and parse orders from a directory containing a saved AliExpress HTML."""
    html_file, images_folder = find_source_files(directory)
    if not html_file:
        label = 'archive' if is_archived else 'active'
        print(f"No HTML file found in {label}/ folder, skipping.")
        return [], None

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    orders = parse_orders(html_content, usd_to_eur, is_archived=is_archived)
    label = 'archive' if is_archived else 'active'
    print(f"Found {len(orders)} orders in {label}/ ({html_file.name})")
    return orders, images_folder


def main():
    """Main entry point."""
    # Get exchange rate
    usd_to_eur = get_usd_to_eur_rate()

    # Load orders from active and archive folders
    active_orders, active_images = load_orders_from_dir(ACTIVE_DIR, usd_to_eur)
    archive_orders, archive_images = load_orders_from_dir(ARCHIVE_DIR, usd_to_eur, is_archived=True)

    all_orders = active_orders + archive_orders
    if not all_orders:
        print("No orders found in active/ or archive/ folders.")
        return

    # Build images lookup: map each order to its images folder
    images_map = {}
    for order in active_orders:
        images_map[order.order_number] = active_images
    for order in archive_orders:
        images_map[order.order_number] = archive_images

    # Generate HTML
    output_html = generate_html(all_orders, images_map)

    # Save output
    output_path = BASE_DIR / OUTPUT_FILENAME
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)

    # Summary
    total_price = sum(o.price for o in all_orders)
    active_count = len(active_orders)
    archive_count = len(archive_orders)
    print(f"\nHTML file saved to: {output_path}")
    print(f"{len(all_orders)} orders total ({active_count} active, {archive_count} archived), total: €{total_price:.2f}")


if __name__ == '__main__':
    main()
