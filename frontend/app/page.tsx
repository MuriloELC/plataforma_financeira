"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type JsonMap = Record<string, unknown>;

type RawFile = {
  id: string;
  original_filename: string;
  source_type: string | null;
  status: string;
  uploaded_at: string;
  file_size_bytes: number;
};

type Account = {
  id: string;
  institution: string;
  account_name: string;
  account_type: string;
};

type Category = {
  id: string;
  name: string;
  type: string;
};

type Decision = {
  id: string;
  decision_date: string;
  item_name: string;
  amount: string;
  verdict: string | null;
  explanation: string | null;
};

type UploadResponse = {
  raw_file: RawFile;
  import_batch: { id: string; status: string; source_type: string };
  duplicate: boolean;
};

const navItems = [
  ["dashboard", "Dashboard"],
  ["imports", "Importacao"],
  ["review", "Revisao"],
  ["manual", "Lancamentos"],
  ["investments", "Investimentos"],
  ["cards", "Cartoes"],
  ["gold", "Indicadores"],
  ["simulator", "Simulador"],
  ["history", "Historico"],
] as const;

type Tab = (typeof navItems)[number][0];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers:
      init?.body instanceof FormData
        ? init.headers
        : { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep HTTP status text when the response body is not JSON.
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function money(value: unknown): string {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number.isFinite(amount) ? amount : 0);
}

function field(form: HTMLFormElement, name: string): string {
  return String(new FormData(form).get(name) ?? "").trim();
}

function checkbox(form: HTMLFormElement, name: string): boolean {
  return new FormData(form).get(name) === "on";
}

export default function Home() {
  const [active, setActive] = useState<Tab>("dashboard");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<JsonMap | null>(null);
  const [files, setFiles] = useState<RawFile[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [gold, setGold] = useState<Record<string, JsonMap[]>>({});
  const [lastUpload, setLastUpload] = useState<UploadResponse | null>(null);
  const [preview, setPreview] = useState<JsonMap | null>(null);
  const [simulation, setSimulation] = useState<JsonMap | null>(null);

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  async function loadData() {
    setStatus("loading");
    setError(null);
    try {
      const [
        healthResult,
        filesResult,
        accountsResult,
        categoriesResult,
        decisionsResult,
        passive,
        goal,
        reserve,
        allocation,
        commitments,
        context,
        alerts,
      ] = await Promise.all([
        api<JsonMap>("/health"),
        api<RawFile[]>("/files"),
        api<Account[]>("/manual/accounts"),
        api<Category[]>("/categories"),
        api<Decision[]>("/purchase-decisions"),
        api<JsonMap[]>("/gold/passive-income?limit=1"),
        api<JsonMap[]>("/gold/goal-100k?limit=1"),
        api<JsonMap[]>("/gold/reserve?limit=1"),
        api<JsonMap[]>("/gold/allocation?limit=20"),
        api<JsonMap[]>("/gold/future-commitments?limit=20"),
        api<JsonMap[]>("/gold/decision-context?limit=1"),
        api<JsonMap[]>("/gold/alerts?limit=20"),
      ]);
      setHealth(healthResult);
      setFiles(filesResult);
      setAccounts(accountsResult);
      setCategories(categoriesResult);
      setDecisions(decisionsResult);
      setGold({ passive, goal, reserve, allocation, commitments, context, alerts });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar dados.");
    } finally {
      setStatus("idle");
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const formData = new FormData(event.currentTarget);
    try {
      const uploaded = await api<UploadResponse>("/files/upload", {
        method: "POST",
        body: formData,
      });
      setLastUpload(uploaded);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no upload.");
    }
  }

  async function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const batchId = field(event.currentTarget, "batch_id");
    try {
      setPreview(await api<JsonMap>(`/import-batches/${batchId}/preview`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na pre-visualizacao.");
    }
  }

  async function approveImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const batchId = field(event.currentTarget, "batch_id");
    try {
      setPreview(await api<JsonMap>(`/import-batches/${batchId}/approve`, { method: "POST" }));
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na aprovacao.");
    }
  }

  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/manual/accounts", {
        method: "POST",
        body: JSON.stringify({
          institution: field(form, "institution"),
          account_name: field(form, "account_name"),
          account_type: field(form, "account_type"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar conta.");
    }
  }

  async function createCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/categories", {
        method: "POST",
        body: JSON.stringify({
          name: field(form, "name"),
          type: field(form, "type"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar categoria.");
    }
  }

  async function createTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/manual/transactions", {
        method: "POST",
        body: JSON.stringify({
          account_id: field(form, "account_id"),
          transaction_date: field(form, "transaction_date"),
          description_raw: field(form, "description_raw"),
          amount: field(form, "amount"),
          category_id: field(form, "category_id") || null,
          transaction_type: "manual",
          is_transfer: checkbox(form, "is_transfer"),
          is_recurring: checkbox(form, "is_recurring"),
          notes: field(form, "notes") || null,
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar lancamento.");
    }
  }

  async function createInvestment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/manual/investments", {
        method: "POST",
        body: JSON.stringify({
          institution: field(form, "institution"),
          product_name: field(form, "product_name"),
          asset_class: field(form, "asset_class"),
          reference_date: field(form, "reference_date"),
          gross_value: field(form, "gross_value"),
          net_value: field(form, "net_value") || null,
          liquidity: field(form, "liquidity") || null,
          maturity_date: field(form, "maturity_date") || null,
          rate_description: field(form, "rate_description") || null,
          counts_as_reserve: checkbox(form, "counts_as_reserve"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar investimento.");
    }
  }

  async function refreshGold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const referenceDate = field(event.currentTarget, "reference_date");
    try {
      await api(`/gold/refresh?reference_date=${referenceDate}`, { method: "POST" });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar Gold.");
    }
  }

  async function simulatePurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      const result = await api<JsonMap>("/purchase-decisions/simulate", {
        method: "POST",
        body: JSON.stringify({
          item: field(form, "item"),
          amount: field(form, "amount"),
          category_id: field(form, "category_id") || null,
          payment_method: field(form, "payment_method"),
          installments: Number(field(form, "installments") || "1"),
          reason: field(form, "reason"),
          urgency: field(form, "urgency"),
          is_planned: checkbox(form, "is_planned"),
          is_technology: checkbox(form, "is_technology"),
          justification: field(form, "justification") || null,
          decision_date: field(form, "decision_date") || null,
        }),
      });
      setSimulation(result);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na simulacao.");
    }
  }

  const latestPassive = gold.passive?.[0];
  const latestGoal = gold.goal?.[0];
  const latestReserve = gold.reserve?.[0];
  const latestContext = gold.context?.[0];

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Navegacao">
        <div className="brand">
          <span>SDFP</span>
          <strong>Decisao Financeira</strong>
        </div>
        <nav>
          {navItems.map(([id, label]) => (
            <button
              className={active === id ? "nav-item active" : "nav-item"}
              key={id}
              onClick={() => setActive(id)}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h1>{navItems.find(([id]) => id === active)?.[1]}</h1>
            <span className="status-pill">{status === "loading" ? "Carregando" : health ? "API online" : "API"}</span>
          </div>
          <button className="secondary" onClick={() => void loadData()} type="button">
            Atualizar
          </button>
        </header>

        {error ? <div className="error">{error}</div> : null}

        {active === "dashboard" ? (
          <section className="grid metrics">
            <Metric label="Renda passiva mes" value={money(latestPassive?.received_amount)} />
            <Metric label="Meta R$100 mil" value={`${Number(latestGoal?.progress_pct ?? 0).toFixed(1)}%`} />
            <Metric label="Reserva" value={money(latestReserve?.eligible_reserve_amount)} />
            <Metric label="Aporte minimo" value={money(latestContext?.minimum_monthly_contribution)} />
          </section>
        ) : null}

        {active === "imports" ? (
          <section className="workspace-grid">
            <form className="surface" onSubmit={submitUpload}>
              <h2>Importar arquivo</h2>
              <input name="file" required type="file" />
              <button type="submit">Enviar</button>
            </form>
            <div className="surface">
              <h2>Arquivos Bronze</h2>
              <DataTable
                columns={["Arquivo", "Fonte", "Status"]}
                rows={files.map((file) => [file.original_filename, file.source_type ?? "-", file.status])}
              />
              {lastUpload ? <pre>{JSON.stringify(lastUpload.import_batch, null, 2)}</pre> : null}
            </div>
          </section>
        ) : null}

        {active === "review" ? (
          <section className="workspace-grid">
            <form className="surface" onSubmit={submitPreview}>
              <h2>Pre-visualizar lote</h2>
              <input name="batch_id" placeholder="import_batch_id" required />
              <button type="submit">Prever</button>
            </form>
            <form className="surface" onSubmit={approveImport}>
              <h2>Aprovar para Silver</h2>
              <input name="batch_id" placeholder="import_batch_id" required />
              <button type="submit">Aprovar</button>
            </form>
            <div className="surface wide">
              <h2>Resultado</h2>
              {preview ? <pre>{JSON.stringify(preview, null, 2)}</pre> : <Empty />}
            </div>
          </section>
        ) : null}

        {active === "manual" ? (
          <section className="workspace-grid">
            <form className="surface" onSubmit={createAccount}>
              <h2>Conta</h2>
              <input name="institution" placeholder="Instituicao" required />
              <input name="account_name" placeholder="Nome da conta" required />
              <input name="account_type" placeholder="Tipo" required />
              <button type="submit">Criar conta</button>
            </form>
            <form className="surface" onSubmit={createCategory}>
              <h2>Categoria</h2>
              <input name="name" placeholder="Nome" required />
              <select name="type" required>
                <option value="expense">Despesa</option>
                <option value="income">Renda</option>
                <option value="investment">Investimento</option>
              </select>
              <button type="submit">Criar categoria</button>
            </form>
            <form className="surface wide" onSubmit={createTransaction}>
              <h2>Lancamento</h2>
              <select name="account_id" required>
                <option value="">Conta</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.institution} - {account.account_name}
                  </option>
                ))}
              </select>
              <input defaultValue={today} name="transaction_date" required type="date" />
              <input name="description_raw" placeholder="Descricao" required />
              <input name="amount" placeholder="Valor" required type="number" step="0.01" />
              <select name="category_id">
                <option value="">Categoria</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
              <label className="check"><input name="is_transfer" type="checkbox" /> Transferencia</label>
              <label className="check"><input name="is_recurring" type="checkbox" /> Recorrente</label>
              <input name="notes" placeholder="Notas" />
              <button type="submit">Salvar lancamento</button>
            </form>
          </section>
        ) : null}

        {active === "investments" ? (
          <section className="workspace-grid">
            <form className="surface wide" onSubmit={createInvestment}>
              <h2>Investimento manual</h2>
              <input name="institution" placeholder="Instituicao" required />
              <input name="product_name" placeholder="Produto" required />
              <select name="asset_class" required>
                <option value="cdb">CDB</option>
                <option value="fund">Fundo</option>
                <option value="alternative">Alternativo</option>
                <option value="pension">Previdencia</option>
              </select>
              <input defaultValue={today} name="reference_date" required type="date" />
              <input name="gross_value" placeholder="Valor bruto" required type="number" step="0.01" />
              <input name="net_value" placeholder="Valor liquido" type="number" step="0.01" />
              <input name="liquidity" placeholder="Liquidez" />
              <input name="maturity_date" type="date" />
              <input name="rate_description" placeholder="Taxa" />
              <label className="check"><input name="counts_as_reserve" type="checkbox" /> Conta como reserva</label>
              <button type="submit">Salvar investimento</button>
            </form>
          </section>
        ) : null}

        {active === "cards" ? (
          <section className="surface">
            <h2>Parcelas futuras</h2>
            <DataTable
              columns={["Mes", "Origem", "Descricao", "Valor"]}
              rows={(gold.commitments ?? []).map((item) => [
                String(item.due_month ?? "-"),
                String(item.source ?? "-"),
                String(item.description ?? "-"),
                money(item.amount),
              ])}
            />
          </section>
        ) : null}

        {active === "gold" ? (
          <section className="workspace-grid">
            <form className="surface" onSubmit={refreshGold}>
              <h2>Refresh Gold</h2>
              <input defaultValue={today} name="reference_date" required type="date" />
              <button type="submit">Atualizar Gold</button>
            </form>
            <div className="surface wide">
              <h2>Alocacao</h2>
              <DataTable
                columns={["Classe", "Valor", "%", "Reserva"]}
                rows={(gold.allocation ?? []).map((item) => [
                  String(item.asset_class ?? "-"),
                  money(item.amount),
                  `${Number(item.allocation_pct ?? 0).toFixed(1)}%`,
                  item.counts_as_reserve ? "Sim" : "Nao",
                ])}
              />
            </div>
          </section>
        ) : null}

        {active === "simulator" ? (
          <section className="workspace-grid">
            <form className="surface wide" onSubmit={simulatePurchase}>
              <h2>Posso Comprar?</h2>
              <input name="item" placeholder="Item" required />
              <input name="amount" placeholder="Valor" required type="number" step="0.01" />
              <select name="category_id">
                <option value="">Categoria</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
              <select name="payment_method" required>
                <option value="pix">Pix</option>
                <option value="debit">Debito</option>
                <option value="credit_card">Cartao</option>
              </select>
              <input defaultValue="1" min="1" name="installments" type="number" />
              <input name="reason" placeholder="Motivo" required />
              <select name="urgency" required>
                <option value="baixa">Baixa</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
              </select>
              <input defaultValue={today} name="decision_date" type="date" />
              <label className="check"><input name="is_planned" type="checkbox" /> Planejado</label>
              <label className="check"><input name="is_technology" type="checkbox" /> Tecnologia</label>
              <input name="justification" placeholder="Justificativa financeira" />
              <button type="submit">Simular</button>
            </form>
            <div className="surface">
              <h2>Resultado</h2>
              {simulation ? (
                <div className="result">
                  <strong>{String(simulation.verdict)}</strong>
                  <span>{String(simulation.explanation)}</span>
                  <span>{String(simulation.recommendation)}</span>
                </div>
              ) : (
                <Empty />
              )}
            </div>
          </section>
        ) : null}

        {active === "history" ? (
          <section className="surface">
            <h2>Decisoes</h2>
            <DataTable
              columns={["Data", "Item", "Valor", "Veredito"]}
              rows={decisions.map((decision) => [
                decision.decision_date,
                decision.item_name,
                money(decision.amount),
                decision.verdict ?? "-",
              ])}
            />
          </section>
        ) : null}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DataTable({ columns, rows }: { columns: string[]; rows: string[][] }) {
  if (rows.length === 0) {
    return <Empty />;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${row.join("-")}-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${cell}-${cellIndex}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Empty() {
  return <div className="empty">Sem dados</div>;
}
