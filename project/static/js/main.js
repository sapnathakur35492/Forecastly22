function showError(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('input-error');
    let err = el.parentNode.querySelector('.error-msg-' + id);
    if (!err) {
        err = document.createElement('div');
        err.className = 'error-msg error-msg-' + id;
        err.style.cssText = 'color:#DC2626;font-size:0.75rem;font-weight:600;margin-top:0.4rem;width:100%;display:flex;align-items:center;gap:4px;';
        el.parentNode.appendChild(err);
    }
    err.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> ${msg}`;
    err.style.display = 'flex';
}

function clearErrors() {
    document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
    document.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');
}

function validateMarketTitle(t) {
    if (!t) return { valid: false, msg: 'Please enter a market name.' };
    if (t.trim().length < 3) return { valid: false, msg: 'Title too short.' };
    return { valid: true };
}

function getCSRF() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue || (document.querySelector("[name=csrfmiddlewaretoken]") ? document.querySelector("[name=csrfmiddlewaretoken]").value : "");
}

var verifiedEmail = '',
    generatedCode = '',
    selectedPayMethod = 'paypal',
    orders = [];
var segmentationOn = false;
var pendingAction = null;

function showPage(p) {
    document.querySelectorAll('.page').forEach(function(pg) {
        pg.classList.remove('active')
    });
    const target = document.getElementById('page-' + p);
    if (target) {
        target.classList.add('active');
    }

    if (p === 'dashboard') {
        const nav = document.querySelector('.nav');
        if (nav) nav.style.display = 'none';
        if (typeof refreshDashboard === 'function') refreshDashboard();
    } else {
        const nav = document.querySelector('.nav');
        if (nav) nav.style.display = '';
    }
    window.scrollTo(0, 0);
}

function scrollToSec(id) {
    // If we're on home page, scroll to section
    if (window.location.pathname === '/') {
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({
            behavior: 'smooth'
        });
    } else {
        // If not on home, check if this section belongs to a dedicated page
        const SLUG_MAP = {
            'how-sec': '/how-it-works/',
            'price-sec': '/pricing/',
            'faq-sec': '/faq/',
            'methodology-sec': '/behind-the-numbers/',
            'meth-sec': '/behind-the-numbers/'
        };
        if (SLUG_MAP[id]) {
            window.location.href = SLUG_MAP[id];
        } else {
            window.location.href = '/#' + id;
        }
    }
}

function startReport() {
    clearErrors();
    const qInput = document.getElementById('homeSearchInput') || document.getElementById('reportTitleInput');
    if (!qInput) {
        window.location.href = '/builder/';
        return;
    }
    var q = qInput.value.trim();

    var v = validateMarketTitle(q);
    if (!v.valid) {
        if (window.location.pathname === '/') {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            setTimeout(function() {
                qInput.focus();
                showError(qInput.id, v.msg);
            }, 300);
        } else {
            showError(qInput.id, v.msg);
        }
        return;
    }

    if (window.location.pathname !== '/builder/') {
        // Use localStorage to pass title to builder page
        localStorage.setItem('pendingReportTitle', q);
        window.location.href = '/builder/';
    } else {
        document.getElementById('gateOverlay').style.display = 'none';
        document.getElementById('builderContent').style.display = 'block';
        document.getElementById('reportTitleInput').value = q;
        initBuilder();
    }
}

// Check for pending report title on page load (for builder)
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/builder/') {
        const pending = localStorage.getItem('pendingReportTitle');
        if (pending) {
            localStorage.removeItem('pendingReportTitle');
            const input = document.getElementById('reportTitleInput');
            if (input) {
                input.value = pending;
                // If not gated, init builder
                const gate = document.getElementById('gateOverlay');
                if (gate && gate.style.display === 'none') {
                    initBuilder();
                }
            }
        }
    }
});

async function sendCode() {
    clearErrors();
    var email = document.getElementById('gateEmail').value.trim();
    if (!email || !email.includes('@') || !email.includes('.')) {
        showError('gateEmail', 'Please enter a valid business email.');
        return;
    }
    var btn = document.querySelector('#gateStep1 button');
    var oldText = btn.textContent;
    btn.textContent = 'Sending...';
    btn.disabled = true;
    try {
        const res = await fetch('/api/send-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF()
            },
            body: JSON.stringify({
                email
            })
        });
        const data = await res.json();
        if (data.status === 'code_sent') {
            document.getElementById('gateStep1').style.display = 'none';
            document.getElementById('gateStep2').style.display = 'block';
            document.getElementById('gateDesc').textContent = 'Code sent to ' + email;
        } else {
            showError('gateEmail', data.error || 'Failed to send code.');
        }
    } catch (e) {
        console.error(e);
        showError('gateEmail', 'Network error. Please try again.');
    }
    btn.textContent = oldText;
    btn.disabled = false;
}

async function verifyCode() {
    clearErrors();
    var code = document.getElementById('gateCode').value.trim();
    var email = document.getElementById('gateEmail').value.trim();
    if (!code) {
        showError('gateCode', 'Please enter the 6-digit code.');
        return;
    }
    var btn = document.querySelector('#gateStep2 button');
    var oldText = btn.textContent;
    btn.textContent = 'Verifying...';
    btn.disabled = true;
    try {
        const res = await fetch('/api/verify-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF()
            },
            body: JSON.stringify({
                email: email,
                code: code
            })
        });
        const data = await res.json();
        if (data.status === 'verified') {
            verifiedEmail = email;
            document.getElementById('gateOverlay').style.display = 'none';
            document.getElementById('builderContent').style.display = 'block';

            const de = document.getElementById('dashEmail');
            if (de) de.textContent = email;
            const da = document.getElementById('dsAvatar');
            if (da) da.textContent = email.substring(0, 2).toUpperCase();

            if (pendingAction === 'demo') {
                pendingAction = null;
                buildExcel();
            } else if (pendingAction === 'buy') {
                pendingAction = null;
                openBuyNow();
            }
        } else {
            showError('gateCode', data.error || 'Invalid or expired code.');
        }
    } catch (e) {
        console.error(e);
        showError('gateCode', 'Verification error. Please try again.');
    }
    btn.textContent = oldText;
    btn.disabled = false;
}

function resetGate() {
    document.getElementById('gateStep1').style.display = 'block';
    document.getElementById('gateStep2').style.display = 'none';
    document.getElementById('gateDesc').textContent = 'Enter your business email to access the report builder.';
    document.getElementById('gateEmail').value = '';
    document.getElementById('gateCode').value = '';
    generatedCode = ''
}

var XX = "xx.xx",
    XXP = "x.x%",
    SRC = "Source: Primary Interviews, Secondary Research, Internal Databases and Estimately.io Research";
var regionData = [];
var PP = {
    per_country: 20,
    global: 20,
    seg: 99,
    pro: 199,
    pro_th: 10,
    ent: 299,
    extra: 20,
    both: 1.5,
    min: 0
};
var selectedCountries = new Set(),
    customCountries = {},
    countryCheckboxes = {},
    currentSegmentation = [],
    globalSelected = false;

async function loadDynamicConfig() {
    try {
        const [resSite, resPrice, resReg] = await Promise.all([
            fetch('/api/site-config/'),
            fetch('/api/pricing-config/'),
            fetch('/api/regions/')
        ]);
        const site = await resSite.json();
        const price = await resPrice.json();
        const regs = await resReg.json();

        PP = {
            per_country: Number(price.per_country_price),
            global: Number(price.global_price),
            seg: Number(price.segmentation_price),
            pro: Number(price.pro_cap),
            pro_th: Number(price.pro_cap_threshold),
            ent: Number(price.enterprise_cap),
            extra: Number(price.extra_country_price),
            both: Number(price.both_metric_multiplier),
            min: Number(price.min_order)
        };

        regionData = regs.map(r => ({
            name: r.name,
            countries: r.countries.map(c => c.name)
        }));

        if (window.location.pathname === '/') {
            renderLandingPage(site);
        }

        if (window.location.pathname === '/builder/') {
            renderRegions();
            updatePriceDisplay();
        }
    } catch (e) {
        console.error("Failed to load config", e);
    }
}

document.addEventListener('DOMContentLoaded', loadDynamicConfig);

var builderInited = false;

function initBuilder() {
    if (builderInited) return;
    const builderEl = document.getElementById('builderContent');
    if (!builderEl) return;
    builderInited = true;
    renderRegions();
    updatePriceDisplay();
    updateForecastOptions();
    var q = document.getElementById('reportTitleInput').value.trim();
    if (q) refreshSeg();

    document.getElementById('reportTitleInput').addEventListener('input', refreshSeg);
    document.getElementById('baseYear').addEventListener('change', updateForecastOptions);
    document.getElementById('marketMetric').addEventListener('change', updatePriceDisplay);
    document.getElementById('chk_global').addEventListener('change', function() {
        globalSelected = this.checked;
        updatePriceDisplay();
    });

    document.getElementById('addCountryBtn').addEventListener('click', function() {
        var inp = document.getElementById('customCountryInput'),
            regSel = document.getElementById('customRegionSelect');
        var v = inp.value.trim();
        if (!v) return;
        customCountries[v] = regSel.value;
        renderCustomInRegion(v, regSel.value);
        updatePriceDisplay();
        inp.value = '';
    });
}

function getDefaultSelectedCount() {
    var c = 0;
    regionData.forEach(function(r) {
        r.countries.forEach(function(co) {
            if (selectedCountries.has(co)) c++
        })
    });
    return c
}

function getCustomCount() {
    return Object.keys(customCountries).length
}

function calcPrice() {
    var defCount = getDefaultSelectedCount();
    var custCount = getCustomCount();
    var globalCount = globalSelected ? 1 : 0;
    var totalUnits = defCount + globalCount;
    var rawDefault = totalUnits * PP.per_country;
    var cappedDefault = totalUnits >= PP.pro_th ? Math.min(rawDefault, PP.pro) : rawDefault;
    var extraPrice = custCount * PP.extra;
    var segPrice = segmentationOn ? PP.seg : 0;
    var subtotal = cappedDefault + segPrice;
    var cappedSub = Math.min(subtotal, PP.ent);
    var baseTotal = cappedSub + extraPrice;
    var rawTotal = rawDefault + extraPrice + segPrice;
    var total = baseTotal;
    var metricVal = document.getElementById('marketMetric') ? document.getElementById('marketMetric').value : 'revenue';
    if (metricVal === 'both') {
        total = Math.round(total * PP.both)
    }
    if (total > 0 && total < PP.min) {
        total = PP.min
    }
    total = Math.max(total, 0);
    var savings = rawTotal - baseTotal;
    if (savings < 0) savings = 0;
    return {
        total: total,
        defCount: defCount,
        custCount: custCount,
        globalCount: globalCount,
        totalUnits: totalUnits,
        rawDefault: rawDefault,
        cappedDefault: cappedDefault,
        extraPrice: extraPrice,
        segPrice: segPrice,
        savings: savings,
        proCapped: rawDefault > PP.pro,
        entCapped: (cappedDefault + segPrice) > PP.ent,
        metricValue: metricVal
    }
}

function updatePriceDisplay() {
    var p = calcPrice();
    var amountEl = document.getElementById('priceLiveAmount');
    var detailEl = document.getElementById('priceLiveDetail');
    var savingsEl = document.getElementById('priceLiveSavings');
    if (!amountEl) return;

    var totalCount = p.defCount + p.custCount + p.globalCount;
    if (totalCount === 0 && !segmentationOn) {
        amountEl.textContent = '$0';
        detailEl.textContent = 'Select Global or countries to begin';
        savingsEl.style.display = 'none'
    } else {
        amountEl.textContent = '$' + p.total;
        var parts = [];
        if (p.globalCount > 0) parts.push('Global');
        if (p.defCount > 0) parts.push(p.defCount + ' countries');
        if (p.globalCount > 0 || p.defCount > 0) {
            var unitLabel = (p.globalCount > 0 ? 'Global + ' : '') + (p.defCount > 0 ? p.defCount + ' items \u00d7 $' + PP.per_country : '');
            if (p.proCapped) {
                parts = ['(Global' + (p.defCount > 0 ? ' + ' + p.defCount + ' countries' : '') + ') $' + p.rawDefault + ' \u2192 capped $' + p.cappedDefault]
            } else {
                parts = [unitLabel + ' = $' + p.rawDefault]
            }
        }
        if (p.custCount > 0) parts.push('+' + p.custCount + ' extra = $' + p.extraPrice);
        if (segmentationOn) parts.push('+Segments $' + PP.seg);
        if (p.metricValue === 'both') parts.push('\u00d71.5 (Rev+Vol)');
        detailEl.textContent = parts.join(' | ');
        if (p.savings > 0) {
            savingsEl.style.display = 'block';
            var capName = p.entCapped ? 'Enterprise' : 'Professional';
            savingsEl.textContent = '\ud83c\udf89 You save $' + p.savings + ' with ' + capName + ' cap!'
        } else {
            savingsEl.style.display = 'none'
        }
    }
    var mn = document.getElementById('metricNote');
    if (mn) {
        mn.style.display = p.metricValue === 'both' ? 'block' : 'none'
    }
    updateUpsell(p);
    renderPricingCards(p)
}

function updateUpsell(p) {
    var banner = document.getElementById('upsellBanner');
    if (!banner) return;
    var totalDef = p.defCount + p.globalCount;
    if (totalDef >= 7 && totalDef < PP.pro_th) {
        var need = PP.pro_th - totalDef;
        var wouldSave = (totalDef + need) * PP.per_country - PP.pro;
        banner.style.display = 'block';
        banner.innerHTML = '\ud83d\udca1 Add ' + need + ' more ' + (need === 1 ? 'country' : 'countries') + ' to unlock $' + PP.pro + ' cap and save $' + wouldSave + '!'
    } else if (totalDef >= PP.pro_th && !segmentationOn) {
        banner.style.display = 'block';
        banner.innerHTML = '\u2705 Professional cap active! Add segmentation for just $' + PP.seg + ' more (caps at $' + PP.ent + ')'
    } else {
        banner.style.display = 'none'
    }
}

function toggleSegmentation() {
    segmentationOn = !segmentationOn;
    var wrap = document.getElementById('segToggleWrap');
    var toggle = document.getElementById('segToggle');
    var knob = document.getElementById('segToggleKnob');
    var title = document.getElementById('segToggleTitle');
    var desc = document.getElementById('segToggleDesc');

    if (segmentationOn) {
        wrap.style.background = '#F0F9FF';
        wrap.style.borderColor = '#0284C7';
        wrap.style.borderWidth = '2px';
        wrap.style.boxShadow = '0 10px 15px -3px rgba(14, 165, 233, 0.2)';
        toggle.style.background = '#0284C7';
        knob.style.left = '22px';
        title.style.color = '#0369A1';
        desc.style.color = '#075985';
    } else {
        wrap.style.background = '#F0F9FF';
        wrap.style.borderColor = '#0EA5E9';
        wrap.style.borderWidth = '1.5px';
        wrap.style.boxShadow = '0 4px 6px -1px rgba(14, 165, 233, 0.1)';
        toggle.style.background = '#CBD5E1';
        knob.style.left = '2px';
        title.style.color = '#0369A1';
        desc.style.color = '#0C4A6E';
    }
    updatePriceDisplay();
}

function renderRegions() {
    var c = document.getElementById('regionsContainer');
    if (!c) return;
    c.innerHTML = '';
    regionData.forEach(function(r) {
        var d = document.createElement('div');
        d.className = 'region-group';
        d.innerHTML = `
            <div class="region-header">
                <span class="region-name">📍 ${r.name}</span>
                <div class="region-actions">
                    <button class="region-action-btn select-all-btn">Select All</button>
                    <button class="region-action-btn clear-all-btn">Clear All</button>
                </div>
            </div>
            <div class="country-grid"></div>
            <div class="country-grid" id="custom_${r.name.replace(/\s/g, '_')}"></div>`;

        var g = d.querySelector('.country-grid');
        r.countries.forEach(function(co) {
            var w = document.createElement('div');
            w.className = 'country-check' + (co.startsWith('Rest of') ? ' rest-tag' : '');
            var id = 'chk_' + co.replace(/\s/g, '_');
            w.innerHTML = '<input type="checkbox" id="' + id + '" value="' + co + '"><label for="' + id + '">' + co + '</label>';
            var cb = w.querySelector('input');
            cb.addEventListener('change', function() {
                if (cb.checked) {
                    selectedCountries.add(co)
                } else {
                    selectedCountries.delete(co)
                }
                updatePriceDisplay()
            });
            countryCheckboxes[co] = cb;
            g.appendChild(w)
        });

        d.querySelector('.select-all-btn').addEventListener('click', function() {
            r.countries.forEach(function(c) {
                selectedCountries.add(c);
                if (countryCheckboxes[c]) countryCheckboxes[c].checked = true;
            });
            updatePriceDisplay();
        });

        d.querySelector('.clear-all-btn').addEventListener('click', function() {
            r.countries.forEach(function(c) {
                selectedCountries.delete(c);
                if (countryCheckboxes[c]) countryCheckboxes[c].checked = false;
            });
            updatePriceDisplay();
        });

        c.appendChild(d)
    })
}

function renderCustomInRegion(name, region) {
    var regId = 'custom_' + region.replace(/\s/g, '_');
    var container = document.getElementById(regId);
    if (!container) return;
    var w = document.createElement('div');
    w.className = 'country-check';
    w.style.background = '#E2E8F0';
    w.style.border = '1px dashed #42A5F5';
    w.id = 'ccust_' + name.replace(/\s/g, '_');
    w.innerHTML = '<span style="font-size:.78rem;color:#0A3D62;font-weight:500">' + name + ' <span class="rm" style="cursor:pointer;color:#DC2626;font-weight:700;margin-left:.3rem" data-c="' + name + '">\u2715<\/span> <span style="font-size:.55rem;background:#42A5F5;color:white;padding:.1rem .3rem;border-radius:10px">+$20<\/span><\/span>';
    w.querySelector('.rm').addEventListener('click', function() {
        delete customCountries[name];
        w.remove();
        updatePriceDisplay()
    });
    container.appendChild(w)
}

function renderPricingCards(p) {
    var c = document.getElementById('pricingCards');
    if (!c) return;
    c.innerHTML = '';
    var total = p.total;
    var hasCountries = (p.defCount + p.custCount) > 0;
    var hasAnything = hasCountries || globalSelected || segmentationOn;
    var btnDemo = '<button class="pkg-btn-demo" style="width:100%;margin-top:.5rem" onclick="buildExcel()">\ud83d\udce5 Download Demo Excel<\/button>';
    var btnBuy = '<button class="pkg-btn-buy" style="width:100%;margin-top:.4rem" onclick="openBuyNow()">\ud83d\uded2 Buy Now \u2014 $' + total + '<\/button>';
    if (!hasAnything) {
        c.innerHTML = '<div style="text-align:center;padding:1.5rem;color:#94A3B8;font-size:.82rem">\u2190 Select Global or countries to see pricing<\/div>';
        return
    }
    var configParts = [];
    if (globalSelected) configParts.push('Global');
    configParts.push((p.defCount + p.custCount) + ' ' + (p.defCount + p.custCount === 1 ? 'country' : 'countries'));
    if (segmentationOn) configParts.push('Segmentation');
    c.innerHTML = '<div style="background:#F8FAFC;border:1.5px solid #CBD5E1;border-radius:12px;padding:.8rem;text-align:center"><div style="font-size:.78rem;font-weight:700;color:#0A3D62;margin-bottom:.3rem">Your Configuration<\/div><div style="font-size:.7rem;color:#0A3D62">' + configParts.join(' + ') + '<\/div><div style="font-size:1.5rem;font-weight:800;color:#0A3D62;margin:.3rem 0">$' + total + '<\/div>' + (p.savings > 0 ? '<div style="font-size:.65rem;color:#1E88E5;font-weight:600">\ud83c\udf89 Saving $' + p.savings + ' with auto-cap<\/div>' : '') + '<\/div>' + btnDemo + btnBuy
}

function updateForecastOptions() {
    var baseEl = document.getElementById('baseYear');
    if (!baseEl) return;
    var base = +baseEl.value;
    var fc = document.getElementById('forecastPeriod');
    var fStart = base + 1;
    fc.innerHTML = '';
    [{
        end: fStart + 4,
        label: fStart + '\u2013' + (fStart + 4) + ' (5Y)'
    }, {
        end: fStart + 6,
        label: fStart + '\u2013' + (fStart + 6) + ' (7Y)'
    }, {
        end: 2033,
        label: fStart + '\u20132033 (' + (2033 - fStart + 1) + 'Y)'
    }].forEach(function(p, i) {
        var o = document.createElement('option');
        o.value = p.end;
        o.textContent = p.label;
        if (i === 2) o.selected = true;
        fc.appendChild(o)
    })
}

async function buildExcel() {
    clearErrors();
    var titleInput = document.getElementById('reportTitleInput');
    if (!titleInput) return;
    var title = titleInput.value.trim();
    if (!title) {
        showError('reportTitleInput', "Report title is required to generate a demo Excel.");
        titleInput.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        return;
    }

    var p = calcPrice();
    if (p.total === 0) {
        showToast("Please select at least one geography (Global or Country) to generate a report.", true);
        return;
    }

    if (!verifiedEmail) {
        pendingAction = 'demo';
        document.getElementById('gateOverlay').style.display = 'flex';
        return;
    }

    const dn = document.getElementById('downloadNotice');
    if (dn) {
        dn.style.display = 'block';
        dn.textContent = "⚙️ Generating branded Excel...";
    }

    try {
        const syncRes = await fetch('/api/report/update/' + activeReportId + '/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF()
            },
            body: JSON.stringify({
                segments: currentSegmentation,
                countries: Array.from(selectedCountries).concat(Object.keys(customCountries)),
                is_global: globalSelected
            })
        });

        if (!syncRes.ok) throw new Error("Failed to sync report state");

        const baseYear = document.getElementById('baseYear').value;
        const forecastYear = document.getElementById('forecastPeriod').value;
        const metric = document.getElementById('marketMetric').value;
        const currency = document.getElementById('currency').value;
        const planType = segmentationOn ? 'enterprise' : 'professional';

        const downloadUrl = `/api/download/${activeReportId}/${planType}/?demo=true&base_year=${baseYear}&forecast_year=${forecastYear}&metric=${encodeURIComponent(metric)}&currency=${currency}&global=${globalSelected}`;

        window.location.href = downloadUrl;

        if (dn) {
            setTimeout(() => {
                dn.textContent = "✅ Demo Excel downloaded!";
                setTimeout(() => {
                    dn.style.display = 'none';
                }, 5000);
            }, 2000);
        }
    } catch (e) {
        console.error(e);
        showErrorToast("Download failed. Please try again.");
        if (dn) dn.style.display = 'none';
    }
}

var activeReportId = '';
var segTimer;
var loadStep = 0;
var loadMsgs = ["Initializing AI...", "Analyzing market taxonomy...", "Researching commercial viability...", "Structuring hierarchical segments...", "Finalizing output..."];

function advanceLoader(c) {
    if (loadStep < loadMsgs.length) {
        c.innerHTML = '<div style="padding:4rem;text-align:center"><div class="spinner" style="margin:0 auto"></div><p style="margin-top:1.5rem;font-weight:700;color:var(--accent);animation:fade 1s">' + loadMsgs[loadStep] + '</p></div>';
        loadStep++;
        segTimer = setTimeout(() => advanceLoader(c), 1500);
    }
}

async function refreshSeg() {
    clearErrors();
    const input = document.getElementById('reportTitleInput');
    if (!input) return;
    var t = input.value.trim(),
        c = document.getElementById('segmentationLevels');

    var v = validateMarketTitle(t);
    if (!v.valid) {
        currentSegmentation = [];
        if (t) {
            c.innerHTML = `<div style="background:#FEF2F2;border:1.5px solid #FCA5A5;border-radius:12px;padding:1.5rem;text-align:center;color:#991B1B">⚠️ <b style="font-size:0.8rem">${v.msg}</b></div>`;
        } else {
            c.innerHTML = '<div class="seg-empty">Type a market niche above for AI to generate segments.</div>';
        }
        return;
    }
    const titleEl = document.getElementById('builderReportTitle');
    if (titleEl) titleEl.textContent = t;
    clearTimeout(segTimer);
    loadStep = 0;
    advanceLoader(c);

    try {
        const res = await fetch('/api/generate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF()
            },
            body: JSON.stringify({
                market_name: t
            })
        });
        const data = await res.json();
        clearTimeout(segTimer);

        if (data.error) {
            let errHtml = `<div style="background:#FEF2F2;border:2.5px solid #FCA5A5;border-radius:16px;padding:2rem;text-align:center;color:#991B1B;box-shadow:0 10px 25px rgba(220,38,38,0.1)">
                     <div style="font-size:2.5rem;margin-bottom:.8rem">⚠️</div>
                     <div style="font-weight:900;font-size:1rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem">${data.error}</div>`;

            if (data.error.includes("INVALID")) {
                errHtml += `<div style="font-size:.85rem;color:#7F1D1D;max-width:350px;margin:0 auto">Please provide a specific industry or technology name (e.g., "AI in Healthcare" instead of just "AI").</div>`;
            } else {
                errHtml += `<div style="font-size:.75rem;margin-top:.8rem;color:#7F1D1D;line-height:1.4">Our AI engine is currently throttled or disconnected. Update the <b>OPENAI_API_KEY</b> in your .env file to restore dynamic industry research.</div>`;
            }
            errHtml += `</div>`;
            c.innerHTML = errHtml;
            return;
        }

        if (data.is_fallback) {
            showToast("Using Expert Industry Lenses (AI Offline)", true);
        }

        activeReportId = data.report_id || 'MPI-' + Date.now();
        if (data.segments) {
            currentSegmentation = data.segments.map(function(s) {
                return {
                    name: s.name,
                    items: s.subsegments || s.items || []
                };
            });
            renderInteractiveSegments(c);
        } else {
            c.innerHTML = '<div class="seg-empty" style="color:red">Expert analysis failed. Please try a different market title.</div>';
        }
    } catch (e) {
        clearTimeout(segTimer);
        console.error(e);
        c.innerHTML = '<div class="seg-empty" style="color:red">Failed to generate AI segments. Check server connection.</div>';
    }
}

function renderInteractiveSegments(container) {
    if (!container) return;
    var h = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem"><h4 style="color:var(--navy)">Editable Segmentation Tree</h4><button onclick="addSegment()" style="font-size:0.75rem;padding:0.4rem 0.8rem;border:none;border-radius:6px;background:var(--gray-200);cursor:pointer">+ Add Segment</button></div>';
    currentSegmentation.forEach((s, sIdx) => {
        h += `<div class="segment-block" style="background:#fff;border:1px solid var(--gray-200);border-radius:12px;margin-bottom:1rem;overflow:hidden;transition:all 0.3s">
        <div style="background:var(--gray-50);padding:0.8rem 1rem;display:flex;justify-content:space-between;align-items:center;cursor:pointer" onclick="toggleSegTree(${sIdx})">
            <input type="text" value="${s.name}" onclick="event.stopPropagation()" onchange="updateSegName(${sIdx}, event.target.value)" style="font-weight:800;color:var(--navy);border:none;background:transparent;outline:none;width:80%">
            <span style="font-size:0.8rem;color:var(--accent)">↕ Expand</span>
        </div>
        <ul id="seg-tree-${sIdx}" style="padding:1rem;margin:0;list-style:none;border-top:1px solid var(--gray-100)">`;
        s.items.forEach((item, iIdx) => {
            h += `<li style="display:flex;align-items:center;margin-bottom:0.5rem;gap:0.5rem">
            <div style="width:6px;height:6px;border-radius:50%;background:var(--accent)"></div>
            <input type="text" value="${item}" onchange="updateSubName(${sIdx}, ${iIdx}, event.target.value)" style="flex:1;border:1px solid transparent;padding:0.2rem;border-radius:4px;outline:none;font-size:0.85rem">
            <button onclick="removeSub(${sIdx}, ${iIdx})" style="background:transparent;border:none;color:red;cursor:pointer;opacity:0.5">✕</button>
          </li>`;
        });
        h += `<li style="margin-top:0.5rem"><button onclick="addSub(${sIdx})" style="font-size:0.75rem;padding:0.2rem 0.6rem;border:1px solid var(--gray-200);border-radius:4px;background:#fff;cursor:pointer">+ Subsegment</button></li>
     </ul>
      </div>`;
    });
    container.innerHTML = h;
}

function toggleSegTree(idx) {
    var el = document.getElementById('seg-tree-' + idx);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function updateSegName(sIdx, val) {
    currentSegmentation[sIdx].name = val;
}

function updateSubName(sIdx, iIdx, val) {
    currentSegmentation[sIdx].items[iIdx] = val;
}

function addSub(sIdx) {
    currentSegmentation[sIdx].items.push("New Subsegment");
    renderInteractiveSegments(document.getElementById('segmentationLevels'));
}

function removeSub(sIdx, iIdx) {
    currentSegmentation[sIdx].items.splice(iIdx, 1);
    renderInteractiveSegments(document.getElementById('segmentationLevels'));
}

function addSegment() {
    currentSegmentation.push({
        name: "New Custom Segment",
        items: ["Custom Subsegment"]
    });
    renderInteractiveSegments(document.getElementById('segmentationLevels'));
}

function showToast(msg, isError = false) {
    const toast = document.createElement('div');
    toast.style.cssText = `position:fixed;bottom:2rem;right:2rem;padding:1rem 2rem;background:${isError ? '#F44336' : '#4CAF50'};color:white;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.2);z-index:10000;animation:fade 0.3s;font-weight:600;`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function showErrorToast(msg) {
    showToast(msg, true);
}

function toggleMobileMenu() {
    var hm = document.getElementById('mobileMenu');
    var hmb = document.querySelector('.hamburger');
    if (hm) hm.classList.toggle('open');
    if (hmb) hmb.classList.toggle('open');
}

function closeMobileMenu() {
    var hm = document.getElementById('mobileMenu');
    var hmb = document.querySelector('.hamburger');
    if (hm) hm.classList.remove('open');
    if (hmb) hmb.classList.remove('open');
}

function renderLandingPage(data) {
    if (data.site) {
        let n = document.querySelectorAll('.nav-name');
        n.forEach(el => el.innerHTML = data.site.name + '<span>| ' + data.site.tagline + '</span>');
        let footers = document.querySelectorAll('.footer');
        footers.forEach(f => {
            f.innerHTML = data.site.footer_text || ('© 2026 ' + data.site.name + ' · <a href="#">Privacy</a> · <a href="#">Terms</a>');
        });

        let ht = document.querySelector('.hero h1');
        if (ht) ht.innerHTML = data.site.hero_title || ht.innerHTML;
        let hs = document.querySelector('.hero-sub');
        if (hs) hs.textContent = data.site.hero_subtitle || hs.textContent;
        // document.title is set in the template
    }
}
