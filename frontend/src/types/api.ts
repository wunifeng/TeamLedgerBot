// ── API Types matching backend Pydantic schemas exactly ─────────────────────

export type TransactionType = 'income' | 'expense' | 'salary'
export type CategoryType = 'income' | 'expense'

// Dashboard
export interface SummaryResponse {
  total_income: number
  total_expense: number
  total_salary: number
  net_profit: number
  transaction_count: number
  income_count: number
  expense_count: number
  salary_count: number
}

export interface DailyTrendItem {
  date: string // YYYY-MM-DD
  income: number
  expense: number
  net: number
}

export interface DailyTrendResponse {
  data: DailyTrendItem[]
  period_days: number
}

export interface MonthlyTrendItem {
  month: string // YYYY-MM
  income: number
  expense: number
  salary: number
  net: number
}

export interface MonthlyTrendResponse {
  data: MonthlyTrendItem[]
  period_months: number
}

export interface CategoryBreakdownItem {
  category_id: string
  category_name: string
  type: string
  total: number
  count: number
  percentage: number
}

export interface CategoryBreakdownResponse {
  income: CategoryBreakdownItem[]
  expense: CategoryBreakdownItem[]
}

// Transactions
export interface TransactionResponse {
  id: string
  type: TransactionType
  amount: number
  category_id: string | null
  category_name: string | null
  member_id: string
  member_name: string
  remark: string | null
  bonus: number | null
  created_at: string
  updated_at: string
}

export interface TransactionListResponse {
  items: TransactionResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface TransactionWriteResponse {
  transaction: TransactionResponse
  alerts: string[]
}

// Members
export interface MemberResponse {
  id: string
  name: string
  role: string | null
  is_active: boolean
  created_at: string
}

// Categories
export interface CategoryResponse {
  id: string
  name: string
  type: CategoryType
  description: string | null
  is_active: boolean
  created_at: string
}

// Write payloads
export interface IncomeCreate {
  amount: number
  category_id?: string
  member_id: string
  remark?: string
  timestamp?: string
}

export interface ExpenseCreate {
  amount: number
  category_id?: string
  member_id: string
  remark?: string
  timestamp?: string
}

export interface SalaryCreate {
  member_id: string
  salary_amount: number
  bonus?: number
  remark?: string
  timestamp?: string
}

export interface MemberCreate {
  name: string
  role?: string
}

export interface CategoryCreate {
  name: string
  type: CategoryType
  description?: string
}
