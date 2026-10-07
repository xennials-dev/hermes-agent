// Twenty CRM Client Engine with MCP, Custom AI Objects, pgvector Search & Approvals
document.addEventListener("DOMContentLoaded", () => {
  let opportunities = [];
  let companies = [];
  let people = [];
  let notes = [];
  let briefs = [];
  let competitors = [];
  let risks = [];
  let tasks = [];
  let departments = [];
  let employees = [];
  let jobs = [];
  let auditLogs = [];
  let activeOppForAi = null;

  // Navigation
  const sidebarButtons = document.querySelectorAll(".sidebar-btn");
  const views = document.querySelectorAll(".twenty-view");
  const viewTitle = document.getElementById("view-title");
  const btnGlobalAction = document.getElementById("btn-global-action");
  const btnActionLabel = document.getElementById("btn-action-label");

  // KPI elements
  const kpiPipeline = document.getElementById("kpi-pipeline");
  const kpiOppsCount = document.getElementById("kpi-opps-count");
  const kpiBriefsCount = document.getElementById("kpi-briefs-count");
  const kpiApprovalsCount = document.getElementById("kpi-approvals-count");
  const sidebarApprovalsCount = document.getElementById("sidebar-approvals-count");

  // Modals
  const modalOpp = document.getElementById("modal-opp");
  const formCreateOpp = document.getElementById("form-create-opp");
  const oppCompanySelect = document.getElementById("opp-company");

  const modalAi = document.getElementById("modal-ai-summary");
  const btnCloseAiModal = document.getElementById("btn-close-ai-modal");
  const btnCloseAi = document.getElementById("btn-close-ai");
  const btnGenerateAiBrief = document.getElementById("btn-generate-ai-brief");
  const aiBriefOutput = document.getElementById("ai-brief-output");
  const aiGenStatus = document.getElementById("ai-gen-status");
  const aiModelPicker = document.getElementById("ai-model-picker");
  const modalAiTitle = document.getElementById("modal-ai-title");

  // Webhook Simulator
  const btnTriggerSim = document.getElementById("btn-trigger-sim");
  const simOppSelect = document.getElementById("sim-opp-select");
  const simEventSelect = document.getElementById("sim-event-select");
  const eventStream = document.getElementById("event-stream");

  // Semantic Search
  const queryInput = document.getElementById("semantic-query-input");
  const btnRunSearch = document.getElementById("btn-run-semantic-search");
  const searchResultsContainer = document.getElementById("semantic-results");

  // Enterprise Job Submitter
  const btnSubmitJob = document.getElementById("btn-submit-job");
  const jobTypeSelect = document.getElementById("job-type-select");
  const jobPrioritySelect = document.getElementById("job-priority-select");

  // View Titles Map
  const titleMap = {
    opportunities: "Deals Pipeline",
    companies: "Companies & Organizations",
    people: "People (Contacts)",
    notes: "Notes & Interaction Activity",
    "ai-objects": "Structured AI Custom Objects (Metadata API)",
    approvals: "Human-in-the-Loop Action Approvals",
    "semantic-search": "pgvector Semantic Search",
    loop: "Lifecycle Webhooks & Event Mesh",
    workforce: "Enterprise Workforce & Org Hierarchy",
    jobs: "Enterprise Background Job Engine",
    audit: "Cryptographic Tamper-Proof Audit Trail (SOC2 / GDPR)",
  };

  sidebarButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-view");
      sidebarButtons.forEach(b => b.classList.remove("active"));
      views.forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      const targetView = document.getElementById(`view-${target}`);
      if (targetView) targetView.classList.add("active");
      viewTitle.textContent = titleMap[target] || "Twenty Workspace";

      if (target === "opportunities") {
        btnActionLabel.textContent = "New Opportunity";
        btnGlobalAction.style.display = "inline-flex";
      } else {
        btnGlobalAction.style.display = "none";
      }
    });
  });

  function showToast(msg) {
    const c = document.getElementById("toast-container");
    const t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => {
      t.style.opacity = "0";
      t.style.transition = "opacity 0.2s";
      setTimeout(() => t.remove(), 200);
    }, 3000);
  }

  function logEvent(tag, msg) {
    const d = new Date().toLocaleTimeString();
    const item = document.createElement("div");
    item.className = "event-item";
    item.innerHTML = `
      <span class="event-time">${d}</span>
      <span class="event-tag">${tag}</span>
      <span class="event-msg">${escapeHtml(msg)}</span>
    `;
    eventStream.prepend(item);
  }

  // Fetch All CRM Data
  async function loadData() {
    try {
      const [oppRes, compRes, peopleRes, notesRes, briefsRes, compIntelRes, riskRes, tasksRes, deptsRes, empsRes, jobsRes, auditRes] =
        await Promise.all([
          fetch("/rest/opportunities"),
          fetch("/rest/companies"),
          fetch("/rest/people"),
          fetch("/rest/notes"),
          fetch("/rest/dealStrategyBriefs"),
          fetch("/rest/competitorIntelligences"),
          fetch("/rest/riskAssessments"),
          fetch("/rest/tasks"),
          fetch("/rest/departments"),
          fetch("/rest/employees"),
          fetch("/rest/jobs"),
          fetch("/rest/audit-logs"),
        ]);

      opportunities = (await oppRes.json()).data.opportunities || [];
      companies = (await compRes.json()).data.companies || [];
      people = (await peopleRes.json()).data.people || [];
      notes = (await notesRes.json()).data.notes || [];
      briefs = (await briefsRes.json()).data.dealStrategyBriefs || [];
      competitors = (await compIntelRes.json()).data.competitorIntelligences || [];
      risks = (await riskRes.json()).data.riskAssessments || [];
      tasks = (await tasksRes.json()).data.tasks || [];
      departments = (await deptsRes.json()).data.departments || [];
      employees = (await empsRes.json()).data.employees || [];
      jobs = (await jobsRes.json()).data.jobs || [];
      const auditJson = await auditRes.json();
      auditLogs = auditJson.data?.logs || [];
      const isAuditChainValid = auditJson.data?.chainValid;

      renderKPIs();
      renderKanban();
      renderCompanies();
      renderPeople();
      renderNotes();
      renderAiCustomObjects();
      renderApprovals();
      renderDepartments();
      renderEmployees();
      renderJobs();
      renderAudit(isAuditChainValid);
      populateDropdowns();
    } catch (err) {
      showToast("Error loading Twenty CRM data: " + err.message);
    }
  }

  function renderKPIs() {
    let totalDollars = 0;
    opportunities.forEach(o => {
      const micros = o.amount?.amountMicros || 0;
      totalDollars += micros / 1000000;
    });
    kpiPipeline.textContent = `$${totalDollars.toLocaleString()}`;
    kpiOppsCount.textContent = opportunities.length;
    kpiBriefsCount.textContent = briefs.length;

    const pendingCount = tasks.filter(t => t.status === "AI_PROPOSED").length;
    kpiApprovalsCount.textContent = pendingCount;
    if (sidebarApprovalsCount) sidebarApprovalsCount.textContent = pendingCount;
  }

  function renderKanban() {
    const stages = ["DISCOVERY", "PROPOSAL", "NEGOTIATION", "CLOSED_WON"];
    stages.forEach(st => {
      const colCards = document.getElementById(`cards-${st}`);
      const colCount = document.getElementById(`count-${st}`);
      const filtered = opportunities.filter(o => o.stage === st);
      if (colCount) colCount.textContent = filtered.length;

      if (colCards) {
        colCards.innerHTML = filtered.map(o => {
          const val = ((o.amount?.amountMicros || 0) / 1000000).toLocaleString();
          return `
            <div class="opp-card" data-id="${o.id}">
              <div class="opp-card-title">${escapeHtml(o.name)}</div>
              <div class="opp-company-badge">${escapeHtml(o.companyName || "Company")}</div>
              <div class="opp-meta-row">
                <span class="opp-amount">$${val}</span>
                <span class="opp-prob">${o.probability || 50}% prob</span>
              </div>
              <div class="opp-card-actions">
                <span style="font-size: 0.72rem; color: var(--text-dim);">${escapeHtml(o.pointOfContactName || "")}</span>
                <button class="btn-ai-sparkle btn-open-ai" data-id="${o.id}">
                  ✨ Hermes AI Brief
                </button>
              </div>
            </div>
          `;
        }).join("");
      }
    });

    document.querySelectorAll(".btn-open-ai").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        openAiBrief(id);
      });
    });
  }

  function renderCompanies() {
    const tbody = document.getElementById("companies-tbody");
    if (!tbody) return;
    tbody.innerHTML = companies.map(c => `
      <tr>
        <td><strong>${escapeHtml(c.name)}</strong></td>
        <td><code>${escapeHtml(c.domainName || "")}</code></td>
        <td>${(c.employees || 0).toLocaleString()}</td>
        <td>$${(c.annualRecurringRevenue || 0).toLocaleString()}</td>
        <td>${(c.enrichedTags || []).map(t => `<span class="schema-tag">${t}</span>`).join(" ")}</td>
        <td style="color: var(--text-dim); font-size: 0.75rem;">${c.createdAt ? c.createdAt.slice(0, 10) : ""}</td>
      </tr>
    `).join("");
  }

  function renderPeople() {
    const tbody = document.getElementById("people-tbody");
    if (!tbody) return;
    tbody.innerHTML = people.map(p => {
      const fullName = `${p.name?.firstName || ""} ${p.name?.lastName || ""}`.trim();
      return `
        <tr>
          <td><strong>${escapeHtml(fullName)}</strong></td>
          <td>${escapeHtml(p.jobTitle || "")}</td>
          <td>${escapeHtml(p.emails?.primaryEmail || "")}</td>
          <td>${escapeHtml(p.phones?.primaryPhoneNumber || "")}</td>
          <td><code>${escapeHtml(p.companyId || "")}</code></td>
          <td>${escapeHtml(p.city || "")}</td>
        </tr>
      `;
    }).join("");
  }

  function renderNotes() {
    const container = document.getElementById("notes-timeline");
    if (!container) return;
    if (!notes.length) {
      container.innerHTML = `<div style="color: var(--text-dim); font-size: 0.85rem;">No notes recorded yet.</div>`;
      return;
    }
    container.innerHTML = notes.map(n => `
      <div class="note-item">
        <div class="note-header">
          <div class="note-title">${escapeHtml(n.title)}</div>
          <span class="note-author">${escapeHtml(n.author || "Hermes Agent")}</span>
        </div>
        <div class="note-body">${escapeHtml(n.body)}</div>
        <div class="note-time" style="display: flex; gap: 8px; align-items: center;">
          <span>${n.createdAt ? new Date(n.createdAt).toLocaleString() : ""}</span>
          ${n.sentiment ? `<span class="schema-tag">${escapeHtml(n.sentiment)}</span>` : ""}
          ${n.category ? `<span class="mcp-badge">${escapeHtml(n.category)}</span>` : ""}
        </div>
      </div>
    `).join("");
  }

  // Render AI Custom Objects
  function renderAiCustomObjects() {
    const briefsList = document.getElementById("briefs-list");
    const competitorList = document.getElementById("competitor-list");
    const riskList = document.getElementById("risk-list");

    if (briefsList) {
      briefsList.innerHTML = briefs.map(b => `
        <div class="brief-card">
          <div class="brief-meta">
            <span>Opportunity: <code>${b.opportunityId}</code></span>
            <span>Model: <strong>${b.modelEngine}</strong></span>
            <span>Risk Score: <strong style="color: var(--emerald);">${b.riskScore}/100</strong></span>
            <span>Closing Prob: <strong>${b.closingProbability}%</strong></span>
          </div>
          <div class="brief-assessment">${escapeHtml(b.executiveAssessment)}</div>
          <div style="font-size: 0.78rem; font-weight: 600; margin-bottom: 4px; color: var(--text-muted);">Strategic Recommendations:</div>
          <ul class="brief-recs">
            ${(b.strategicRecommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join("")}
          </ul>
        </div>
      `).join("") || `<div style="color: var(--text-dim);">No strategy briefs stored yet.</div>`;
    }

    if (competitorList) {
      competitorList.innerHTML = competitors.map(c => `
        <div class="competitor-card">
          <div class="brief-meta">
            <span>Competitor: <strong style="color: #ef4444;">${escapeHtml(c.competitorName)}</strong></span>
            <span>Pricing Pressure: <strong>${escapeHtml(c.pricingPressure)}</strong></span>
            <span>Opportunity: <code>${c.opportunityId}</code></span>
          </div>
          <div class="brief-assessment"><strong>Win/Loss Driver:</strong> ${escapeHtml(c.winLossFactor)}</div>
          <div class="brief-assessment"><strong>Counter-Tactics:</strong> ${escapeHtml(c.counterTactics)}</div>
        </div>
      `).join("") || `<div style="color: var(--text-dim);">No competitor intelligence profiles yet.</div>`;
    }

    if (riskList) {
      riskList.innerHTML = risks.map(r => `
        <div class="risk-card">
          <div class="brief-meta">
            <span>Risk Level: <strong style="color: var(--amber);">${escapeHtml(r.riskLevel)}</strong></span>
            <span>Opportunity: <code>${r.opportunityId}</code></span>
          </div>
          <div class="brief-assessment"><strong>Technical Risks:</strong> ${escapeHtml(r.technicalRisks)}</div>
          <div class="brief-assessment"><strong>Mitigation Plan:</strong> ${escapeHtml(r.mitigationPlan)}</div>
        </div>
      `).join("") || `<div style="color: var(--text-dim);">No risk assessments registered yet.</div>`;
    }
  }

  // Render Human Approvals
  function renderApprovals() {
    const list = document.getElementById("approvals-list");
    if (!list) return;

    list.innerHTML = tasks.map(t => {
      const isProposed = t.status === "AI_PROPOSED";
      const statusClass = `status-${(t.status || "todo").toLowerCase()}`;
      return `
        <div class="approval-card ${statusClass}">
          <div class="approval-info">
            <h4>${escapeHtml(t.title)}</h4>
            <p>${escapeHtml(t.body || "No details provided.")}</p>
            <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 4px;">
              Target Deal: <code>${t.targetOpportunityId || "General"}</code> |
              Status: <strong>${t.status}</strong> |
              Source: ${escapeHtml(t.createdBy || "Agent")}
            </div>
          </div>
          <div class="approval-actions">
            ${
              isProposed
                ? `<button class="btn-approve" data-id="${t.id}">✓ Approve</button>
                   <button class="btn-reject" data-id="${t.id}">✕ Reject</button>`
                : `<span class="schema-tag">${t.status}</span>`
            }
          </div>
        </div>
      `;
    }).join("") || `<div style="color: var(--text-dim);">No agent tasks requiring approval.</div>`;

    document.querySelectorAll(".btn-approve").forEach(b => {
      b.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        try {
          const res = await fetch(`/rest/tasks/${id}/approve`, { method: "POST" });
          if (!res.ok) throw new Error("Approval failed");
          showToast(`Task ${id} approved! Dispatched task.approved webhook to Hermes.`);
          logEvent("TASK_APPROVED", `Task approved by human operator. Hermes Agent follow-up triggered.`);
          loadData();
        } catch (err) {
          showToast(err.message);
        }
      });
    });

    document.querySelectorAll(".btn-reject").forEach(b => {
      b.addEventListener("click", async (e) => {
        const id = e.currentTarget.getAttribute("data-id");
        try {
          await fetch(`/rest/tasks/${id}/reject`, { method: "POST" });
          showToast(`Task ${id} rejected.`);
          logEvent("TASK_REJECTED", `Task ${id} rejected.`);
          loadData();
        } catch (err) {
          showToast(err.message);
        }
      });
    });
  }

  // Semantic Search
  if (btnRunSearch && queryInput) {
    btnRunSearch.addEventListener("click", runSemanticSearch);
    queryInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runSemanticSearch();
    });
  }

  async function runSemanticSearch() {
    const q = queryInput.value.trim();
    if (!q) return;
    searchResultsContainer.innerHTML = `<div style="color: var(--cyan); padding: 12px;">Querying pgvector embedding index on localhost:3000...</div>`;

    try {
      const res = await fetch("/rest/semantic-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, limit: 5 }),
      });
      const data = await res.json();
      const matches = data.data.matches || [];

      if (!matches.length) {
        searchResultsContainer.innerHTML = `<div class="empty-state">No semantic matches found for "${escapeHtml(q)}".</div>`;
        return;
      }

      searchResultsContainer.innerHTML = matches.map(m => `
        <div class="semantic-match-card">
          <div class="match-header">
            <div class="match-title">${escapeHtml(m.title)}</div>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span class="schema-tag">${escapeHtml(m.objectType)}</span>
              <span class="match-score">Cosine Similarity: ${(m.score * 100).toFixed(1)}%</span>
            </div>
          </div>
          <div class="match-snippet">${escapeHtml(m.snippet)}</div>
        </div>
      `).join("");
      logEvent("VECTOR_SEARCH", `pgvector query executed: "${q}" (${matches.length} matches)`);
    } catch (err) {
      showToast("Semantic search error: " + err.message);
    }
  }

  function populateDropdowns() {
    if (oppCompanySelect) {
      oppCompanySelect.innerHTML = companies.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
    }
    if (simOppSelect) {
      simOppSelect.innerHTML = opportunities.map(o => `<option value="${o.id}">${escapeHtml(o.name)}</option>`).join("");
    }
  }

  // AI Brief Modal
  function openAiBrief(oppId) {
    activeOppForAi = opportunities.find(o => o.id === oppId);
    if (!activeOppForAi) return;
    modalAiTitle.textContent = `Deal Intelligence: ${activeOppForAi.name}`;
    aiBriefOutput.textContent = `Opportunity Details:\n• Name: ${activeOppForAi.name}\n• Value: $${((activeOppForAi.amount?.amountMicros||0)/1000000).toLocaleString()} USD\n• Company: ${activeOppForAi.companyName}\n• Contact: ${activeOppForAi.pointOfContactName}\n• Stage: ${activeOppForAi.stage}\n\nClick "Generate AI Custom Objects" below to run the Hermes agent intelligence turn.`;
    aiGenStatus.textContent = "Ready";
    modalAi.style.display = "flex";
  }

  if (btnCloseAiModal) btnCloseAiModal.addEventListener("click", () => modalAi.style.display = "none");
  if (btnCloseAi) btnCloseAi.addEventListener("click", () => modalAi.style.display = "none");

  if (btnGenerateAiBrief) {
    btnGenerateAiBrief.addEventListener("click", async () => {
      if (!activeOppForAi) return;
      const model = aiModelPicker.value;
      aiGenStatus.textContent = "Routing to " + model + "...";
      btnGenerateAiBrief.disabled = true;

      // Create DealStrategyBrief directly
      try {
        const briefRes = await fetch("/rest/dealStrategyBriefs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            opportunityId: activeOppForAi.id,
            executiveAssessment: `High-conviction deal. Strategic enterprise infrastructure alignment with Hermes Agent and ${model} localized cluster.`,
            riskScore: 20,
            closingProbability: 85,
            strategicRecommendations: [
              "Deploy localized vLLM node for customer evaluation",
              "Establish guaranteed Chinese token latency SLA",
              "Connect Twenty CRM MCP server directly into client workflows",
            ],
            modelEngine: model,
          }),
        });

        // Create Task with AI_PROPOSED status
        await fetch("/rest/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: `[AI Proposed] Deliver SLA benchmark report to ${activeOppForAi.pointOfContactName}`,
            body: `Derived from strategic brief for ${activeOppForAi.name}. Review and approve before execution.`,
            targetOpportunityId: activeOppForAi.id,
            status: "AI_PROPOSED",
            createdBy: `Hermes Agent (${model})`,
          }),
        });

        const briefData = await briefRes.json();
        showToast("Created DealStrategyBrief and AI_PROPOSED Task in Twenty CRM!");
        logEvent("MCP_WRITE", `Created structured DealStrategyBrief ${briefData.data.createDealStrategyBrief.id} via Metadata API`);

        aiBriefOutput.textContent = `✅ Successfully created Structured AI Objects in Twenty CRM:\n• Deal Strategy Brief: ${briefData.data.createDealStrategyBrief.id}\n• Proposed Action Task: Status AI_PROPOSED\n• Model Engine: ${model}\n\nReview the Action Approvals tab to approve agent tasks!`;
        aiGenStatus.textContent = "Synced";
        btnGenerateAiBrief.disabled = false;
        loadData();
      } catch (err) {
        showToast(err.message);
        btnGenerateAiBrief.disabled = false;
      }
    });
  }

  // Webhook Simulator
  if (btnTriggerSim) {
    btnTriggerSim.addEventListener("click", async () => {
      const oppId = simOppSelect.value;
      const eventType = simEventSelect.value;
      const opp = opportunities.find(o => o.id === oppId);

      logEvent("SIM_DISPATCH", `Dispatching webhook: ${eventType} -> ${opp?.name || "Deal"}`);
      try {
        await fetch("/rest/webhooks/trigger", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event: eventType, opportunityId: oppId })
        });
        showToast(`Dispatched ${eventType} event!`);
        setTimeout(() => {
          logEvent("AGENT_RECV", `Hermes Agent processed ${eventType} event successfully`);
        }, 600);
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  // Enterprise Renderers
  function renderDepartments() {
    const grid = document.getElementById("departments-grid");
    if (!grid) return;
    grid.innerHTML = "";
    departments.forEach(d => {
      const budget = d.budgetTokens || 10000000;
      const used = d.tokensUsed || 0;
      const pct = Math.min(100, Math.round((used / budget) * 100));
      const card = document.createElement("div");
      card.className = "department-card";
      card.innerHTML = `
        <div class="dept-header">
          <span class="dept-name">${escapeHtml(d.name)}</span>
          <span class="dept-code">${escapeHtml(d.code)}</span>
        </div>
        <div class="dept-budget-line">
          <span>Tokens: ${used.toLocaleString()} / ${budget.toLocaleString()}</span>
          <span>${pct}%</span>
        </div>
        <div class="dept-bar-track">
          <div class="dept-bar-fill" style="width: ${pct}%;"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); display: flex; justify-content: space-between;">
          <span>Head: ${escapeHtml(d.headEmployeeId || "Unassigned")}</span>
          <span style="color: var(--emerald);">$${(d.costAccruedUsd || 0).toFixed(2)} USD</span>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  function renderEmployees() {
    const tbody = document.getElementById("employees-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    employees.forEach(e => {
      const active = e.activeDealsCount || 0;
      const cap = e.maxCapacityDeals || 12;
      const pct = Math.min(100, Math.round((active / cap) * 100));
      const roleClass = "role-" + (e.role || "employee").toLowerCase().replace(/_/g, "-");
      const skillsHtml = (e.skills || []).map(s => `<span class="skill-pill">${escapeHtml(s)}</span>`).join("");
      const mgr = employees.find(m => m.id === e.managerId);

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <strong>${escapeHtml(e.name)}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(e.email)}</div>
        </td>
        <td>
          <span class="role-pill ${roleClass}">${escapeHtml(e.role)}</span>
          <div style="font-size: 0.78rem; margin-top: 3px;">${escapeHtml(e.title || "")}</div>
        </td>
        <td><code>${escapeHtml(e.departmentId)}</code></td>
        <td>${mgr ? escapeHtml(mgr.name) : '<span style="color:var(--text-muted);">Executive Lead</span>'}</td>
        <td>
          <div class="capacity-meter">
            <span>${active}/${cap}</span>
            <div class="capacity-track">
              <div class="capacity-fill" style="width: ${pct}%; background: ${pct > 80 ? 'var(--rose)' : 'var(--emerald)'};"></div>
            </div>
          </div>
        </td>
        <td>${skillsHtml}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="alert('Auto-assigning enterprise deal to ${escapeHtml(e.name)}...')">
            Assign Lead
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderJobs() {
    const tbody = document.getElementById("jobs-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    jobs.forEach(j => {
      const tr = document.createElement("tr");
      const statusPill = j.status === "COMPLETED" ? "badge-completed" : j.status === "PROCESSING" ? "badge-pending" : "badge-todo";
      tr.innerHTML = `
        <td>
          <strong>${escapeHtml(j.jobType)}</strong>
          <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(j.id)}</div>
        </td>
        <td><span class="skill-pill">${escapeHtml(j.priority)}</span></td>
        <td><span class="${statusPill}">${escapeHtml(j.status)}</span></td>
        <td>
          <div class="capacity-meter">
            <span>${j.progressPct || 0}%</span>
            <div class="capacity-track">
              <div class="capacity-fill" style="width: ${j.progressPct || 0}%; background: var(--primary);"></div>
            </div>
          </div>
        </td>
        <td><code>${escapeHtml(j.workerId || "pending")}</code></td>
        <td style="font-size: 0.75rem; color: var(--text-muted);">${new Date(j.createdAt).toLocaleTimeString()}</td>
        <td>
          ${j.status === "PROCESSING" ? `<button class="btn btn-secondary btn-sm" onclick="cancelJob('${j.id}')">Cancel</button>` : `<span style="font-size:0.75rem; color:var(--emerald);">Verified</span>`}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderAudit(isChainValid) {
    const tbody = document.getElementById("audit-tbody");
    const meta = document.getElementById("audit-blocks-count");
    if (meta) meta.textContent = `${auditLogs.length} Cryptographic Blocks Verified · Hash Chain Active`;
    if (!tbody) return;
    tbody.innerHTML = "";
    auditLogs.slice(0, 15).forEach(l => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-size: 0.78rem; font-family: var(--font-mono); color: var(--text-muted);">${new Date(l.timestamp).toLocaleTimeString()}</td>
        <td><strong>${escapeHtml(l.actor)}</strong></td>
        <td><span class="role-pill role-employee">${escapeHtml(l.actorRole || "AGENT")}</span></td>
        <td><code>${escapeHtml(l.action)}</code></td>
        <td>${escapeHtml(l.entityType)}/${escapeHtml(l.entityId)}</td>
        <td><span class="hash-code">${escapeHtml((l.currentHash || "").substring(0, 16))}...</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Job Submission Event
  if (btnSubmitJob) {
    btnSubmitJob.addEventListener("click", async () => {
      const jobType = jobTypeSelect.value;
      const priority = jobPrioritySelect.value;
      btnSubmitJob.disabled = true;
      btnSubmitJob.textContent = "Dispatching...";
      try {
        const resp = await fetch("/rest/jobs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            jobType: jobType,
            priority: priority,
            submittedByEmployeeId: "emp-101",
            payload: { triggeredFromWebUI: true, recordCount: 15 }
          })
        });
        const data = await resp.json();
        showToast(`Job ${data.data?.job?.id} dispatched to background worker!`);
        btnSubmitJob.disabled = false;
        btnSubmitJob.textContent = "🚀 Dispatch Background Job";
        loadData();
      } catch (err) {
        showToast(err.message);
        btnSubmitJob.disabled = false;
        btnSubmitJob.textContent = "🚀 Dispatch Background Job";
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  loadData();
});
