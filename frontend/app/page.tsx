"use client";

import { FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

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

type ImportBatch = {
  id: string;
  raw_file_id: string;
  source_type: string;
  status: string;
  parser_name: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  error_message: string | null;
  raw_file: RawFile;
};

type Institution = {
  id: string;
  name: string;
  institution_type: string;
  is_active: boolean;
};

type ReferenceOption = {
  id: string;
  option_group: string;
  option_key: string;
  label: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
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

type Card = {
  id: string;
  institution: string;
  institution_id: string | null;
  card_name: string;
  brand: string | null;
  brand_id: string | null;
  last_four_digits: string | null;
  credit_limit: string | null;
  is_virtual: boolean;
  is_active: boolean;
};

type CardInvoice = {
  id: string;
  card_id: string;
  reference_month: string;
  due_date: string | null;
  total_amount: string;
  status: string;
};

type Decision = {
  id: string;
  decision_date: string;
  item_name: string;
  amount: string;
  verdict: string | null;
  explanation: string | null;
};

type ManualInvestment = {
  id: string;
  institution: string;
  product_name: string;
  product_id: string | null;
  asset_class: string;
  reference_date: string;
  gross_value: string;
  net_value: string | null;
  liquidity: string | null;
  liquidity_type: string | null;
  maturity_date: string | null;
  rate_description: string | null;
  rate_type: string | null;
  rate_index: string | null;
  rate_percent: string | null;
  rate_spread: string | null;
  rate_periodicity: string | null;
  counts_as_reserve: boolean;
};

type ManualTransaction = {
  id: string;
  account_id: string;
  transaction_date: string;
  description_raw: string;
  amount: string;
  category_id: string | null;
  transaction_type: string;
  direction: string;
  is_transfer: boolean;
  is_recurring: boolean;
  created_at: string;
};

type CardTransaction = {
  id: string;
  invoice_id: string;
  card_id: string;
  card_name: string | null;
  invoice_reference_month: string | null;
  purchase_date: string;
  description_raw: string;
  amount: string;
  category_id: string | null;
  category_name: string | null;
  installment_number: number;
  installment_total: number;
  is_installment: boolean;
  created_at: string;
};

type ActivityItem = {
  occurred_at: string;
  event_type: string;
  action: string;
  title: string;
  payload: JsonMap;
};

type UploadResponse = {
  raw_file: RawFile;
  import_batch: { id: string; status: string; source_type: string };
  duplicate: boolean;
};

type TabId =
  | "dashboard"
  | "imports"
  | "review"
  | "manual"
  | "investments"
  | "cards"
  | "gold"
  | "simulator"
  | "history"
  | "config";

const navItems: { id: TabId; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "imports", label: "Importacao" },
  { id: "review", label: "Revisao" },
  { id: "manual", label: "Lancamentos" },
  { id: "investments", label: "Investimentos" },
  { id: "cards", label: "Cartoes" },
  { id: "gold", label: "Indicadores" },
  { id: "simulator", label: "Simulador" },
  { id: "history", label: "Historico geral" },
  { id: "config", label: "Config" },
];

const STATIC_LABELS: Record<string, Record<string, string>> = {
  account_type: {
    cash: "Dinheiro",
    checking: "Conta corrente",
    investment: "Investimento",
    wallet: "Carteira",
  },
  action: {
    approved_to_silver: "Aprovado",
    create: "Criado",
    duplicate: "Duplicado",
    failed: "Falhou",
    raw_extracted: "Extraido",
    rejected: "Recusado",
    update: "Atualizado",
    upload_received: "Recebido",
    uploaded: "Enviado",
  },
  category_type: {
    expense: "Despesa",
    income: "Renda",
    investment: "Investimento",
    transfer: "Transferencia",
  },
  commitment_type: {
    installment: "Parcela",
  },
  event_type: {
    alteracao_manual: "Alteracao manual",
    arquivo_importado: "Arquivo importado",
    lote_importacao: "Lote de importacao",
  },
  investment_class: {
    acao: "Acao",
    alternative: "Alternativo",
    cdb: "CDB",
    etf: "ETF",
    fii: "FII",
    fund: "Fundo",
    pension: "Previdencia",
    renda_fixa: "Renda fixa",
  },
  invoice_status: {
    closed: "Fechada",
    open: "Aberta",
    paid: "Paga",
  },
  payment_method: {
    credit_card: "Cartao",
    debit: "Debito",
    pix: "Pix",
  },
  rate_index: {
    cdi: "CDI",
    fixed: "Fixa",
    ipca: "IPCA",
    selic: "Selic",
  },
  rate_periodicity: {
    annual: "Anual",
    monthly: "Mensal",
  },
  rate_type: {
    compound: "Composta",
    fixed: "Prefixada",
    indexed: "Indexada",
    post_fixed: "Pos-fixada",
  },
  severity: {
    error: "Erro",
    info: "Info",
    warning: "Atencao",
  },
  source: {
    card_installment: "Parcela de cartao",
  },
  status: {
    active: "Ativo",
    approved_to_silver: "Aprovado",
    building: "Em formacao",
    closed: "Fechado",
    complete: "Completa",
    duplicate: "Duplicado",
    empty: "Vazia",
    failed: "Falhou",
    open: "Aberto",
    paid: "Pago",
    raw_extracted: "Extraido",
    rejected: "Recusado",
    upload_received: "Recebido",
    uploaded: "Enviado",
  },
};

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
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (body.detail !== undefined) {
        detail = JSON.stringify(body.detail);
      }
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

function numberValue(value: unknown): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function percent(value: unknown): string {
  return `${numberValue(value).toFixed(1)}%`;
}

function field(form: HTMLFormElement, name: string): string {
  return String(new FormData(form).get(name) ?? "").trim();
}

function checkbox(form: HTMLFormElement, name: string): boolean {
  return new FormData(form).get(name) === "on";
}

function dateLabel(value: unknown): string {
  const text = String(value ?? "");
  return text.length >= 10 ? text.slice(0, 10) : text || "-";
}

function monthLabel(value: unknown): string {
  const text = String(value ?? "");
  return text.length >= 7 ? text.slice(0, 7) : text || "-";
}

function dateTimeLabel(value: unknown): string {
  const text = String(value ?? "");
  if (!text) {
    return "-";
  }
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) {
    return text;
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function compactJson(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function translate(group: string, value: unknown, options: ReferenceOption[] = []): string {
  const key = String(value ?? "");
  if (!key) {
    return "-";
  }
  const configured = options.find((option) => option.option_group === group && option.option_key === key);
  return configured?.label ?? STATIC_LABELS[group]?.[key] ?? key;
}

function optionKeyFromLabel(label: string): string {
  return label
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function reverseSeries(rows: JsonMap[], labelKey: string, valueKey: string): ChartPoint[] {
  return [...rows]
    .reverse()
    .map((item) => ({ label: monthLabel(item[labelKey]), value: numberValue(item[valueKey]) }));
}

function groupedCommitments(rows: JsonMap[]): ChartPoint[] {
  const grouped = new Map<string, number>();
  for (const row of rows) {
    const label = monthLabel(row.due_month);
    grouped.set(label, (grouped.get(label) ?? 0) + numberValue(row.amount));
  }
  return [...grouped.entries()].map(([label, value]) => ({ label, value })).slice(0, 8);
}

function groupedChartData(rows: ChartPoint[]): ChartPoint[] {
  const grouped = new Map<string, number>();
  for (const row of rows) {
    grouped.set(row.label, (grouped.get(row.label) ?? 0) + row.value);
  }
  return [...grouped.entries()].map(([label, value]) => ({ label, value }));
}

export default function Home() {
  const [active, setActive] = useState<TabId>("dashboard");
  const [importsTab, setImportsTab] = useState("send");
  const [reviewTab, setReviewTab] = useState("pending");
  const [manualTab, setManualTab] = useState("accounts");
  const [investmentsTab, setInvestmentsTab] = useState("form");
  const [cardsTab, setCardsTab] = useState("cards");
  const [goldTab, setGoldTab] = useState("refresh");
  const [simulatorTab, setSimulatorTab] = useState("simulate");
  const [configTab, setConfigTab] = useState("institutions");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<JsonMap | null>(null);
  const [files, setFiles] = useState<RawFile[]>([]);
  const [importBatches, setImportBatches] = useState<ImportBatch[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [referenceOptions, setReferenceOptions] = useState<ReferenceOption[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [cards, setCards] = useState<Card[]>([]);
  const [cardInvoices, setCardInvoices] = useState<CardInvoice[]>([]);
  const [cardTransactions, setCardTransactions] = useState<CardTransaction[]>([]);
  const [manualTransactions, setManualTransactions] = useState<ManualTransaction[]>([]);
  const [manualInvestments, setManualInvestments] = useState<ManualInvestment[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [gold, setGold] = useState<Record<string, JsonMap[]>>({});
  const [lastUpload, setLastUpload] = useState<UploadResponse | null>(null);
  const [lastGoldRefresh, setLastGoldRefresh] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<JsonMap | null>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [fileDetail, setFileDetail] = useState<JsonMap | null>(null);
  const [simulation, setSimulation] = useState<JsonMap | null>(null);
  const [categoryPreview, setCategoryPreview] = useState<JsonMap | null>(null);

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  async function loadData() {
    setStatus("loading");
    setError(null);
    try {
      const autoRefresh = await api<JsonMap>(`/gold/refresh?reference_date=${today}`, { method: "POST" }).catch(() => null);
      if (autoRefresh?.reference_date) {
        setLastGoldRefresh(String(autoRefresh.reference_date));
      }
      const [
        healthResult,
        filesResult,
        importBatchesResult,
        institutionsResult,
        referenceOptionsResult,
        accountsResult,
        categoriesResult,
        cardsResult,
        invoicesResult,
        cardTransactionsResult,
        manualTransactionsResult,
        investmentsResult,
        decisionsResult,
        activityResult,
        passive,
        goal,
        reserve,
        allocation,
        commitments,
        context,
        alerts,
      ] = await Promise.all([
        api<JsonMap>("/health"),
        api<RawFile[]>("/files?limit=100"),
        api<ImportBatch[]>("/import-batches?limit=100"),
        api<Institution[]>("/config/institutions?include_inactive=true"),
        api<ReferenceOption[]>("/config/options?include_inactive=true"),
        api<Account[]>("/manual/accounts"),
        api<Category[]>("/categories"),
        api<Card[]>("/cards"),
        api<CardInvoice[]>("/card-invoices"),
        api<CardTransaction[]>("/card-transactions?limit=150"),
        api<ManualTransaction[]>("/manual/transactions"),
        api<ManualInvestment[]>("/manual/investments"),
        api<Decision[]>("/purchase-decisions?limit=25"),
        api<ActivityItem[]>("/activity?limit=150"),
        api<JsonMap[]>("/gold/passive-income?limit=24"),
        api<JsonMap[]>("/gold/goal-100k?limit=24"),
        api<JsonMap[]>("/gold/reserve?limit=24"),
        api<JsonMap[]>("/gold/allocation?limit=50"),
        api<JsonMap[]>("/gold/future-commitments?limit=80"),
        api<JsonMap[]>("/gold/decision-context?limit=24"),
        api<JsonMap[]>("/gold/alerts?limit=50"),
      ]);
      setHealth(healthResult);
      setFiles(filesResult);
      setImportBatches(importBatchesResult);
      setInstitutions(institutionsResult);
      setReferenceOptions(referenceOptionsResult);
      setAccounts(accountsResult);
      setCategories(categoriesResult);
      setCards(cardsResult);
      setCardInvoices(invoicesResult);
      setCardTransactions(cardTransactionsResult);
      setManualTransactions(manualTransactionsResult);
      setManualInvestments(investmentsResult);
      setDecisions(decisionsResult);
      setActivity(activityResult);
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

  const activeInstitutions = institutions.filter((institution) => institution.is_active);
  const activeReferenceOptions = referenceOptions.filter((option) => option.is_active);
  const optionsFor = (group: string) => activeReferenceOptions.filter((option) => option.option_group === group);
  const formOptionsFor = (group: string): ReferenceOption[] => {
    const configured = optionsFor(group);
    if (configured.length > 0) {
      return configured;
    }
    return Object.entries(STATIC_LABELS[group] ?? {}).map(([option_key, label]) => ({
      id: `fallback-${group}-${option_key}`,
      option_group: group,
      option_key,
      label,
      description: null,
      is_system: true,
      is_active: true,
    }));
  };
  const pendingBatches = importBatches.filter((batch) =>
    ["raw_extracted", "upload_received"].includes(batch.status),
  );

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      const uploaded = await api<UploadResponse>("/files/upload", {
        method: "POST",
        body: formData,
      });
      setLastUpload(uploaded);
      setImportsTab("files");
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no upload.");
    }
  }

  async function viewFile(rawFileId: string) {
    try {
      setFileDetail(await api<JsonMap>(`/files/${rawFileId}`));
      setImportsTab("files");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao visualizar arquivo.");
    }
  }

  async function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const batchId = field(event.currentTarget, "batch_id");
    await previewImportBatch(batchId);
  }

  async function previewImportBatch(batchId: string) {
    try {
      setReviewResult(await api<JsonMap>(`/import-batches/${batchId}/preview`));
      setSelectedBatchId(batchId);
      setReviewTab("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na pre-visualizacao.");
    }
  }

  async function approveImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const batchId = field(event.currentTarget, "batch_id");
    await approveImportBatch(batchId);
  }

  async function approveImportBatch(batchId: string) {
    if (!batchId || !window.confirm("Aprovar este lote para Silver?")) {
      return;
    }
    try {
      setReviewResult(await api<JsonMap>(`/import-batches/${batchId}/approve`, { method: "POST" }));
      setSelectedBatchId(batchId);
      setReviewTab("preview");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na aprovacao.");
    }
  }

  async function rejectImportBatch(batchId: string) {
    if (!batchId) {
      return;
    }
    const reason = window.prompt("Motivo da recusa", "Importacao recusada na revisao.");
    if (reason === null) {
      return;
    }
    try {
      setReviewResult(
        await api<JsonMap>(`/import-batches/${batchId}/reject`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        }),
      );
      setSelectedBatchId(batchId);
      setReviewTab("preview");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao recusar lote.");
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

  async function createCategorizationRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/categorization-rules", {
        method: "POST",
        body: JSON.stringify({
          pattern: field(form, "pattern"),
          match_type: field(form, "match_type"),
          category_id: field(form, "category_id"),
          transaction_type: field(form, "transaction_type") || null,
          priority: Number(field(form, "priority") || "100"),
          confidence_score: field(form, "confidence_score") || "0.8000",
          is_active: true,
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar regra.");
    }
  }

  async function previewCategorization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      const result = await api<JsonMap>("/categorize/preview", {
        method: "POST",
        body: JSON.stringify({
          description: field(form, "description"),
          transaction_type: field(form, "transaction_type") || null,
        }),
      });
      setCategoryPreview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao prever categoria.");
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
    const productId = field(form, "product_id") || null;
    const productOption = productId ? activeReferenceOptions.find((option) => option.id === productId) : null;
    const productName = field(form, "product_name") || productOption?.label || "";
    try {
      if (!productName) {
        throw new Error("Informe ou selecione um produto.");
      }
      await api("/manual/investments", {
        method: "POST",
        body: JSON.stringify({
          institution: field(form, "institution"),
          product_name: productName,
          product_id: productId,
          asset_class: field(form, "asset_class"),
          reference_date: field(form, "reference_date"),
          gross_value: field(form, "gross_value"),
          net_value: field(form, "net_value") || null,
          liquidity: field(form, "liquidity") || null,
          liquidity_type: field(form, "liquidity_type") || null,
          maturity_date: field(form, "maturity_date") || null,
          rate_description: field(form, "rate_description") || null,
          rate_type: field(form, "rate_type") || null,
          rate_index: field(form, "rate_index") || null,
          rate_percent: field(form, "rate_percent") || null,
          rate_spread: field(form, "rate_spread") || null,
          rate_periodicity: field(form, "rate_periodicity") || null,
          counts_as_reserve: checkbox(form, "counts_as_reserve"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar investimento.");
    }
  }

  async function createCard(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const institutionId = field(form, "institution_id") || null;
    const institution = institutionId ? activeInstitutions.find((item) => item.id === institutionId) : null;
    const brandId = field(form, "brand_id") || null;
    const brand = brandId ? activeReferenceOptions.find((item) => item.id === brandId) : null;
    try {
      await api("/cards", {
        method: "POST",
        body: JSON.stringify({
          institution: institution?.name ?? field(form, "institution"),
          institution_id: institutionId,
          card_name: field(form, "card_name"),
          brand: brand?.label ?? (field(form, "brand") || null),
          brand_id: brandId,
          last_four_digits: field(form, "last_four_digits") || null,
          credit_limit: field(form, "credit_limit") || null,
          is_virtual: checkbox(form, "is_virtual"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar cartao.");
    }
  }

  async function createCardInvoice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/card-invoices", {
        method: "POST",
        body: JSON.stringify({
          card_id: field(form, "card_id"),
          reference_month: field(form, "reference_month"),
          due_date: field(form, "due_date") || null,
          total_amount: field(form, "total_amount") || "0",
          minimum_payment: field(form, "minimum_payment") || null,
          status: field(form, "status") || "open",
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar fatura.");
    }
  }

  async function createCardTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const invoiceId = field(form, "invoice_id");
    try {
      await api(`/card-invoices/${invoiceId}/transactions`, {
        method: "POST",
        body: JSON.stringify({
          purchase_date: field(form, "purchase_date"),
          description_raw: field(form, "description_raw"),
          amount: field(form, "amount"),
          category_id: field(form, "category_id") || null,
          installment_number: Number(field(form, "installment_number") || "1"),
          installment_total: Number(field(form, "installment_total") || "1"),
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar compra do cartao.");
    }
  }

  async function refreshGold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const referenceDate = field(event.currentTarget, "reference_date");
    try {
      const refreshed = await api<JsonMap>(`/gold/refresh?reference_date=${referenceDate}`, { method: "POST" });
      setLastGoldRefresh(String(refreshed.reference_date ?? referenceDate));
      setGoldTab("allocation");
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
      setSimulatorTab("simulate");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na simulacao.");
    }
  }

  async function createInstitution(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/config/institutions", {
        method: "POST",
        body: JSON.stringify({
          name: field(form, "name"),
          institution_type: field(form, "institution_type") || "other",
          is_active: true,
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar instituicao.");
    }
  }

  async function updateInstitution(institution: Institution, patch: Partial<Institution>) {
    try {
      await api(`/config/institutions/${institution.id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar instituicao.");
    }
  }

  async function editInstitution(institution: Institution) {
    const name = window.prompt("Nome da instituicao", institution.name);
    if (name === null || !name.trim()) {
      return;
    }
    await updateInstitution(institution, { name: name.trim() });
  }

  async function createReferenceOption(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const label = field(form, "label");
    try {
      await api("/config/options", {
        method: "POST",
        body: JSON.stringify({
          option_group: field(form, "option_group"),
          option_key: field(form, "option_key") || optionKeyFromLabel(label),
          label,
          description: field(form, "description") || null,
          is_active: true,
        }),
      });
      form.reset();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar opcao.");
    }
  }

  async function updateReferenceOption(option: ReferenceOption, patch: Partial<ReferenceOption>) {
    try {
      await api(`/config/options/${option.id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar opcao.");
    }
  }

  async function editReferenceOption(option: ReferenceOption) {
    const label = window.prompt("Rotulo", option.label);
    if (label === null || !label.trim()) {
      return;
    }
    await updateReferenceOption(option, { label: label.trim() });
  }

  const latestPassive = gold.passive?.[0];
  const latestGoal = gold.goal?.[0];
  const latestReserve = gold.reserve?.[0];
  const latestContext = gold.context?.[0];
  const passiveSeries = reverseSeries(gold.passive ?? [], "month", "received_amount");
  const goalSeries = reverseSeries(gold.goal ?? [], "reference_date", "invested_amount");
  const commitmentSeries = groupedCommitments(gold.commitments ?? []);
  const reserveBars = [
    { label: "Reserva", value: numberValue(latestReserve?.eligible_reserve_amount) },
    { label: "Alvo", value: numberValue(latestReserve?.reserve_target) },
  ];
  const allocationData = groupedChartData(
    (gold.allocation ?? []).map((item) => ({
      label: translate("investment_class", item.asset_class, referenceOptions),
      value: numberValue(item.amount),
    })),
  );
  const totalCommitments = commitmentSeries.reduce((sum, item) => sum + item.value, 0);
  const activeLabel = navItems.find((item) => item.id === active)?.label ?? "Dashboard";

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Navegacao">
        <div className="brand">
          <span>SDFP</span>
          <strong>Decisao Financeira</strong>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              className={active === item.id ? "nav-item active" : "nav-item"}
              key={item.id}
              onClick={() => setActive(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h1>{activeLabel}</h1>
            <span className="status-pill">{status === "loading" ? "Carregando" : health ? "API online" : "API"}</span>
            {lastGoldRefresh ? <span className="status-pill">Gold {dateLabel(lastGoldRefresh)}</span> : null}
          </div>
          <button className="secondary" onClick={() => void loadData()} type="button">
            Atualizar
          </button>
        </header>

        {error ? <div className="error">{error}</div> : null}

        {active === "dashboard" ? (
          <section className="dashboard">
            <div className="kpi-grid">
              <KpiCard
                detail={`Media 3M ${money(latestPassive?.avg_3m_received)}`}
                label="Renda passiva mes"
                value={money(latestPassive?.received_amount)}
              />
              <KpiCard
                detail={`${money(latestGoal?.invested_amount)} investidos`}
                label="Meta R$100 mil"
                value={percent(latestGoal?.progress_pct)}
              />
              <KpiCard
                detail={`Alvo ${money(latestReserve?.reserve_target)}`}
                label="Reserva"
                value={money(latestReserve?.eligible_reserve_amount)}
              />
              <KpiCard
                detail={`Proximos meses ${money(totalCommitments)}`}
                label="Compromissos"
                value={money(latestContext?.future_commitments_next_month)}
              />
            </div>

            <div className="dashboard-grid">
              <ChartPanel title="Meta R$100 mil">
                <LineChart color="#2563eb" data={goalSeries} valueLabel={money} />
              </ChartPanel>
              <ChartPanel title="Reserva vs alvo">
                <BarChart color="#059669" data={reserveBars} valueLabel={money} />
              </ChartPanel>
              <ChartPanel title="Alocacao patrimonial">
                <DonutChart data={allocationData} />
              </ChartPanel>
              <ChartPanel title="Renda passiva">
                <LineChart color="#b45309" data={passiveSeries} valueLabel={money} />
              </ChartPanel>
              <ChartPanel title="Compromissos futuros">
                <BarChart color="#7c3aed" data={commitmentSeries} valueLabel={money} />
              </ChartPanel>
              <section className="surface">
                <h2>Alertas</h2>
                <DataTable
                  columns={["Data", "Tipo", "Severidade", "Mensagem"]}
                  rows={(gold.alerts ?? []).slice(0, 5).map((item) => [
                    dateLabel(item.reference_date),
                    String(item.alert_type ?? "-"),
                    translate("severity", item.severity, referenceOptions),
                    String(item.message ?? "-"),
                  ])}
                />
              </section>
            </div>
          </section>
        ) : null}

        {active === "imports" ? (
          <section className="module">
            <ModuleTabs
              active={importsTab}
              onChange={setImportsTab}
              tabs={[
                { id: "send", label: "Enviar" },
                { id: "files", label: "Arquivos" },
              ]}
            />
            {importsTab === "send" ? (
              <form className="surface form-grid" onSubmit={submitUpload}>
                <h2>Importar arquivo</h2>
                <Field label="Arquivo">
                  <input name="file" required type="file" />
                </Field>
                <Field label="Tipo do arquivo">
                  <select name="source_type">
                    <option value="">Detectar automaticamente</option>
                    {formOptionsFor("import_source_type").map((option) => (
                      <option key={option.id} value={option.option_key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <div className="form-actions">
                  <button type="submit">Enviar</button>
                </div>
              </form>
            ) : null}
            {importsTab === "files" ? (
              <section className="surface">
                <h2>Arquivos Bronze</h2>
                <DataTable
                  columns={["Arquivo", "Fonte", "Importado em", "Status", "Acoes"]}
                  rows={files.map((file) => [
                    file.original_filename,
                    translate("import_source_type", file.source_type, referenceOptions),
                    dateTimeLabel(file.uploaded_at),
                    translate("status", file.status, referenceOptions),
                    <div className="row-actions">
                      <button className="secondary" onClick={() => void viewFile(file.id)} type="button">
                        Visualizar
                      </button>
                      <a className="button-link" href={`${API_BASE}/files/${file.id}/download`} rel="noreferrer" target="_blank">
                        Baixar
                      </a>
                    </div>,
                  ])}
                />
                {fileDetail ? (
                  <div className="result-stack">
                    <h2>Detalhe do arquivo</h2>
                    <SummaryRows
                      rows={[
                        ["Arquivo", String(fileDetail.original_filename ?? "-")],
                        ["Fonte", translate("import_source_type", fileDetail.source_type, referenceOptions)],
                        ["Data/hora", dateTimeLabel(fileDetail.uploaded_at)],
                        ["Status", translate("status", fileDetail.status, referenceOptions)],
                      ]}
                    />
                  </div>
                ) : null}
                {lastUpload ? (
                  <SummaryRows
                    rows={[
                      ["Ultimo lote", lastUpload.import_batch.id],
                      ["Status", translate("status", lastUpload.import_batch.status, referenceOptions)],
                    ]}
                  />
                ) : null}
              </section>
            ) : null}
          </section>
        ) : null}

        {active === "review" ? (
          <section className="module">
            <ModuleTabs
              active={reviewTab}
              onChange={setReviewTab}
              tabs={[
                { id: "pending", label: "Pendentes" },
                { id: "preview", label: "Previa" },
                { id: "history", label: "Historico" },
              ]}
            />
            {reviewTab === "pending" ? (
              <section className="surface">
                <h2>Lotes pendentes</h2>
                <DataTable
                  columns={["Arquivo", "Fonte", "Registros", "Status", "Acoes"]}
                  rows={pendingBatches.map((batch) => [
                    batch.raw_file.original_filename,
                    translate("import_source_type", batch.source_type, referenceOptions),
                    String(batch.total_records),
                    translate("status", batch.status, referenceOptions),
                    <div className="row-actions">
                      <button onClick={() => void previewImportBatch(batch.id)} type="button">
                        Visualizar
                      </button>
                      <button className="secondary" onClick={() => void rejectImportBatch(batch.id)} type="button">
                        Recusar
                      </button>
                    </div>,
                  ])}
                />
              </section>
            ) : null}
            {reviewTab === "preview" ? (
              <section className="surface">
                <h2>Previa do lote</h2>
                <form className="form-grid inline-form" onSubmit={submitPreview}>
                  <Field label="Import batch ID">
                    <input defaultValue={selectedBatchId} name="batch_id" required />
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Carregar</button>
                  </div>
                </form>
                <ReviewResult options={referenceOptions} value={reviewResult} />
                {selectedBatchId ? (
                  <div className="row-actions">
                    <button onClick={() => void approveImportBatch(selectedBatchId)} type="button">
                      Aprovar
                    </button>
                    <button className="secondary" onClick={() => void rejectImportBatch(selectedBatchId)} type="button">
                      Recusar
                    </button>
                  </div>
                ) : null}
              </section>
            ) : null}
            {reviewTab === "history" ? (
              <section className="surface">
                <h2>Historico de revisao</h2>
                <DataTable
                  columns={["Data/hora", "Arquivo", "Fonte", "Status", "Registros"]}
                  rows={importBatches.map((batch) => [
                    dateTimeLabel(batch.created_at),
                    batch.raw_file.original_filename,
                    translate("import_source_type", batch.source_type, referenceOptions),
                    translate("status", batch.status, referenceOptions),
                    String(batch.total_records),
                  ])}
                />
              </section>
            ) : null}
            <form className="sr-only" onSubmit={approveImport}>
              <Field label="Import batch ID">
                <input name="batch_id" />
              </Field>
            </form>
            <form className="sr-only" onSubmit={submitPreview}>
                <Field label="Import batch ID">
                  <input name="batch_id" />
                </Field>
            </form>
          </section>
        ) : null}

        {active === "manual" ? (
          <section className="module">
            <ModuleTabs
              active={manualTab}
              onChange={setManualTab}
              tabs={[
                { id: "accounts", label: "Contas" },
                { id: "categories", label: "Categorias" },
                { id: "rules", label: "Regras" },
                { id: "transaction", label: "Transacao" },
              ]}
            />
            {manualTab === "accounts" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createAccount}>
                  <h2>Conta</h2>
                  <Field label="Instituicao">
                    <select name="institution" required>
                      <option value="">Selecione</option>
                      {activeInstitutions.map((institution) => (
                        <option key={institution.id} value={institution.name}>
                          {institution.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Nome da conta">
                    <input name="account_name" required />
                  </Field>
                  <Field label="Tipo">
                    <select name="account_type" required>
                      {formOptionsFor("account_type").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Criar conta</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Contas cadastradas</h2>
                  <DataTable
                    columns={["Instituicao", "Conta", "Tipo"]}
                    rows={accounts.map((account) => [
                      account.institution,
                      account.account_name,
                      translate("account_type", account.account_type, referenceOptions),
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {manualTab === "categories" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createCategory}>
                  <h2>Categoria</h2>
                  <Field label="Nome">
                    <input name="name" required />
                  </Field>
                  <Field label="Tipo">
                    <select name="type" required>
                      <option value="expense">Despesa</option>
                      <option value="income">Renda</option>
                      <option value="investment">Investimento</option>
                    </select>
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Criar categoria</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Categorias</h2>
                  <DataTable
                    columns={["Nome", "Tipo"]}
                    rows={categories.map((category) => [category.name, translate("category_type", category.type, referenceOptions)])}
                  />
                </section>
              </div>
            ) : null}
            {manualTab === "rules" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createCategorizationRule}>
                  <h2>Regra de categoria</h2>
                  <Field label="Padrao textual">
                    <input name="pattern" required />
                  </Field>
                  <Field label="Categoria">
                    <select name="category_id" required>
                      <option value="">Selecione</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Tipo de match">
                    <select name="match_type" required>
                      <option value="contains">Contem</option>
                      <option value="startswith">Comeca com</option>
                      <option value="exact">Exato</option>
                    </select>
                  </Field>
                  <Field label="Tipo de transacao">
                    <input name="transaction_type" />
                  </Field>
                  <Field label="Prioridade">
                    <input defaultValue="100" min="0" name="priority" type="number" />
                  </Field>
                  <Field label="Confianca">
                    <input defaultValue="0.8000" max="1" min="0" name="confidence_score" step="0.0001" type="number" />
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Salvar regra</button>
                  </div>
                </form>
                <form className="surface form-grid" onSubmit={previewCategorization}>
                  <h2>Prever categoria</h2>
                  <Field label="Descricao">
                    <input name="description" required />
                  </Field>
                  <Field label="Tipo de transacao">
                    <input name="transaction_type" />
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Prever</button>
                  </div>
                  {categoryPreview ? (
                    <div className="result full">
                      <strong>{String(categoryPreview.category_name ?? "Nao classificado")}</strong>
                      <span>Confianca {numberValue(categoryPreview.confidence_score).toFixed(2)}</span>
                    </div>
                  ) : null}
                </form>
              </div>
            ) : null}
            {manualTab === "transaction" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createTransaction}>
                  <h2>Novo lancamento</h2>
                  <Field label="Conta">
                    <select name="account_id" required>
                      <option value="">Selecione</option>
                      {accounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.institution} - {account.account_name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Data">
                    <input defaultValue={today} name="transaction_date" required type="date" />
                  </Field>
                  <Field label="Descricao">
                    <input name="description_raw" required />
                  </Field>
                  <Field label="Valor">
                    <input name="amount" required step="0.01" type="number" />
                  </Field>
                  <Field label="Categoria">
                    <select name="category_id">
                      <option value="">Sem categoria</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Notas">
                    <input name="notes" />
                  </Field>
                  <CheckboxField label="Transferencia">
                    <input name="is_transfer" type="checkbox" />
                  </CheckboxField>
                  <CheckboxField label="Recorrente">
                    <input name="is_recurring" type="checkbox" />
                  </CheckboxField>
                  <div className="form-actions">
                    <button type="submit">Salvar lancamento</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Historico de lancamentos</h2>
                  <DataTable
                    columns={["Data", "Descricao", "Valor", "Tipo"]}
                    rows={manualTransactions.map((transaction) => [
                      dateLabel(transaction.transaction_date),
                      transaction.description_raw,
                      money(transaction.amount),
                      transaction.direction === "inflow" ? "Entrada" : "Saida",
                    ])}
                  />
                </section>
              </div>
            ) : null}
          </section>
        ) : null}

        {active === "investments" ? (
          <section className="module">
            <ModuleTabs
              active={investmentsTab}
              onChange={setInvestmentsTab}
              tabs={[
                { id: "form", label: "Cadastro" },
                { id: "allocation", label: "Patrimonio" },
              ]}
            />
            {investmentsTab === "form" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createInvestment}>
                  <h2>Novo investimento</h2>
                  <Field label="Instituicao">
                    <select name="institution" required>
                      <option value="">Selecione</option>
                      {activeInstitutions.map((institution) => (
                        <option key={institution.id} value={institution.name}>
                          {institution.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Produto cadastrado">
                    <select name="product_id">
                      <option value="">Produto livre</option>
                      {formOptionsFor("investment_product").map((option) => (
                        <option key={option.id} value={option.id}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Produto livre">
                    <input name="product_name" />
                  </Field>
                  <Field label="Classe">
                    <select name="asset_class" required>
                      {formOptionsFor("investment_class").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Data de referencia">
                    <input defaultValue={today} name="reference_date" required type="date" />
                  </Field>
                  <Field label="Valor bruto">
                    <input name="gross_value" required step="0.01" type="number" />
                  </Field>
                  <Field label="Valor liquido">
                    <input name="net_value" step="0.01" type="number" />
                  </Field>
                  <Field label="Tipo de liquidez">
                    <select name="liquidity_type">
                      <option value="">Selecione</option>
                      {formOptionsFor("liquidity").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Liquidez detalhe">
                    <input name="liquidity" />
                  </Field>
                  <Field label="Vencimento">
                    <input name="maturity_date" type="date" />
                  </Field>
                  <Field label="Tipo de taxa">
                    <select name="rate_type">
                      <option value="">Selecione</option>
                      {formOptionsFor("rate_type").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Indicador">
                    <select name="rate_index">
                      <option value="">Selecione</option>
                      {formOptionsFor("rate_index").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="% taxa">
                    <input name="rate_percent" step="0.0001" type="number" />
                  </Field>
                  <Field label="Spread adicional">
                    <input name="rate_spread" step="0.0001" type="number" />
                  </Field>
                  <Field label="Periodicidade">
                    <select name="rate_periodicity">
                      <option value="">Selecione</option>
                      {formOptionsFor("rate_periodicity").map((option) => (
                        <option key={option.id} value={option.option_key}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Taxa texto">
                    <input name="rate_description" />
                  </Field>
                  <CheckboxField label="Conta como reserva">
                    <input name="counts_as_reserve" type="checkbox" />
                  </CheckboxField>
                  <div className="form-actions">
                    <button type="submit">Salvar investimento</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Investimentos cadastrados</h2>
                  <DataTable
                    columns={["Origem", "Produto", "Classe", "Valor", "Taxa", "Liquidez", "Reserva"]}
                    rows={manualInvestments.map((investment) => [
                      investment.institution,
                      investment.product_name,
                      translate("investment_class", investment.asset_class, referenceOptions),
                      money(investment.net_value ?? investment.gross_value),
                      [
                        translate("rate_type", investment.rate_type, referenceOptions),
                        translate("rate_index", investment.rate_index, referenceOptions),
                        investment.rate_percent ? `${investment.rate_percent}%` : "",
                        investment.rate_spread ? `+ ${investment.rate_spread}%` : "",
                        translate("rate_periodicity", investment.rate_periodicity, referenceOptions),
                      ]
                        .filter((item) => item && item !== "-")
                        .join(" ") || investment.rate_description || "-",
                      investment.liquidity_type ? translate("liquidity", investment.liquidity_type, referenceOptions) : investment.liquidity || "-",
                      investment.counts_as_reserve ? "Sim" : "Nao",
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {investmentsTab === "allocation" ? (
              <section className="surface">
                <h2>Patrimonio por classe</h2>
                <DataTable
                  columns={["Classe", "Valor", "% da carteira", "Reserva"]}
                  rows={(gold.allocation ?? []).map((item) => [
                    translate("investment_class", item.asset_class, referenceOptions),
                    money(item.amount),
                    percent(item.allocation_pct),
                    item.counts_as_reserve ? "Sim" : "Nao",
                  ])}
                />
              </section>
            ) : null}
          </section>
        ) : null}

        {active === "cards" ? (
          <section className="module">
            <ModuleTabs
              active={cardsTab}
              onChange={setCardsTab}
              tabs={[
                { id: "cards", label: "Cartoes" },
                { id: "invoices", label: "Faturas" },
                { id: "purchases", label: "Compras" },
                { id: "installments", label: "Parcelas futuras" },
              ]}
            />
            {cardsTab === "cards" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createCard}>
                  <h2>Cartao</h2>
                  <Field label="Instituicao">
                    <select name="institution_id" required>
                      <option value="">Selecione</option>
                      {activeInstitutions.map((institution) => (
                        <option key={institution.id} value={institution.id}>
                          {institution.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Nome do cartao">
                    <input name="card_name" required />
                  </Field>
                  <Field label="Bandeira">
                    <select name="brand_id">
                      <option value="">Sem bandeira</option>
                      {formOptionsFor("card_brand").map((option) => (
                        <option key={option.id} value={option.id}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Ultimos 4 digitos">
                    <input maxLength={4} name="last_four_digits" />
                  </Field>
                  <Field label="Limite">
                    <input name="credit_limit" step="0.01" type="number" />
                  </Field>
                  <CheckboxField label="Cartao virtual">
                    <input name="is_virtual" type="checkbox" />
                  </CheckboxField>
                  <div className="form-actions">
                    <button type="submit">Criar cartao</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Cartoes cadastrados</h2>
                  <DataTable
                    columns={["Instituicao", "Cartao", "Bandeira", "Final", "Virtual", "Status"]}
                    rows={cards.map((card) => [
                      card.institution,
                      card.card_name,
                      card.brand ?? "-",
                      card.last_four_digits ?? "-",
                      card.is_virtual ? "Sim" : "Nao",
                      card.is_active ? "Ativo" : "Inativo",
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {cardsTab === "invoices" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createCardInvoice}>
                  <h2>Fatura</h2>
                  <Field label="Cartao">
                    <select name="card_id" required>
                      <option value="">Selecione</option>
                      {cards.map((card) => (
                        <option key={card.id} value={card.id}>
                          {card.institution} - {card.card_name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Mes de referencia">
                    <input defaultValue={today.slice(0, 8) + "01"} name="reference_month" required type="date" />
                  </Field>
                  <Field label="Vencimento">
                    <input name="due_date" type="date" />
                  </Field>
                  <Field label="Total">
                    <input name="total_amount" step="0.01" type="number" />
                  </Field>
                  <Field label="Pagamento minimo">
                    <input name="minimum_payment" step="0.01" type="number" />
                  </Field>
                  <Field label="Status">
                    <select name="status">
                      <option value="open">Aberta</option>
                      <option value="closed">Fechada</option>
                      <option value="paid">Paga</option>
                    </select>
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Criar fatura</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Faturas</h2>
                  <DataTable
                    columns={["Mes", "Total", "Status"]}
                    rows={cardInvoices.map((invoice) => [
                      monthLabel(invoice.reference_month),
                      money(invoice.total_amount),
                      translate("invoice_status", invoice.status, referenceOptions),
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {cardsTab === "purchases" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createCardTransaction}>
                  <h2>Nova compra</h2>
                  <Field label="Fatura">
                    <select name="invoice_id" required>
                      <option value="">Selecione</option>
                      {cardInvoices.map((invoice) => (
                        <option key={invoice.id} value={invoice.id}>
                          {monthLabel(invoice.reference_month)} - {money(invoice.total_amount)} - {translate("invoice_status", invoice.status, referenceOptions)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Data da compra">
                    <input defaultValue={today} name="purchase_date" required type="date" />
                  </Field>
                  <Field label="Descricao">
                    <input name="description_raw" required />
                  </Field>
                  <Field label="Valor da parcela">
                    <input name="amount" required step="0.01" type="number" />
                  </Field>
                  <Field label="Categoria">
                    <select name="category_id">
                      <option value="">Sem categoria</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Parcela atual">
                    <input defaultValue="1" min="1" name="installment_number" type="number" />
                  </Field>
                  <Field label="Total de parcelas">
                    <input defaultValue="1" min="1" name="installment_total" type="number" />
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Salvar compra</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Historico de compras</h2>
                  <DataTable
                    columns={["Data", "Cartao", "Descricao", "Valor", "Parcelas", "Categoria", "Acoes"]}
                    rows={cardTransactions.map((transaction) => [
                      dateLabel(transaction.purchase_date),
                      transaction.card_name ?? "-",
                      transaction.description_raw,
                      money(transaction.amount),
                      `${transaction.installment_number}/${transaction.installment_total}`,
                      transaction.category_name ?? "-",
                      <button className="secondary" onClick={() => window.alert(compactJson(transaction))} type="button">
                        Detalhe
                      </button>,
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {cardsTab === "installments" ? (
              <section className="surface">
                <h2>Parcelas futuras</h2>
                <DataTable
                  columns={["Mes", "Origem", "Descricao", "Valor"]}
                  rows={(gold.commitments ?? []).map((item) => [
                    monthLabel(item.due_month),
                    translate("source", item.source, referenceOptions),
                    String(item.description ?? "-"),
                    money(item.amount),
                  ])}
                />
              </section>
            ) : null}
          </section>
        ) : null}

        {active === "gold" ? (
          <section className="module">
            <ModuleTabs
              active={goldTab}
              onChange={setGoldTab}
              tabs={[
                { id: "refresh", label: "Refresh" },
                { id: "allocation", label: "Alocacao" },
                { id: "alerts", label: "Alertas" },
              ]}
            />
            {goldTab === "refresh" ? (
              <form className="surface form-grid" onSubmit={refreshGold}>
                <h2>Refresh Gold</h2>
                <Field label="Data de referencia">
                  <input defaultValue={today} name="reference_date" required type="date" />
                </Field>
                <div className="form-actions">
                  <button type="submit">Atualizar Gold</button>
                </div>
              </form>
            ) : null}
            {goldTab === "allocation" ? (
              <div className="workspace-grid">
                <section className="surface">
                  <h2>Alocacao</h2>
                  <DonutChart data={allocationData} />
                </section>
                <section className="surface">
                  <h2>Detalhe</h2>
                  <DataTable
                    columns={["Classe", "Valor", "% da carteira", "Reserva"]}
                  rows={(gold.allocation ?? []).map((item) => [
                      translate("investment_class", item.asset_class, referenceOptions),
                      money(item.amount),
                      percent(item.allocation_pct),
                      item.counts_as_reserve ? "Sim" : "Nao",
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {goldTab === "alerts" ? (
              <section className="surface">
                <h2>Alertas</h2>
                <DataTable
                  columns={["Data", "Tipo", "Severidade", "Mensagem"]}
                  rows={(gold.alerts ?? []).map((item) => [
                    dateLabel(item.reference_date),
                    String(item.alert_type ?? "-"),
                    translate("severity", item.severity, referenceOptions),
                    String(item.message ?? "-"),
                  ])}
                />
              </section>
            ) : null}
          </section>
        ) : null}

        {active === "simulator" ? (
          <section className="module">
            <ModuleTabs
              active={simulatorTab}
              onChange={setSimulatorTab}
              tabs={[
                { id: "simulate", label: "Simular" },
                { id: "history", label: "Historico" },
              ]}
            />
            {simulatorTab === "simulate" ? (
              <section className="surface">
                <form className="form-grid" onSubmit={simulatePurchase}>
                  <h2>Posso Comprar?</h2>
                  <Field label="Item">
                    <input name="item" required />
                  </Field>
                  <Field label="Valor">
                    <input name="amount" required step="0.01" type="number" />
                  </Field>
                  <Field label="Categoria">
                    <select name="category_id">
                      <option value="">Sem categoria</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Forma de pagamento">
                    <select name="payment_method" required>
                      <option value="pix">Pix</option>
                      <option value="debit">Debito</option>
                      <option value="credit_card">Cartao</option>
                    </select>
                  </Field>
                  <Field label="Parcelas">
                    <input defaultValue="1" min="1" name="installments" type="number" />
                  </Field>
                  <Field label="Motivo">
                    <input name="reason" required />
                  </Field>
                  <Field label="Urgencia">
                    <select name="urgency" required>
                      <option value="baixa">Baixa</option>
                      <option value="media">Media</option>
                      <option value="alta">Alta</option>
                    </select>
                  </Field>
                  <Field label="Data da decisao">
                    <input defaultValue={today} name="decision_date" type="date" />
                  </Field>
                  <Field label="Justificativa financeira">
                    <input name="justification" />
                  </Field>
                  <CheckboxField label="Planejado">
                    <input name="is_planned" type="checkbox" />
                  </CheckboxField>
                  <CheckboxField label="Tecnologia">
                    <input name="is_technology" type="checkbox" />
                  </CheckboxField>
                  <div className="form-actions">
                    <button type="submit">Simular</button>
                  </div>
                </form>
                {simulation ? (
                  <div className="result full">
                    <strong>{String(simulation.verdict)}</strong>
                    <span>{String(simulation.explanation)}</span>
                    <span>{String(simulation.recommendation)}</span>
                  </div>
                ) : null}
              </section>
            ) : null}
            {simulatorTab === "history" ? (
              <section className="surface">
                <h2>Historico de simulacoes</h2>
                <DataTable
                  columns={["Data", "Item", "Valor", "Veredito"]}
                  rows={decisions.map((decision) => [
                    dateLabel(decision.decision_date),
                    decision.item_name,
                    money(decision.amount),
                    decision.verdict ?? "-",
                  ])}
                />
              </section>
            ) : null}
          </section>
        ) : null}

        {active === "history" ? (
          <section className="surface">
            <h2>Historico geral</h2>
            <DataTable
              columns={["Data/hora", "Evento", "Acao", "Titulo", "Detalhe"]}
              rows={activity.map((item) => [
                dateTimeLabel(item.occurred_at),
                translate("event_type", item.event_type, referenceOptions),
                translate("action", item.action, referenceOptions),
                item.title,
                compactJson(item.payload),
              ])}
            />
          </section>
        ) : null}

        {active === "config" ? (
          <section className="module">
            <ModuleTabs
              active={configTab}
              onChange={setConfigTab}
              tabs={[
                { id: "institutions", label: "Instituicoes" },
                { id: "options", label: "Opcoes" },
              ]}
            />
            {configTab === "institutions" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createInstitution}>
                  <h2>Nova instituicao</h2>
                  <Field label="Nome">
                    <input name="name" required />
                  </Field>
                  <Field label="Tipo">
                    <select name="institution_type">
                      <option value="bank">Banco</option>
                      <option value="broker">Corretora</option>
                      <option value="wallet">Carteira</option>
                      <option value="other">Outro</option>
                    </select>
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Salvar instituicao</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Instituicoes</h2>
                  <DataTable
                    columns={["Nome", "Tipo", "Status", "Acoes"]}
                    rows={institutions.map((institution) => [
                      institution.name,
                      institution.institution_type,
                      institution.is_active ? "Ativa" : "Inativa",
                      <div className="row-actions">
                        <button className="secondary" onClick={() => void editInstitution(institution)} type="button">
                          Editar
                        </button>
                        <button
                          className="secondary"
                          onClick={() => void updateInstitution(institution, { is_active: !institution.is_active })}
                          type="button"
                        >
                          {institution.is_active ? "Inativar" : "Ativar"}
                        </button>
                      </div>,
                    ])}
                  />
                </section>
              </div>
            ) : null}
            {configTab === "options" ? (
              <div className="workspace-grid">
                <form className="surface form-grid" onSubmit={createReferenceOption}>
                  <h2>Nova opcao</h2>
                  <Field label="Grupo">
                    <select name="option_group" required>
                      <option value="investment_product">Produto de investimento</option>
                      <option value="investment_class">Classe de investimento</option>
                      <option value="card_brand">Bandeira de cartao</option>
                      <option value="liquidity">Liquidez</option>
                      <option value="rate_type">Tipo de taxa</option>
                      <option value="rate_index">Indicador</option>
                      <option value="rate_periodicity">Periodicidade</option>
                      <option value="account_type">Tipo de conta</option>
                      <option value="import_source_type">Tipo de arquivo</option>
                    </select>
                  </Field>
                  <Field label="Rotulo">
                    <input name="label" required />
                  </Field>
                  <Field label="Chave">
                    <input name="option_key" />
                  </Field>
                  <Field label="Descricao">
                    <input name="description" />
                  </Field>
                  <div className="form-actions">
                    <button type="submit">Salvar opcao</button>
                  </div>
                </form>
                <section className="surface">
                  <h2>Opcoes cadastradas</h2>
                  <DataTable
                    columns={["Grupo", "Chave", "Rotulo", "Status", "Acoes"]}
                    rows={referenceOptions.map((option) => [
                      option.option_group,
                      option.option_key,
                      option.label,
                      option.is_active ? "Ativa" : "Inativa",
                      <div className="row-actions">
                        <button className="secondary" onClick={() => void editReferenceOption(option)} type="button">
                          Editar
                        </button>
                        <button
                          className="secondary"
                          onClick={() => void updateReferenceOption(option, { is_active: !option.is_active })}
                          type="button"
                        >
                          {option.is_active ? "Inativar" : "Ativar"}
                        </button>
                      </div>,
                    ])}
                  />
                </section>
              </div>
            ) : null}
          </section>
        ) : null}
      </section>
    </main>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function CheckboxField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="check">
      {children}
      <span>{label}</span>
    </label>
  );
}

function ModuleTabs({
  active,
  onChange,
  tabs,
}: {
  active: string;
  onChange: (value: string) => void;
  tabs: { id: string; label: string }[];
}) {
  return (
    <div className="module-tabs">
      {tabs.map((tab) => (
        <button className={active === tab.id ? "tab-button active" : "tab-button"} key={tab.id} onClick={() => onChange(tab.id)} type="button">
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function KpiCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function ChartPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="surface chart-panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

type ChartPoint = {
  label: string;
  value: number;
};

function LineChart({
  data,
  color,
  valueLabel,
}: {
  data: ChartPoint[];
  color: string;
  valueLabel: (value: number) => string;
}) {
  const values = data.map((point) => point.value);
  const max = Math.max(...values, 1);
  const width = 420;
  const height = 190;
  const padding = 28;
  const points = data
    .map((point, index) => {
      const x = padding + (index * (width - padding * 2)) / Math.max(data.length - 1, 1);
      const y = height - padding - (point.value / max) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(" ");

  if (data.length === 0) {
    return <Empty />;
  }

  return (
    <div className="chart">
      <svg aria-hidden="true" role="img" viewBox={`0 0 ${width} ${height}`}>
        <line className="axis" x1={padding} x2={width - padding} y1={height - padding} y2={height - padding} />
        <line className="axis" x1={padding} x2={padding} y1={padding} y2={height - padding} />
        <polyline fill="none" points={points} stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" />
        {data.map((point, index) => {
          const x = padding + (index * (width - padding * 2)) / Math.max(data.length - 1, 1);
          const y = height - padding - (point.value / max) * (height - padding * 2);
          return <circle cx={x} cy={y} fill={color} key={`${point.label}-${index}`} r="4" />;
        })}
      </svg>
      <div className="chart-footer">
        <span>{data[0]?.label}</span>
        <strong>{valueLabel(data[data.length - 1]?.value ?? 0)}</strong>
        <span>{data[data.length - 1]?.label}</span>
      </div>
    </div>
  );
}

function BarChart({
  data,
  color,
  valueLabel,
}: {
  data: ChartPoint[];
  color: string;
  valueLabel: (value: number) => string;
}) {
  const max = Math.max(...data.map((point) => point.value), 1);

  if (data.length === 0) {
    return <Empty />;
  }

  return (
    <div className="bar-chart">
      {data.map((point, index) => (
        <div className="bar-row" key={`${point.label}-${index}`}>
          <span>{point.label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ background: color, width: `${Math.max((point.value / max) * 100, 2)}%` }} />
          </div>
          <strong>{valueLabel(point.value)}</strong>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ data }: { data: ChartPoint[] }) {
  const total = data.reduce((sum, point) => sum + point.value, 0);
  const colors = ["#2563eb", "#059669", "#b45309", "#dc2626", "#7c3aed", "#0891b2", "#4d7c0f"];
  let offset = 0;

  if (total <= 0 || data.length === 0) {
    return <Empty />;
  }

  return (
    <div className="donut-layout">
      <svg aria-hidden="true" className="donut" role="img" viewBox="0 0 160 160">
        <circle className="donut-base" cx="80" cy="80" fill="none" r="58" strokeWidth="18" />
        {data.map((point, index) => {
          const share = (point.value / total) * 100;
          const segment = (
            <circle
              className="donut-segment"
              cx="80"
              cy="80"
              fill="none"
              key={`${point.label}-${index}`}
              pathLength={100}
              r="58"
              stroke={colors[index % colors.length]}
              strokeDasharray={`${share} ${100 - share}`}
              strokeDashoffset={-offset}
              strokeWidth="18"
              transform="rotate(-90 80 80)"
            />
          );
          offset += share;
          return segment;
        })}
      </svg>
      <div className="donut-legend">
        {data.map((point, index) => (
          <div key={`${point.label}-${index}`}>
            <span style={{ background: colors[index % colors.length] }} />
            <strong>{point.label}</strong>
            <small>{percent((point.value / total) * 100)}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function SummaryRows({ rows }: { rows: string[][] }) {
  return (
    <dl className="summary-rows">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function ReviewResult({ value, options }: { value: JsonMap | null; options: ReferenceOption[] }) {
  if (!value) {
    return <Empty />;
  }

  const records = Array.isArray(value.records) ? (value.records as JsonMap[]) : [];
  const silverCounts = value.silver_counts as JsonMap | undefined;
  const rows = [
    ["Fonte", translate("import_source_type", value.source_type, options)],
    ["Status", translate("status", value.status, options)],
    ["Parser", String(value.parser_name ?? "-")],
    ["Registros", records.length ? String(records.length) : String(value.total_records ?? "-")],
  ];

  return (
    <div className="result-stack">
      <SummaryRows rows={rows} />
      {records.length > 0 ? (
        <DataTable
          columns={["#", "Revisao", "Dados"]}
          rows={records.slice(0, 80).map((record, index) => [
            String(index + 1),
            record.needs_review ? "Precisa revisar" : "OK",
            compactJson(record.data),
          ])}
        />
      ) : null}
      {silverCounts ? (
        <DataTable
          columns={["Silver", "Total"]}
          rows={Object.entries(silverCounts).map(([key, item]) => [key, String(item)])}
        />
      ) : null}
    </div>
  );
}

function DataTable({ columns, rows }: { columns: string[]; rows: ReactNode[][] }) {
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
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
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
