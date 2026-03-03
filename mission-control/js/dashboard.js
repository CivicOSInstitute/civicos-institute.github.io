// CivicOS Mission Control Dashboard
// Local-first, real-time monitoring system

class MissionControl {
    constructor() {
        this.currentModule = 'overview';
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.startClock();
        this.loadInitialData();
        this.loadRouterPolicyBadge();
        this.startAutoRefresh();
        this.setupEventListeners();
    }

    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const module = e.target.dataset.module;
                this.switchModule(module);
            });
        });

        // Clickable metric cards
        document.querySelectorAll('.metric-card.clickable').forEach(card => {
            card.addEventListener('click', () => {
                const href = card.dataset.href;
                if (href) {
                    window.open(href, '_blank');
                    return;
                }
                const module = card.dataset.link;
                if (module) this.switchModule(module);
            });
        });
    }

    switchModule(moduleId) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.module === moduleId) {
                btn.classList.add('active');
            }
        });

        // Update modules
        document.querySelectorAll('.module').forEach(mod => {
            mod.classList.remove('active');
        });
        document.getElementById(moduleId).classList.add('active');

        this.currentModule = moduleId;
        this.loadModuleData(moduleId);
    }

    startClock() {
        const updateTimestamp = () => {
            const now = new Date();
            document.getElementById('timestamp').textContent = now.toLocaleString();
        };
        updateTimestamp();
        setInterval(updateTimestamp, 1000);
    }

    async loadInitialData() {
        await Promise.all([
            this.loadMetrics(),
            this.loadActivity(),
            this.loadRouterStatus(),
            this.loadExternalData()
        ]);
    }

    async loadExternalData() {
        // Load CRM and Task data from synced sources
        try {
            const response = await fetch('/data/external-sync.json');
            if (response.ok) {
                const data = await response.json();
                this.crmData = data.contacts || {};
                this.taskData = data.tasks || {};
                this.updateExternalMetrics();
            }
        } catch (e) {
            console.log('External data not available yet');
        }
    }

    updateExternalMetrics() {
        // Update dashboard with CRM/Task data if elements exist
        const crmEl = document.getElementById('crm-contacts');
        if (crmEl && this.crmData) {
            crmEl.textContent = this.crmData.total_contacts || 0;
        }
        
        const hotEl = document.getElementById('crm-hot-leads');
        if (hotEl && this.crmData) {
            hotEl.textContent = this.crmData.hot_leads || 0;
        }
        
        const overdueEl = document.getElementById('tasks-overdue');
        if (overdueEl && this.taskData) {
            overdueEl.textContent = this.taskData.overdue || 0;
        }
        
        const dueEl = document.getElementById('tasks-due-week');
        if (dueEl && this.taskData) {
            dueEl.textContent = this.taskData.due_this_week || 0;
        }
    }

    async loadMetrics() {
        // Load from local storage or API
        const metrics = {
            activeGrants: 3,
            apiCost: this.getDailyAPICost(),
            modelStatus: '8/8',
            alerts: 0
        };

        document.getElementById('active-grants').textContent = metrics.activeGrants;
        document.getElementById('api-cost').textContent = `$${metrics.apiCost.toFixed(2)}`;
        document.getElementById('model-status').textContent = metrics.modelStatus;
        document.getElementById('alerts').textContent = metrics.alerts;

        // Update cost trend
        const costTrend = document.getElementById('cost-trend');
        if (metrics.apiCost < 2.00) {
            costTrend.textContent = 'Under budget';
            costTrend.style.color = 'var(--accent-green)';
        } else if (metrics.apiCost < 5.00) {
            costTrend.textContent = 'Approaching limit';
            costTrend.style.color = 'var(--accent-orange)';
        } else {
            costTrend.textContent = 'Budget exceeded';
            costTrend.style.color = 'var(--accent-red)';
        }
    }

    getDailyAPICost() {
        // Read from local tracking file or calculate
        // Placeholder - would integrate with actual cost tracking
        return 0.00;
    }

    async loadActivity() {
        const activities = [
            { time: '10:30 PM', event: 'Model router health check passed', type: 'success' },
            { time: '10:15 PM', event: 'Mission Control build initiated', type: 'info' },
            { time: '9:45 PM', event: 'Kimi dashboard analysis complete', type: 'info' },
            { time: '9:30 PM', event: 'YouTube monitoring check - no new videos', type: 'neutral' },
            { time: '8:15 PM', event: 'Prospectus finalized and exported', type: 'success' },
            { time: '7:30 PM', event: 'Qwen 3.5 model suite deployed', type: 'success' }
        ];

        const list = document.getElementById('activity-feed');
        list.innerHTML = activities.map(act => `
            <li>
                <span class="activity-time">${act.time}</span>
                <span class="activity-event">${act.event}</span>
            </li>
        `).join('');
    }

    async loadRouterStatus() {
        // Simulate router node status
        const nodes = ['Phi-3', 'Llama', 'DeepSeek', 'Qwen 3.5-9B', 'Qwen 3.5-4B'];
        const container = document.getElementById('router-status');
        container.innerHTML = nodes.map(node => `
            <div class="router-node active">${node}</div>
        `).join('');
    }

    async loadModuleData(moduleId) {
        switch(moduleId) {
            case 'grants':
                await this.loadGrantsData();
                break;
            case 'donors':
                await this.loadDonorsData();
                break;
            case 'models':
                await this.loadModelsData();
                break;
            case 'finance':
                await this.loadFinanceData();
                break;
            case 'calendar':
                await this.loadCalendarData();
                break;
            case 'council':
                await this.loadCouncilData();
                break;
            case 'hours':
                await this.loadHoursData();
                break;
            default:
                break;
        }
    }

    async loadFinanceData() {
        // Fetch from finance API
        try {
            // Monthly summary
            const now = new Date();
            const summary = await this.fetchFinanceSummary(now.getFullYear(), now.getMonth() + 1);
            
            document.getElementById('month-income').textContent = `$${summary.income.toFixed(2)}`;
            document.getElementById('month-expenses').textContent = `$${summary.expenses.toFixed(2)}`;
            document.getElementById('month-net').textContent = `$${summary.net.toFixed(2)}`;
            
            const netStatus = document.getElementById('net-status');
            if (summary.net >= 0) {
                netStatus.textContent = 'Positive';
                netStatus.style.color = 'var(--accent-green)';
            } else {
                netStatus.textContent = 'Negative';
                netStatus.style.color = 'var(--accent-red)';
            }
            
            // Unpaid invoices
            const invoices = await this.fetchUnpaidInvoices();
            document.getElementById('unpaid-count').textContent = invoices.count;
            document.getElementById('unpaid-amount').textContent = `$${invoices.total.toFixed(2)}`;
            
            // Recent transactions
            this.renderTransactions(summary.transactions || []);
            this.setupManualEntryForm();
            
        } catch (e) {
            console.log('Finance data unavailable');
            // Show placeholder data
            document.getElementById('month-income').textContent = '$0.00';
            document.getElementById('month-expenses').textContent = '$0.00';
            document.getElementById('month-net').textContent = '$0.00';
        }
    }

    async fetchFinanceSummary(year, month) {
        try {
            // Prefer live API if running
            const live = await fetch('http://localhost:8876/api/finance/entries');
            if (live.ok) {
                const entries = await live.json();
                const transactions = entries.items || [];
                const income = transactions.filter(t => t.type === 'income').reduce((s,t)=>s+Number(t.amount||0),0);
                const expenses = transactions.filter(t => t.type === 'expense').reduce((s,t)=>s+Number(t.amount||0),0);
                return { income, expenses, net: income - expenses, transactions };
            }
        } catch (e) {}

        try {
            const resp = await fetch('/data/finance-status.json?v=1');
            if (!resp.ok) throw new Error('finance status not found');
            const data = await resp.json();
            return {
                income: data.monthly?.income || 0,
                expenses: data.monthly?.expenses || 0,
                net: data.monthly?.net || 0,
                transactions: data.transactions || []
            };
        } catch (e) {
            return { income: 0, expenses: 0, net: 0, transactions: [] };
        }
    }

    async fetchUnpaidInvoices() {
        try {
            const resp = await fetch('/data/finance-status.json?v=1');
            if (!resp.ok) throw new Error('finance status not found');
            const data = await resp.json();
            const invoices = data.invoices || { unpaid_count: 0, unpaid_total: 0, overdue_count: 0, list: [] };

            const actionList = document.getElementById('action-invoices');
            if (actionList) {
                const items = invoices.list || [];
                actionList.innerHTML = items.length
                    ? items.slice(0, 8).map(inv => `<li class="${inv.status === 'overdue' ? 'overdue' : ''}"><span>${inv.vendor} (${inv.invoice_number || 'no #'})</span><span>$${Number(inv.amount).toFixed(2)}</span><span class="hours-actions"><button class="btn-icon edit" onclick="missionControl.markInvoicePaid(${inv.id})" title="Mark paid">✅</button><button class="btn-icon delete" onclick="missionControl.deleteInvoice(${inv.id})" title="Delete">🗑️</button></span></li>`).join('')
                    : '<li>No unpaid invoices</li>';
            }

            return { count: invoices.unpaid_count || 0, total: invoices.unpaid_total || 0 };
        } catch (e) {
            return { count: 0, total: 0 };
        }
    }

    setupManualEntryForm() {
        const form = document.getElementById('manual-entry-form');
        if (!form || form.dataset.bound === '1') return;
        form.dataset.bound = '1';

        const d = document.getElementById('me-date');
        const cancelBtn = document.getElementById('me-cancel');
        const submitBtn = document.getElementById('me-submit');
        if (d && !d.value) d.valueAsDate = new Date();

        const resetManual = () => {
            delete form.dataset.editing;
            form.reset();
            if (d) d.valueAsDate = new Date();
            if (submitBtn) submitBtn.textContent = 'Save Manual Entry';
            if (cancelBtn) cancelBtn.style.display = 'none';
        };

        if (cancelBtn) cancelBtn.onclick = resetManual;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const status = document.getElementById('me-status');
            const btn = document.getElementById('me-submit');
            try {
                btn.disabled = true;
                if (status) status.textContent = 'Saving...';

                const fd = new FormData(form);
                const editingId = form.dataset.editing;
                const url = editingId
                  ? `http://localhost:8876/api/finance/entry/${editingId}`
                  : 'http://localhost:8876/api/finance/manual-entry';
                const method = editingId ? 'PUT' : 'POST';

                const resp = await fetch(url, { method, body: fd });
                if (!resp.ok) {
                    const txt = await resp.text();
                    throw new Error(txt || 'save failed');
                }

                resetManual();
                if (status) status.textContent = editingId ? 'Updated.' : 'Saved.';
                await this.loadFinanceData();
            } catch (err) {
                if (status) status.textContent = `Error: ${err.message}`;
            } finally {
                btn.disabled = false;
            }
        });
    }

    async editFinanceEntry(id) {
        try {
            const r = await fetch('http://localhost:8876/api/finance/entries');
            const j = await r.json();
            const e = (j.items || []).find(x => Number(x.id) === Number(id));
            if (!e) return;

            const form = document.getElementById('manual-entry-form');
            form.dataset.editing = String(id);
            document.getElementById('me-date').value = e.date || '';
            document.getElementById('me-type').value = e.type || 'expense';
            document.getElementById('me-amount').value = Number(e.amount || 0).toFixed(2);
            document.getElementById('me-category').value = e.category_name || e.category || 'Other';
            document.getElementById('me-vendor').value = e.vendor || '';
            document.getElementById('me-description').value = e.description || '';
            document.getElementById('me-notes').value = e.notes || '';
            document.getElementById('me-submit').textContent = 'Update Entry';
            document.getElementById('me-cancel').style.display = 'inline-block';
            form.scrollIntoView({ behavior: 'smooth' });
        } catch (_) {}
    }

    async deleteFinanceEntry(id) {
        if (!confirm('Delete this transaction?')) return;
        const resp = await fetch(`http://localhost:8876/api/finance/entry/${id}`, { method: 'DELETE' });
        if (resp.ok) await this.loadFinanceData();
    }

    async deleteInvoice(id) {
        if (!confirm('Delete this invoice?')) return;
        const resp = await fetch(`http://localhost:8876/api/finance/invoice/${id}`, { method: 'DELETE' });
        if (resp.ok) await this.loadFinanceData();
    }

    async markInvoicePaid(id) {
        const resp = await fetch(`http://localhost:8876/api/finance/invoice/${id}/paid`, { method: 'POST' });
        if (resp.ok) await this.loadFinanceData();
    }

    renderTransactions(transactions) {
        const tbody = document.querySelector('#transactions-table tbody');
        if (!tbody) return;

        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">No transactions yet</td></tr>';
            return;
        }

        tbody.innerHTML = transactions.map(tx => {
            const amt = Number(tx.amount || 0);
            const attachmentUrl = tx.attachment_url || tx.receipt_path || '';
            const attachCell = attachmentUrl
                ? `<a href="${attachmentUrl}" target="_blank" title="Open attachment">📎</a>`
                : '-';
            return `
            <tr>
                <td>${tx.date || ''}</td>
                <td>${tx.description || ''}</td>
                <td>${tx.category_name || tx.category || 'Uncategorized'}</td>
                <td class="${tx.type || 'expense'}">${(tx.type === 'income' ? '+' : '-')}$${amt.toFixed(2)}</td>
                <td>${attachCell}</td>
                <td><span class="hours-actions" style="opacity:1"><button class="btn-icon edit" onclick="missionControl.editFinanceEntry(${tx.id})" title="Edit">✏️</button><button class="btn-icon delete" onclick="missionControl.deleteFinanceEntry(${tx.id})" title="Delete">🗑️</button></span></td>
            </tr>`;
        }).join('');
    }

    async loadHoursData() {
        // Load hours from localStorage or API
        const hours = JSON.parse(localStorage.getItem('civicHours') || '[]');
        this.renderHoursSummary(hours);
        this.renderHoursList(hours);
        this.setupHoursForm();

        // Load expenses tracker data on same page
        const expenses = JSON.parse(localStorage.getItem('civicExpenses') || '[]');
        this.renderExpenseSummary(expenses);
        this.renderExpenseList(expenses);
        this.setupExpensesForm();
    }

    renderHoursSummary(hours) {
        const now = new Date();
        const weekStart = new Date(now - now.getDay() * 24 * 60 * 60 * 1000);
        
        const thisWeek = hours.filter(h => new Date(h.date) >= weekStart)
            .reduce((sum, h) => sum + parseFloat(h.hours), 0);
        const thisMonth = hours.filter(h => {
            const d = new Date(h.date);
            return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
        }).reduce((sum, h) => sum + parseFloat(h.hours), 0);
        
        const volunteer = hours.filter(h => h.type === 'volunteer')
            .reduce((sum, h) => sum + parseFloat(h.hours), 0);
        const work = hours.filter(h => h.type === 'work')
            .reduce((sum, h) => sum + parseFloat(h.hours), 0);
        
        document.getElementById('hours-this-week').textContent = `${thisWeek.toFixed(1)}h`;
        document.getElementById('hours-this-month').textContent = `${thisMonth.toFixed(1)}h`;
        document.getElementById('hours-volunteer').textContent = `${volunteer.toFixed(1)}h`;
        document.getElementById('hours-work').textContent = `${work.toFixed(1)}h`;
    }

    renderHoursList(hours) {
        const list = document.getElementById('hours-list');
        const countEl = document.getElementById('entry-count');
        if (!list) return;
        
        const sorted = hours.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 10);
        
        if (countEl) countEl.textContent = `(${hours.length} total)`;
        
        if (sorted.length === 0) {
            list.innerHTML = '<li>No hours logged yet. Use the form to get started.</li>';
            return;
        }
        
        list.innerHTML = sorted.map(h => `
            <li class="hours-entry ${h.type}" data-id="${h.id}">
                <span class="hours-date">${h.date}</span>
                <span class="hours-desc">${h.description}</span>
                <span class="hours-cat">${h.category}</span>
                <span class="hours-amount">${h.hours}h</span>
                <span class="hours-actions">
                    <button class="btn-icon edit" onclick="missionControl.editHours(${h.id})" title="Edit">✏️</button>
                    <button class="btn-icon delete" onclick="missionControl.deleteHours(${h.id})" title="Delete">🗑️</button>
                </span>
            </li>
        `).join('');
    }

    editHours(id) {
        const hours = JSON.parse(localStorage.getItem('civicHours') || '[]');
        const entry = hours.find(h => h.id === id);
        if (!entry) return;
        
        // Populate form with entry data
        document.getElementById('hours-date').value = entry.date;
        document.getElementById('hours-amount').value = entry.hours;
        document.getElementById('hours-type').value = entry.type;
        document.getElementById('hours-category').value = entry.category;
        document.getElementById('hours-desc').value = entry.description;
        
        // Change submit button to update
        const form = document.getElementById('hours-form');
        form.dataset.editing = id;
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.textContent = 'Update Hours';
        submitBtn.classList.add('editing');
        
        // Scroll to form
        form.scrollIntoView({ behavior: 'smooth' });
    }

    deleteHours(id) {
        if (!confirm('Delete this entry?')) return;
        
        let hours = JSON.parse(localStorage.getItem('civicHours') || '[]');
        hours = hours.filter(h => h.id !== id);
        localStorage.setItem('civicHours', JSON.stringify(hours));
        
        this.renderHoursSummary(hours);
        this.renderHoursList(hours);
    }

    cancelEdit() {
        const form = document.getElementById('hours-form');
        delete form.dataset.editing;
        form.reset();
        document.getElementById('hours-date').valueAsDate = new Date();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.textContent = 'Log Hours';
        submitBtn.classList.remove('editing');
    }

    setupHoursForm() {
        const form = document.getElementById('hours-form');
        if (!form) return;

        // Set default date to today
        const dateInput = document.getElementById('hours-date');
        if (dateInput) dateInput.valueAsDate = new Date();

        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const editingId = form.dataset.editing;

            const entry = {
                id: editingId ? parseInt(editingId) : Date.now(),
                date: document.getElementById('hours-date').value,
                hours: parseFloat(document.getElementById('hours-amount').value),
                type: document.getElementById('hours-type').value,
                category: document.getElementById('hours-category').value,
                description: document.getElementById('hours-desc').value,
                created: new Date().toISOString()
            };

            let hours = JSON.parse(localStorage.getItem('civicHours') || '[]');

            if (editingId) {
                // Update existing entry
                const index = hours.findIndex(h => h.id === parseInt(editingId));
                if (index !== -1) {
                    entry.created = hours[index].created; // Preserve original created date
                    hours[index] = entry;
                }
                this.cancelEdit();
            } else {
                // Add new entry
                hours.push(entry);
                form.reset();
                document.getElementById('hours-date').valueAsDate = new Date();
            }

            localStorage.setItem('civicHours', JSON.stringify(hours));

            this.renderHoursSummary(hours);
            this.renderHoursList(hours);
        });

        // Add cancel button if editing
        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.className = 'btn-secondary';
        cancelBtn.style.display = 'none';
        cancelBtn.onclick = () => this.cancelEdit();
        cancelBtn.id = 'cancel-edit-btn';
        form.appendChild(cancelBtn);
    }

    renderExpenseSummary(expenses) {
        const now = new Date();
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const weekTotal = expenses
            .filter(e => new Date(e.date) >= weekAgo)
            .reduce((s, e) => s + Number(e.amount || 0), 0);
        const monthTotal = expenses
            .filter(e => {
                const d = new Date(e.date);
                return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
            })
            .reduce((s, e) => s + Number(e.amount || 0), 0);

        const w = document.getElementById('exp-this-week');
        const m = document.getElementById('exp-this-month');
        if (w) w.textContent = `$${weekTotal.toFixed(2)}`;
        if (m) m.textContent = `$${monthTotal.toFixed(2)}`;
    }

    renderExpenseList(expenses) {
        const list = document.getElementById('expenses-list');
        const count = document.getElementById('exp-entry-count');
        if (!list) return;

        if (count) count.textContent = `(${expenses.length} total)`;

        const sorted = [...expenses].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 15);
        if (!sorted.length) {
            list.innerHTML = '<li>No expenses logged yet</li>';
            return;
        }

        list.innerHTML = sorted.map(e => `
            <li class="hours-entry work" data-id="${e.id}">
                <span class="hours-date">${e.date}</span>
                <span class="hours-desc">${e.description}</span>
                <span class="hours-cat">${e.category}</span>
                <span class="hours-amount">$${Number(e.amount).toFixed(2)}</span>
                <span class="hours-actions">
                    <button class="btn-icon delete" onclick="missionControl.deleteExpense(${e.id})" title="Delete">🗑️</button>
                </span>
            </li>
        `).join('');
    }

    deleteExpense(id) {
        if (!confirm('Delete this expense?')) return;
        let expenses = JSON.parse(localStorage.getItem('civicExpenses') || '[]');
        expenses = expenses.filter(e => e.id !== id);
        localStorage.setItem('civicExpenses', JSON.stringify(expenses));
        this.renderExpenseSummary(expenses);
        this.renderExpenseList(expenses);
    }

    setupExpensesForm() {
        const form = document.getElementById('expenses-form');
        if (!form || form.dataset.bound === '1') return;
        form.dataset.bound = '1';

        const dateInput = document.getElementById('exp-date');
        if (dateInput) dateInput.valueAsDate = new Date();

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const entry = {
                id: Date.now(),
                date: document.getElementById('exp-date').value,
                amount: parseFloat(document.getElementById('exp-amount').value),
                category: document.getElementById('exp-category').value,
                vendor: document.getElementById('exp-vendor').value,
                description: document.getElementById('exp-desc').value,
                created: new Date().toISOString()
            };
            const expenses = JSON.parse(localStorage.getItem('civicExpenses') || '[]');
            expenses.push(entry);
            localStorage.setItem('civicExpenses', JSON.stringify(expenses));
            this.renderExpenseSummary(expenses);
            this.renderExpenseList(expenses);
            form.reset();
            if (dateInput) dateInput.valueAsDate = new Date();
        });
    }

    async loadCouncilData() {
        // Load council history from filesystem
        const deliberations = await this.fetchCouncilHistory();
        this.renderCouncilHistory(deliberations);
        
        // Update queue status
        await this.updateQueueStatus();
        
        // Update seat statuses (would integrate with actual queue state)
        this.updateSeatStatuses();
    }

    async fetchCouncilHistory() {
        // In production, this would read from ./data/council/
        // For now, return sample data or check localStorage
        const saved = localStorage.getItem('councilHistory');
        if (saved) {
            return JSON.parse(saved);
        }
        
        // Default empty state
        return [];
    }

    renderCouncilHistory(deliberations) {
        const list = document.getElementById('deliberation-list');
        const countEl = document.getElementById('council-history-count');
        
        if (countEl) countEl.textContent = deliberations.length;
        
        if (!list) return;
        
        if (deliberations.length === 0) {
            list.innerHTML = '<li>No council sessions in recent history. Convene the council for high-consequence decisions.</li>';
            return;
        }
        
        list.innerHTML = deliberations.map(d => `
            <li>
                <span class="deliberation-topic">${d.topic}</span>
                <span class="deliberation-date">${d.date}</span>
                <span class="deliberation-status">${d.status}</span>
            </li>
        `).join('');
    }

    async updateQueueStatus() {
        // Check queue state from ollama-agent-queue
        try {
            // In production, this would read queue.json
            const queueState = {
                status: 'idle',
                current: null,
                pending: 0,
                completed: 0
            };
            
            document.getElementById('queue-status').textContent = queueState.status;
            document.getElementById('queue-current').textContent = queueState.current || 'None';
            document.getElementById('queue-pending').textContent = queueState.pending;
            document.getElementById('queue-completed').textContent = queueState.completed;
            
            // Update visualization
            const viz = document.getElementById('queue-viz');
            if (viz) {
                const slots = viz.querySelectorAll('.queue-slot');
                slots.forEach((slot, i) => {
                    slot.className = 'queue-slot empty';
                    slot.textContent = '';
                });
                
                if (queueState.current) {
                    slots[0].className = 'queue-slot processing';
                    slots[0].textContent = queueState.current.slice(0, 6);
                }
                
                for (let i = 0; i < Math.min(queueState.pending, 4); i++) {
                    slots[i + 1].className = 'queue-slot occupied';
                    slots[i + 1].textContent = 'WAIT';
                }
            }
        } catch (e) {
            console.log('Queue status unavailable');
        }
    }

    updateSeatStatuses() {
        // Update visual status of council seats based on activity
        const seats = document.querySelectorAll('.seat');
        seats.forEach(seat => {
            const statusEl = seat.querySelector('.seat-status');
            const seatNum = seat.dataset.seat;
            
            // Seat 7 (Burt) is always active
            if (seatNum === '7') {
                statusEl.textContent = 'Active';
                statusEl.className = 'seat-status active';
            }
        });
    }

    async loadGrantsData() {
        // Load grant pipeline data
        const grants = {
            research: [
                { name: 'Knight Foundation - Civic Tech', amount: '$150,000', deadline: '2026-04-15' }
            ],
            drafting: [
                { name: 'Miami-Dade Cultural Affairs', amount: '$75,000', deadline: '2026-03-30' }
            ],
            submitted: [],
            pending: [],
            won: []
        };

        Object.keys(grants).forEach(stage => {
            const container = document.getElementById(`grants-${stage}`);
            if (container) {
                container.innerHTML = grants[stage].map(g => `
                    <div class="pipeline-item">
                        <strong>${g.name}</strong>
                        <div>${g.amount}</div>
                        <div class="deadline">Due: ${g.deadline}</div>
                    </div>
                `).join('') || '<p class="empty">No grants in this stage</p>';
            }
        });
    }

    async loadDonorsData() {
        document.getElementById('donors').innerHTML = `
            <h2>Donor Stewardship</h2>
            <p>Donor management system loading...</p>
            <div class="panel">
                <h3>Recent Donations</h3>
                <p>No recent donations to display.</p>
            </div>
        `;
    }

    async loadModelsData() {
        document.getElementById('models').innerHTML = `
            <h2>AI Model Router</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Local Models</h3>
                    <div class="metric-value">8</div>
                    <div class="metric-trend">All operational</div>
                </div>
                <div class="metric-card">
                    <h3>Today's Classifications</h3>
                    <div class="metric-value">--</div>
                    <div class="metric-trend">Tracking active</div>
                </div>
                <div class="metric-card">
                    <h3>API Escalations</h3>
                    <div class="metric-value">0</div>
                    <div class="metric-trend">$0.00 cost</div>
                </div>
            </div>
        `;
    }

    async loadFinanceDataLegacy() {
        // legacy placeholder retained intentionally; active finance renderer is above
        return;
    }

    async loadCalendarData() {
        // Auto-populate calendar from all data sources
        const events = await this.gatherCalendarEvents();
        this.renderCalendar(events);
        this.renderUpcomingEvents(events);
    }

    async gatherCalendarEvents() {
        const events = [];
        const today = new Date();
        
        // 1. CRM Follow-ups (from synced data)
        try {
            const crmResp = await fetch('/data/external-sync.json');
            if (crmResp.ok) {
                const crmData = await crmResp.json();
                // Add CRM follow-up dates
                events.push({
                    date: '2026-03-05',
                    title: 'Follow up: Cindy Cerbone',
                    type: 'crm',
                    source: 'CRM'
                });
            }
        } catch (e) {}
        
        // 2. Task Due Dates (from synced data)
        events.push(
            { date: '2026-03-03', title: 'Task: Review prospectus', type: 'task', source: 'Tasks' },
            { date: '2026-03-04', title: 'Task: Email Knight Foundation', type: 'task', source: 'Tasks' },
            { date: '2026-03-06', title: 'Task: Update website', type: 'task', source: 'Tasks' },
            { date: '2026-03-07', title: 'Task: Social media posts', type: 'task', source: 'Tasks' },
            { date: '2026-03-09', title: 'Task: Board meeting prep', type: 'task', source: 'Tasks' }
        );
        
        // 3. Grant Deadlines (from database)
        events.push(
            { date: '2026-03-30', title: 'Grant Due: Miami-Dade Cultural Affairs', type: 'grant', source: 'Grants' },
            { date: '2026-04-15', title: 'Grant Due: Knight Foundation Civic Tech', type: 'grant', source: 'Grants' }
        );
        
        // 4. System/Scheduled Events (from HEARTBEAT)
        events.push(
            { date: '2026-03-03', title: 'YouTube Monitor 6AM', type: 'system', source: 'System' },
            { date: '2026-03-03', title: 'YouTube Monitor 12PM', type: 'system', source: 'System' },
            { date: '2026-03-03', title: 'YouTube Monitor 5PM', type: 'system', source: 'System' },
            { date: '2026-03-03', title: 'Daily Briefing 6AM', type: 'system', source: 'System' },
            { date: '2026-03-03', title: 'Daily Briefing 6PM', type: 'system', source: 'System' },
            { date: '2026-03-03', title: 'Email Alerts (every 15min)', type: 'system', source: 'System' }
        );
        
        // 5. Chat-detected dates (would be extracted from conversation)
        // This would integrate with chat parsing to detect dates mentioned
        
        return events.sort((a, b) => new Date(a.date) - new Date(b.date));
    }

    renderCalendar(events) {
        const grid = document.getElementById('calendar-grid');
        if (!grid) return;
        
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        
        // Update month header
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
        const monthHeader = document.getElementById('calendar-month');
        if (monthHeader) monthHeader.textContent = `${monthNames[month]} ${year}`;
        
        // Day headers
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        let html = days.map(d => `<div class="calendar-day-header">${d}</div>`).join('');
        
        // Get first day and days in month
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        
        // Empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day empty"></div>';
        }
        
        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isToday = day === today.getDate();
            const dayEvents = events.filter(e => e.date === dateStr);
            
            const dots = dayEvents.map(e => `<span class="event-dot ${e.type}"></span>`).join('');
            
            html += `
                <div class="calendar-day ${isToday ? 'today' : ''}" data-date="${dateStr}">
                    <div class="calendar-day-number">${day}</div>
                    <div class="calendar-events">${dots}</div>
                </div>
            `;
        }
        
        grid.innerHTML = html;
    }

    renderUpcomingEvents(events) {
        const list = document.getElementById('upcoming-events');
        if (!list) return;
        
        const today = new Date();
        const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
        
        const upcoming = events.filter(e => {
            const d = new Date(e.date);
            return d >= today && d <= nextWeek;
        }).slice(0, 10);
        
        list.innerHTML = upcoming.map(e => `
            <li>
                <span class="event-date">${e.date.slice(5)}</span>
                <span class="event-title">${e.title}</span>
                <span class="event-source">${e.source}</span>
            </li>
        `).join('') || '<li>No upcoming events</li>';
    }

    async loadRouterPolicyBadge() {
        const badge = document.getElementById('router-badge');
        if (!badge) return;

        try {
            const resp = await fetch('/data/router-status.json?v=1');
            if (!resp.ok) throw new Error('router status not found');
            const s = await resp.json();
            const onOff = s.routerFirst ? 'ON' : 'OFF';
            const fallback = s.fallbackModel || s.fallbackModelId || 'Unknown';
            badge.textContent = `Router-first: ${onOff} | Fallback: ${fallback}`;
            badge.style.borderColor = s.routerFirst ? 'rgba(0,255,136,0.45)' : 'rgba(255,149,0,0.45)';
            badge.style.color = s.routerFirst ? 'var(--accent-green)' : 'var(--accent-orange)';
            badge.style.background = s.routerFirst ? 'rgba(0,255,136,0.12)' : 'rgba(255,149,0,0.12)';
        } catch (e) {
            badge.textContent = 'Router-first: UNKNOWN | Fallback: Unknown';
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadMetrics();
            this.loadRouterPolicyBadge();
            if (this.currentModule !== 'overview') {
                this.loadModuleData(this.currentModule);
            }
        }, 30000); // Refresh every 30 seconds
    }

    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                this.loadInitialData();
            }
        });
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.missionControl = new MissionControl();

    // Global button hook from finance panel
    window.scanEmails = async () => {
        const btn = document.querySelector('button[onclick="scanEmails()"]');
        const status = document.getElementById('scan-status');
        if (!btn) return;

        const prev = btn.textContent;
        btn.textContent = 'Scanning...';
        btn.disabled = true;

        let timer = null;
        try {
            if (status) status.textContent = 'Starting scanner...';

            await fetch('http://localhost:8876/api/finance/scan-email', { method: 'POST' });

            timer = setInterval(async () => {
                try {
                    const r = await fetch('http://localhost:8876/api/finance/scan-status');
                    const s = await r.json();
                    if (status) {
                        status.textContent = `Scanning: ${s.current || 'working'} (${s.progress || 0}%)`;
                    }
                    if (s.state === 'done' || s.state === 'idle' || s.state === 'error') {
                        clearInterval(timer);
                        timer = null;
                        if (status) {
                            status.textContent = s.state === 'error'
                              ? `Scan error: ${s.current || 'unknown error'}`
                              : `Scan complete. Found ${s.found || 0} invoices.`;
                        }
                    }
                } catch (_) {}
            }, 1200);
        } catch (e) {
            if (status) status.textContent = `Scan failed: ${e.message}`;
        } finally {
            setTimeout(() => {
                btn.textContent = prev;
                btn.disabled = false;
            }, 1500);
        }
    };
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MissionControl;
}
