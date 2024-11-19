from django.db import migrations
from pgvector.psycopg import Bit


def fix_bits(apps, schema_editor):
    PageEmbedding = apps.get_model("api", "PageEmbedding")
    db_alias = schema_editor.connection.alias

    for page_embedding in PageEmbedding.objects.using(db_alias).all():
        if page_embedding.embedding is not None:
            bit_embeddings = Bit(page_embedding.embedding.to_numpy() > 0).to_text()

            PageEmbedding.objects.using(db_alias).filter(id=page_embedding.id).update(
                bit_embedding=bit_embeddings
            )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0028_populate_bits"),
    ]

    operations = [
        migrations.RunPython(fix_bits, reverse_code=migrations.RunPython.noop),
    ]
