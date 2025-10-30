# Project Overview: Excel Merger

This document provides a summary of the Excel Merger application based on the project's `README.md`.

## 1. Core Purpose

The Excel Merger is a desktop GUI application built with **PySide6**. Its primary function is to merge multiple sheets from various Excel files (`.xlsx`, `.xls`) into a single output Excel file.

## 2. Key Features

*   **File & Sheet Selection:**
    *   Add multiple Excel files via a file dialog or drag-and-drop.
    *   Select individual sheets from the added files to be included in the merge.
    *   Reorder files and sheets to control the merge sequence.
    *   Convenience options to select all sheets or specific sheets by their position (e.g., the 1st and 3rd sheet of every file).

*   **Merge Strategies:**
    *   **Sheet Merge:** Each selected sheet becomes a separate sheet in the output file.
    *   **Vertical Merge:** Data from all selected sheets is appended vertically (top-to-bottom) into a single sheet.
    *   **Horizontal Merge:** Data from all selected sheets is appended horizontally (side-by-side) into a single sheet.

*   **Password Handling:**
    *   **Encrypted Input:** The application can open password-protected Excel files using the `msoffcrypto-tool` library. It supports a global password for convenience and will prompt the user for individual passwords if needed.
    *   **Encrypted Output:** Users can set a password to encrypt the final merged Excel file.

*   **Advanced Options:**
    *   **High-Quality Merge (Windows Only):** On Windows, a special mode can be used to perform a full sheet copy, preserving all formatting and formulas (similar to a VBA macro).
    *   **Sheet Naming Rules:** Customize how the merged sheets are named in the output file.
    *   **SheetTrim:** Automatically remove a specified number of consecutive empty rows or columns during the merge process.
    *   **Value-Only Copy:** Option to copy only the cell values, ignoring formulas.

*   **User Interface:**
    *   Provides real-time progress updates via a progress bar.
    *   Displays a detailed log of all operations, including errors and successful steps.
    *   Includes a debug mode for more verbose logging.

## 3. General Workflow

1.  **Add Files:** The user adds one or more Excel files to the file list.
2.  **Select Sheets:** The user selects a file to see its sheets, then adds the desired sheets to the merge list.
3.  **Configure Merge:** The user chooses a merge strategy (Sheet, Vertical, or Horizontal) and sets other options like output sheet naming.
4.  **Set Output:** The user specifies the save location and filename for the merged file.
5.  **Start Merge:** The user initiates the process. The application handles any necessary password prompts, merges the data, and saves the final file.

## 4. Settings & Configuration

*   The application saves settings (like the global password and output encryption settings) to a configuration file.
*   Passwords stored in the configuration file are encrypted for security.

## 5. UI Component Details

### main_ui

| **Object Name** | **Function** |
| --- | --- |
| listFileAdded | List of files added for processing. Supports drag-and-drop, Ctrl/Shift multi-selection, and deletion (Del/double-click). Displays file names. |
| listSheetInFile | List of sheets within a selected file. When a file is clicked in `listFileAdded`, its sheets are displayed here. Supports Ctrl/Shift multi-selection. Double-clicking or pressing Enter moves selected sheets to the merge list. Items can also be dragged to `listSheetToMerge`. |
| listSheetToMerge | List of sheets to be merged. The order can be changed via drag-and-drop. Supports deletion (Del/double-click). Displays items in "FileName/SheetName" format. Can receive items dropped from `listSheetInFile`. |
| btnSheetToMergeAdd, btnSheetToMergeRemove | Buttons to add/remove sheets between `listSheetInFile` and `listSheetToMerge`. |
| lineEditSavePath | Displays and allows direct input of the save path. |
| btnBrowsePath | Opens a file dialog to select the save location and name for the output file. |
| btnOpenPath | Opens the save location's folder directly in the system's file explorer. |
| txtLogOutput | A text browser for displaying operation logs. |
| lblCurrentFile | Continuously displays the current file/sheet being processed during the merge operation (e.g., "Merging Sheet1 from File1.xlsx..."). |
| progressBar | Displays the real-time progress of the merge operation from 0-100%. |
| radioButtonAll | Activates the option to select all sheets from all added Excel files. `listSheetInFile` is disabled, and `listSheetToMerge` becomes read-only, populated with all sheets. Mutually exclusive with other sheet selection modes. |
| radioButtonSpecific | Activates `lineEditSheetSpecific` and makes `listSheetToMerge` read-only. Allows specifying the n-th sheets to merge (e.g., "1,3" merges the 1st and 3rd sheet from every file). Mutually exclusive with other modes. |
| radioButtonChoice | Allows the user to freely select sheets and manually build the merge list. `listSheetInFile` and `listSheetToMerge` are fully interactive. Mutually exclusive with other modes. |
| lineEditSheetSpecific | An input field, enabled by `radioButtonSpecific`, for entering comma-separated numbers to select sheets by their order (e.g., 1,4,7). |
| actionActivateDebugMode | If checked, enables more verbose debug logging. |
| actionAddExcelFile | Opens a file explorer to add Excel files to `listFileAdded`. |
| actionSetSavePath | Same function as `btnBrowsePath`; specifies the save path. |
| actionCancelWork | - |
| actionUndoCancel | Redoes a canceled action (Redo). Shortcut: Ctrl+Y. |
| actionSetGlobalPassword | Opens the `globalpassword.ui` dialog for setting a global password. |
| actionSetOutPutEncryption | Opens the `encryption.ui` dialog for setting the output file's encryption password. |
| checkBoxOnlyValue | If checked, copies only the values from cells, ignoring formulas. |
| btnStart | Starts the merge process for all sheets in `listSheetToMerge` using the selected merge strategy. Shortcut: F5. |

### encryption_ui

| **Object Name** | **Function Description** |
| --- | --- |
| chkEnablePassword | If checked, encrypts the final output file with the provided password. The state and encrypted password are saved in the settings file. |
| lineEditPassword | Input field for the output file's encryption password. |
| buttonBox | OK: Applies changes and closes the dialog. Cancel: Discards changes and closes the dialog. |

### globalpassword_ui

| **Object Name** | **Function Description** |
| --- | --- |
| chkGlobalPassword | If checked, uses the provided password as a global password when opening any encrypted file. The state and encrypted password are saved in the settings file. |
| lineEditGlobalPassword | Input field for the global password. |
| buttonBox | OK: Applies changes and closes the dialog. Cancel: Discards changes and closes the dialog. |

### password_ui

This dialog is shown when trying to open an encrypted file if the global password is not set or is incorrect. Files that fail to open with the password entered here are skipped.

| **Object Name** | **Function Description** |
| --- | --- |
| textEditOpenFile | Displays the name of the file currently requiring a password. |
| chkKeepPassword | If checked, uses the password from `lineEditKeepPassword` for subsequent files in the current session without prompting again. Resets when the program closes. |
| lineEditKeepPassword | Input field for a temporary password to open an encrypted file. |
| buttonBox | OK: Retries opening the file with the entered password. Cancel: Skips the current file. |
| btnStop | When adding multiple files, this stops the entire password-prompting process and only adds the files that were successfully opened up to that point. |

### options_ui

Contains options moved from the main UI.

| **Object Name** | **Function Description** |
| --- | --- |
| radioButtonSheet | Merges all selected sheets as individual sheets within a single new Excel file. |
| radioButtonHorizontal | Appends the data from all selected sheets horizontally (side-by-side) into a single sheet. |
| radioButtonVertical | Appends the data from all selected sheets vertically (top-to-bottom) into a single sheet. |
| radioButtonOriginalBoth | Sets the output sheet names to "OriginalFileName_OriginalSheetName". Mutually exclusive with the option below. |
| radioButtonOriginalSheet | Sets the output sheet names to "OriginalSheetName". Appends a number for duplicates. Mutually exclusive with the option above. |
| spinBoxEmpty | Numeric input for the "SheetTrim" feature. Removes consecutive empty rows/columns that exceed this number. `0` disables the feature. |
| checkBoxEmptyRow | If checked, enables SheetTrim for empty rows. |
| checkBoxEmptyColumn | If checked, enables SheetTrim for empty columns. |
