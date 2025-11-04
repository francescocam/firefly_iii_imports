# Architecture

## System Architecture

The Firefly III CSV Converter is a modular Python CLI application built with Click, designed for converting Italian bank statements to Firefly III import format. The architecture follows a clean separation of concerns with dedicated converter modules for each bank.

## Source Code Paths

```
firefly_iii_imports/
├── app.py                 # Main CLI application entry point
├── converters/
│   ├── fineco.py          # Fineco Bank Excel converter
│   └── paypal.py          # PayPal CSV converter
├── config/                # Configuration files directory
├── input/                 # Input files directory
├── output/                # Output files directory
└── requirements.txt       # Python dependencies
```

## Key Technical Decisions

### CLI Framework
- **Choice**: Click library for command-line interface
- **Rationale**: Provides robust argument parsing, help generation, and composable commands
- **Benefits**: Automatic help text, option validation, and extensible command structure

### Modular Converter Design
- **Pattern**: Separate converter modules for each bank
- **Benefits**: Easy to add new banks, isolated testing, clear responsibilities
- **Interface**: Each converter exposes a main function with consistent signature

### Configuration Management
- **Format**: JSON-based configuration files
- **Structure**: Hierarchical config with bank-specific sections
- **Validation**: Runtime validation of required configuration keys

### Data Processing
- **Fineco**: Uses pandas for Excel processing with openpyxl engine
- **PayPal**: Custom CSV parsing with decimal handling for Italian formatting
- **Output**: Standardized CSV format for Firefly III import

## Design Patterns in Use

### Command Pattern
- CLI commands (`fineco`, `paypal`) encapsulate conversion operations
- Context passing via Click's `pass_obj` decorator
- Consistent error handling and user feedback

### Strategy Pattern
- Different conversion strategies for each bank
- Configurable behavior through strategy parameters
- Extensible for adding new bank converters

### Factory Pattern
- Configuration loading and validation
- Converter instantiation based on command type
- Error handling for missing or invalid configurations

## Component Relationships

### Main Application (app.py)
- **Responsibilities**: CLI setup, configuration loading, command routing
- **Dependencies**: Click, pathlib, converters modules
- **Outputs**: Processed CSV files, user feedback

### Fineco Converter (converters/fineco.py)
- **Input**: Excel files (.xlsx) with specific column structure
- **Processing**: Data validation, amount calculation, account mapping
- **Output**: Firefly III compatible CSV with transaction details

### PayPal Converter (converters/paypal.py)
- **Input**: CSV files with paired transaction rows
- **Processing**: Decimal parsing (Italian format), orphan row detection
- **Output**: Firefly III CSV with proper transaction types

### Configuration System
- **Centralized**: Single JSON file for all settings
- **Validated**: Runtime checks for required keys and types
- **Flexible**: Bank-specific configuration sections

## Critical Implementation Paths

### Fineco Conversion Flow
1. Load and validate configuration
2. Parse Excel file with pandas
3. Extract account name from first row
4. Calculate net amounts (entrate - uscite)
5. Determine transaction types and account mappings
6. Generate output CSV with required Firefly III columns

### PayPal Conversion Flow
1. Load and validate configuration
2. Read CSV with UTF-8 BOM handling
3. Process paired rows (header + accounting)
4. Parse Italian decimal format amounts
5. Handle currency conversion transactions
6. Generate output CSV, report orphan rows

### Error Handling
- Configuration validation at startup
- File existence and format checks
- Data validation during processing
- User-friendly error messages with Click exceptions