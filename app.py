#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import click
from pathlib import Path
from converters.fineco import prepare_fineco_csv
from converters.paypal import convert_paypal_csv_to_firefly


@click.group()
@click.option('--config', default='config/config.json', help='Path to configuration JSON file')
@click.pass_context
def cli(ctx, config):
    """Firefly III CSV Converter App"""
    try:
        with open(config, 'r', encoding='utf-8') as f:
            ctx.obj = json.load(f)
    except FileNotFoundError:
        click.echo(f"Configuration file '{config}' not found.", err=True)
        raise click.Abort()
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in configuration file: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.pass_obj
def fineco(config, input_file, output_file):
    """Convert Fineco Excel file to Firefly III CSV format."""
    output_path = Path("output") / output_file
    try:
        prepare_fineco_csv(Path(input_file), output_path, config)
        click.echo(f"Successfully converted {input_file} to {output_path}")
    except Exception as e:
        click.echo(f"Error converting Fineco file: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.argument('output_file', type=click.Path(), required=False)
@click.pass_obj
def paypal(config, input_file, output_file):
    """Convert PayPal CSV file to Firefly III CSV format."""
    paypal_config = config["paypal"]
    input_path = input_file or paypal_config["default_input"]
    output_path = output_file or paypal_config["default_output"]
    if output_file:
        output_path = Path("output") / output_file

    try:
        convert_paypal_csv_to_firefly(input_path, output_path, config)
        click.echo(f"Successfully converted {input_path} to {output_path}")
    except Exception as e:
        click.echo(f"Error converting PayPal file: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()