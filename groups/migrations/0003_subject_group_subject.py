from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('groups', '0002_initial'),   # depends on existing 0002_initial
    ]
    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',       models.CharField(max_length=100)),
                ('code',       models.CharField(max_length=20)),
                ('department', models.CharField(choices=[('SE','Software Engineering'),('CS','Computer Science')], max_length=2)),
                ('is_active',  models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'subjects', 'ordering': ['department', 'name']},
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(fields=['code','department'], name='unique_subject_code_dept'),
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='group',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups', to='groups.subject'),
        ),
    ]
