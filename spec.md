# TeamLedgerBot 业务规格说明

## 1. 业务范围

TeamLedgerBot 用于记录团队成员的每日业务流水、成员垫付支出和工资月结。

### 1.1 每日流水

成员通过网页表单上报：

- 日期：必须包含年份，默认当天。
- 人员：从成员列表选择。
- 场子：从场子配置选择。
- 游戏：从工资规则配置读取固定列表。
- 卡号：自由文本，`0` 表示未看到会员卡号。
- 本金、点码、输反、赢亏、备注。

系统必须校验：

```text
赢亏 = 点码 + 输反 - 本金
```

校验不一致时拒绝提交。

同一成员同一天可以提交多条流水，但以下组合不允许重复：

```text
成员 + 日期 + 场子 + 赢亏
```

### 1.2 自动工资

工资不由成员填写。系统根据场子的输返比例、游戏和赢亏区间，从
`backend/app/data/salary_config.json` 计算单条流水工资。

每条流水必须保存工资结果和规则快照。工资账期按自然月汇总，支持登记实际发放金额，并展示应付、已付和未付。

### 1.3 成员垫付

成员替团队支付费用时，通过网页登记：

- 日期、成员、分类、金额、备注。
- 可选凭证上传。
- 已报销或未报销状态。

不需要审批流程。

### 1.4 Telegram

Telegram 群组仅接收通知，不作为数据录入入口。

## 2. 场子与游戏配置

- 场子由设置页面维护名称、启停状态和输返比例。
- 输返比例必须存在于工资规则配置中。
- 游戏列表从工资规则配置读取，当前包括 `BJ`、`UTH`、`俄罗斯`、`百家乐`。

## 3. 部署说明

- 数据库迁移使用 Alembic。
- 本次迁移会删除旧 `transactions` 和旧 `salary_settlements` 数据，不执行旧数据转换。
- 凭证默认存储到 `UPLOAD_DIR`。Railway 部署时必须将 `UPLOAD_DIR` 指向持久化 Volume，例如 `/data/uploads`。
- 若后续切换对象存储，应保留现有 `receipt_url` 协议。

## 4. 本地验证

后端：

```powershell
cd backend
.\.venv312\Scripts\python.exe -m unittest discover -s .\tests -p 'test_*.py' -v
.\.venv312\Scripts\alembic.exe upgrade head --sql
```

前端：

```powershell
cd frontend
npm run build
```
