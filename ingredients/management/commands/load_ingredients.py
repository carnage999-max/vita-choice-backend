import csv
from django.core.management.base import BaseCommand
from ingredients.models import Ingredient

class Command(BaseCommand):
    help = 'Import ingredients from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        self.stdout.write(self.style.WARNING(f'Starting import from {csv_file}...'))
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        name = row.get('Ingredient', '').strip()
                        
                        if not name:
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: Skipping - no name')
                            )
                            error_count += 1
                            continue
                        
                        ingredient, created = Ingredient.objects.update_or_create(
                            name=name,
                            defaults={
                                'category': row.get('Category', '').strip(),
                                'source': row.get('Source', '').strip(),
                                'safety': row.get('Safety', '').strip(),
                                'evidence': row.get('Evidence', '').strip(),
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: {str(e)}')
                        )
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            return
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'✅ Created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'🔄 Updated: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS(f'📊 Total: {created_count + updated_count}'))
        self.stdout.write(self.style.SUCCESS('='*50))