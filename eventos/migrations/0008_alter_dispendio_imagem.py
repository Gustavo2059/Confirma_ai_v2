from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0007_dispendio_imagem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dispendio',
            name='imagem',
            field=models.FileField(blank=True, null=True, upload_to='dispendios/'),
        ),
    ]
