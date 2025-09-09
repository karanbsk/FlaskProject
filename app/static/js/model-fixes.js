document.addEventListener('DOMContentLoaded', function () {
  const modalEl = document.getElementById('createUserModal');
  if (!modalEl) return;

  modalEl.addEventListener('click', function (ev) {
    const btn = ev.target.closest('[data-action="reset-modal"]');
    if (btn) {
      const form = modalEl.querySelector('#createUserForm');
      if (form) form.reset();

      // clear validation/error classes
      modalEl.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
      modalEl.querySelectorAll('.invalid-feedback').forEach(el => (el.textContent = ''));

      // remove server-rendered alerts inside modal
      modalEl.querySelectorAll('.alert').forEach(el => el.remove());
    }
  });
});
