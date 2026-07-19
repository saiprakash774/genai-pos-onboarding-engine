let currentMenu = [];
let cart = [];
let currentCategory = null;
let selectedItem = null;
let selectedSize = null;
let selectedMods = new Set();

// Setup Clock
setInterval(() => {
    document.getElementById('clock').innerText = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}, 1000);

// File Upload Logic
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--primary)'; });
dropZone.addEventListener('dragleave', () => dropZone.style.borderColor = 'var(--border)');
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border)';
    if(e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
    if(e.target.files.length) handleFile(e.target.files[0]);
});

async function handleFile(file) {
    document.getElementById('drop-zone').classList.add('hidden');
    document.getElementById('pipeline-status').classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        await fetch('/api/upload', { method: 'POST', body: formData });
        pollPipeline();
    } catch (e) {
        alert("Upload failed.");
    }
}

// Launch Sample Button
document.getElementById('launch-sample-btn').addEventListener('click', () => {
    loadMenuAndLaunch();
});

async function pollPipeline() {
    const label = document.getElementById('currentStateLabel');
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            const status = data.pipeline.status;
            
            label.innerText = status.toUpperCase();
            
            if (status === 'synced' || status === 'sync_failed' || status === 'validated') {
                clearInterval(interval);
                label.innerText = "SUCCESS! Launching POS...";
                setTimeout(loadMenuAndLaunch, 1500);
            } else if (status.includes('fail') && status !== 'sync_failed' && status !== 'validation_failed') {
                clearInterval(interval);
                label.innerText = "PIPELINE FAILED";
            }
        } catch (e) { console.error(e); }
    }, 1000);
}

// POS UI Logic
async function loadMenuAndLaunch() {
    const res = await fetch('/api/menu');
    currentMenu = await res.json();
    
    document.getElementById('upload-view').classList.remove('active');
    document.getElementById('pos-view').classList.add('active');
    
    renderCategories();
}

function renderCategories() {
    const tabs = document.getElementById('category-tabs');
    const categories = [...new Set(currentMenu.map(m => m.Category).filter(Boolean))];
    
    tabs.innerHTML = '';
    categories.forEach((cat, idx) => {
        const btn = document.createElement('button');
        btn.className = `category-tab ${idx === 0 ? 'active' : ''}`;
        btn.innerText = cat;
        btn.onclick = () => {
            document.querySelectorAll('.category-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderItems(cat);
        };
        tabs.appendChild(btn);
    });
    
    if(categories.length > 0) renderItems(categories[0]);
}

function renderItems(category) {
    currentCategory = category;
    const grid = document.getElementById('menu-grid');
    grid.innerHTML = '';
    
    // Group by Base Drink
    const items = currentMenu.filter(m => m.Category === category);
    const baseDrinks = [...new Set(items.map(m => m.Base_Drink))];
    
    baseDrinks.forEach(drinkName => {
        const drinkVariations = items.filter(m => m.Base_Drink === drinkName);
        const basePrice = Math.min(...drinkVariations.map(m => m.Base_Price));
        
        const btn = document.createElement('div');
        btn.className = 'menu-item-btn';
        btn.innerHTML = `
            <div class="menu-item-name">${drinkName}</div>
            <div class="menu-item-price">From $${basePrice.toFixed(2)}</div>
        `;
        btn.onclick = () => openModifierModal(drinkName, drinkVariations);
        grid.appendChild(btn);
    });
}

// Modal Logic
function openModifierModal(drinkName, variations) {
    selectedItem = { name: drinkName, variations: variations };
    selectedSize = variations[0].Size;
    selectedMods.clear();
    
    document.getElementById('modal-title').innerText = drinkName;
    
    // Render Sizes
    const sizeContainer = document.getElementById('size-options');
    sizeContainer.innerHTML = '';
    variations.forEach(v => {
        const btn = document.createElement('button');
        btn.className = `opt-btn ${v.Size === selectedSize ? 'selected' : ''}`;
        btn.innerText = `${v.Size || 'Regular'} ($${v.Base_Price.toFixed(2)})`;
        btn.onclick = () => {
            selectedSize = v.Size;
            Array.from(sizeContainer.children).forEach(c => c.classList.remove('selected'));
            btn.classList.add('selected');
            updateModalPrice();
        };
        sizeContainer.appendChild(btn);
    });
    
    // Render Modifiers (from Gherkin mapping)
    const modContainer = document.getElementById('modifier-options');
    modContainer.innerHTML = '';
    
    let allMods = [];
    variations.forEach(v => {
        if(v.Allowed_Modifiers) allMods = allMods.concat(v.Allowed_Modifiers);
    });
    allMods = [...new Set(allMods)];
    
    if (allMods.length === 0) {
        document.getElementById('modifiers-container').style.display = 'none';
    } else {
        document.getElementById('modifiers-container').style.display = 'block';
        allMods.forEach(mod => {
            const btn = document.createElement('button');
            btn.className = 'opt-btn';
            btn.innerText = mod;
            btn.onclick = () => {
                if(selectedMods.has(mod)) {
                    selectedMods.delete(mod);
                    btn.classList.remove('selected');
                } else {
                    selectedMods.add(mod);
                    btn.classList.add('selected');
                }
            };
            modContainer.appendChild(btn);
        });
    }
    
    updateModalPrice();
    document.getElementById('modifier-modal').classList.add('active');
}

function updateModalPrice() {
    const v = selectedItem.variations.find(v => v.Size === selectedSize) || selectedItem.variations[0];
    document.getElementById('modal-price').innerText = `$${v.Base_Price.toFixed(2)}`;
}

document.getElementById('cancel-item').onclick = () => {
    document.getElementById('modifier-modal').classList.remove('active');
};

document.getElementById('add-to-order').onclick = () => {
    const v = selectedItem.variations.find(v => v.Size === selectedSize) || selectedItem.variations[0];
    cart.push({
        name: selectedItem.name,
        size: selectedSize,
        price: v.Base_Price,
        mods: Array.from(selectedMods)
    });
    document.getElementById('modifier-modal').classList.remove('active');
    renderCart();
};

function renderCart() {
    const list = document.getElementById('order-list');
    list.innerHTML = '';
    
    if(cart.length === 0) {
        list.innerHTML = '<div class="empty-cart">Order is empty</div>';
        updateTotals(0);
        return;
    }
    
    let subtotal = 0;
    cart.forEach(item => {
        subtotal += item.price;
        const el = document.createElement('div');
        el.className = 'cart-item';
        el.innerHTML = `
            <div class="cart-item-header">
                <span>${item.size ? item.size + ' ' : ''}${item.name}</span>
                <span>$${item.price.toFixed(2)}</span>
            </div>
            ${item.mods.length ? `<div class="cart-item-mods">+ ${item.mods.join(', ')}</div>` : ''}
        `;
        list.appendChild(el);
    });
    updateTotals(subtotal);
}

function updateTotals(subtotal) {
    const tax = subtotal * 0.08;
    const total = subtotal + tax;
    document.getElementById('subtotal').innerText = `$${subtotal.toFixed(2)}`;
    document.getElementById('tax').innerText = `$${tax.toFixed(2)}`;
    document.getElementById('total').innerText = `$${total.toFixed(2)}`;
}

document.getElementById('pay-btn').onclick = () => {
    if(cart.length === 0) return;
    alert('Order sent to kitchen! Total: ' + document.getElementById('total').innerText);
    cart = [];
    renderCart();
};

// Continuous Background Auto-Correction
setInterval(async () => {
    // Only poll if POS view is active
    if (!document.getElementById('pos-view').classList.contains('active')) return;
    
    try {
        const res = await fetch('/api/menu');
        const newData = await res.json();
        
        // Compare with current data (simple JSON diff)
        if (JSON.stringify(newData) !== JSON.stringify(currentMenu) && newData.length > 0) {
            console.log("Menu payload updated. Auto-correcting POS UI...");
            currentMenu = newData;
            
            // Re-render tabs and active items silently
            renderCategories();
            if (currentCategory) {
                renderItems(currentCategory);
            }
            
            // Visual feedback
            const header = document.querySelector('.pos-header');
            header.classList.remove('flash-update');
            void header.offsetWidth; // Trigger reflow
            header.classList.add('flash-update');
        }
    } catch (e) {
        console.error("Auto-correction poll failed:", e);
    }
}, 5000);

// Admin Toolbar Logic
document.getElementById('admin-upload-btn').onclick = () => document.getElementById('admin-file-input').click();

document.getElementById('admin-file-input').addEventListener('change', async (e) => {
    if(!e.target.files.length) return;
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    try {
        await fetch('/api/upload', { method: 'POST', body: formData });
        // The background polling interval will automatically pick up the new menu once parsed!
    } catch (err) {
        alert("Upload failed.");
    }
});

document.getElementById('admin-simulate-btn').onclick = async () => {
    try {
        const res = await fetch('/api/simulate_update', { method: 'POST' });
        const data = await res.json();
        if(data.status !== "success") alert(data.message);
    } catch (e) {
        alert("Simulation failed.");
    }
};

document.getElementById('admin-delete-btn').onclick = async () => {
    if(!confirm("Are you sure you want to delete the menu?")) return;
    try {
        await fetch('/api/delete_menu', { method: 'POST' });
        // Reset UI
        currentMenu = [];
        cart = [];
        document.getElementById('pos-view').classList.remove('active');
        document.getElementById('upload-view').classList.add('active');
        document.getElementById('pipeline-status').classList.add('hidden');
        document.getElementById('drop-zone').classList.remove('hidden');
        document.getElementById('currentStateLabel').innerText = "Processing...";
    } catch (e) {
        alert("Delete failed.");
    }
};
