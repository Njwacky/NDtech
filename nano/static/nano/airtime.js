(() => {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  function setResult(el, ok, msg) {
    if (!el) return;
    el.classList.remove('ok', 'err');
    el.classList.add(ok ? 'ok' : 'err');
    el.textContent = msg;
    el.style.display = 'block';
  }

  async function postJson(url, payload) {
    const csrftoken = getCookie('csrftoken');
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrftoken ? { 'X-CSRFToken': csrftoken } : {}),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify(payload),
      credentials: 'same-origin',
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.error || `HTTP ${resp.status}`);
    }
    return data;
  }

  function wireDashboardSaleForm() {
    const form = document.getElementById('airtimeSaleForm');
    if (!form) return;

    const result = document.getElementById('airtimeSaleResult');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const productId = fd.get('product_id');
      const customerPhone = (fd.get('customer_phone') || '').toString().trim();
      const quantity = Number(fd.get('quantity') || 1);

      if (!productId) return setResult(result, false, 'Please select a product.');
      if (!customerPhone) return setResult(result, false, 'Customer phone is required.');

      try {
        const data = await postJson('/airtime/process/', {
          product_id: Number(productId),
          customer_phone: customerPhone,
          quantity: Number.isFinite(quantity) && quantity > 0 ? quantity : 1,
        });
        setResult(result, true, data?.message || 'Sale processed.');
        form.reset();
      } catch (err) {
        setResult(result, false, err?.message || 'Failed to process sale.');
      }
    });
  }

  function wireVerifyPhoneButtons() {
    const btns = document.querySelectorAll('.js-verify-phone');
    if (!btns.length) return;

    btns.forEach((btn) => {
      btn.addEventListener('click', async () => {
        const saleId = btn.getAttribute('data-sale-id');
        if (!saleId) return;

        const confirmedPhone = window.prompt('Enter confirmed phone number (10-15 digits):');
        if (!confirmedPhone) return;

        try {
          const data = await postJson(`/airtime/verify-phone/${saleId}/`, {
            confirmed_phone: confirmedPhone.trim(),
            customer_confirmed: true,
          });
          window.alert(data?.message || 'Verified.');
          window.location.reload();
        } catch (err) {
          window.alert(err?.message || 'Verification failed.');
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    wireDashboardSaleForm();
    wireVerifyPhoneButtons();
  });
})();

