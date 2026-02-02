# Initial Evaluation DocType - Setup Documentation

## Date: October 8, 2025

## Overview
Successfully created the **Initial Evaluation** DocType in the `phc_projects` custom app, copying all fields from the original `Initial Evaluation RM` in the `rowad_project` app.

---

## DocType Details

### Basic Information
- **Name**: Initial Evaluation
- **Module**: Phc Projects
- **Autoname**: IE-.######
- **Is Submittable**: Yes
- **Total Fields**: 56 fields
- **Track Changes**: Yes

### Source
- **Original DocType**: Initial Evaluation RM
- **Original App**: rowad_project
- **Source File**: `/apps/rowad_project/rowad_project/rowad_project/doctype/initial_evaluation_rm/initial_evaluation_rm.json`

---

## Field Structure

### 1. Customer Details Section
**Fields**:
- `rm_project_name` - Data (Required, Unique, In List View)
- `description` - Small Text (Description of competition)
- `location` - Data
- `customer_name` - Data
- `contractor_name` - Data

### 2. Evaluation Determinants Section
**Criteria with Yes/No or Status**:
- `completing_competition_documents` - Select (Yes/No)
- `specifications_and_requirements` - Select (There is/There isn't any)
- `lists_and_quantities` - Select (There is/There isn't any)
- `drawing` - Select (There is/There isn't any)
- `other` - Select (There is/There isn't any)
- `description_of_ed` - Small Text

**Location & Interview**:
- `location_of_ed` - Select (Yes/No)
- `location_provided` - Small Text
- `notes` - Data
- `description_of_ed2` - Small Text
- `interview_with_the_client_or_his_representative` - Select (Yes/No)
- `description_of_ed3` - Small Text

### 3. Evaluation Elements Section

**First - Nature of the Project**:
- `first_nature_of_the_project` - Select (Appropriate/Inappropriate)
- `description_of_ee` - Small Text

**Second - Project Type** (HTML Label + Checkboxes):
- `second_project_type` - HTML Label
- `operation` - Check
- `maintenance` - Check
- `construction` - Check
- `description_of_ee1` - Small Text

**Third - Type of Activity** (HTML Label + Checkboxes):
- `third_type_of_activity` - HTML Label
- `civil` - Check
- `electricity` - Check
- `mechanics` - Check

**Fourth - Preliminary Turnover Assessment**:
- `forth` - Select (Small/Medium/Big)
- `description_of_ee2` - Small Text

**Fifth - Initial Risk Assessment**:
- `fifth` - Select (Small/Medium/Big)

**Sixth - Contractor Requirements**:
- `sixth` - Select (Complete/Incomplete)
- `description_of_ee3` - Small Text

**Seventh - Logistical Support**:
- `seventh` - Select (Easy/Medium/Hard)
- `description_of_ee4` - Small Text

### 4. Board of Directors Section
**Fields**:
- `board_of_dirctors_approval` - Select
  - "Initial approval and completion of the study"
  - "Final rejection and referral of the project for termination"
- `notes_of_bd` - Small Text

### 5. Amendment Field
- `amended_from` - Link to Initial Evaluation

---

## Python Logic (`initial_evaluation.py`)

### Class: InitialEvaluation

**Methods**:

1. **validate()**
   - Validates the document before saving
   - Calls project name validation

2. **validate_project_name()**
   - Ensures project name uniqueness
   - Throws error if duplicate found
   - Checks across all Initial Evaluation documents

3. **on_submit()**
   - Placeholder for submit actions
   - Can be extended for workflows

4. **on_cancel()**
   - Placeholder for cancel actions
   - Can be extended for cleanup

---

## JavaScript Enhancements (`initial_evaluation.js`)

### Features

**1. Refresh Handler**:
- Adds custom buttons when submitted
- Sets up field properties
- Configures visibility based on document status

**2. Field Triggers**:
- `first_nature_of_the_project`: Shows warning if "Inappropriate"
- `board_of_dirctors_approval`: Shows alerts based on approval/rejection

**3. Helper Functions**:
- `setup_field_properties()`: Configures field requirements dynamically

---

## Permissions

### Roles with Access:

| Role | Create | Read | Write | Submit | Cancel | Delete | Amend |
|------|--------|------|-------|--------|--------|--------|-------|
| System Manager | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Projects Manager | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Projects User | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## File Structure

```
/apps/phc_projects/phc_projects/phc_projects/doctype/initial_evaluation/
├── __init__.py
├── initial_evaluation.json (56 fields)
├── initial_evaluation.py (validation logic)
└── initial_evaluation.js (client-side enhancements)
```

---

## Key Differences from Original

### Updates Made:
1. **Module**: Changed from "Rowad Project" to "Phc Projects"
2. **amended_from**: Now links to "Initial Evaluation" instead of "Initial Evaluation RM"
3. **Permissions**: Added Projects Manager and Projects User roles
4. **Track Changes**: Enabled for audit trail
5. **Links**: Removed original link to "Price Determination Form RM"

### Preserved:
- ✅ All 56 fields (exact copy)
- ✅ Field order maintained
- ✅ Field properties (required, unique, etc.)
- ✅ Select options
- ✅ HTML labels
- ✅ Section structure
- ✅ Autoname format (IE-.######)
- ✅ Submittable status

---

## Usage Instructions

### Creating a New Initial Evaluation

**Step 1**: Navigate to Initial Evaluation
- Desk → Search → "Initial Evaluation"
- Or: Projects Module → Initial Evaluation

**Step 2**: Create New
- Click "New" button
- Enter required Project Name (must be unique)

**Step 3**: Fill Customer Details
- Description of competition
- Location
- Customer Name
- Contractor Name

**Step 4**: Complete Evaluation Determinants
- Answer Yes/No questions
- Provide descriptions where needed
- Note location details
- Record client interview status

**Step 5**: Evaluation Elements
- Set nature of project (Appropriate/Inappropriate)
- Check applicable project types (operation/maintenance/construction)
- Check activity types (civil/electricity/mechanics)
- Assess turnover (Small/Medium/Big)
- Assess risk (Small/Medium/Big)
- Evaluate contractor requirements (Complete/Incomplete)
- Rate logistical support (Easy/Medium/Hard)

**Step 6**: Board of Directors
- Select approval status
- Add board notes

**Step 7**: Save and Submit
- Save draft
- Review all fields
- Submit for approval

---

## Validation Rules

### 1. Project Name
- **Required**: Yes
- **Unique**: Yes across all Initial Evaluations
- **Error**: "Project Name '{name}' already exists in another Initial Evaluation"

### 2. Submittable
- Document must be submitted to be final
- Can be amended after submission
- Cancelled documents cannot be resubmitted

---

## Client-Side Alerts

### Warning Alert
**Trigger**: Nature of project = "Inappropriate"
**Message**: "Project nature is marked as Inappropriate. Please review carefully."
**Color**: Orange

### Rejection Alert
**Trigger**: Board approval contains "rejection"
**Message**: "Project marked for rejection"
**Color**: Red

### Approval Alert
**Trigger**: Board approval contains "approval"
**Message**: "Project approved for study completion"
**Color**: Green

---

## Database Schema

### Table Name
`tabInitial Evaluation`

### Key Indexes
- Primary Key: `name`
- Unique: `rm_project_name`
- Search Index: `amended_from`

### Docstatus Values
- 0: Draft
- 1: Submitted
- 2: Cancelled

---

## Integration Points

### Potential Integrations
1. **Project Creation**: Link to Project DocType
2. **Price Determination**: Create price determination forms
3. **Workflow**: Add approval workflows
4. **Reports**: Generate evaluation reports
5. **Dashboard**: Add evaluation metrics

---

## Testing Checklist

### Basic Functionality
- [ ] Create new Initial Evaluation
- [ ] Save as draft
- [ ] Submit document
- [ ] Cancel document
- [ ] Amend submitted document

### Validation
- [ ] Project name uniqueness check
- [ ] Required fields validation
- [ ] Duplicate project name error

### UI/UX
- [ ] All fields display correctly
- [ ] Checkboxes work properly
- [ ] Select dropdowns populate
- [ ] Descriptions save properly
- [ ] Warnings show appropriately

### Permissions
- [ ] System Manager has full access
- [ ] Projects Manager can create/submit
- [ ] Projects User can only read
- [ ] Unauthorized users blocked

---

## Deployment Status

### Sites Updated
✅ All 5 sites successfully imported:
- local
- locale
- mnc.pioneers-holding.link
- phc.pioneers-holding.link
- rac.pioneers-holding.link

### Build Status
✅ App built successfully
✅ Cache cleared
✅ DocType accessible in all sites

---

## Future Enhancements

### Possible Additions
1. **Scoring System**: Auto-calculate evaluation scores
2. **Workflow**: Multi-level approval process
3. **Email Notifications**: Alert stakeholders
4. **PDF Generation**: Printable evaluation reports
5. **Dashboard Charts**: Evaluation statistics
6. **Document Linking**: Link to related projects
7. **Audit Trail**: Track all changes
8. **Custom Print Format**: Professional evaluation forms

---

## Maintenance

### To Update Fields
1. Edit `initial_evaluation.json`
2. Run: `bench migrate`
3. Clear cache: `bench clear-cache`
4. Rebuild: `bench build --app phc_projects`

### To Modify Logic
1. Edit `initial_evaluation.py`
2. Restart bench: `bench restart`

### To Update UI
1. Edit `initial_evaluation.js`
2. Clear cache: `bench clear-cache`
3. Rebuild: `bench build --app phc_projects`

---

## Troubleshooting

### Issue: DocType not appearing
**Solution**: 
- Run: `bench migrate`
- Clear cache: `bench clear-cache`
- Check module in DocType list

### Issue: Fields missing
**Solution**:
- Verify JSON has all fields
- Re-import: `bench console` → `import_file_by_path()`
- Check field_order in JSON

### Issue: Validation errors
**Solution**:
- Check Python logic in `.py` file
- Review error logs: `bench --site [site] logs`
- Test in console

---

## Support

### Documentation
- This file: `/apps/phc_projects/INITIAL_EVALUATION_SETUP.md`
- Original doctype: `/apps/rowad_project/.../initial_evaluation_rm.json`

### Contact
- System Administrator
- PHC Projects Team

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-08 | Initial creation from Initial Evaluation RM |

---

## Conclusion

The **Initial Evaluation** DocType has been successfully created in the `phc_projects` app with:

✅ **56 fields** copied from original  
✅ **All field properties** preserved  
✅ **Validation logic** implemented  
✅ **Client-side enhancements** added  
✅ **Multi-role permissions** configured  
✅ **Deployed to all sites** successfully  

**Status**: ✅ Fully operational and ready for use

---

**Created By**: AI Assistant  
**Date**: October 8, 2025  
**App**: phc_projects  
**Module**: Phc Projects

