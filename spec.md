# TeamLedgerBot 前端软件规格说明书 (Software Specification)

本项目作为 `TeamLedgerBot` 的前端部分，旨在为团队提供一个现代、高效、美观的记账与财务管理可视化界面。前端将与已有的 FastAPI 后端完全分离部署，前端托管于 Vercel，后端托管于 Railway。

---

## 1. 需求分析与规格 (Requirements & Features)

前端界面采用 **方案 C（自适应双端响应式）** 设计，在不同设备上提供最适合的交互体验：
*   **移动端 (Mobile)**：聚焦于“随手记账”和“快速查看流水”，采用底部导航栏 (Bottom Navigation)，提供极简、大按钮的记账表单。
*   **桌面端 (Desktop)**：聚焦于“财务深度分析”和“团队管理”，采用左侧侧边栏 (Sidebar) 导航，提供丰富的收支统计图表、成员列表以及全局结算看板。

### 核心功能模块 (Core Modules)

#### 1.1 仪表盘 (Dashboard)
*   **总体收支看板**：展示当前账期的“总收入”、“总支出”、“应付未结工资”。
*   **收支趋势图**：以平滑折线图 (Area Chart) 展示最近几个账期的收支走势。
*   **分类占比图**：以环形图 (Donut Chart) 展示各项支出分类的占比（如服务器、餐饮、采购等）。
*   **快速记账入口**：一个浮动或置顶的“新增交易”按钮，点击后弹出记账模态框 (Modal)。

#### 1.2 交易流水 (Transactions)
*   **交易历史列表**：展示所有收支记录（金额、类型、分类、经手人、时间、备注）。
*   **多维度筛选**：支持按收支类型（收入/支出）、成员、分类目录、时间范围进行复合筛选。
*   **单笔详情与删除**：点击单条流水可查看完整详情，支持管理员删除或修改记录。

#### 1.3 成员与薪资管理 (Members & Salary)
*   **团队成员看板**：展示所有成员的头像、角色、当前未结余额。
*   **应付薪资统计**：自动计算每位成员在当前账期应发、已发和未发薪资。
*   **一键结算工资**：提供结算工资的交互流程（支持部分结算或全额结算），更新后端余额。

#### 1.4 分类与系统设置 (Categories & Settings)
*   **分类管理列表**：展示当前的收入/支出分类，支持自定义配色和图标。
*   **新增/编辑分类**：支持实时创建新的账目分类，以便记账时选择。

---

## 2. 视觉设计与 UI/UX 规范 (Design System)

为体现财务管理的专业性与现代感，我们将设计一套 **Premium Sleek Dark Mode (精致暗黑风格)** 视觉系统：

### 2.1 调色板 (Color Palette)
*   **背景色 (Background)**：`#0B0F19` (深邃蓝黑) / 卡片背景 `#161F30` (带微弱渐变与毛玻璃投影)。
*   **前景色 (Text)**：主文本 `#F3F4F6` (接近纯白) / 辅助文本 `#9CA3AF` (灰度级)。
*   **品牌主色 (Primary)**：`#6366F1` (靛蓝 Indigo) / `#3B82F6` (科技蓝 Blue)。
*   **状态色 (Status)**：
    *   收入 (Income)：`#10B981` (翡翠绿 Emerald)
    *   支出 (Expense)：`#F43F5E` (玫瑰红 Rose)
    *   薪资/待结 (Salary)：`#8B5CF6` (皇家紫 Violet)

### 2.2 核心设计元素 (Premium Visual Elements)
*   **毛玻璃质感 (Glassmorphism)**：使用 `backdrop-filter: blur(12px)` 配合半透明边框 `rgba(255,255,255,0.08)`，卡片自带深邃投影，营造三维悬浮质感。
*   **平滑微动效 (Micro-animations)**：
    *   按钮 hover 时自带柔和外发光 (Glow Effect) 与轻微缩放。
    *   弹窗/模态框唤起时使用缩放渐入 (Scale-in & Fade-in)。
    *   图表加载时提供平滑的动态绘制效果。

---

## 3. 技术栈选型 (Technology Stack)

*   **核心框架**：React 18+ (使用 TypeScript)
*   **构建工具**：Vite (极速的热更新与打包)
*   **样式系统**：Tailwind CSS (用于快速布局与自适应断点) + Vanilla CSS (用于自定义复杂动效与毛玻璃变量)
*   **图表库**：Recharts 或 Chart.js（专为 React 优化的响应式精美图表）
*   **网络请求**：Axios (支持请求拦截，全局处理 loading 和 error)
*   **状态管理**：React Context API (全局账期状态、当前登录用户状态)
*   **部署平台**：Vercel

---

## 4. API 联调与集成 (API Integration)

前端将通过环境变量 `VITE_API_BASE_URL` 配置 API 基础路径：
*   **本地开发**：`http://localhost:8000` (FastAPI 默认端口)
*   **生产环境**：Railway 部署的后端域名 (如 `https://team-ledger-bot-production.up.railway.app`)

### 接口对接点对应：
*   `GET /api/v1/dashboard/summary` -> 仪表盘统计
*   `GET /api/v1/transactions/` -> 交易流水列表
*   `POST /api/v1/transactions/` -> 新增记账交易
*   `GET /api/v1/members/` -> 成员列表
*   `POST /api/v1/salary/settle` -> 薪资结算交互
