import os
import zipfile
import pandas as pd
from django.core.management.base import BaseCommand
from libraryapi.models import Author  # Replace 'libraryapi' with your actual app name
from django.db import transaction

class Command(BaseCommand):
    help = 'Seed Author data from a JSON file inside a ZIP archive in chunks'

    def handle(self, *args, **options):
        zip_file_path = '/var/www/html/spotter/archive.zip'  # Update this path
        json_file_name = 'authors.json/authors.json'  # Update with your JSON file name
        chunk_size = 10000
        total = 0
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            with z.open(json_file_name) as json_file:
                # Read the JSON data in chunks
                reader = pd.read_json(json_file, lines=True, chunksize=chunk_size)
                for chunk in reader:
                    records = chunk.to_dict(orient='records')
                    inserted_count = self.seed_authors_from_json(records)
                    total += inserted_count

        self.stdout.write(self.style.SUCCESS(f'Successfully inserted total {total} records.'))

    def seed_authors_from_json(self, records):
        objects_to_create = []
        existing_ids = set(
            Author.objects.filter(id__in=[record['id'] for record in records if 'id' in record])
            .values_list('id', flat=True)
        )

        for record in records:
            if 'id' in record and record['id'] in existing_ids:
                continue  # Skip existing records

            author = Author(
                id=record.get('id', None),  # Use None if you want Django to auto-generate the ID
                name=record.get('name', ''),
                gender=record.get('gender', ''),
                image_url=record.get('image_url', ''),
                about=record.get('about', ''),
                ratings_count=record.get('ratings_count', 0),
                average_rating=record.get('average_rating', 0.00),
                text_reviews_count=record.get('text_reviews_count', 0),
                fans_count=record.get('fans_count', 0),
                works_count=record.get('works_count', 0)
            )
            objects_to_create.append(author)

        # Insert the records into the database with exception handling
        inserted_count = 0
        for author in objects_to_create:
            try:
                with transaction.atomic():
                    author.save()
                inserted_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inserting author '{author.name}': {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'Successfully inserted {inserted_count} records.'))
        return inserted_count
