# Firefly III CSV Converter

A command-line tool for converting bank statement CSV files from Fineco and PayPal to Firefly III import format.

## Features

- **Fineco Converter**: Converts Fineco Excel files (.xlsx) to Firefly III CSV format
- **PayPal Converter**: Converts PayPal CSV files to Firefly III CSV format
- **Configurable**: Uses JSON configuration files for customization
- **CLI Interface**: Built with Click for easy command-line usage

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd firefly_iii_imports
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a configuration file (see Configuration section below)

## Usage

### Basic Usage

```bash
python app.py --help
```

### Fineco Conversion

Convert a Fineco Excel file to Firefly III format:

```bash
python app.py fineco input.xlsx output.csv
```

### PayPal Conversion

Convert a PayPal CSV file to Firefly III format:

```bash
python app.py paypal input.csv output.csv
```

If input/output files are not specified, defaults from the configuration will be used.

### Options

- `--config`: Path to configuration JSON file (default: `config/config.json`)
- `--output-dir`: Directory where converted files will be written (default: `output`)

## Configuration

Create a `config/config.json` file with the following structure:

```json
{
  "fineco": {
    "default_account": "Fineco Account",
    "header_row": 0,
    "required_columns": ["Data_Valuta", "Descrizione", "Entrate", "Uscite"],
    "currency_code": "EUR",
    "card_a": "Carta A",
    "card_b": "Carta B"
  },
  "paypal": {
    "source_account": "PayPal",
    "output_columns": ["date", "description", "amount", "currency_code", "type", "source_account", "destination_account"],
    "default_input": "input/paypal.csv",
    "default_output": "output/paypal_firefly.csv",
    "positive_is_withdrawal": true
  }
}
```

### Fineco Configuration

- `default_account`: Default account name for transactions
- `header_row`: Row number containing column headers (0-based)
- `required_columns`: List of required columns in the Excel file
- `currency_code`: Currency code for transactions
- `card_a` and `card_b`: Account names for specific card transactions

### PayPal Configuration

- `source_account`: PayPal account name
- `output_columns`: Columns to include in the output CSV
- `default_input`: Default input file path
- `default_output`: Default output file path
- `positive_is_withdrawal`: Whether positive amounts represent withdrawals (default: true)

## File Structure

```
firefly_iii_imports/
├── app.py                 # Main CLI application
├── requirements.txt       # Python dependencies
├── config/
│   └── config.json        # Configuration file
├── converters/
│   ├── fineco.py          # Fineco converter module
│   └── paypal.py          # PayPal converter module
├── input/                 # Input files directory
├── output/                # Output files directory
└── README.md              # This file
```

## Development

### Running Tests

```bash
# Add test commands here when implemented
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add license information here]

## Support

For issues and questions, please [create an issue](link-to-issues) in the repository.