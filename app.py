#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import click
from datetime import datetime
from pathlib import Path
from converters.fineco import prepare_fineco_csv
from converters.paypal import convert_paypal_csv_to_firefly
from converters.n26 import convert_n26_csv_to_firefly


@click.group()
@click.option('--config', default='config/config.json', help='Path to configuration JSON file')
@click.option(
    '--output-dir',
    default='output',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    show_default=True,
    help='Directory where converted files will be written',
)
@click.pass_context
def cli(ctx, config, output_dir):
    """Firefly III CSV Converter App"""
    try:
        with open(config, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
    except FileNotFoundError:
        click.echo(f"Configuration file '{config}' not found.", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in configuration file: {e}", err=True)
        raise click.Abort()

    ctx.ensure_object(dict)
    ctx.obj['config'] = loaded_config
    ctx.obj['output_dir'] = Path(output_dir)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False), required=False)
@click.pass_obj
def fineco(ctx_obj, input_file):
    """Convert Fineco Excel file to Firefly III CSV format."""
    config = ctx_obj['config']
    output_dir = ctx_obj['output_dir']

    if input_file is None:
        # Look for Excel files in input directory
        input_dir = Path('input')
        excel_files = list(input_dir.glob('*.xlsx'))
        if not excel_files:
            raise click.ClickException("No Excel files found in input directory. Please specify an input file or place .xlsx files in the 'input' directory.")
        if len(excel_files) > 1:
            raise click.ClickException("Multiple Excel files found in input directory. Please specify which file to convert.")
        input_file = str(excel_files[0])

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"fineco_to_firefly_{timestamp}.csv"
    output_path = output_dir / output_filename

    try:
        dropped = prepare_fineco_csv(Path(input_file), output_path, config)
    except ValueError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Successfully converted {input_file} to {output_path}")
    if dropped:
        click.echo(
            f"Skipped {dropped} transaction(s) lacking date or amount information.",
            err=True,
        )


@cli.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.pass_obj
def paypal(ctx_obj, input_file):
    """Convert PayPal CSV file to Firefly III CSV format."""
    config = ctx_obj['config']
    if "paypal" not in config:
        raise click.ClickException("Missing 'paypal' section in configuration.")
    paypal_config = config["paypal"]

    if input_file is None:
        # Look for CSV files in input directory
        input_dir = Path('input')
        csv_files = list(input_dir.glob('*.csv'))
        if not csv_files:
            try:
                input_path = paypal_config["default_input"]
            except KeyError as exc:
                raise click.ClickException(
                    f"Missing required PayPal configuration key: {exc.args[0]}"
                ) from exc
        else:
            if len(csv_files) > 1:
                raise click.ClickException("Multiple CSV files found in input directory. Please specify which file to convert.")
            input_path = str(csv_files[0])
    else:
        input_path = input_file

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"paypal_to_firefly_{timestamp}.csv"
    output_path = ctx_obj['output_dir'] / output_filename

    try:
        orphan_rows = convert_paypal_csv_to_firefly(input_path, output_path, config)
    except ValueError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Successfully converted {input_path} to {output_path}")
    if orphan_rows:
        details = ", ".join(
            f"row {entry['row_number']}: {entry['name']}" for entry in orphan_rows
        )
        click.echo(
            "Skipped unpaired PayPal rows – review CSV near " + details,
            err=True,
        )


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False), required=False)
@click.pass_obj
def n26(ctx_obj, input_file):
    """Convert N26 CSV file to Firefly III CSV format."""
    config = ctx_obj['config']
    if "n26" not in config:
        raise click.ClickException("Missing 'n26' section in configuration.")
    n26_config = config["n26"]

    if input_file is None:
        # Look for CSV files in input directory
        input_dir = Path('input')
        csv_files = list(input_dir.glob('*.csv'))
        if not csv_files:
            raise click.ClickException("No CSV files found in input directory. Please specify an input file or place .csv files in the 'input' directory.")
        if len(csv_files) > 1:
            raise click.ClickException("Multiple CSV files found in input directory. Please specify which file to convert.")
        input_file = str(csv_files[0])

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"n26_to_firefly_{timestamp}.csv"
    output_path = ctx_obj['output_dir'] / output_filename

    try:
        dropped = convert_n26_csv_to_firefly(Path(input_file), output_path, config)
    except ValueError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Successfully converted {input_file} to {output_path}")
    if dropped:
        click.echo(
            f"Skipped {dropped} transaction(s) lacking date or amount information.",
            err=True,
        )


if __name__ == "__main__":
    cli()