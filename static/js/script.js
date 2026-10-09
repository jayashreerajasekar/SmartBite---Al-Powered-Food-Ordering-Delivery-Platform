/*
 * script.js
 * ---------
 * Small browser-side helpers. All the important business logic (prices,
 * discounts, orders) lives in Python - this file only handles things a
 * browser must do locally: opening the food customization modal, live
 * updating the "ADD TO CART" price preview, and toggling favorite icons
 * without a full page reload.
 */

let currentModalUnitPrice = 0;
let currentModalQty = 1;

function openFoodModal(button) {
    const data = button.dataset;
    document.getElementById('foodModalTitle').textContent = data.name;
    document.getElementById('foodModalImage').src = data.image;
    document.getElementById('foodModalDesc').textContent = data.desc;
    document.getElementById('foodModalCalories').textContent = '🔥 ' + data.calories + ' kcal';
    document.getElementById('foodModalPrep').textContent = '⏱ ' + data.prep + ' min';
    document.getElementById('foodModalRating').textContent = '⭐ ' + data.rating;

    currentModalUnitPrice = parseInt(data.price, 10);
    currentModalQty = 1;
    document.getElementById('foodModalQty').textContent = currentModalQty;
    document.getElementById('foodModalQtyInput').value = currentModalQty;

    // Reset size/extras from any previous selection
    document.getElementById('sizeRegular').checked = true;
    document.querySelectorAll('#foodModalForm input[name="extras"]').forEach(cb => cb.checked = false);

    const form = document.getElementById('foodModalForm');
    if (window.RSB_ADD_TO_CART_URL_BASE) {
        form.action = window.RSB_ADD_TO_CART_URL_BASE + '/' + data.id;
    }

    updateModalPrice();

    document.querySelectorAll('#foodModalForm input[type=radio], #foodModalForm input[type=checkbox]')
        .forEach(el => el.addEventListener('change', updateModalPrice));

    const modal = new bootstrap.Modal(document.getElementById('foodModal'));
    modal.show();
}

function updateModalPrice() {
    let price = currentModalUnitPrice;
    const sizeLarge = document.getElementById('sizeLarge');
    if (sizeLarge && sizeLarge.checked) { price += 60; }

    const extrasPriceMap = { 'Extra Cheese': 40, 'Extra Chicken': 80, 'Extra Sauce': 20 };
    document.querySelectorAll('#foodModalForm input[name="extras"]:checked').forEach(cb => {
        price += extrasPriceMap[cb.value] || 0;
    });

    const total = price * currentModalQty;
    const totalEl = document.getElementById('foodModalTotalPrice');
    if (totalEl) { totalEl.textContent = total; }
}

function changeModalQty(delta) {
    currentModalQty = Math.max(1, currentModalQty + delta);
    document.getElementById('foodModalQty').textContent = currentModalQty;
    document.getElementById('foodModalQtyInput').value = currentModalQty;
    updateModalPrice();
}

function toggleFavRestaurant(restaurantId, el) {
    fetch(`/favorite/restaurant/${restaurantId}`, { method: 'POST' })
        .then(res => {
            if (res.status === 302 || res.redirected) {
                window.location.href = '/login';
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (!data) return;
            if (el.tagName === 'BUTTON' && el.classList.contains('rsb-fav-btn')) {
                el.textContent = data.is_favorite ? '❤️' : '🤍';
                el.classList.toggle('active', data.is_favorite);
            } else {
                el.textContent = data.is_favorite ? '❤️ Saved to Favorites' : '🤍 Add to Favorites';
            }
        })
        .catch(() => {});
}
