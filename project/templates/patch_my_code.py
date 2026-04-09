import io

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Replace CSS
start_css = "/* PAGE 3: DASHBOARD */\n.dash-layout"
end_css = "@media(max-width:768px){.dash-sidebar{width:60px;overflow:hidden}.dash-nav li span:not(.nav-emoji){display:none}.dash-sidebar-brand .ds-name{display:none}.dash-sidebar-brand{padding:0 .8rem 1rem}}"

new_css = """/* PAGE 3: DASHBOARD */
.dashboard-layout { display: flex; min-height: calc(100vh - 72px); background: var(--gray-50); } 
.dashboard-sidebar { width: 280px; background: white; border-right: 1px solid var(--gray-200); padding: 2rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; } 
.dashboard-sidebar .menu-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; margin: 0.25rem 0; border-radius: var(--radius-md); color: var(--gray-700); font-weight: 500; cursor: pointer; transition: all 0.2s; } 
.dashboard-sidebar .menu-item:hover { background: var(--gray-100); color: var(--primary); } 
.dashboard-sidebar .menu-item.active { background: rgba(246, 139, 30, 0.1); color: var(--accent); border-left: 3px solid var(--accent); } 
.dashboard-content { flex: 1; padding: 2rem; overflow-y: auto; } 
.order-summary-card { background: white; border-radius: var(--radius-xl); padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--gray-200); box-shadow: var(--shadow-md); } 
.payment-methods { display: flex; gap: 1rem; margin-top: 1.5rem; } 
.payment-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.8rem; border-radius: var(--radius-md); font-weight: 600; cursor: pointer; transition: all 0.2s; border: 1px solid var(--gray-200); background: white; } 
.payment-btn.paypal { background: #0070BA; color: white; border: none; } 
.payment-btn.stripe { background: #635BFF; color: white; border: none; } 
.report-id { font-family: monospace; background: var(--gray-100); padding: 0.25rem 0.5rem; border-radius: var(--radius-sm); font-size: 0.8rem; }"""

idx1 = html.find(start_css)
idx2 = html.find(end_css)
if idx1 != -1 and idx2 != -1:
    idx2 += len(end_css)
    html = html[:idx1] + new_css + html[idx2:]
else:
    print("Could not find CSS block")

# 2. Replace HTML
start_html = '<!-- PAGE 3: CLIENT DASHBOARD -->'
end_html = '<!-- PAYMENT UI MOVED TO DASHBOARD TAB -->'

new_html = """<!-- PAGE 3: DASHBOARD -->
<div id="page-dashboard" class="page"> 
    <div class="dashboard-layout"> 
        <div class="dashboard-sidebar"> 
            <div class="menu-item active" onclick="renderDashboardContent('orders')" data-tab="orders"><i class="fas fa-chart-line"></i> Orders</div> 
            <div class="menu-item" onclick="renderDashboardContent('reports')" data-tab="reports"><i class="fas fa-file-alt"></i> Reports</div> 
            <div class="menu-item" onclick="renderDashboardContent('billing')" data-tab="billing"><i class="fas fa-credit-card"></i> Billing</div> 
            <div class="menu-item" onclick="renderDashboardContent('profile')" data-tab="profile"><i class="fas fa-user"></i> Profile</div> 
            <div class="menu-item" onclick="renderDashboardContent('settings')" data-tab="settings"><i class="fas fa-cog"></i> Settings</div> 
            <div class="menu-item" onclick="renderDashboardContent('support')" data-tab="support"><i class="fas fa-headset"></i> Support</div> 
            <div class="menu-item" style="margin-top:auto;border-top:1px solid var(--gray-200);padding-top:1rem" onclick="showPage('home')"><i class="fas fa-home"></i> Back to Home</div>
        </div> 
        <div class="dashboard-content" id="dashboardContent"></div> 
    </div> 
</div>
<!-- PAYMENT UI MOVED TO DASHBOARD TAB -->"""

idx3 = html.find(start_html)
idx4 = html.find(end_html)
if idx3 != -1 and idx4 != -1:
    idx4 += len(end_html)
    html = html[:idx3] + new_html + html[idx4:]
else:
    print("Could not find HTML block")


# 3. Replace JS openBuyNow & simulatePayment
import re
js_start = "var pendingOrder=null;"
js_end = "function switchDashTab(tab,el){"

new_js = """var generatedOrderId = '';
var currentReportTitleForPayment = '';
var currentPackageForPayment = '';
var pendingOrder = null;

function openBuyNow() {
    clearErrors();
    var title = document.getElementById('reportTitleInput').value.trim();
    if (!title) {
        showError('reportTitleInput', "Report title is required to generate segments and price.");
        document.getElementById('reportTitleInput').scrollIntoView({behavior:'smooth', block:'center'});
        return;
    }
    var p = calcPrice();
    if (p.total === 0) {
        showToast("Please select at least one geography (Global or Country) to proceed.", true);
        return;
    }
    
    currentReportTitleForPayment = title;
    var descParts = [];
    if (globalSelected) descParts.push('Global');
    descParts.push((p.defCount + p.custCount) + ' countries');
    if (segmentationOn) descParts.push('Segments');
    currentPackageForPayment = descParts.join(' + ');
    
    generatedOrderId = 'MP-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
    pendingOrder = {
        id: generatedOrderId,
        title: title,
        price: '$' + p.total,
        total: p.total,
        status: 'pending'
    };
    
    showPage('dashboard');
    renderDashboardContent('orders');
}

function renderDashboardContent(tab) { 
    const contentDiv = document.getElementById('dashboardContent'); 
    if (tab === 'orders') { 
        let amountText = pendingOrder ? pendingOrder.price : '$0';
        contentDiv.innerHTML = ` 
            <div class="order-summary-card"> 
                <h2 style="color: var(--primary); margin-bottom: 1rem;">Order Summary</h2> 
                <p><strong>Order ID:</strong> <span class="report-id">${generatedOrderId}</span></p> 
                <p><strong>Report Title:</strong> ${currentReportTitleForPayment}</p> 
                <p><strong>Package:</strong> ${currentPackageForPayment}</p> 
                <p><strong>Amount:</strong> <span style="font-weight:bold">${amountText}</span></p> 
                <p><strong>Status:</strong> <span style="color: var(--accent);">Pending Payment</span></p> 
                <div class="payment-methods"> 
                    <button id="paypal-btn" class="payment-btn paypal" onclick="simulatePayment('PayPal')"><i class="fab fa-paypal"></i> PayPal</button> 
                    <button id="stripe-btn" class="payment-btn stripe" onclick="simulatePayment('Stripe')"><i class="fas fa-bolt"></i> Stripe</button> 
                </div> 
                <div id="payment-message" style="margin-top: 1rem; font-size: 0.85rem;"></div> 
            </div> 
        `; 
    } else if (tab === 'reports') { 
        contentDiv.innerHTML = `<div class="order-summary-card"><h3>Your Reports</h3><p>You have 1 pending report: ${currentReportTitleForPayment}</p><p>Once payment is completed, you can download the full Excel report here.</p></div>`; 
    } else { 
        contentDiv.innerHTML = `<div class="order-summary-card"><h3>${tab.charAt(0).toUpperCase() + tab.slice(1)}</h3><p>This section is under development. Please check back soon.</p></div>`; 
    } 
    document.querySelectorAll('.dashboard-sidebar .menu-item').forEach(item => { 
        item.classList.remove('active'); 
        if (item.getAttribute('data-tab') === tab) item.classList.add('active'); 
    }); 
}

function simulatePayment(method) { 
    const msgDiv = document.getElementById('payment-message'); 
    msgDiv.innerHTML = `<div style="background: #E8F5E9; padding: 0.8rem; border-radius: 8px; color: #2E7D32; font-weight:500;">✅ Payment via ${method} successful! Your order is now confirmed. You will receive an email with the report download link.</div>`; 
    // Wait briefly and update reports tab
    if (pendingOrder) {
        pendingOrder.status = 'paid';
        orders.push(pendingOrder);
        // Ensure profile updates orders count
        var profileEl = document.getElementById('profileOrders');
        if(profileEl) profileEl.textContent = orders.length;
    }
}

function switchDashTab(tab,el){
"""

idx5 = html.find(js_start)
# find end of switchDashTab to just replace the whole thing since we don't need switchDashTab anymore actually wait we do?
# We have refreshDashboard that assumes `switchDashTab` isn't entirely removed. The PDF had renderDashboardContent, while the old one uses switchDashTab.
# To not break `refreshDashboard()`, we should either remove `switchDashTab` calls in `refreshDashboard` or replace `switchDashTab` with a redirect to `renderDashboardContent()`.

new_js = new_js.replace("function switchDashTab(tab,el){\n", "function switchDashTab(tab, el) { renderDashboardContent(tab); }\n")
# find end of simulatePayment in the old code
idx6 = html.find("function switchDashTab(tab,el){")
if idx5 != -1 and idx6 != -1:
    idx6end = html.find("}", idx6) + 1
    html = html[:idx5] + new_js + html[idx6end:]
else:
    print("Could not find JS block 1")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Patching complete.")
