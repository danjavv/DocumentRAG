"""
Invoice-PO Mismatch Detection System

This module provides functionality to compare invoices with their referenced purchase orders
and identify mismatches in amounts, line items, and other details.
"""

import json
import os
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from pathlib import Path


class InvoicePOMatcher:
    """
    Compares invoices with their referenced purchase orders to identify mismatches.
    """

    def __init__(self, data_dir: str = "data/synthetic"):
        """
        Initialize the matcher with data directory.

        Args:
            data_dir: Directory containing invoices.json and purchase_orders.json
        """
        self.data_dir = Path(data_dir)
        self.invoices = []
        self.purchase_orders = []
        self.po_lookup = {}

        self.load_data()

    def load_data(self):
        """Load invoices and purchase orders from JSON files."""
        invoice_file = self.data_dir / "invoices.json"
        po_file = self.data_dir / "purchase_orders.json"

        # Load invoices
        if invoice_file.exists():
            with open(invoice_file, 'r') as f:
                self.invoices = json.load(f)
        else:
            raise FileNotFoundError(f"Invoices file not found: {invoice_file}")

        # Load purchase orders
        if po_file.exists():
            with open(po_file, 'r') as f:
                self.purchase_orders = json.load(f)
        else:
            raise FileNotFoundError(f"Purchase orders file not found: {po_file}")

        # Create PO lookup dictionary for fast access
        self.po_lookup = {po['po_number']: po for po in self.purchase_orders}

        print(f"Loaded {len(self.invoices)} invoices and {len(self.purchase_orders)} purchase orders")

    def compare_line_items(self, invoice_items: List[Dict], po_items: List[Dict]) -> Dict[str, Any]:
        """
        Compare line items between invoice and PO.

        Returns:
            Dictionary with comparison results
        """
        mismatches = []
        matched_items = 0

        # Create lookup for PO items by item_code
        po_items_lookup = {item['item_code']: item for item in po_items}

        for inv_item in invoice_items:
            item_code = inv_item['item_code']

            if item_code not in po_items_lookup:
                mismatches.append({
                    'type': 'ITEM_NOT_IN_PO',
                    'item_code': item_code,
                    'description': inv_item['description'],
                    'invoice_quantity': inv_item['quantity'],
                    'issue': 'Item in invoice but not in referenced PO'
                })
            else:
                po_item = po_items_lookup[item_code]
                item_issues = []

                # Compare quantity
                if inv_item['quantity'] != po_item['quantity']:
                    item_issues.append({
                        'field': 'quantity',
                        'invoice_value': inv_item['quantity'],
                        'po_value': po_item['quantity'],
                        'difference': inv_item['quantity'] - po_item['quantity']
                    })

                # Compare unit price
                if abs(inv_item['unit_price'] - po_item['unit_price']) > 0.01:
                    item_issues.append({
                        'field': 'unit_price',
                        'invoice_value': inv_item['unit_price'],
                        'po_value': po_item['unit_price'],
                        'difference': inv_item['unit_price'] - po_item['unit_price']
                    })

                # Compare total
                if abs(inv_item['total'] - po_item['total']) > 0.01:
                    item_issues.append({
                        'field': 'total',
                        'invoice_value': inv_item['total'],
                        'po_value': po_item['total'],
                        'difference': inv_item['total'] - po_item['total']
                    })

                if item_issues:
                    mismatches.append({
                        'type': 'ITEM_MISMATCH',
                        'item_code': item_code,
                        'description': inv_item['description'],
                        'issues': item_issues
                    })
                else:
                    matched_items += 1

        # Check for items in PO but not in invoice
        invoice_item_codes = {item['item_code'] for item in invoice_items}
        for po_item in po_items:
            if po_item['item_code'] not in invoice_item_codes:
                mismatches.append({
                    'type': 'ITEM_NOT_IN_INVOICE',
                    'item_code': po_item['item_code'],
                    'description': po_item['description'],
                    'po_quantity': po_item['quantity'],
                    'issue': 'Item in PO but not invoiced'
                })

        return {
            'total_items_in_invoice': len(invoice_items),
            'total_items_in_po': len(po_items),
            'matched_items': matched_items,
            'mismatches': mismatches,
            'has_line_item_issues': len(mismatches) > 0
        }

    def compare_invoice_with_po(self, invoice: Dict) -> Optional[Dict[str, Any]]:
        """
        Compare a single invoice with its referenced PO.

        Returns:
            Comparison results or None if PO not found
        """
        po_reference = invoice.get('po_reference')
        if not po_reference:
            return {
                'invoice_number': invoice['invoice_number'],
                'status': 'ERROR',
                'error': 'Invoice has no PO reference'
            }

        po = self.po_lookup.get(po_reference)
        if not po:
            return {
                'invoice_number': invoice['invoice_number'],
                'po_reference': po_reference,
                'status': 'ERROR',
                'error': f'Referenced PO {po_reference} not found'
            }

        # Perform comparisons
        issues = []

        # Compare vendor
        if invoice.get('vendor_name') != po.get('vendor_name'):
            issues.append({
                'field': 'vendor_name',
                'invoice_value': invoice.get('vendor_name'),
                'po_value': po.get('vendor_name'),
                'severity': 'HIGH'
            })

        if invoice.get('vendor_id') != po.get('vendor_id'):
            issues.append({
                'field': 'vendor_id',
                'invoice_value': invoice.get('vendor_id'),
                'po_value': po.get('vendor_id'),
                'severity': 'HIGH'
            })

        # Compare currency
        if invoice.get('currency') != po.get('currency'):
            issues.append({
                'field': 'currency',
                'invoice_value': invoice.get('currency'),
                'po_value': po.get('currency'),
                'severity': 'HIGH'
            })

        # Compare amounts (with tolerance for floating point)
        tolerance = 0.01

        subtotal_diff = abs(invoice.get('subtotal', 0) - po.get('subtotal', 0))
        if subtotal_diff > tolerance:
            issues.append({
                'field': 'subtotal',
                'invoice_value': invoice.get('subtotal'),
                'po_value': po.get('subtotal'),
                'difference': invoice.get('subtotal', 0) - po.get('subtotal', 0),
                'severity': 'HIGH'
            })

        tax_diff = abs(invoice.get('tax', 0) - po.get('tax', 0))
        if tax_diff > tolerance:
            issues.append({
                'field': 'tax',
                'invoice_value': invoice.get('tax'),
                'po_value': po.get('tax'),
                'difference': invoice.get('tax', 0) - po.get('tax', 0),
                'severity': 'MEDIUM'
            })

        total_diff = abs(invoice.get('total_amount', 0) - po.get('total_amount', 0))
        if total_diff > tolerance:
            issues.append({
                'field': 'total_amount',
                'invoice_value': invoice.get('total_amount'),
                'po_value': po.get('total_amount'),
                'difference': invoice.get('total_amount', 0) - po.get('total_amount', 0),
                'severity': 'HIGH'
            })

        # Compare line items
        line_item_comparison = self.compare_line_items(
            invoice.get('line_items', []),
            po.get('line_items', [])
        )

        # Determine overall status
        has_issues = len(issues) > 0 or line_item_comparison['has_line_item_issues']
        status = 'MISMATCH' if has_issues else 'MATCH'

        return {
            'invoice_number': invoice['invoice_number'],
            'invoice_date': invoice.get('invoice_date'),
            'po_reference': po_reference,
            'po_date': po.get('po_date'),
            'vendor_name': invoice.get('vendor_name'),
            'invoice_total': invoice.get('total_amount'),
            'po_total': po.get('total_amount'),
            'status': status,
            'header_issues': issues,
            'line_item_comparison': line_item_comparison,
            'total_issues': len(issues) + len(line_item_comparison['mismatches'])
        }

    def find_all_mismatches(self) -> Dict[str, Any]:
        """
        Find all invoices that have mismatches with their referenced POs.

        Returns:
            Summary of all mismatches
        """
        results = {
            'total_invoices': len(self.invoices),
            'matched': [],
            'mismatched': [],
            'errors': [],
            'summary': {
                'total_matched': 0,
                'total_mismatched': 0,
                'total_errors': 0,
                'total_amount_variance': 0.0,
                'high_severity_issues': 0,
                'medium_severity_issues': 0
            }
        }

        for invoice in self.invoices:
            comparison = self.compare_invoice_with_po(invoice)

            if comparison['status'] == 'MATCH':
                results['matched'].append(comparison)
                results['summary']['total_matched'] += 1
            elif comparison['status'] == 'MISMATCH':
                results['mismatched'].append(comparison)
                results['summary']['total_mismatched'] += 1

                # Calculate amount variance
                if 'invoice_total' in comparison and 'po_total' in comparison:
                    variance = abs(comparison['invoice_total'] - comparison['po_total'])
                    results['summary']['total_amount_variance'] += variance

                # Count severity issues
                for issue in comparison.get('header_issues', []):
                    if issue.get('severity') == 'HIGH':
                        results['summary']['high_severity_issues'] += 1
                    elif issue.get('severity') == 'MEDIUM':
                        results['summary']['medium_severity_issues'] += 1
            else:  # ERROR
                results['errors'].append(comparison)
                results['summary']['total_errors'] += 1

        return results

    def get_mismatch_summary_text(self) -> str:
        """
        Generate a human-readable summary of all mismatches.

        Returns:
            Formatted text summary
        """
        results = self.find_all_mismatches()
        summary = results['summary']

        lines = []
        lines.append("=" * 80)
        lines.append("INVOICE-PO MISMATCH ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total Invoices Analyzed: {results['total_invoices']}")
        lines.append(f"  ✓ Matched: {summary['total_matched']} ({summary['total_matched']/results['total_invoices']*100:.1f}%)")
        lines.append(f"  ✗ Mismatched: {summary['total_mismatched']} ({summary['total_mismatched']/results['total_invoices']*100:.1f}%)")
        lines.append(f"  ! Errors: {summary['total_errors']}")
        lines.append("")
        lines.append(f"Total Amount Variance: ${summary['total_amount_variance']:,.2f}")
        lines.append(f"High Severity Issues: {summary['high_severity_issues']}")
        lines.append(f"Medium Severity Issues: {summary['medium_severity_issues']}")
        lines.append("")

        if results['mismatched']:
            lines.append("=" * 80)
            lines.append("MISMATCHED INVOICES DETAIL")
            lines.append("=" * 80)
            lines.append("")

            for idx, mismatch in enumerate(results['mismatched'], 1):
                lines.append(f"\n{idx}. Invoice: {mismatch['invoice_number']} → PO: {mismatch['po_reference']}")
                lines.append(f"   Vendor: {mismatch['vendor_name']}")
                lines.append(f"   Invoice Total: ${mismatch['invoice_total']:,.2f} | PO Total: ${mismatch['po_total']:,.2f}")
                lines.append(f"   Total Issues: {mismatch['total_issues']}")

                if mismatch['header_issues']:
                    lines.append(f"\n   Header Issues:")
                    for issue in mismatch['header_issues']:
                        field = issue['field']
                        inv_val = issue['invoice_value']
                        po_val = issue['po_value']
                        severity = issue.get('severity', 'MEDIUM')

                        if 'difference' in issue:
                            diff = issue['difference']
                            lines.append(f"     - {field} [{severity}]: Invoice=${inv_val:,.2f} vs PO=${po_val:,.2f} (Diff: ${diff:+,.2f})")
                        else:
                            lines.append(f"     - {field} [{severity}]: Invoice='{inv_val}' vs PO='{po_val}'")

                line_item_comp = mismatch['line_item_comparison']
                if line_item_comp['mismatches']:
                    lines.append(f"\n   Line Item Issues:")
                    for item_issue in line_item_comp['mismatches']:
                        if item_issue['type'] == 'ITEM_MISMATCH':
                            lines.append(f"     - Item {item_issue['item_code']} ({item_issue['description']}):")
                            for detail in item_issue['issues']:
                                field = detail['field']
                                inv_val = detail['invoice_value']
                                po_val = detail['po_value']
                                diff = detail['difference']
                                lines.append(f"       • {field}: Invoice={inv_val} vs PO={po_val} (Diff: {diff:+})")
                        elif item_issue['type'] == 'ITEM_NOT_IN_PO':
                            lines.append(f"     - {item_issue['item_code']}: In invoice but NOT in PO (Qty: {item_issue['invoice_quantity']})")
                        elif item_issue['type'] == 'ITEM_NOT_IN_INVOICE':
                            lines.append(f"     - {item_issue['item_code']}: In PO but NOT invoiced (Qty: {item_issue['po_quantity']})")

                lines.append("")

        if results['errors']:
            lines.append("=" * 80)
            lines.append("ERRORS")
            lines.append("=" * 80)
            for error in results['errors']:
                lines.append(f"  - Invoice {error['invoice_number']}: {error['error']}")

        lines.append("")
        return "\n".join(lines)

    def get_mismatches_for_vendor(self, vendor_name: str) -> List[Dict]:
        """Get mismatches for a specific vendor."""
        all_results = self.find_all_mismatches()
        vendor_mismatches = [
            m for m in all_results['mismatched']
            if m['vendor_name'].lower() == vendor_name.lower()
        ]
        return vendor_mismatches

    def get_mismatches_above_amount(self, amount: float) -> List[Dict]:
        """Get mismatches where the variance is above a certain amount."""
        all_results = self.find_all_mismatches()
        high_variance_mismatches = [
            m for m in all_results['mismatched']
            if abs(m['invoice_total'] - m['po_total']) > amount
        ]
        return high_variance_mismatches


def main():
    """Main function for standalone testing."""
    matcher = InvoicePOMatcher()

    print("\n" + matcher.get_mismatch_summary_text())

    # Export results to JSON
    results = matcher.find_all_mismatches()
    output_file = Path("data/mismatch_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
