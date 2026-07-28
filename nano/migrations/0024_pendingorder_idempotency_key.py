from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('nano', '0023_sale_processed_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendingorder',
            name='idempotency_key',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
