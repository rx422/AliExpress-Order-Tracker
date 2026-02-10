const container = document.getElementById('orders-container');

// Get deleted orders from localStorage
function getDeletedOrders() {
    try {
        return JSON.parse(localStorage.getItem('deleted_orders') || '[]');
    } catch {
        return [];
    }
}

// Save deleted orders to localStorage
function saveDeletedOrders(deleted) {
    localStorage.setItem('deleted_orders', JSON.stringify(deleted));
}

// Hide deleted orders on load
const deletedOrders = getDeletedOrders();
document.querySelectorAll('.order-card').forEach(card => {
    if (deletedOrders.includes(card.dataset.order)) {
        card.remove();
    }
});

// Store original order for default sort (after removing deleted)
const originalOrder = Array.from(container.children);

// Load saved checkbox states (skip archived/disabled checkboxes)
document.querySelectorAll('input[type="checkbox"][data-order]').forEach(cb => {
    if (cb.disabled) return;
    const key = 'order_' + cb.dataset.order;
    cb.checked = localStorage.getItem(key) === 'true';

    // Save state on change
    cb.addEventListener('change', () => {
        localStorage.setItem(key, cb.checked);
    });
});

// Delete button handlers
document.querySelectorAll('.trash-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const orderNum = btn.dataset.order;
        if (confirm('Delete this order from the list?')) {
            const deleted = getDeletedOrders();
            if (!deleted.includes(orderNum)) {
                deleted.push(orderNum);
                saveDeletedOrders(deleted);
            }
            btn.closest('.order-card').remove();
            updateCounts();
        }
    });
});

// Update order count and total
function updateCounts() {
    const cards = container.querySelectorAll('.order-card:not(.hidden)');
    const count = cards.length;
    let total = 0;
    cards.forEach(card => {
        total += parseFloat(card.dataset.price) || 0;
    });
    const totalStr = total.toFixed(2).replace('.', ',');
    document.querySelectorAll('.summary-text, .footer-text').forEach(el => {
        el.textContent = count + ' orders';
    });
    document.querySelectorAll('.summary-total, .footer-total').forEach(el => {
        el.textContent = 'Total: € ' + totalStr;
    });
}

// Sorting function
let currentSort = { field: null, asc: true };

function toggleSort(field) {
    const btn = document.querySelector(`[data-sort="${field}"]`);
    const cards = Array.from(container.querySelectorAll('.order-card'));
    
    // Toggle direction if same field, otherwise reset to asc
    if (currentSort.field === field) {
        currentSort.asc = !currentSort.asc;
    } else {
        currentSort.field = field;
        currentSort.asc = true;
    }
    
    // Update button states and arrows
    document.querySelectorAll('.sort-btn').forEach(b => {
        b.classList.remove('active');
        const baseText = b.dataset.sort === 'default' ? 'Default' : 
                         b.dataset.sort === 'price' ? 'Price' :
                         b.dataset.sort === 'date' ? 'Date' : 'Received';
        b.textContent = baseText;
    });
    
    if (field !== 'default') {
        btn.classList.add('active');
        const baseText = field === 'price' ? 'Price' : field === 'date' ? 'Date' : 'Received';
        btn.textContent = baseText + (currentSort.asc ? ' ↑' : ' ↓');
    } else {
        btn.classList.add('active');
    }
    
    let sorted;
    switch(field) {
        case 'price':
            sorted = cards.sort((a, b) => {
                const diff = parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                return currentSort.asc ? diff : -diff;
            });
            break;
        case 'date':
            sorted = cards.sort((a, b) => {
                const dateA = a.dataset.date || '9999-12-31';
                const dateB = b.dataset.date || '9999-12-31';
                const diff = dateA.localeCompare(dateB);
                return currentSort.asc ? diff : -diff;
            });
            break;
        case 'checked':
            sorted = cards.sort((a, b) => {
                const aChecked = a.querySelector('input[type="checkbox"]').checked ? 0 : 1;
                const bChecked = b.querySelector('input[type="checkbox"]').checked ? 0 : 1;
                const diff = aChecked - bChecked;
                return currentSort.asc ? diff : -diff;
            });
            break;
        default:
            currentSort.field = null;
            sorted = originalOrder.filter(card => container.contains(card));
    }
    
    sorted.forEach(card => container.appendChild(card));
}

// Update counts on load (after removing deleted)
updateCounts();

// Filter state: 0 = show all, 1 = hide received, 2 = received only
let filterState = parseInt(localStorage.getItem('filter_state') || '0');

function updateHideState() {
    const btn = document.getElementById('hideCheckedBtn');
    
    // Update button text and style based on state
    const states = ['Show All', 'Hide Received', 'Received Only'];
    btn.textContent = states[filterState];
    btn.classList.toggle('active', filterState !== 0);
    
    document.querySelectorAll('.order-card').forEach(card => {
        const cb = card.querySelector('input[type="checkbox"]');
        const isChecked = cb && cb.checked;
        
        if (filterState === 0) {
            // Show all
            card.classList.remove('hidden');
        } else if (filterState === 1) {
            // Hide received (show only unchecked)
            card.classList.toggle('hidden', isChecked);
        } else if (filterState === 2) {
            // Received only (show only checked)
            card.classList.toggle('hidden', !isChecked);
        }
    });
    updateCounts();
}

function toggleHideChecked() {
    filterState = (filterState + 1) % 3;
    localStorage.setItem('filter_state', filterState);
    updateHideState();
}

// Apply hide state on load
updateHideState();

// Update hide state when checkbox changes (skip archived/disabled)
document.querySelectorAll('input[type="checkbox"][data-order]').forEach(cb => {
    if (cb.disabled) return;
    cb.addEventListener('change', () => {
        if (filterState !== 0) {
            updateHideState();
        }
    });
});
