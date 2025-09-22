from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0004_alter_leaverequest_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateField(unique=True)),
                ('is_public', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
