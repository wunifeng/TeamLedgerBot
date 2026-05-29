import apiClient from './apiClient'
import type {
  SummaryResponse,
  DailyTrendResponse,
  MonthlyTrendResponse,
  CategoryBreakdownResponse,
  TransactionListResponse,
  TransactionResponse,
  TransactionWriteResponse,
  MemberResponse,
  CategoryResponse,
  IncomeCreate,
  ExpenseCreate,
  SalaryCreate,
  MemberCreate,
  CategoryCreate,
  TransactionType,
  SalarySettlementCreate,
  SalarySettlementListResponse,
  SalaryPaymentCreate,
  SalaryPaymentResponse,
  SalarySettlementResponse,
} from '@/types/api'

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardApi = {
  getSummary: (params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<SummaryResponse>('/api/dashboard/summary', { params }).then((r) => r.data),

  getDailyTrend: (days = 30) =>
    apiClient.get<DailyTrendResponse>('/api/dashboard/trend/daily', { params: { days } }).then((r) => r.data),

  getMonthlyTrend: (months = 12) =>
    apiClient.get<MonthlyTrendResponse>('/api/dashboard/trend/monthly', { params: { months } }).then((r) => r.data),

  getCategoryBreakdown: (params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<CategoryBreakdownResponse>('/api/dashboard/category-breakdown', { params }).then((r) => r.data),
}

// ── Transactions ──────────────────────────────────────────────────────────────

export const transactionsApi = {
  list: (params?: {
    type?: TransactionType
    member_id?: string
    start_date?: string
    end_date?: string
    page?: number
    limit?: number
  }) =>
    apiClient.get<TransactionListResponse>('/api/transactions', { params }).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<TransactionResponse>(`/api/transactions/${id}`).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/api/transactions/${id}`),

  createIncome: (data: IncomeCreate) =>
    apiClient.post<TransactionWriteResponse>('/api/income', data).then((r) => r.data),

  createExpense: (data: ExpenseCreate) =>
    apiClient.post<TransactionWriteResponse>('/api/expense', data).then((r) => r.data),

  createSalary: (data: SalaryCreate) =>
    apiClient.post<TransactionWriteResponse>('/api/salary', data).then((r) => r.data),
}

// ── Salary settlements ───────────────────────────────────────────────────────

export const salaryApi = {
  listSettlements: (params?: {
    period_start?: string
    period_end?: string
    include_inactive?: boolean
  }) =>
    apiClient
      .get<SalarySettlementListResponse>('/api/salary/settlements', { params })
      .then((r) => r.data),

  upsertSettlement: (data: SalarySettlementCreate) =>
    apiClient
      .post<SalarySettlementResponse>('/api/salary/settlements', data)
      .then((r) => r.data),

  paySettlement: (id: string, data: SalaryPaymentCreate) =>
    apiClient
      .post<SalaryPaymentResponse>(`/api/salary/settlements/${id}/pay`, data)
      .then((r) => r.data),
}

// ── Members ───────────────────────────────────────────────────────────────────

export const membersApi = {
  list: (include_inactive = false) =>
    apiClient.get<MemberResponse[]>('/api/members', { params: { include_inactive } }).then((r) => r.data),

  create: (data: MemberCreate) =>
    apiClient.post<MemberResponse>('/api/members', data).then((r) => r.data),

  update: (id: string, data: Partial<MemberCreate & { is_active: boolean }>) =>
    apiClient.patch<MemberResponse>(`/api/members/${id}`, data).then((r) => r.data),

  deactivate: (id: string) =>
    apiClient.delete(`/api/members/${id}`),
}

// ── Categories ────────────────────────────────────────────────────────────────

export const categoriesApi = {
  list: (params?: { type?: string; include_inactive?: boolean }) =>
    apiClient.get<CategoryResponse[]>('/api/categories', { params }).then((r) => r.data),

  create: (data: CategoryCreate) =>
    apiClient.post<CategoryResponse>('/api/categories', data).then((r) => r.data),

  update: (id: string, data: Partial<CategoryCreate & { is_active: boolean }>) =>
    apiClient.patch<CategoryResponse>(`/api/categories/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/api/categories/${id}`),
}
