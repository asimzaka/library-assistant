import os
import zipfile
import pandas as pd
from django.core.management.base import BaseCommand
from libraryapi.models import Author, Book, RatingDistribution
from django.db import transaction
import re
from datetime import datetime
from libraryapi.utils import BookVectorizer
from bs4 import BeautifulSoup

def clean_text(text):
    if pd.isna(text):
        return text

    # Remove HTML tags
    text = BeautifulSoup(text, "lxml").text

    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text)     # Replace multiple spaces with a single space

    return text.strip()

class Command(BaseCommand):
    help = 'Seed Book and Author data from a JSON file inside a ZIP archive in chunks'

    def handle(self, *args, **options):
        zip_file_path = '/var/www/html/spotter/archive.zip'  # Update this path
        json_file_name = 'books.json/books.json'  # Update with your JSON file name
        chunk_size = 5000
        total_books = 0
        records_to_skip = 800000
        records_skipped = 0
        vectorizer = BookVectorizer() 

        with zipfile.ZipFile(zip_file_path, 'r') as z:
            with z.open(json_file_name) as json_file:
                # Read the JSON data in chunks
                reader = pd.read_json(json_file, lines=True, chunksize=chunk_size)
                for chunk in reader:
                    # Skip records until we reach the required number
                    if records_skipped < records_to_skip:
                        records_skipped += len(chunk)
                        if records_skipped >= records_to_skip:
                            # If we've skipped enough records, take the remainder to process
                            remainder = records_skipped - records_to_skip
                            chunk = chunk.iloc[remainder:]
                        else:
                            continue
                    # for chunk in reader:
                    chunk['authors'] = chunk['authors'].fillna(0)
                    chunk['num_pages'] = chunk['num_pages'].replace('', 0)
                    chunk['description'] = chunk['description'].apply(clean_text)
                    records = chunk.to_dict(orient='records')
                    print("Processing chunck ..... seed_books_from_json", chunk_size)
                    total_books += self.seed_books_from_json(records, vectorizer)
                    print("Chunck Processed..... seed_books_from_json", total_books)

        self.stdout.write(self.style.SUCCESS(f'Successfully inserted total: {total_books} books.'))

    def seed_books_from_json(self, records, vectorizer):
        objects_to_create = []
        existing_work_ids = set(
            Book.objects.filter(work_id__in=[record['work_id'] for record in records if 'work_id' in record])
            .values_list('work_id', flat=True)
        )
        for record in records:
            try:
                # if 'work_id' in record and record['work_id'] in existing_work_ids:
                #     continue  # Skip existing records
                authors = []
                authors_list = record.get('authors', [])
                if authors_list:
                    for a in authors_list:
                        try:
                            author = Author.objects.get(id=a['id'])
                            authors.append(author)
                        except Author.DoesNotExist:
                            pass

                publication_date = self.parse_date(record.get('publication_date', None))
                original_publication_date = self.parse_date(record.get('original_publication_date', None))

                vector = vectorizer.generate_vector(record.get('title', ''), record.get('description', ''))
                book = Book(
                    title=record.get('title', ''),
                    work_id=record.get('work_id', ''),
                    isbn=record.get('isbn', ''),
                    isbn13=record.get('isbn13', ''),
                    asin=record.get('asin', ''),
                    language=record.get('language', ''),
                    average_rating=record.get('average_rating', 0.00),
                    ratings_count=record.get('ratings_count', 0),
                    text_reviews_count=record.get('text_reviews_count', 0),
                    publication_date=publication_date,
                    original_publication_date=original_publication_date,
                    format=record.get('format', ''),
                    edition_information=record.get('edition_information', ''),
                    image_url=record.get('image_url', ''),
                    publisher=record.get('publisher', ''),
                    num_pages=record.get('num_pages', 0),
                    description=record.get('description', ''),
                    vector=vector
                )
                book.save()
                book.authors.set(authors)

                rating_dist_str = record.get('rating_dist', '')
                rating_dist = self.parse_rating_dist(rating_dist_str)
                
                # Create or update the RatingDistribution instance
                if rating_dist:
                    rating_distribution = RatingDistribution.objects.create(
                        rating_5=rating_dist.get('5', 0),
                        rating_4=rating_dist.get('4', 0),
                        rating_3=rating_dist.get('3', 0),
                        rating_2=rating_dist.get('2', 0),
                        rating_1=rating_dist.get('1', 0),
                        total=rating_dist.get('total', 0)
                    )
                    book.rating_distribution = rating_distribution
                    book.save()
                
                objects_to_create.append(book)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inserting book '{record.get('title', 'Unknown')}': {str(e)}"))
        if objects_to_create:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS(f'Successfully inserted {len(objects_to_create)} books.'))
        return len(objects_to_create)

    def parse_date(self, date_str):
        if date_str:
            try:
                # Check if date_str is in YYYY-MM format
                if re.match(r'^\d{4}-\d{2}$', date_str):
                    # Append '-01' to make it YYYY-MM-DD
                    date_str += '-01'
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None

    def parse_rating_dist(self, rating_dist_str):
        # Use a regular expression to extract the rating distribution values
        pattern = r'(\d+):(\d+)'
        rating_dist = {k: int(v) for k, v in re.findall(pattern, rating_dist_str)}

        # Extract the total
        total_match = re.search(r'total:(\d+)', rating_dist_str)
        if total_match:
            rating_dist['total'] = int(total_match.group(1))
        
        return rating_dist
