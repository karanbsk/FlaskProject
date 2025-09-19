// static/js/modal-fixes.js
(function () {
  function log(...args) {
    if (window && window.console && typeof console.log === 'function') console.log('[modal-fixes]', ...args);
  }

  function showGlobalFlash(message, category = 'info', timeout = 5000) {
    if (window.UIFlash && typeof window.UIFlash.show === 'function') {
      window.UIFlash.show(message, category, timeout);
      return;
    }
    try {
      const container = document.getElementById('flash-container');
      if (!container) return;
      const div = document.createElement('div');
      div.className = 'app-flash-item alert alert-' + category + ' alert-dismissible show';
      div.setAttribute('role', 'alert');
      div.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
      container.appendChild(div);
      setTimeout(() => { try { new bootstrap.Alert(div).close(); } catch (e) { div.remove(); } }, timeout);
    } catch (e) {
      log('showGlobalFlash fallback failed', e);
    }
  }

  function clearFormFieldErrors(form) {
    form.querySelectorAll('.field-error').forEach(function (el) { el.remove(); });
    form.querySelectorAll('.is-invalid').forEach(function (inp) { inp.classList.remove('is-invalid'); });
  }

  // Only render inline errors if the form allows it (data-inline-errors !== "false")
  function renderFieldErrors(form, errors) {
    if (form && form.dataset && form.dataset.inlineErrors === 'false') {
      // Don't render inline errors for this form — convert to global flash(s)
      // pick first error message to show globally
      try {
        const firstField = Object.keys(errors || {})[0];
        const firstMsg = Array.isArray(errors[firstField]) ? errors[firstField][0] : errors[firstField];
        showGlobalFlash(firstMsg || 'Validation failed', 'danger', 7000);
      } catch (e) {
        showGlobalFlash('Validation failed', 'danger', 7000);
      }
      return;
    }

    // default behavior: show inline feedback beside fields
    clearFormFieldErrors(form);
    Object.keys(errors || {}).forEach(field => {
      const input = form.querySelector('[name="' + field + '"]');
      const msg = Array.isArray(errors[field]) ? errors[field][0] : errors[field];
      if (input) {
        input.classList.add('is-invalid');
        const el = document.createElement('div');
        el.className = 'field-error invalid-feedback';
        el.innerText = msg;
        if (input.nextSibling) input.parentNode.insertBefore(el, input.nextSibling);
        else input.parentNode.appendChild(el);
      } else {
        showGlobalFlash(msg, 'danger', 7000);
      }
    });
  }

  async function submitJsonForm(form) {
    try {
      const action = form.getAttribute('action') || window.location.href;
      const method = (form.getAttribute('method') || 'POST').toUpperCase();

      const fd = new FormData(form);
      const payload = {};
      for (const [k, v] of fd.entries()) payload[k] = v;

      log('submitJsonForm invoked for', form, 'Payload:', payload, 'action:', action);

      const resp = await fetch(action, {
        method: method,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      log('Response status:', resp.status);

      if (resp.ok) {
        let data = {};
        try { data = await resp.json(); } catch (e) { /* no json */ }
        const message = data.message || 'Success';

        // close modal if present
        const modalEl = form.closest('.modal');
        if (modalEl && window.bootstrap && bootstrap.Modal) {
          try {
            const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
            bsModal.hide();
          } catch (e) { log('modal hide fail', e); }
        }

        showGlobalFlash(message, 'success', 5000);

        // If this is the Create User form, refresh the users table so the new user appears
        if (form.id === 'createUserForm') {
          // short delay so user sees the flash before reload
          setTimeout(() => { location.reload(); }, 900);
        }

        return;
      }

      if (resp.status === 422) {
        let data = {};
        try { data = await resp.json(); } catch (e) { log('422 but no JSON'); }
        if (data.errors) {
          renderFieldErrors(form, data.errors);
        }
        if (data.message) {
          showGlobalFlash(data.message, 'danger', 7000);
        }
        return;
      }

      let errText = await resp.text();
      try {
        const parsed = JSON.parse(errText);
        if (parsed.message) errText = parsed.message;
      } catch (e) {}
      showGlobalFlash(errText || ('Request failed: ' + resp.status), 'danger', 7000);

    } catch (e) {
      log('submitJsonForm caught', e);
      showGlobalFlash('Unexpected error. See console.', 'danger', 7000);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const createForm = document.getElementById('createUserForm');
    if (createForm) {
      log('Attached JSON submit to createUserForm');
      createForm.addEventListener('submit', function (ev) {
        ev.preventDefault();
        submitJsonForm(createForm);
      });
    }

    document.querySelectorAll('form.reset-password-form').forEach(function (form) {
      log('Attached JSON submit to reset form', form);
      form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        submitJsonForm(form);
      });
    });

    document.body.addEventListener('click', function (ev) {
      const btn = ev.target.closest('.js-delete-user-btn');
      if (!btn) return;
      ev.preventDefault();
      const userId = btn.getAttribute('data-user-id');
      const confirmMsg = btn.getAttribute('data-confirm') || 'Are you sure?';
      if (!confirm(confirmMsg)) return;

      const action = `/api/users/${userId}`;
      log('Deleting user', userId);
      fetch(action, { method: 'DELETE', headers: { 'Accept': 'application/json' } })
        .then(async function (resp) {
          if (resp.ok) {
            let data = {};
            try { data = await resp.json(); } catch (e) {}
            const message = data.message || 'User deleted';
            const row = btn.closest('tr');
            if (row && row.parentNode) row.parentNode.removeChild(row);
            showGlobalFlash(message, 'success', 4000);
            return;
          }
          if (resp.status === 422) {
            const data = await resp.json();
            showGlobalFlash(data.message || 'Validation failed', 'danger', 6000);
            return;
          }
          const text = await resp.text();
          showGlobalFlash(text || ('Delete failed: ' + resp.status), 'danger', 6000);
        })
        .catch(function (err) {
          log('Delete request failed', err);
          showGlobalFlash('Network error deleting user', 'danger', 7000);
        });
    }, false);
  });

  window.ModalFixes = { showGlobalFlash };
})();
