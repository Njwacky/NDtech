import io
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import pandas as pd
from nano.models import Workspace, UserProfile, WarehousePrice, PriceComparison
from nano.views_pos import warehouse_import, run_price_comparison


class WarehouseImportRecheckTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.ws = Workspace.objects.create(name='W')
        self.user = User.objects.create_user(username='m', password='x', is_staff=True)
        UserProfile.objects.create(user=self.user, role='manager', workspace=self.ws)

    def _import(self, df, warehouse_name='ShopX'):
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        csv_file = SimpleUploadedFile('prices.csv', buf.read(), content_type='text/csv')
        req = self.factory.post('/warehouse/import/', data={'file': csv_file, 'warehouse_name': warehouse_name})
        req.user = self.user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))
        return warehouse_import(req)

    # Point 1: standard Warehouse format (Product Name, Price) imports without crash
    def test_warehouse_format_imports(self):
        df = pd.DataFrame([
            {'Product Name': 'Sugar', 'Price': 19.99, 'Category': 'groceries',
             'Barcode': '123', 'Stock': 50, 'Unit Size': '1kg',
             'SKU': 'SUG-1', 'Supplier': 'Acme', 'Status': 'active', 'Description': 'sweet'}
        ])
        resp = self._import(df)
        self.assertEqual(resp.status_code, 302)
        wp = WarehousePrice.objects.get(product_name='Sugar', warehouse_name='ShopX')
        self.assertEqual(wp.price, Decimal('19.99'))
        self.assertEqual(wp.category, 'groceries')
        self.assertEqual(wp.workspace, self.ws)
        self.assertEqual(wp.unit_size, '1kg')
        self.assertEqual(wp.imported_by, self.user)

    # Point 2: product-format columns (name,price) are mapped correctly
    def test_product_format_imports(self):
        df = pd.DataFrame([
            {'name': 'Milk', 'price': 14.50, 'category': 'dairy', 'stock': 20, 'barcode': '456', 'unit_size': '1L'}
        ])
        self._import(df)
        wp = WarehousePrice.objects.get(product_name='Milk')
        self.assertEqual(wp.price, Decimal('14.50'))
        self.assertEqual(wp.warehouse_name, 'ShopX')

    # Point 3: no stray model-field crashes - extra SKU/Supplier/Status/Description columns ignored
    def test_extra_columns_ignored(self):
        df = pd.DataFrame([
            {'Product Name': 'Salt', 'Price': 5.0, 'sku': 'x', 'supplier': 'y',
             'status': 'z', 'description': 'w', 'notes': 'extra stuff'}
        ])
        # lowercase extra columns - should not crash
        resp = self._import(df)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(WarehousePrice.objects.filter(product_name='Salt').exists())

    # Point 4: update_or_create updates existing row instead of duplicating
    def test_upsert_no_duplicates(self):
        df1 = pd.DataFrame([{'Product Name': 'Bread', 'Price': 15.0}])
        df2 = pd.DataFrame([{'Product Name': 'Bread', 'Price': 12.0}])
        self._import(df1)
        self._import(df2)
        self.assertEqual(WarehousePrice.objects.filter(product_name='Bread').count(), 1)
        self.assertEqual(WarehousePrice.objects.get(product_name='Bread').price, Decimal('12.0'))

    # Point 5: price comparison is workspace-scoped and not crashing
    def test_price_comparison_scoped(self):
        ws2 = Workspace.objects.create(name='W2')
        WarehousePrice.objects.create(product_name='Rice', warehouse_name='WA', price=Decimal('20'), workspace=self.ws, imported_by=self.user)
        WarehousePrice.objects.create(product_name='Rice', warehouse_name='WB', price=Decimal('25'), workspace=self.ws, imported_by=self.user)
        WarehousePrice.objects.create(product_name='Rice', warehouse_name='WC', price=Decimal('99'), workspace=ws2, imported_by=self.user)
        run_price_comparison(workspace=self.ws)
        pcs = PriceComparison.objects.filter(workspace=self.ws, product_name='Rice')
        self.assertEqual(pcs.count(), 1)
        # comparison only looked at WS_A's prices (20 and 25), difference 5
        self.assertEqual(pcs.first().price_difference, Decimal('5'))
        # ws2 has only one price so no comparison created
        self.assertFalse(PriceComparison.objects.filter(workspace=ws2).exists())
