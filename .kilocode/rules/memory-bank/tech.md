# Tech

## Technologies Used

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Click**: Command-line interface framework
- **Pandas**: Data manipulation and Excel processing
- **NumPy**: Numerical computing support
- **OpenPyXL**: Excel file reading (required but missing from requirements.txt)

### Dependencies
- `pandas`: DataFrame operations and Excel file handling
- `numpy`: Array operations and numerical processing
- `click`: CLI framework for command-line applications
- `openpyxl`: Excel engine for pandas (missing from requirements.txt)

## Development Setup

### Environment Setup
1. Create virtual environment: `python -m venv .venv`
2. Activate virtual environment: `.venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

### Missing Dependencies
- `openpyxl` is required for Excel processing but not listed in requirements.txt
- Add `openpyxl` to requirements.txt for proper Excel file support

## Technical Constraints

### Platform Support
- **Operating System**: Windows (based on current environment)
- **Python Version**: 3.8+ required for type hints and pathlib usage
- **File Formats**: Excel (.xlsx) for Fineco, CSV for PayPal

### Data Format Constraints
- **Fineco Excel**: Specific column structure required (Data_Valuta, Descrizione, Entrate, Uscite)
- **PayPal CSV**: Paired row format (header + accounting line)
- **Italian Localization**: Comma decimal separator, period thousands separator
- **Encoding**: UTF-8 with BOM for PayPal CSV files

### Performance Considerations
- **Memory Usage**: Pandas loads entire Excel files into memory
- **File Size**: No explicit size limits, but large files may impact performance
- **Processing Speed**: Linear processing of transaction rows

## Tool Usage Patterns

### Code Quality
- **Type Hints**: Used throughout codebase for better IDE support
- **Docstrings**: Comprehensive function documentation with examples
- **Error Handling**: Custom exceptions with descriptive messages
- **Validation**: Runtime configuration and data validation

### Testing Strategy
- **Unit Tests**: Not implemented yet (mentioned in README)
- **Integration Tests**: Manual testing with sample files
- **Error Scenarios**: Configuration validation and file format checks

### Development Workflow
- **CLI Testing**: Direct script execution for converter modules
- **Configuration**: JSON-based with hierarchical structure
- **Output Validation**: CSV format verification for Firefly III compatibility

## Build and Deployment

### Packaging
- **Requirements**: Standard pip requirements.txt
- **Entry Point**: `app.py` with Click CLI
- **Distribution**: Not configured for PyPI distribution

### Configuration Management
- **Config Location**: `config/config.json` (not present in repository)
- **Validation**: Runtime checks for required keys
- **Defaults**: Built-in defaults for common use cases

### File Organization
- **Source Code**: Flat structure with converters subdirectory
- **Assets**: Input/output directories for file processing
- **Documentation**: README.md with usage examples