#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import click
from pathlib import Path
from converters.fineco import prepare_fineco_csv
from converters.paypal import convert_paypal_csv_to_firefly


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
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_file', type=click.Path())
@click.pass_obj
def fineco(ctx_obj, input_file, output_file):
    """Convert Fineco Excel file to Firefly III CSV format."""
    config = ctx_obj['config']
    output_dir = ctx_obj['output_dir']
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = output_dir / output_path

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
@click.argument('output_file', type=click.Path(), required=False)
@click.pass_obj
def paypal(ctx_obj, input_file, output_file):
    """Convert PayPal CSV file to Firefly III CSV format."""
    config = ctx_obj['config']
    if "paypal" not in config:
        raise click.ClickException("Missing 'paypal' section in configuration.")
    paypal_config = config["paypal"]
    try:
        input_path = input_file or paypal_config["default_input"]
        output_path = output_file or paypal_config["default_output"]
    except KeyError as exc:
        raise click.ClickException(
            f"Missing required PayPal configuration key: {exc.args[0]}"
        ) from exc
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = Path(output_path)

    if not output_path.is_absolute():
        output_path = ctx_obj['output_dir'] / output_path

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


if __name__ == "__main__":
    cli()