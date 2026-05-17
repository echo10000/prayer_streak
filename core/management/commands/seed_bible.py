import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import BibleBook, BibleChapter


class Command(BaseCommand):
    help = "Seed the built-in Bible reading book data."

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[2] / "data" / "john_kjv.json"
        with data_path.open(encoding="utf-8") as data_file:
            payload = json.load(data_file)

        with transaction.atomic():
            book, _ = BibleBook.objects.update_or_create(
                abbreviation=payload["abbreviation"],
                defaults={
                    "name": payload["name"],
                    "testament": payload["testament"],
                    "total_chapters": len(payload["chapters"]),
                    "description": payload["description"],
                    "sort_order": payload["sort_order"],
                },
            )

            for chapter_data in payload["chapters"]:
                BibleChapter.objects.update_or_create(
                    book=book,
                    number=chapter_data["number"],
                    defaults={
                        "title": chapter_data.get("title", ""),
                        "text": chapter_data["text"],
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {book.name} with {book.total_chapters} chapters."
            )
        )
