# Product Description

## What This Project Does

Firefly III CSV Converter is a command-line tool that automates the conversion of bank statement files from Italian financial institutions (Fineco Bank and PayPal) into the CSV import format required by Firefly III, a popular self-hosted personal finance management application.

## Problems It Solves

1. **Manual Data Entry Burden**: Eliminates the tedious process of manually entering bank transactions into Firefly III
2. **Format Incompatibility**: Bridges the gap between proprietary bank export formats and Firefly III's expected CSV structure
3. **Italian Localization**: Handles Italian-specific formatting (decimal separators, date formats, currency)
4. **Multi-Bank Support**: Supports multiple Italian banking institutions in a single tool
5. **Error Reduction**: Automated processing reduces human error in transaction categorization and amount calculation

## How It Works

The application provides two main conversion commands:

### Fineco Converter
- Reads Excel (.xlsx) files exported from Fineco Bank
- Processes transaction data with separate "Entrate" (deposits) and "Uscite" (withdrawals) columns
- Handles card-specific transactions (Carta A, Carta B)
- Calculates net transaction amounts and determines transaction types
- Outputs standardized Firefly III CSV format

### PayPal Converter
- Reads CSV files exported from PayPal
- Processes paired transaction rows (header + accounting line)
- Handles Italian decimal formatting (comma as decimal separator)
- Manages currency conversion transactions
- Identifies and reports unpaired/orphan rows

## User Experience Goals

- **Simple CLI Interface**: Easy-to-use command-line interface with clear help text
- **Configuration-Driven**: JSON-based configuration for customization without code changes
- **Robust Error Handling**: Clear error messages and validation of input files
- **Progress Feedback**: Informative output about conversion progress and any issues
- **Zero-Configuration Defaults**: Sensible defaults that work out-of-the-box for common use cases
- **Extensible Design**: Modular architecture that can easily support additional banks

## Target Users

- Self-hosters of Firefly III who want to automate transaction imports
- Users of Italian banking services (Fineco, PayPal)
- Individuals who prefer command-line tools for batch processing
- Users who want to maintain control over their financial data processing