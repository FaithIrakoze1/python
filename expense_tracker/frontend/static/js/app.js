(function () {
    const API_URL = 'http://127.0.0.1:8000/api';

    // UI elements
    const categorySelect = document.getElementById('category');
    const filterCategory = document.getElementById('filterCategory');
    const periodSelect = document.getElementById('period');
    const expensesListEl = document.getElementById('expensesList');

    document.getElementById('date').valueAsDate = new Date();

    document.addEventListener('DOMContentLoaded', () => {
      loadCategories().then(() => {
        loadExpenses();
        loadSummary();
      });
    });

    // Load categories from backend and populate selects
    async function loadCategories() {
      try {
        const res = await fetch(`${API_URL}/categories`);
        if (!res.ok) throw new Error('Failed to load categories');
        const categories = await res.json();

        // reset selects
        categorySelect.innerHTML = '';
        filterCategory.innerHTML = '<option value="">All Categories</option>';

        // add a placeholder
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = 'Select category';
        placeholder.disabled = true;
        placeholder.selected = true;
        categorySelect.appendChild(placeholder);

        categories.forEach(cat => {
          const option = document.createElement('option');
          option.value = cat.name; // send name to backend
          option.textContent = cat.name;
          categorySelect.appendChild(option);

          const filterOption = document.createElement('option');
          filterOption.value = cat.name;
          filterOption.textContent = cat.name;
          filterCategory.appendChild(filterOption);
        });
      } catch (err) {
        console.error(err);
        categorySelect.innerHTML = '<option value="">Error loading categories</option>';
      }
    }

    // Create or update expense
    document.getElementById('expenseForm').addEventListener('submit', async function (e) {
      e.preventDefault();

      const id = document.getElementById('expenseId').value;
      const payload = {
        amount: parseFloat(document.getElementById('amount').value),
        description: document.getElementById('description').value,
        category: document.getElementById('category').value
      };

      // date is optional for backend (server sets created_at), but we keep it for UI
      const dateVal = document.getElementById('date').value;
      if (dateVal) payload.date = dateVal;

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
        await loadExpenses();
        await loadSummary();
      } catch (err) {
        alert('Error saving expense: ' + (err.message || err));
        console.error(err);
      }
    });

    // Load expenses from API and render table (with filtering & period)
    async function loadExpenses() {
      try {
        const res = await fetch(`${API_URL}/expenses`);
        if (!res.ok) throw new Error('Failed to load expenses');
        let expenses = await res.json();

        // Normalize category info:
        // Some APIs return { category_id } only, others include nested category { name }.
        // Ensure each expense has: expense_id, amount, description, created_at, categoryName
        expenses = expenses.map(exp => {
          const categoryName = exp.category?.name ?? exp.category_name ?? exp.category ?? null;
          const createdAt = exp.created_at ?? exp.date ?? exp.createdAt ?? null;
          return {
            ...exp,
            categoryName,
            created_at: createdAt,
          };
        });

        // Apply filter by category
        const categoryFilter = filterCategory.value;
        if (categoryFilter) {
          expenses = expenses.filter(e => e.categoryName === categoryFilter);
        }

        // Apply period filtering
        const period = periodSelect.value;
        const now = new Date();
        expenses = expenses.filter(e => {
          if (!e.created_at) return true; // if no date, keep it
          const d = new Date(e.created_at);
          if (period === 'this_month') {
            return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
          } else if (period === 'this_year') {
            return d.getFullYear() === now.getFullYear();
          } else if (period === 'this_week') {
            const oneJan = new Date(now.getFullYear(),0,1);
            const nowWeek = Math.ceil((((now - oneJan) / 86400000) + oneJan.getDay()+1)/7);
            const dWeek = Math.ceil((((d - oneJan) / 86400000) + oneJan.getDay()+1)/7);
            return now.getFullYear() === d.getFullYear() && nowWeek === dWeek;
          }
          return true;
        });

        renderExpenses(expenses);
      } catch (err) {
        console.error('Error loading expenses:', err);
        expensesListEl.innerHTML = '<tr><td colspan="5">Error loading expenses</td></tr>';
      }
    }

    // Render rows
    function renderExpenses(expenses) {
      expensesListEl.innerHTML = '';

      if (!expenses.length) {
        expensesListEl.innerHTML = '<tr><td colspan="5">No expenses yet</td></tr>';
        document.getElementById('totalCount').textContent = '0';
        document.getElementById('monthlyTotal').textContent = '0 RWF';
        document.getElementById('weeklyTotal').textContent = '0 RWF';
        document.getElementById('yearlyTotal').textContent = '0 RWF';
        return;
      }

      expenses.forEach(exp => {
        const tr = document.createElement('tr');

        const dateText = exp.created_at ? new Date(exp.created_at).toLocaleDateString() : '-';
        const desc = exp.description ?? '';
        const amount = Number(exp.amount ?? 0);

        const catName = exp.categoryName ?? (() => {
          // try category_id lookup: we'll simply show category_id if no name
          return exp.category_id ? `#${exp.category_id}` : 'Uncategorized';
        })();

        tr.innerHTML = `
          <td>${dateText}</td>
          <td>${escapeHtml(desc)}</td>
          <td><span class="category-badge category-${escapeCssClass(catName)}">${escapeHtml(catName)}</span></td>
          <td class="right">${amount.toLocaleString()} RWF</td>
          <td>
            <button class="btn btn-edit" onclick="window.editExpense(${exp.expense_id})">Edit</button>
            <button class="btn btn-danger" onclick="window.deleteExpense(${exp.expense_id})">Delete</button>
          </td>
        `;
        expensesListEl.appendChild(tr);
      });

      // update counts + totals
      const totalCount = expenses.length;
      const totalMonthly = calcPeriodTotal(expenses, 'month');
      const totalWeekly = calcPeriodTotal(expenses, 'week');
      const totalYearly = calcPeriodTotal(expenses, 'year');

      document.getElementById('totalCount').textContent = totalCount;
      document.getElementById('monthlyTotal').textContent = formatCurrency(totalMonthly);
      document.getElementById('weeklyTotal').textContent = formatCurrency(totalWeekly);
      document.getElementById('yearlyTotal').textContent = formatCurrency(totalYearly);
    }

    // Helpers: calculate period totals from the current (already filtered) expense list
    function calcPeriodTotal(expenses, period) {
      const now = new Date();
      return expenses.reduce((sum, e) => {
        if (!e.created_at) return sum;
        const d = new Date(e.created_at);
        if (period === 'month') {
          if (d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()) return sum + Number(e.amount || 0);
          return sum;
        } else if (period === 'week') {
          const start = startOfWeek(now);
          const end = new Date(start); end.setDate(end.getDate() + 7);
          if (d >= start && d < end) return sum + Number(e.amount || 0);
          return sum;
        } else if (period === 'year') {
          if (d.getFullYear() === now.getFullYear()) return sum + Number(e.amount || 0);
          return sum;
        }
        return sum;
      }, 0);
    }

    function startOfWeek(date) {
      const d = new Date(date);
      const day = d.getDay(); // 0..6
      const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Monday-start
      return new Date(d.setDate(diff));
    }

    function formatCurrency(n) {
      return Number(n || 0).toLocaleString() + ' RWF';
    }

    // Expose edit/delete for inline buttons
    window.editExpense = async function (id) {
      try {
        const res = await fetch(`${API_URL}/expenses/${id}`);
        if (!res.ok) throw new Error('Failed to load expense');
        const exp = await res.json();

        document.getElementById('expenseId').value = exp.expense_id;
        document.getElementById('amount').value = exp.amount;
        document.getElementById('description').value = exp.description;
        // set categorySelect by name (if provided) or by id lookup
        const catName = exp.category?.name ?? exp.category_name ?? exp.category ?? null;
        if (catName) categorySelect.value = catName;

        document.getElementById('formTitle').textContent = 'Edit Expense';
        document.getElementById('submitBtn').textContent = 'Update Expense';
        document.getElementById('cancelBtn').style.display = 'inline-block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (err) {
        console.error(err);
        alert('Could not load expense');
      }
    };

    window.deleteExpense = async function (id) {
      if (!confirm('Are you sure you want to delete this expense?')) return;
      try {
        const res = await fetch(`${API_URL}/expenses/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');
        await loadExpenses();
        await loadSummary();
      } catch (err) {
        console.error(err);
        alert('Could not delete expense');
      }
    };

    // Summary: fetch expenses and compute totals (fallback if API summary endpoints not used)
    async function loadSummary() {
      try {
        const res = await fetch(`${API_URL}/expenses`);
        if (!res.ok) throw new Error('Failed to load expenses for summary');
        const expenses = await res.json();
        // normalize and compute totals
        const norm = expenses.map(e => ({
          ...e,
          categoryName: e.category?.name ?? e.category ?? null,
          created_at: e.created_at ?? e.date ?? null
        }));
        const monthly = calcTotalFromList(norm, 'month');
        const weekly = calcTotalFromList(norm, 'week');
        const yearly = calcTotalFromList(norm, 'year');
        document.getElementById('monthlyTotal').textContent = formatCurrency(monthly);
        document.getElementById('weeklyTotal').textContent = formatCurrency(weekly);
        document.getElementById('yearlyTotal').textContent = formatCurrency(yearly);
        document.getElementById('totalCount').textContent = norm.length;
      } catch (err) {
        console.error('Error loading summary', err);
      }
    }

    function calcTotalFromList(expenses, period) {
      const now = new Date();
      return expenses.reduce((sum, e) => {
        if (!e.created_at) return sum;
        const d = new Date(e.created_at);
        if (period === 'month') {
          if (d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()) return sum + Number(e.amount || 0);
        } else if (period === 'week') {
          const start = startOfWeek(now);
          const end = new Date(start); end.setDate(end.getDate() + 7);
          if (d >= start && d < end) return sum + Number(e.amount || 0);
        } else if (period === 'year') {
          if (d.getFullYear() === now.getFullYear()) return sum + Number(e.amount || 0);
        }
        return sum;
      }, 0);
    }

    // Reset form
    window.resetForm = function () {
      document.getElementById('expenseForm').reset();
      document.getElementById('expenseId').value = '';
      document.getElementById('date').valueAsDate = new Date();
      document.getElementById('formTitle').textContent = 'Add New Expense';
      document.getElementById('submitBtn').textContent = 'Add Expense';
      document.getElementById('cancelBtn').style.display = 'none';
    };

    // Helpers for safe HTML/CSS class names
    function escapeHtml(unsafe) {
      if (unsafe == null) return '';
      return String(unsafe).replace(/[&<>"'`=\/]/g, s => ({
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','/':'&#x2F;','`':'&#x60;','=':'&#x3D;'
      })[s]);
    }
    function escapeCssClass(name) {
      if (!name) return 'unknown';
      return String(name).replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-_]/g, '').toLowerCase();
    }

  })();