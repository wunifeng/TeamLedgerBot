import apiClient from './apiClient'
import type {
  CategoryResponse,
  DailyFlowCreate,
  DailyFlowListResponse,
  DailyFlowResponse,
  DailyTrendResponse,
  MemberCreate,
  MemberExpenseListResponse,
  MemberExpenseResponse,
  MemberResponse,
  SalaryPaymentResponse,
  SalarySettlementListResponse,
  SummaryResponse,
  VenueBreakdownResponse,
  VenueResponse,
} from '@/types/api'

export const dashboardApi = {
  getSummary: () => apiClient.get<SummaryResponse>('/api/dashboard/summary').then((r) => r.data),
  getDailyTrend: (days = 30) => apiClient.get<DailyTrendResponse>('/api/dashboard/trend/daily', { params: { days } }).then((r) => r.data),
  getVenueBreakdown: () => apiClient.get<VenueBreakdownResponse>('/api/dashboard/venue-breakdown').then((r) => r.data),
}

export const flowsApi = {
  list: (params?: { member_id?: string; venue_id?: string; start_date?: string; end_date?: string; page?: number; limit?: number }) =>
    apiClient.get<DailyFlowListResponse>('/api/flows', { params }).then((r) => r.data),
  create: (data: DailyFlowCreate) => apiClient.post<DailyFlowResponse>('/api/flows', data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/flows/${id}`),
}

export const expensesApi = {
  list: (params?: { member_id?: string; reimbursed?: boolean }) =>
    apiClient.get<MemberExpenseListResponse>('/api/expenses', { params }).then((r) => r.data),
  create: (data: FormData) => apiClient.post<MemberExpenseResponse>('/api/expenses', data).then((r) => r.data),
  setReimbursed: (id: string, reimbursed: boolean) =>
    apiClient.patch<MemberExpenseResponse>(`/api/expenses/${id}/reimbursed`, { reimbursed }).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/expenses/${id}`),
}

export const salaryApi = {
  listSettlements: (params: { period_start: string; period_end: string; include_inactive?: boolean }) =>
    apiClient.get<SalarySettlementListResponse>('/api/salary/settlements', { params }).then((r) => r.data),
  paySettlement: (id: string, data: { amount: number; remark?: string }) =>
    apiClient.post<SalaryPaymentResponse>(`/api/salary/settlements/${id}/pay`, data).then((r) => r.data),
}

export const membersApi = {
  list: (include_inactive = false) =>
    apiClient.get<MemberResponse[]>('/api/members', { params: { include_inactive } }).then((r) => r.data),
  create: (data: MemberCreate) => apiClient.post<MemberResponse>('/api/members', data).then((r) => r.data),
  update: (id: string, data: Partial<MemberCreate & { is_active: boolean }>) =>
    apiClient.patch<MemberResponse>(`/api/members/${id}`, data).then((r) => r.data),
}

export const venuesApi = {
  list: (include_inactive = false) =>
    apiClient.get<VenueResponse[]>('/api/venues', { params: { include_inactive } }).then((r) => r.data),
  games: () => apiClient.get<string[]>('/api/venues/games').then((r) => r.data),
  rebateRates: () => apiClient.get<number[]>('/api/venues/rebate-rates').then((r) => r.data),
  create: (data: { name: string; rebate_rate: number }) =>
    apiClient.post<VenueResponse>('/api/venues', data).then((r) => r.data),
  update: (id: string, data: Partial<{ name: string; rebate_rate: number; is_active: boolean }>) =>
    apiClient.patch<VenueResponse>(`/api/venues/${id}`, data).then((r) => r.data),
}

export const categoriesApi = {
  listExpenses: () => apiClient.get<CategoryResponse[]>('/api/categories', { params: { type: 'expense' } }).then((r) => r.data),
  createExpense: (data: { name: string; description?: string }) =>
    apiClient.post<CategoryResponse>('/api/categories', { ...data, type: 'expense' }).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/categories/${id}`),
}
