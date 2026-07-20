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

// Template Picker
async function loadTemplates() {
    try {
        const res = await fetch('/api/templates');
        const data = await res.json();
        const list = document.getElementById('template-list');
        if (!data.templates || data.templates.length === 0) {
            list.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">No templates available yet.</p>';
            return;
        }
        list.innerHTML = '';
        data.templates.forEach(filename => {
            const btn = document.createElement('button');
            btn.className = 'template-btn';
            btn.innerHTML = `
                <span class="file-icon">📊</span>
                <span class="file-name">${filename}</span>
                <span class="load-label">Load →</span>
            `;
            btn.addEventListener('click', () => loadTemplate(filename));
            list.appendChild(btn);
        });
    } catch (e) {
        console.error('Failed to load templates:', e);
    }
}

async function loadTemplate(filename) {
    document.getElementById('drop-zone').classList.add('hidden');
    document.querySelector('.template-picker').classList.add('hidden');
    document.getElementById('pipeline-status').classList.remove('hidden');
    
    try {
        await fetch('/api/load_template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        pollPipeline();
    } catch (e) {
        alert("Failed to load template.");
    }
}

// Load templates on page init
loadTemplates();

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
        btn.onclick = () => openModifierModal(drinkName, drinkVariations, category);
        grid.appendChild(btn);
    });
}

// Configuration
const MODIFIER_PRICING = {
    "Espresso Shots": { 
        keywords: ["shot", "espresso", "roast"], 
        items: ["Extra Shot", "Blonde Espresso", "Decaf Espresso"],
        price: 1.00, freeItems: [] 
    },
    "Flavors": { 
        keywords: ["syrup", "sauce", "drizzle", "vanilla", "caramel", "mocha", "dolce"], 
        items: ["Vanilla Syrup", "Caramel Syrup", "Mocha Sauce", "Classic Syrup", "Cinnamon Dolce Syrup"],
        price: 0.80, freeItems: ["classic syrup"] 
    },
    "Milk": { 
        keywords: ["milk", "cream", "soy", "oat", "almond", "coconut", "half"], 
        items: ["2% Milk", "Whole Milk", "Nonfat Milk", "Oatmilk", "Almondmilk", "Soymilk"],
        price: 0.70, freeItems: ["2% milk", "whole milk", "nonfat milk"] 
    },
    "Toppings": { 
        keywords: ["foam", "whip", "topping", "powder", "cookie", "crunch"], 
        items: ["Cold Foam", "Whipped Cream", "Caramel Drizzle", "Cinnamon Powder"],
        price: 1.25, freeItems: [] 
    }
};

const CATEGORY_ROUTING = {
    "Cold Coffee": ["Size", "Espresso Shots", "Flavors", "Milk", "Toppings"],
    "Hot Coffee": ["Size", "Espresso Shots", "Flavors", "Milk", "Toppings"],
    "Frappuccino": ["Size", "Flavors", "Milk", "Toppings"],
    "Refreshers & Cold Drinks": ["Size", "Flavors", "Toppings"],
    "Smoothie": ["Size", "Flavors", "Toppings"],
    "Iced Tea": ["Size", "Flavors", "Toppings"],
    "Hot Tea": ["Size", "Flavors", "Toppings"],
    "Hot Drinks": ["Size", "Flavors", "Milk", "Toppings"],
    "DEFAULT": ["Size", "Flavors", "Milk", "Toppings"]
};

let wizardSteps = [];
let currentWizardStep = 0;
let parsedModifiers = {};

function categorizeModifier(modStr) {
    const lower = modStr.toLowerCase();
    for (const [cat, data] of Object.entries(MODIFIER_PRICING)) {
        if (data.keywords.some(k => lower.includes(k))) return cat;
    }
    return "Other";
}

function getModifierPrice(modStr) {
    const lower = modStr.toLowerCase();
    const cat = categorizeModifier(modStr);
    if(cat === "Other") return 0;
    const data = MODIFIER_PRICING[cat];
    if(data.freeItems.some(f => lower.includes(f))) return 0;
    return data.price;
}

// Modal Logic
function openModifierModal(drinkName, variations, category) {
    selectedItem = { name: drinkName, variations: variations, category: category };
    selectedSize = variations[0].Size;
    selectedMods.clear();
    currentWizardStep = 0;
    
    document.getElementById('modal-title').innerText = drinkName;
    
    let allMods = [];
    variations.forEach(v => {
        if(v.Allowed_Modifiers) allMods = allMods.concat(v.Allowed_Modifiers);
    });
    allMods = [...new Set(allMods)];
    
    parsedModifiers = { "Size": variations.map(v => v.Size || 'Regular') };
    allMods.forEach(mod => {
        const cat = categorizeModifier(mod);
        if(!parsedModifiers[cat]) parsedModifiers[cat] = [];
        parsedModifiers[cat].push(mod);
    });
    
    const route = CATEGORY_ROUTING[category] || CATEGORY_ROUTING["DEFAULT"];
    wizardSteps = route.filter(step => step === "Size" || MODIFIER_PRICING[step]);
    
    renderWizardStep();
    updateModalPrice();
    document.getElementById('modifier-modal').classList.add('active');
}

function renderWizardStep() {
    const container = document.getElementById('wizard-container');
    container.innerHTML = '';
    
    if (wizardSteps.length === 0) {
        document.getElementById('wizard-step-label').innerText = `No Customizations Available`;
        document.getElementById('wizard-progress-bar').style.width = `100%`;
        const addBtn = document.getElementById('add-to-order');
        addBtn.style.display = 'block';
        document.getElementById('wizard-next-btn').style.display = 'none';
        return;
    }

    const stepName = wizardSteps[currentWizardStep];
    document.getElementById('wizard-step-label').innerText = `Step ${currentWizardStep + 1} of ${wizardSteps.length}: ${stepName}`;
    const progress = ((currentWizardStep + 1) / wizardSteps.length) * 100;
    document.getElementById('wizard-progress-bar').style.width = `${progress}%`;
    
    const stepDiv = document.createElement('div');
    stepDiv.className = 'wizard-step active';
    
    const h4 = document.createElement('h4');
    h4.innerText = `Select ${stepName}`;
    h4.style.marginBottom = '1rem';
    stepDiv.appendChild(h4);
    
    const grid = document.createElement('div');
    grid.className = 'options-grid';
    
    if(stepName === "Size") {
        selectedItem.variations.forEach(v => {
            const btn = document.createElement('button');
            btn.className = `opt-btn ${v.Size === selectedSize ? 'selected' : ''}`;
            btn.innerHTML = `${v.Size || 'Regular'} <span class="mod-price-label">$${v.Base_Price.toFixed(2)}</span>`;
            btn.onclick = () => {
                selectedSize = v.Size;
                Array.from(grid.children).forEach(c => c.classList.remove('selected'));
                btn.classList.add('selected');
                updateModalPrice();
            };
            grid.appendChild(btn);
        });
    } else {
        let mods = parsedModifiers[stepName] || [];
        if (mods.length === 0 && MODIFIER_PRICING[stepName]) {
            mods = MODIFIER_PRICING[stepName].items;
        }
        
        mods.forEach(mod => {
            const price = getModifierPrice(mod);
            const priceStr = price > 0 ? `+$${price.toFixed(2)}` : 'Free';
            
            const btn = document.createElement('button');
            btn.className = `opt-btn ${selectedMods.has(mod) ? 'selected' : ''}`;
            btn.innerHTML = `${mod} <span class="mod-price-label">${priceStr}</span>`;
            btn.onclick = () => {
                if(selectedMods.has(mod)) {
                    selectedMods.delete(mod);
                    btn.classList.remove('selected');
                } else {
                    selectedMods.add(mod);
                    btn.classList.add('selected');
                }
                updateModalPrice();
            };
            grid.appendChild(btn);
        });
    }
    
    stepDiv.appendChild(grid);
    container.appendChild(stepDiv);
    
    const backBtn = document.getElementById('wizard-back-btn');
    const nextBtn = document.getElementById('wizard-next-btn');
    const addBtn = document.getElementById('add-to-order');
    
    backBtn.style.visibility = currentWizardStep > 0 ? 'visible' : 'hidden';
    
    if(currentWizardStep === wizardSteps.length - 1) {
        nextBtn.style.display = 'none';
        addBtn.style.display = 'block';
    } else {
        nextBtn.style.display = 'block';
        addBtn.style.display = 'none';
    }
}

document.getElementById('wizard-next-btn').onclick = () => {
    if(currentWizardStep < wizardSteps.length - 1) {
        currentWizardStep++;
        renderWizardStep();
    }
};

document.getElementById('wizard-back-btn').onclick = () => {
    if(currentWizardStep > 0) {
        currentWizardStep--;
        renderWizardStep();
    }
};

function updateModalPrice() {
    const v = selectedItem.variations.find(v => v.Size === selectedSize) || selectedItem.variations[0];
    let total = v.Base_Price;
    selectedMods.forEach(mod => {
        total += getModifierPrice(mod);
    });
    document.getElementById('modal-price').innerText = `$${total.toFixed(2)}`;
    return total;
}

document.getElementById('cancel-item').onclick = () => {
    document.getElementById('modifier-modal').classList.remove('active');
};

document.getElementById('add-to-order').onclick = () => {
    const finalPrice = updateModalPrice();
    cart.push({
        name: selectedItem.name,
        size: selectedSize,
        price: finalPrice,
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
