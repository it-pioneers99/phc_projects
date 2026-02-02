# Budget Expense Management System - Implementation Summary

## Overview
This document describes the Budget Expense Management System implemented in the PHC Projects app. The system provides comprehensive budget control for projects with real-time tracking of budget vs actual spending.

## Components Created

### 1. DocTypes

#### Budget Expense Item (Master Data)
- **Path**: `phc_projects/phc_projects/phc_projects/doctype/budget_expense_item/`
- **Purpose**: Master data for budget items
- **Fields**:
  - Budget Item Name (Data, Unique, Required)
  - Budget Item Type (Select: Civil/Mechanic/Electric, Required)
  - Budget Item Source (Data)
  - Unit Cost (Currency, Required)

#### Budget Expense Detail (Child Table)
- **Path**: `phc_projects/phc_projects/phc_projects/doctype/budget_expense_detail/`
- **Purpose**: Child table for Budget Expense document
- **Fields**:
  1. Budget Item Name (Link → Budget Expense Item, Required)
  2. Budget Item Cost (Currency, Read Only) - Calculated as Unit Cost × Qty
  3. Used Cost (PO) (Currency, Read Only) - From Purchase Orders
  4. Difference (Currency, Read Only) - Budget Cost - (PO + PI)
  5. Budget Item Type (Select, Read Only) - Fetched from master
  6. Budget Item Qty (Float, Required)
  7. Used Cost (PI/PC Clearance) (Currency, Read Only) - From Purchase Invoices and PC Clearance
  8. Budget Item Source (Data, Read Only) - Fetched from master

#### Budget Expense (Main Document)
- **Path**: `phc_projects/phc_projects/phc_projects/doctype/budget_expense/`
- **Purpose**: Main budget control document
- **Features**:
  - Submittable document
  - Track changes enabled
  - Project-wise budget control
  - Auto-calculation of totals
- **Fields**:
  - Project (Link → Project, Required)
  - Company (Link → Company, Required)
  - Budget Date (Date)
  - Budget Expense Detail (Table)
  - **Totals Section**:
    - Total Budget Cost (Currency, Read Only)
    - Total Used PO Cost (Currency, Read Only)
    - Total Used PI Cost (Currency, Read Only)
    - Total Difference (Currency, Read Only)

### 2. Custom Fields

#### Purchase Order Item
- **Field**: `budget_expense_item` (Link → Budget Expense Item)
- **Properties**: Mandatory, In List View
- **Location**: After "project" field

#### PC Clearance Detail
- **Field**: `budget_expense_item` (Link → Budget Expense Item)
- **Properties**: Mandatory, In List View
- **Location**: After "project" field

#### Purchase Invoice Item
- **Field**: `budget_expense_item` (Link → Budget Expense Item)
- **Properties**: Optional (for tracking)
- **Location**: After "project" field

### 3. Server Scripts

#### Budget Validation
- **Path**: `phc_projects/phc_projects/phc_projects/budget_control/purchase_order_validation.py`
- **Functions**:
  - `validate_budget_on_po_submit()`: Prevents PO submission if budget exceeded
  - `validate_budget_on_pc_clearance_submit()`: Prevents PC Clearance submission if budget exceeded
- **Hooks**: Configured in `hooks.py` via `doc_events`

### 4. Reports

#### Budget vs Actual Report
- **Path**: `phc_projects/phc_projects/phc_projects/report/budget_vs_actual/`
- **Type**: Script Report
- **Columns**:
  - Project
  - Budget Expense Item
  - Budget Item Type
  - Budget Cost
  - PO Actual
  - PI/PC Actual
  - Total Actual
  - Difference
  - Status (Over Budget / On Budget / Under Budget)
- **Filters**:
  - Project
  - Budget Item Type (Civil/Mechanic/Electric)

## How It Works

### Budget Creation
1. Create Budget Expense Items (master data)
2. Create Budget Expense document for a project
3. Add budget items in the child table
4. System automatically calculates:
   - Budget Item Cost = Unit Cost × Quantity
   - Used costs from PO and PI/PC Clearance
   - Difference = Budget - Used
5. Submit the Budget Expense document

### Purchase Order Flow
1. When creating a PO, user must select Budget Expense Item for each item
2. On PO submission, system validates:
   - Budget Expense Item is selected
   - Budget exists for the item in the project
   - Budget is not exceeded
3. If validation fails, PO submission is blocked with detailed error message

### PC Clearance Flow
1. When creating PC Clearance, user must select Budget Expense Item for each item
2. On PC Clearance submission, system validates:
   - Budget Expense Item is selected
   - Budget exists for the item in the project
   - Budget is not exceeded
3. If validation fails, PC Clearance submission is blocked with detailed error message

### Budget Tracking
- Budget Expense document automatically calculates used costs from:
  - Purchase Orders (submitted)
  - Purchase Invoices (submitted)
  - PC Clearance (submitted)
- Calculations are project-specific
- Use "Refresh Budget Usage" button to recalculate

## Features

✅ **Project-wise Budget Control**: Each budget is tied to a specific project
✅ **Real-time Budget Tracking**: Automatic calculation of used vs budgeted amounts
✅ **Hard Budget Enforcement**: PO and PC Clearance cannot be submitted if budget exceeded
✅ **Budget vs Actual Report**: Comprehensive reporting with filters
✅ **Multiple Budget Item Types**: Civil, Mechanic, Electric categorization
✅ **Automatic Calculations**: Budget costs, used costs, and differences calculated automatically
✅ **Alerts on Over-spending**: Clear error messages when budget is exceeded

## Installation Steps

1. **Run Migration**:
   ```bash
   bench --site [site-name] migrate
   ```

2. **Create Budget Expense Items**:
   - Navigate to Budget Expense Item
   - Create master records for all budget items

3. **Create Budget Expense Documents**:
   - Navigate to Budget Expense
   - Create budget for each project
   - Add budget items and quantities
   - Submit the document

4. **Use in Purchase Orders and PC Clearance**:
   - Budget Expense Item field will appear automatically
   - Select appropriate budget item for each line item
   - System will validate on submission

## Notes

- Budget Expense must be submitted before it can be used in PO/PC Clearance
- Budget calculations are project-specific
- Used costs are calculated from submitted documents only
- Budget vs Actual report shows real-time status

## Troubleshooting

### Budget not found error
- Ensure Budget Expense document is created and submitted for the project
- Verify Budget Expense Item is correctly linked

### Budget exceeded error
- Check available budget in Budget Expense document
- Review existing PO/PC Clearance for the project
- Adjust budget or reduce purchase amounts

### Calculations not updating
- Click "Refresh Budget Usage" button in Budget Expense document
- Ensure related PO/PC Clearance documents are submitted

