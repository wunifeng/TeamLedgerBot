export type SalarySettlementStatus = 'unpaid' | 'partial' | 'paid'
export type BankrollEntryType = 'initial' | 'top_up' | 'return' | 'adjustment'
export type BankrollAdjustmentDirection = 'increase' | 'decrease'

export interface MemberResponse {
  id: string
  name: string
  role: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface MemberCreate {
  name: string
  role?: string
}

export interface CategoryResponse {
  id: string
  name: string
  type: 'income' | 'expense'
  description: string | null
  is_active: boolean
  created_at: string
}

export interface VenueResponse {
  id: string
  name: string
  rebate_rate: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DailyFlowCreate {
  business_date: string
  member_id: string
  venue_id: string
  game: string
  card_number: string
  principal: number
  chip_code: number
  loss_rebate: number
  profit_loss: number
  remark?: string
}

export interface DailyFlowUpdate {
  principal?: number
  chip_code?: number
  loss_rebate?: number
  profit_loss?: number
  remark?: string
}

export interface DailyFlowResponse extends DailyFlowCreate {
  id: string
  member_name: string
  venue_name: string
  rebate_rate: number
  salary_amount: number
  salary_rule_description: string
  created_at: string
  updated_at: string
}

export interface DailyFlowListResponse {
  items: DailyFlowResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface FlowChangeLogResponse {
  id: string
  flow_id: string
  changed_at: string
  operator_name: string
  change_type: 'create' | 'update' | 'delete'
  before_data: Record<string, string | null> | null
  after_data: Record<string, string | null> | null
}

export interface MemberExpenseResponse {
  id: string
  business_date: string
  member_id: string
  member_name: string
  category_id: string | null
  category_name: string | null
  amount: number
  remark: string | null
  receipt_url: string | null
  reimbursed: boolean
  created_at: string
  updated_at: string
}

export interface MemberExpenseUpdate {
  amount?: number
  category_id?: string | null
  remark?: string | null
}

export interface ExpenseChangeLogResponse {
  id: string
  expense_id: string
  changed_at: string
  operator_name: string
  change_type: 'create' | 'update' | 'delete'
  before_data: Record<string, string | null> | null
  after_data: Record<string, string | null> | null
}

export interface MemberExpenseListResponse {
  items: MemberExpenseResponse[]
  total_amount: number
  total_unreimbursed: number
}

export interface SalarySettlementResponse {
  id: string
  member_id: string
  member_name: string
  period_start: string
  period_end: string
  payable_amount: number
  paid_amount: number
  unpaid_amount: number
  status: SalarySettlementStatus
  remark: string | null
  payments: SalaryPaymentItem[]
  created_at: string
  updated_at: string
}

export interface SalarySettlementListResponse {
  items: SalarySettlementResponse[]
  total_payable: number
  total_paid: number
  total_unpaid: number
}

export interface SalaryPaymentResponse {
  settlement: SalarySettlementResponse
  payment: SalaryPaymentItem
}

export interface SalaryPaymentItem {
  id: string
  settlement_id: string
  amount: number
  remark: string | null
  paid_at: string
  voided_at: string | null
  void_reason: string | null
}

export interface BankrollEntryCreate {
  business_date: string
  member_id: string
  entry_type: BankrollEntryType
  amount: number
  adjustment_direction?: BankrollAdjustmentDirection
  remark?: string
}

export interface BankrollEntryResponse {
  id: string
  business_date: string
  member_id: string
  member_name: string
  entry_type: BankrollEntryType
  amount: number
  adjustment_direction: BankrollAdjustmentDirection | null
  signed_amount: number
  remark: string | null
  voided_at: string | null
  void_reason: string | null
  voided_by_member_id: string | null
  voided_by_name: string | null
  created_at: string
}

export interface BankrollEntryListResponse {
  items: BankrollEntryResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface BankrollMemberBalance {
  member_id: string
  member_name: string
  role: string | null
  is_active: boolean
  balance: number
}

export interface BankrollSummaryResponse {
  items: BankrollMemberBalance[]
  total_balance: number
}

export interface SummaryResponse {
  total_profit_loss: number
  total_expense: number
  total_salary: number
  net_result: number
  flow_count: number
  expense_count: number
  unreimbursed_expense: number
}

export interface DailyTrendItem {
  date: string
  profit_loss: number
  expense: number
  salary: number
  net: number
}

export interface DailyTrendResponse {
  data: DailyTrendItem[]
  period_days: number
}

export interface VenueBreakdownResponse {
  items: Array<{
    venue_name: string
    profit_loss: number
    flow_count: number
  }>
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  member_name: string
  pin: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  member: MemberResponse
}
