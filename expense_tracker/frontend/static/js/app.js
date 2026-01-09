const API_URL = 'http://127.0.0.1:8000/api';

document.addEventListener('DOMContentLoaded', () => {

  // --- DOM elements ---
  const expensesListEl = document.getElementById('expensesList');
  const totalEl = document.getElementById('Total');
  const totalCountEl = document.getElementById('totalCount');
  const expenseForm = document.getElementById('expenseForm');
  const submitBtn = document.getElementById('submitBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  const dateInput = document.getElementById('date');
  const startDate = document.getElementById('startDate');
  const endDate = document.getElementById('endDate');
  const applyBtn = document.getElementById('applyFilters');
  const syncStatusEl = document.getElementById('syncStatus');

  // --- Set default dates ---
  dateInput.valueAsDate = new Date();
  const today = new Date();
  startDate.valueAsDate = new Date(today.getFullYear(), today.getMonth(), 1);
  endDate.valueAsDate = today;

  // --- Form submit: create / update ---
  expenseForm.addEventListener('submit', async e => {
    e.preventDefault();

    const id = document.getElementById('expenseId').value;
    const payload = {
      amount: parseFloat(document.getElementById('amount').value),
      description: document.getElementById('description').value,
      date: dateInput.value
    };

    try {
      if (id) {
        // update
        await fetch(`${API_URL}/expenses/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else {
        // create
        await fetch(`${API_URL}/expenses`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      resetForm();
      await loadExpenses(true);
    } catch (err) {
      console.error(err);
      alert('Error saving expense: ' + (err.message || err));
    }
  });

  // --- Apply date filters ---
  if (applyBtn) {
    applyBtn.addEventListener('click', () => loadExpenses(true));
  }

  // --- Load expenses from API ---
  async function loadExpenses(useBackendFilters = false) {
    try {
      let url = `${API_URL}/expenses`;
      if (useBackendFilters) {
        const params = new URLSearchParams();
        if (startDate.value) params.append('start_date', startDate.value);
        if (endDate.value) params.append('end_date', endDate.value);
        url += `?${params.toString()}`;
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to load expenses');
      const expenses = await res.json();
      renderExpenses(expenses);
    } catch (err) {
      console.error(err);
    }
  }

  // --- Render expenses table ---
  function renderExpenses(expenses) {
    expensesListEl.innerHTML = '';

    if (!expenses.length) {
      expensesListEl.innerHTML = '<tr><td colspan="4">No expenses yet</td></tr>';
      totalEl.textContent = '0 RWF';
      totalCountEl.textContent = '0';
      return;
    }

    let total = 0;

    expenses.forEach(exp => {
      const tr = document.createElement('tr');
      const amount = Number(exp.amount || 0);
      total += amount;

      const dateText = exp.created_at ? new Date(exp.created_at).toLocaleDateString() : '-';
      const isMomo = exp.description?.toLowerCase().includes('momo');
      if (isMomo) tr.classList.add('momo-expense');

      tr.innerHTML = `
        <td>${dateText}</td>
        <td>${escapeHtml(exp.description)}</td>
        <td class="right">${amount.toLocaleString()} RWF</td>
        <td>
          <button class="btn btn-edit" onclick="editExpense(${exp.expense_id})">Edit</button>
          <button class="btn btn-danger" onclick="deleteExpense(${exp.expense_id})">Delete</button>
        </td>
      `;
      expensesListEl.appendChild(tr);
    });

    totalEl.textContent = total.toLocaleString() + ' RWF';
    totalCountEl.textContent = expenses.length;
  }

  // --- Edit expense ---
  window.editExpense = async id => {
    try {
      const res = await fetch(`${API_URL}/expenses/${id}`);
      if (!res.ok) throw new Error('Failed to load expense');
      const exp = await res.json();

      document.getElementById('expenseId').value = exp.expense_id;
      document.getElementById('amount').value = exp.amount;
      document.getElementById('description').value = exp.description;
      if (exp.created_at) dateInput.value = exp.created_at.split('T')[0];

      document.getElementById('formTitle').textContent = 'Edit Expense';
      submitBtn.textContent = 'Update Expense';
      cancelBtn.style.display = 'inline-block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error(err);
      alert('Could not load expense');
    }
  };

  // --- Delete expense ---
  window.deleteExpense = async id => {
    if (!confirm('Are you sure you want to delete this expense?')) return;
    try {
      const res = await fetch(`${API_URL}/expenses/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      await loadExpenses(true);
    } catch (err) {
      console.error(err);
      alert('Could not delete expense');
    }
  };

  // --- Reset form ---
  window.resetForm = () => {
    expenseForm.reset();
    document.getElementById('expenseId').value = '';
    dateInput.valueAsDate = new Date();
    document.getElementById('formTitle').textContent = 'Add New Expense';
    submitBtn.textContent = 'Add Expense';
    cancelBtn.style.display = 'none';
  };

  // --- Helpers ---
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"'`=\/]/g, s => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','/':'&#x2F;','`':'&#x60;','=':'&#x3D;'
    })[s]);
  }

  // --- Initial load ---
  loadExpenses(true);

  // --- MoMo live sync ---
  let lastExpenseCount = 0;
  setInterval(async () => {
    try {
      const res = await fetch(`${API_URL}/expenses`);
      if (!res.ok) return;
      const expenses = await res.json();
      if (expenses.length > lastExpenseCount) {
        lastExpenseCount = expenses.length;
        if (syncStatusEl) syncStatusEl.textContent = '📡 New MoMo transaction received';
        renderExpenses(expenses);
      }
    } catch (err) {
      console.error('MoMo sync error', err);
    }
  }, 5000);

});
