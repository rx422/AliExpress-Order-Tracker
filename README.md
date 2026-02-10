# AliExpress Order Tracker

A simple tool to extract and track your AliExpress orders from saved HTML pages, supporting both active and archived orders.

## Features

- Extract orders from saved AliExpress order list pages
- Support for **active** and **archive** folders (orders merged into one view)
- Archived orders shown as "Received" with disabled checkbox
- Mark orders as received with persistent checkboxes
- Delete orders you don't want to track
- Sort orders by price, date, or received status (toggle asc/desc)
- Filter: Show All / Hide Received / Received Only
- Auto-convert USD to EUR with live exchange rate
- Direct links to AliExpress order pages
- Persistent state via browser localStorage

## How to Use

### Step 1: Save Your AliExpress Order List

1. Go to your AliExpress order list page
2. Scroll down to load all orders you want to track
3. Press `Ctrl+S` to save the page as "Complete webpage"
4. Save it to the `active/` folder for current orders, or `archive/` folder for past orders

### Step 2: Run the Script

```powershell
.\.venv\Scripts\python.exe generate_html.py
```

The script auto-detects the HTML file and `_files` folder in each directory.

### Step 3: Open the Result

Open `AliExpress_Orders.html` in your browser.

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `active/` | Current orders (checkbox interactive) |
| `archive/` | Past orders (checkbox checked + disabled, status shown as "Received") |

Both folders should contain the saved `.html` file and the corresponding `_files/` folder created by the browser.

## Interface Guide

### Sort Controls
| Button | Action |
|--------|--------|
| **Default** | Original order from AliExpress |
| **Price** | Click once: low to high, click again: high to low |
| **Date** | Click once: soonest first, click again: latest first |
| **Received** | Click once: checked first, click again: unchecked first |
| **Show All / Hide Received / Received Only** | Cycles through 3 filter states |

### Order Cards
- **Click anywhere** (except checkbox/trash) opens order on AliExpress
- **Checkbox** marks order as received (saved automatically)
- **Trash icon** deletes order from list (with confirmation)

## Updating Orders

1. Save the new HTML file to the appropriate folder (`active/` or `archive/`)
2. Run the script again

Your checkbox states, deletions, and filter preferences are preserved in browser localStorage.

## Configuration

### USD to EUR Conversion Rate

The exchange rate is fetched automatically from `exchangerate-api.com`.

- **Live rate**: Fetched on each script run (requires internet)
- **Cached rate**: Saved to `exchange_rate_cache.json` for offline use
- **Default fallback**: Uses 0.92 if both API and cache fail

## Requirements

- Python 3.x
- No external packages required (uses only standard library)

## Project Structure

```
├── generate_html.py          # Main generator script
├── requirements.txt          # Python dependencies (stdlib only)
├── templates/
│   ├── base.html             # Main HTML template
│   ├── order_card.html       # Order card component
│   ├── styles.css            # CSS styles
│   └── script.js             # JavaScript functionality
├── active/                   # Current orders (saved HTML + _files/)
├── archive/                  # Past orders (saved HTML + _files/)
├── exchange_rate_cache.json  # Cached exchange rate
└── AliExpress_Orders.html    # Generated output (not tracked in git)
```
