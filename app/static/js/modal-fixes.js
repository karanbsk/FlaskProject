// static/js/modal-fixes.js — Shared modal reset manager + create-user clearing

// static/js/modal-fixes.js — Shared modal reset manager + create-user clearing
(function () {
  // keys we consider sensitive and will redact
  const SENSITIVE_KEYS = new Set(['password','confirm_password','pwd','pass','token','auth']);

  function redact(obj) {
    // shallow/deep clone plain objects/arrays and replace sensitive values with [REDACTED]
    if (obj == null) return obj;
    if (typeof obj !== 'object') return obj;

    try {
      const clone = JSON.parse(JSON.stringify(obj)); // safe for plain JSON-able objects
      const walk = (o) => {
        if (!o || typeof o !== 'object') return;
        if (Array.isArray(o)) {
          o.forEach(item => walk(item));
          return;
        }
        Object.keys(o).forEach(k => {
          if (SENSITIVE_KEYS.has(k.toLowerCase())) {
            o[k] = '[REDACTED]';
          } else {
            walk(o[k]);
          }
        });
      };
      walk(clone);
      return clone;
    } catch (e) {
      // Non-serializable objects: don't attempt to redact deeply
      return '[UNLOGGABLE]';
    }
  }

  // small helper: sanitize a value if it's an object, else return as-is
  function sanitizeForLog(v) {
    if (v && typeof v === 'object') return redact(v);
    return v;
  }

  // DEV-only logger: change the hostname check if you run on a different dev host
  function isDev() {
    return location && (location.hostname === 'localhost' || location.hostname === '127.0.0.1');
  }

  function log(...args) {
    if (!(console && console.log)) return;
    if (!isDev()) return; // disable these logs outside local dev

    const safeArgs = args.map(a => sanitizeForLog(a));
    console.log('[modal-fixes]', ...safeArgs);
  }

  // lightweight app flash (fallback)
  function showGlobalFlash(message, category = 'info', timeout = 5000) {
    if (window.UIFlash && typeof window.UIFlash.show === 'function') {
      window.UIFlash.show(message, category, timeout);
      return;
    }
    try {
      const containerId = 'flash-container';
      let container = document.getElementById(containerId);
      if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.style.position = 'fixed';
        container.style.top = '1rem';
        container.style.right = '1rem';
        container.style.zIndex = 1080;
        document.body.appendChild(container);
      }
      const div = document.createElement('div');
      div.className = 'app-flash-item alert alert-' + category + ' alert-dismissible show';
      div.setAttribute('role', 'alert');
      div.innerHTML = (message || '') + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
      container.appendChild(div);
      setTimeout(() => { try { new bootstrap.Alert(div).close(); } catch (e) { div.remove(); } }, timeout);
    } catch (e) {
      log('showGlobalFlash failed', e);
    }
  }

  // ---------- inline error renderer ----------
  function renderInlineErrors(containerId, errors) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (!errors) return;
    if (typeof errors === 'string') {
      const div = document.createElement('div');
      div.className = 'alert alert-danger';
      div.innerText = errors;
      container.appendChild(div);
      return;
    }
    Object.keys(errors || {}).forEach(key => {
      const msgs = Array.isArray(errors[key]) ? errors[key] : [errors[key]];
      msgs.forEach(m => {
        const div = document.createElement('div');
        div.className = 'alert alert-danger';
        div.innerText = m;
        container.appendChild(div);
      });
    });
  }

  // ---------- clone-clean helper (used to defeat autofill on password inputs) ----------
  function cloneCleanInput(original) {
    if (!original || !original.cloneNode) return null;
    const clone = original.cloneNode(false); // shallow clone
    Array.from(original.attributes || []).forEach(attr => {
      if (attr.name === 'value' || attr.name === 'defaultValue') return;
      try { clone.setAttribute(attr.name, attr.value); } catch (e) {}
    });
    try { clone.setAttribute('autocomplete', 'new-password'); } catch (e) {}
    try { clone.value = ''; clone.defaultValue = ''; } catch (e) {}
    return clone;
  }

  // ---------- Clear functions ----------
  // aggressive clear for shared modal passwords (keeps same IDs)
  function clearPasswordsInSharedModal() {
    const modal = document.getElementById('sharedResetPasswordModal');
    const form = document.getElementById('sharedResetForm');
    if (!modal || !form) return;
    const origPw = document.getElementById('sharedNewPassword');
    const origCpw = document.getElementById('sharedConfirmPassword');
    const replaceList = [origPw, origCpw].filter(Boolean);

    replaceList.forEach(orig => {
      try {
        const parent = orig.parentNode;
        const clone = cloneCleanInput(orig);
        if (!clone || !parent) {
          try { orig.value = ''; if (orig.hasAttribute && orig.hasAttribute('value')) orig.removeAttribute('value'); orig.defaultValue = ''; orig.blur(); } catch (e) {}
          return;
        }
        parent.replaceChild(clone, orig);
        try { clone.blur(); } catch (e) {}
      } catch (e) {
        try { orig.value = ''; if (orig.hasAttribute && orig.hasAttribute('value')) orig.removeAttribute('value'); orig.defaultValue = ''; orig.blur(); } catch (e) {}
      }
    });

    // re-get and clear
    const pw = document.getElementById('sharedNewPassword');
    const cpw = document.getElementById('sharedConfirmPassword');
    [pw, cpw].forEach(i => { if (!i) return; try { i.value = ''; i.defaultValue = ''; i.blur(); i.setAttribute('autocomplete','new-password'); } catch (e) {} });

    setTimeout(() => { [pw, cpw].forEach(i => { if (!i) return; try { i.value=''; i.defaultValue=''; i.blur(); } catch (e) {} }); }, 120);
    setTimeout(() => { [pw, cpw].forEach(i => { if (!i) return; try { i.value=''; i.defaultValue=''; i.blur(); } catch (e) {} }); }, 400);
    setTimeout(() => { [pw, cpw].forEach(i => { if (!i) return; try { i.value=''; i.defaultValue=''; i.blur(); } catch (e) {} }); }, 800);
  }

  // generic form clear that handles text inputs + clones password inputs to defeat autofill
  function clearFormCompletely(formEl) {
    if (!formEl) return;
    try {
      // clear non-password fields
      formEl.querySelectorAll('input:not([type=password]), textarea, select').forEach(function (el) {
        try { el.value = ''; } catch (e) {}
        try { if (el.hasAttribute && el.hasAttribute('value')) el.removeAttribute('value'); } catch (e) {}
        try { el.defaultValue = ''; } catch (e) {}
        try { el.blur(); } catch (e) {}
      });

      // replace password inputs with clean clones
      const pwInputs = Array.from(formEl.querySelectorAll('input[type="password"]'));
      pwInputs.forEach(orig => {
        try {
          const parent = orig.parentNode;
          const clone = cloneCleanInput(orig);
          if (!clone || !parent) {
            // fallback clear
            try { orig.value = ''; if (orig.hasAttribute && orig.hasAttribute('value')) orig.removeAttribute('value'); orig.defaultValue = ''; orig.blur(); } catch (e) {}
            return;
          }
          parent.replaceChild(clone, orig);
          try { clone.blur(); } catch (e) {}
        } catch (e) {
          try { orig.value = ''; if (orig.hasAttribute && orig.hasAttribute('value')) orig.removeAttribute('value'); orig.defaultValue = ''; orig.blur(); } catch (e) {}
        }
      });

      // final deferred clears for safety
      setTimeout(() => {
        formEl.querySelectorAll('input, textarea, select').forEach(function (el) {
          try { el.value = ''; } catch (e) {}
          try { if (el.hasAttribute && el.hasAttribute('value')) el.removeAttribute('value'); } catch (e) {}
          try { el.defaultValue = ''; } catch (e) {}
          try { el.blur(); } catch (e) {}
        });
      }, 150);

      setTimeout(() => {
        formEl.querySelectorAll('input, textarea, select').forEach(function (el) {
          try { el.value = ''; } catch (e) {}
          try { el.defaultValue = ''; } catch (e) {}
          try { el.blur(); } catch (e) {}
        });
      }, 450);
    } catch (e) {
      log('clearFormCompletely failed', e);
    }
  }

  // ---------- generic JSON submit helper (used by createUserForm and sharedResetForm) ----------
  async function submitJsonForm(form) {
    try {
      const action = form.getAttribute('action') || window.location.href;
      const method = (form.getAttribute('method') || 'POST').toUpperCase();
      const fd = new FormData(form);
      const payload = {};
      for (const [k, v] of fd.entries()) payload[k] = v;

      log('submitJsonForm invoked for', form, 'payload:', payload, 'action:', action);

      const resp = await fetch(action, {
        method: method,
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      log('Response status:', resp.status);

      if (resp.ok) {
        let data = {};
        try { data = await resp.json(); } catch (e) {}
        const message = data.message || 'Success';
        // hide modal if relevant and reload for create user
        if (form.id === 'sharedResetForm') {
          const modalEl = document.getElementById('sharedResetPasswordModal');
          try { bootstrap.Modal.getInstance(modalEl)?.hide(); } catch (e) {}
        }
        if (form.id === 'createUserForm') {
          try { bootstrap.Modal.getInstance(document.getElementById('createUserModal'))?.hide(); } catch (e) {}
          setTimeout(() => { location.reload(); }, 700);
        }
        showGlobalFlash(message, 'success', 4000);
        return;
      }

      if (resp.status === 422) {
        let data = {};
        try { data = await resp.json(); } catch (e) { log('422 no json'); }
        if (form.id === 'sharedResetForm') {
          renderInlineErrors('sharedResetInlineErrors', data.errors || data.message || 'Validation failed');
        } else if (form.id === 'createUserForm') {
          // display inline errors inside create modal if present
          if (data.errors) {
            // map errors to input fields
            Object.keys(data.errors).forEach(field => {
              const input = form.querySelector('[name="' + field + '"]');
              if (input) {
                input.classList.add('is-invalid');
                const el = document.createElement('div');
                el.className = 'field-error invalid-feedback';
                el.innerText = Array.isArray(data.errors[field]) ? data.errors[field][0] : data.errors[field];
                if (input.nextSibling) input.parentNode.insertBefore(el, input.nextSibling);
                else input.parentNode.appendChild(el);
              } else {
                showGlobalFlash(Array.isArray(data.errors[field]) ? data.errors[field][0] : data.errors[field], 'danger', 7000);
              }
            });
          }
          if (data.message) showGlobalFlash(data.message, 'danger', 7000);
        } else {
          showGlobalFlash(data.message || 'Validation failed', 'danger', 7000);
        }
        return;
      }

      const txt = await resp.text();
      showGlobalFlash(txt || ('Request failed: ' + resp.status), 'danger', 7000);
    } catch (e) {
      log('submitJsonForm caught', e);
      showGlobalFlash('Unexpected error. See console.', 'danger', 7000);
    }
  }

  // ---------- renderFieldErrors helper (small) ----------
  function clearFormFieldErrors(form) {
    if (!form) return;
    form.querySelectorAll('.field-error').forEach(function (el) { el.remove(); });
    form.querySelectorAll('.is-invalid').forEach(function (inp) { inp.classList.remove('is-invalid'); });
  }

  // ---------- DOM wiring ----------
  document.addEventListener('DOMContentLoaded', function () {
    // createUserForm submit
    const createForm = document.getElementById('createUserForm');
    if (createForm) {
      log('Attached JSON submit to createUserForm');
      createForm.addEventListener('submit', function (ev) {
        ev.preventDefault();
        // clear any previous inline errors before submit
        clearFormFieldErrors(createForm);
        // defensive: clear visible fields (so there is no lingering visual)
        //clearFormCompletely(createForm);
        submitJsonForm(createForm);
      });
    }

    // delete-user handler
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

    // shared-reset modal open: attach click for open buttons
    document.body.addEventListener('click', function (ev) {
      const btn = ev.target.closest('.js-open-reset-modal');
      if (!btn) return;
      const userId = btn.getAttribute('data-user-id');
      const userLabel = btn.getAttribute('data-user-label') || 'user';
      // record opener to restore focus after close
      window.__lastResetOpener = btn;

      // populate hidden input + title
      const uid = document.getElementById('sharedResetUserId');
      const title = document.getElementById('sharedResetTitle');
      if (uid) uid.value = userId;
      if (title) title.textContent = 'Reset Password for ' + userLabel;

      // clear inline errors and password fields
      renderInlineErrors('sharedResetInlineErrors', null);
      clearPasswordsInSharedModal();
      // allow bootstrap to open the modal via data-bs-target
    }, false);

    // capture-phase listener: move focus out BEFORE Bootstrap hides modal to avoid aria-hidden focus issues
    if (!window.__modalSharedCaptureInstalled) {
      document.body.addEventListener('click', function (ev) {
        const dismissBtn = ev.target.closest('[data-bs-dismiss="modal"]');
        if (!dismissBtn) return;
        const modalEl = dismissBtn.closest('#sharedResetPasswordModal, .modal');
        if (!modalEl) return;
        try {
          if (window.__lastResetOpener && typeof window.__lastResetOpener.focus === 'function') {
            window.__lastResetOpener.focus();
          } else {
            try { document.body.focus(); } catch (e) {}
          }
          log('Moved focus out of modal before hide for', modalEl.id || '(no id)');
        } catch (e) { log('Error moving focus before modal hide', e); }
      }, true); // capture
      window.__modalSharedCaptureInstalled = true;
    }

    // attach shared modal shown/hidden events
    const sharedModalEl = document.getElementById('sharedResetPasswordModal');
    if (sharedModalEl) {
      sharedModalEl.addEventListener('shown.bs.modal', function () {
        clearPasswordsInSharedModal();
      });
      sharedModalEl.addEventListener('hidden.bs.modal', function () {
        clearPasswordsInSharedModal();
        renderInlineErrors('sharedResetInlineErrors', null);
        try {
          if (window.__lastResetOpener && typeof window.__lastResetOpener.focus === 'function') {
            window.__lastResetOpener.focus();
          } else {
            try { document.body.focus(); } catch (e) {}
          }
        } catch (e) {}
      });
    }

    // attach submit for shared reset form
    const sharedForm = document.getElementById('sharedResetForm');
    if (sharedForm) {
      sharedForm.addEventListener('submit', function (ev) {
        ev.preventDefault();
        // defensive: capture current field values
        const uid = document.getElementById('sharedResetUserId').value;
        const newPwEl = document.getElementById('sharedNewPassword');
        const confPwEl = document.getElementById('sharedConfirmPassword');
        const newPw = newPwEl ? newPwEl.value : '';
        const confPw = confPwEl ? confPwEl.value : '';

        // clear visible fields right away to avoid leftover visuals
        clearPasswordsInSharedModal();

        if (!uid) {
          renderInlineErrors('sharedResetInlineErrors', 'Target user missing');
          return;
        }

        (async function () {
          try {
            const resp = await fetch(`/api/users/${uid}/reset_password`, {
              method: 'POST',
              headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
              body: JSON.stringify({ new_password: newPw, confirm_password: confPw })
            });

            if (resp.ok) {
              const data = await resp.json().catch(() => ({}));
              try { bootstrap.Modal.getInstance(sharedModalEl)?.hide(); } catch (e) {}
              showGlobalFlash(data.message || 'Password reset', 'success', 4000);
              return;
            }

            if (resp.status === 422) {
              const data = await resp.json().catch(() => ({}));
              renderInlineErrors('sharedResetInlineErrors', data.errors || data.message || 'Validation failed');
              return;
            }

            const txt = await resp.text();
            renderInlineErrors('sharedResetInlineErrors', txt || ('Request failed: ' + resp.status));
          } catch (e) {
            log('shared reset request failed', e);
            renderInlineErrors('sharedResetInlineErrors', 'Network error');
          }
        })();
      });
    }

    // NEW: wire createUserModal shown/hidden to clear the create form (fixes Add User modal autofill / leftover values)
    const createModalEl = document.getElementById('createUserModal');
    const createFormEl = document.getElementById('createUserForm');
    if (createModalEl && createFormEl) {
      createModalEl.addEventListener('shown.bs.modal', function () {
        // clear fields aggressively when create modal is shown
        clearFormCompletely(createFormEl);
        // small extra delayed clear
        setTimeout(() => clearFormCompletely(createFormEl), 120);
      });
      createModalEl.addEventListener('hidden.bs.modal', function () {
        // clear when hidden as well
        clearFormCompletely(createFormEl);
        clearFormFieldErrors(createFormEl);
      });

      // Optional: ensure Cancel inside create modal triggers clear immediately
      createModalEl.addEventListener('click', function (ev) {
        const btn = ev.target.closest('[data-action="reset-modal"], [data-bs-dismiss="modal"]');
        if (!btn) return;
        // only act if inside create modal
        if (!createModalEl.contains(btn)) return;
        // do a quick clear
        clearFormCompletely(createFormEl);
        clearFormFieldErrors(createFormEl);
        log('Cancel clicked inside createUserModal -> cleared create form');
      }, false);
    }

  }); // DOMContentLoaded end

  // expose for debugging
  window.ModalFixes = { showGlobalFlash, clearPasswordsInSharedModal, clearFormCompletely };
})(); 
