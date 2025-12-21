#!/usr/bin/env python3
"""
Generate synthetic procurement documents (Purchase Orders, Invoices, GRNs)
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# For realistic fake data
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    print("Installing faker...")
    import subprocess
    subprocess.check_call(["pip", "install", "faker"])
    from faker import Faker
    fake = Faker()

# Configuration
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Vendor pool
VENDORS = [
    {"id": "V-1001", "name": "Acme Supplies Ltd", "country": "USA"},
    {"id": "V-1002", "name": "Global Tech Solutions", "country": "UK"},
    {"id": "V-1003", "name": "Premier Office Equipment", "country": "Canada"},
    {"id": "V-1004", "name": "Industrial Components Inc", "country": "Germany"},
    {"id": "V-1005", "name": "Swift Logistics Co", "country": "Singapore"},
    {"id": "V-1006", "name": "Quality Manufacturing", "country": "Japan"},
    {"id": "V-1007", "name": "Euro Parts Distributors", "country": "France"},
    {"id": "V-1008", "name": "Pacific Traders", "country": "Australia"},
    {"id": "V-1009", "name": "Nordic Supplies AB", "country": "Sweden"},
    {"id": "V-1010", "name": "Atlas Equipment Corp", "country": "USA"},
]

# Product categories
PRODUCTS = [
    {"code": "IT-001", "name": "Dell Laptop XPS 15", "price_range": (1200, 1800)},
    {"code": "IT-002", "name": "HP Desktop Workstation", "price_range": (800, 1500)},
    {"code": "IT-003", "name": "Cisco Network Switch 24-Port", "price_range": (600, 900)},
    {"code": "IT-004", "name": "Samsung 27\" Monitor", "price_range": (300, 500)},
    {"code": "IT-005", "name": "Logitech Wireless Keyboard & Mouse", "price_range": (50, 100)},
    {"code": "OS-001", "name": "Ergonomic Office Chair", "price_range": (250, 450)},
    {"code": "OS-002", "name": "Standing Desk Adjustable", "price_range": (400, 700)},
    {"code": "OS-003", "name": "Printer Paper A4 (5 Reams)", "price_range": (25, 40)},
    {"code": "OS-004", "name": "Whiteboard 6x4 ft", "price_range": (100, 200)},
    {"code": "OS-005", "name": "File Cabinet 4-Drawer", "price_range": (150, 300)},
    {"code": "IN-001", "name": "Hydraulic Pump Assembly", "price_range": (2000, 3500)},
    {"code": "IN-002", "name": "Steel Beam 10m I-Section", "price_range": (500, 800)},
    {"code": "IN-003", "name": "Safety Harness Kit", "price_range": (150, 250)},
    {"code": "IN-004", "name": "Industrial LED Lighting 100W", "price_range": (80, 150)},
    {"code": "IN-005", "name": "Air Compressor 50L", "price_range": (400, 700)},
]

DEPARTMENTS = ["IT", "Operations", "Facilities", "Manufacturing", "Procurement", "Finance"]
WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-NORTH", "WH-SOUTH"]


class SyntheticDataGenerator:
    def __init__(self):
        self.po_counter = 1000
        self.invoice_counter = 5000
        self.grn_counter = 8000
        self.pos = []
        self.invoices = []
        self.grns = []
        random.seed(42)  # For reproducibility

    def generate_line_items(self, num_items=None):
        """Generate random line items"""
        if num_items is None:
            num_items = random.randint(1, 4)

        items = []
        selected_products = random.sample(PRODUCTS, min(num_items, len(PRODUCTS)))

        for product in selected_products:
            quantity = random.randint(1, 15)
            unit_price = round(random.uniform(*product["price_range"]), 2)
            total = round(quantity * unit_price, 2)

            items.append({
                "item_code": product["code"],
                "description": product["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            })

        return items

    def calc_totals(self, line_items):
        """Calculate subtotal, tax, and total"""
        subtotal = sum(item["total"] for item in line_items)
        tax_rate = random.choice([0.0, 0.05, 0.08, 0.10, 0.13])
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)

        return {
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total
        }

    def generate_po(self, po_date=None):
        """Generate a Purchase Order"""
        if po_date is None:
            po_date = fake.date_between(start_date="-90d", end_date="-30d")

        self.po_counter += 1
        vendor = random.choice(VENDORS)
        line_items = self.generate_line_items()
        totals = self.calc_totals(line_items)

        po = {
            "po_number": f"PO-2024-{self.po_counter:05d}",
            "po_date": po_date.strftime("%Y-%m-%d"),
            "vendor_name": vendor["name"],
            "vendor_id": vendor["id"],
            "buyer_name": fake.name(),
            "department": random.choice(DEPARTMENTS),
            "line_items": line_items,
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "total_amount": totals["total_amount"],
            "currency": "USD",
            "delivery_address": fake.address().replace("\n", ", "),
            "delivery_date": (po_date + timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%d")
        }

        self.pos.append(po)
        return po

    def generate_invoice(self, po, scenario="perfect"):
        """
        Generate invoice from PO
        Scenarios: perfect, price_mismatch, quantity_mismatch, overbilling
        """
        self.invoice_counter += 1
        po_date = datetime.strptime(po["po_date"], "%Y-%m-%d")
        invoice_date = po_date + timedelta(days=random.randint(5, 25))

        line_items = [item.copy() for item in po["line_items"]]

        # Apply scenario modifications
        if scenario == "price_mismatch":
            item_idx = random.randint(0, len(line_items) - 1)
            increase = random.uniform(1.05, 1.15)
            line_items[item_idx]["unit_price"] = round(line_items[item_idx]["unit_price"] * increase, 2)
            line_items[item_idx]["total"] = round(line_items[item_idx]["quantity"] * line_items[item_idx]["unit_price"], 2)

        elif scenario == "quantity_mismatch":
            item_idx = random.randint(0, len(line_items) - 1)
            line_items[item_idx]["quantity"] += random.randint(1, 5)
            line_items[item_idx]["total"] = round(line_items[item_idx]["quantity"] * line_items[item_idx]["unit_price"], 2)

        elif scenario == "overbilling":
            extra_items = self.generate_line_items(num_items=1)
            line_items.extend(extra_items)

        totals = self.calc_totals(line_items)

        invoice = {
            "invoice_number": f"INV-{self.invoice_counter:06d}",
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "po_reference": po["po_number"],
            "vendor_name": po["vendor_name"],
            "vendor_id": po["vendor_id"],
            "line_items": line_items,
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "total_amount": totals["total_amount"],
            "currency": po["currency"],
            "payment_terms": random.choice(["Net 30", "Net 45", "Net 60", "Due on Receipt"]),
            "due_date": (invoice_date + timedelta(days=30)).strftime("%Y-%m-%d")
        }

        self.invoices.append(invoice)
        return invoice

    def generate_orphan_invoice(self):
        """Generate invoice without matching PO"""
        self.invoice_counter += 1
        vendor = random.choice(VENDORS)
        line_items = self.generate_line_items()
        totals = self.calc_totals(line_items)
        invoice_date = fake.date_between(start_date="-60d", end_date="-10d")

        invoice = {
            "invoice_number": f"INV-{self.invoice_counter:06d}",
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "po_reference": f"PO-2024-{random.randint(90000, 99999):05d}",  # Non-existent
            "vendor_name": vendor["name"],
            "vendor_id": vendor["id"],
            "line_items": line_items,
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "total_amount": totals["total_amount"],
            "currency": "USD",
            "payment_terms": "Net 30",
            "due_date": (invoice_date + timedelta(days=30)).strftime("%Y-%m-%d")
        }

        self.invoices.append(invoice)
        return invoice

    def generate_grn(self, po, scenario="perfect"):
        """
        Generate GRN from PO
        Scenarios: perfect, partial_delivery, quality_issue
        """
        self.grn_counter += 1
        po_date = datetime.strptime(po["po_date"], "%Y-%m-%d")
        delivery_date = datetime.strptime(po["delivery_date"], "%Y-%m-%d")
        grn_date = delivery_date + timedelta(days=random.randint(0, 2))

        line_items = []
        for item in po["line_items"]:
            qty_ordered = item["quantity"]
            qty_received = qty_ordered
            qty_rejected = 0

            if scenario == "partial_delivery":
                qty_received = int(qty_ordered * random.uniform(0.7, 0.9))

            elif scenario == "quality_issue":
                qty_rejected = int(qty_ordered * random.uniform(0.1, 0.2))
                qty_received = qty_ordered - qty_rejected

            grn_item = {
                "item_code": item["item_code"],
                "description": item["description"],
                "quantity_received": qty_received,
                "quantity_rejected": qty_rejected,
                "condition": "Good" if qty_rejected == 0 else "Damaged/Defective"
            }
            line_items.append(grn_item)

        grn = {
            "grn_number": f"GRN-{self.grn_counter:05d}",
            "grn_date": grn_date.strftime("%Y-%m-%d"),
            "po_reference": po["po_number"],
            "vendor_name": po["vendor_name"],
            "received_by": fake.name(),
            "warehouse": random.choice(WAREHOUSES),
            "line_items": line_items
        }

        self.grns.append(grn)
        return grn

    def generate_all(self):
        """Generate complete dataset"""
        print("🔄 Generating Purchase Orders...")
        for i in range(50):
            self.generate_po()
        print(f"✅ Generated {len(self.pos)} Purchase Orders")

        print("\n🔄 Generating Invoices...")
        # Perfect matches: 30 invoices
        for po in self.pos[:30]:
            self.generate_invoice(po, scenario="perfect")

        # Price mismatches: 7 invoices
        for po in self.pos[30:37]:
            self.generate_invoice(po, scenario="price_mismatch")

        # Quantity mismatches: 5 invoices
        for po in self.pos[37:42]:
            self.generate_invoice(po, scenario="quantity_mismatch")

        # Overbilling: 3 invoices
        for po in self.pos[42:45]:
            self.generate_invoice(po, scenario="overbilling")

        # Orphan invoices: 8
        for i in range(8):
            self.generate_orphan_invoice()

        # Duplicate invoice
        if len(self.invoices) > 5:
            duplicate = self.invoices[5].copy()
            self.invoice_counter += 1
            duplicate["invoice_number"] = f"INV-{self.invoice_counter:06d}"
            self.invoices.append(duplicate)
            print(f"📋 Added duplicate invoice: {duplicate['invoice_number']} (duplicate of {self.invoices[5]['invoice_number']})")

        print(f"✅ Generated {len(self.invoices)} Invoices")

        print("\n🔄 Generating Goods Received Notes...")
        # Perfect receipts: 35 GRNs
        for po in self.pos[:35]:
            self.generate_grn(po, scenario="perfect")

        # Partial deliveries: 6 GRNs
        for po in self.pos[35:41]:
            self.generate_grn(po, scenario="partial_delivery")

        # Quality issues: 4 GRNs
        for po in self.pos[41:45]:
            self.generate_grn(po, scenario="quality_issue")

        print(f"✅ Generated {len(self.grns)} GRNs")

    def save_to_json(self):
        """Save all data to JSON files"""
        # Save POs
        po_path = OUTPUT_DIR / "purchase_orders.json"
        with open(po_path, "w") as f:
            json.dump(self.pos, f, indent=2)
        print(f"\n💾 Saved Purchase Orders to {po_path}")

        # Save Invoices
        inv_path = OUTPUT_DIR / "invoices.json"
        with open(inv_path, "w") as f:
            json.dump(self.invoices, f, indent=2)
        print(f"💾 Saved Invoices to {inv_path}")

        # Save GRNs
        grn_path = OUTPUT_DIR / "grns.json"
        with open(grn_path, "w") as f:
            json.dump(self.grns, f, indent=2)
        print(f"💾 Saved GRNs to {grn_path}")

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("📊 SYNTHETIC DATA GENERATION SUMMARY")
        print("="*60)

        print(f"\n📦 Total Documents Generated: {len(self.pos) + len(self.invoices) + len(self.grns)}")
        print(f"   • Purchase Orders: {len(self.pos)}")
        print(f"   • Invoices: {len(self.invoices)}")
        print(f"   • Goods Received Notes: {len(self.grns)}")

        # Count scenarios
        perfect_matches = 0
        price_mismatches = 0
        qty_mismatches = 0
        overbilling = 0

        for inv in self.invoices:
            po_ref = inv['po_reference']
            matching_po = next((po for po in self.pos if po['po_number'] == po_ref), None)

            if matching_po:
                if abs(inv['total_amount'] - matching_po['total_amount']) > 0.01:
                    if len(inv['line_items']) > len(matching_po['line_items']):
                        overbilling += 1
                    elif any(inv_item['unit_price'] != po_item['unit_price']
                            for inv_item, po_item in zip(inv['line_items'], matching_po['line_items'])
                            if inv_item['item_code'] == po_item['item_code']):
                        price_mismatches += 1
                    else:
                        qty_mismatches += 1
                else:
                    perfect_matches += 1

        orphan_invoices = len([inv for inv in self.invoices
                              if not any(po['po_number'] == inv['po_reference'] for po in self.pos)])

        print(f"\n🎯 Invoice Scenarios:")
        print(f"   • Perfect matches: {perfect_matches}")
        print(f"   • Price mismatches: {price_mismatches}")
        print(f"   • Quantity mismatches: {qty_mismatches}")
        print(f"   • Overbilling cases: {overbilling}")
        print(f"   • Orphan invoices: {orphan_invoices}")

        # GRN scenarios
        perfect_grns = sum(1 for grn in self.grns
                          if all(item['quantity_rejected'] == 0 for item in grn['line_items']))
        partial_delivery = len([grn for grn in self.grns
                               if not all(item['condition'] == 'Good' for item in grn['line_items'])])

        print(f"\n📦 GRN Scenarios:")
        print(f"   • Perfect receipts: {perfect_grns}")
        print(f"   • Partial deliveries/Quality issues: {len(self.grns) - perfect_grns}")

        # Vendor distribution
        vendor_counts = {}
        for po in self.pos:
            vendor_counts[po['vendor_name']] = vendor_counts.get(po['vendor_name'], 0) + 1

        print(f"\n🏢 Vendor Distribution:")
        for vendor, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {vendor}: {count} POs")

        # Value statistics
        total_po_value = sum(po['total_amount'] for po in self.pos)
        total_invoice_value = sum(inv['total_amount'] for inv in self.invoices)

        print(f"\n💰 Financial Summary:")
        print(f"   • Total PO Value: ${total_po_value:,.2f}")
        print(f"   • Total Invoice Value: ${total_invoice_value:,.2f}")
        print(f"   • Average PO Value: ${total_po_value/len(self.pos):,.2f}")

        print("\n" + "="*60)
        print("✅ Data generation complete!")
        print("="*60)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║    PROCUREMENT DOCUMENT SYNTHETIC DATA GENERATOR          ║
║                                                           ║
║    Generating realistic Purchase Orders, Invoices,       ║
║    and Goods Received Notes for demo purposes            ║
╚═══════════════════════════════════════════════════════════╝
""")

    generator = SyntheticDataGenerator()
    generator.generate_all()
    generator.save_to_json()
    generator.print_summary()

    print("\n🎉 Ready to use! Files saved in data/synthetic/")
    print("   Next step: Run 'python scripts/generate_pdf_documents.py' to create PDFs")
