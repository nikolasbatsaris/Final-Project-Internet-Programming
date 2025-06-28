#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freightflow.settings')
django.setup()

from logistics.models import JobCategory, JobPost
from django.contrib.auth.models import User

def add_sample_data():
    print("Adding sample data to the database...")
    
    # Create job categories
    categories = [
        'General Cargo',
        'Heavy Machinery',
        'Electronics',
        'Food & Beverages',
        'Construction Materials',
        'Automotive',
        'Furniture',
        'Textiles',
        'Chemicals',
        'Agricultural Products'
    ]
    
    created_categories = {}
    for category_name in categories:
        category, created = JobCategory.objects.get_or_create(name=category_name)
        created_categories[category_name] = category
        if created:
            print(f"Created category: {category_name}")
    
    # Get or create a user for posting jobs
    user, created = User.objects.get_or_create(
        username='freight_manager',
        defaults={
            'email': 'manager@freightflow.com',
            'first_name': 'Freight',
            'last_name': 'Manager'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print("Created user: freight_manager")
    
    # Sample job data
    sample_jobs = [
        {
            'title': 'Urgent Electronics Shipment - Athens to Thessaloniki',
            'description': 'Need to transport sensitive electronics equipment including servers and networking devices. Requires climate-controlled transport and careful handling. Delivery needed within 48 hours.',
            'origin': 'Athens, Greece',
            'destination': 'Thessaloniki, Greece',
            'cargo_type': 'Electronics',
            'weight_kg': 2500.0,
            'pickup_date': date.today() + timedelta(days=1)
        },
        {
            'title': 'Heavy Machinery Transport - Piraeus to Patras',
            'description': 'Transport of industrial machinery including CNC machines and production equipment. Requires specialized heavy transport with proper securing. Equipment is fragile and valuable.',
            'origin': 'Piraeus, Greece',
            'destination': 'Patras, Greece',
            'cargo_type': 'Heavy Machinery',
            'weight_kg': 15000.0,
            'pickup_date': date.today() + timedelta(days=3)
        },
        {
            'title': 'Fresh Food Delivery - Crete to Athens',
            'description': 'Transport of fresh agricultural products including vegetables, fruits, and dairy products. Requires refrigerated transport and quick delivery to maintain freshness.',
            'origin': 'Heraklion, Crete',
            'destination': 'Athens, Greece',
            'cargo_type': 'Food & Beverages',
            'weight_kg': 5000.0,
            'pickup_date': date.today() + timedelta(days=2)
        },
        {
            'title': 'Construction Materials - Volos to Larissa',
            'description': 'Transport of construction materials including cement, steel beams, and building supplies. Standard flatbed transport required. Multiple pickup points available.',
            'origin': 'Volos, Greece',
            'destination': 'Larissa, Greece',
            'cargo_type': 'Construction Materials',
            'weight_kg': 8000.0,
            'pickup_date': date.today() + timedelta(days=4)
        },
        {
            'title': 'Automotive Parts - Thessaloniki to Ioannina',
            'description': 'Transport of automotive spare parts and components. Requires careful packaging and handling. Time-sensitive delivery for repair shop.',
            'origin': 'Thessaloniki, Greece',
            'destination': 'Ioannina, Greece',
            'cargo_type': 'Automotive',
            'weight_kg': 1200.0,
            'pickup_date': date.today() + timedelta(days=1)
        },
        {
            'title': 'Furniture Collection - Rhodes to Athens',
            'description': 'Transport of high-end furniture including antiques and custom pieces. Requires white-glove service and climate-controlled environment. Fragile items need special care.',
            'origin': 'Rhodes, Greece',
            'destination': 'Athens, Greece',
            'cargo_type': 'Furniture',
            'weight_kg': 3000.0,
            'pickup_date': date.today() + timedelta(days=5)
        },
        {
            'title': 'Textile Shipment - Komotini to Kavala',
            'description': 'Transport of textile materials and finished garments. Requires clean, dry transport environment. Multiple pallets to be delivered to different locations.',
            'origin': 'Komotini, Greece',
            'destination': 'Kavala, Greece',
            'cargo_type': 'Textiles',
            'weight_kg': 4000.0,
            'pickup_date': date.today() + timedelta(days=2)
        },
        {
            'title': 'Chemical Transport - Patras to Corinth',
            'description': 'Transport of industrial chemicals. Requires certified hazardous materials transport with proper documentation and safety equipment.',
            'origin': 'Patras, Greece',
            'destination': 'Corinth, Greece',
            'cargo_type': 'Chemicals',
            'weight_kg': 6000.0,
            'pickup_date': date.today() + timedelta(days=3)
        },
        {
            'title': 'Agricultural Equipment - Larissa to Volos',
            'description': 'Transport of farming equipment and agricultural machinery. Requires specialized transport for large equipment. Multiple pieces to be delivered.',
            'origin': 'Larissa, Greece',
            'destination': 'Volos, Greece',
            'cargo_type': 'Agricultural Products',
            'weight_kg': 12000.0,
            'pickup_date': date.today() + timedelta(days=4)
        },
        {
            'title': 'General Cargo - Chania to Heraklion',
            'description': 'Mixed general cargo including household items, small machinery, and commercial goods. Standard transport service required. Multiple pickup and delivery points.',
            'origin': 'Chania, Crete',
            'destination': 'Heraklion, Crete',
            'cargo_type': 'General Cargo',
            'weight_kg': 3500.0,
            'pickup_date': date.today() + timedelta(days=1)
        }
    ]
    
    # Create job posts
    for job_data in sample_jobs:
        job, created = JobPost.objects.get_or_create(
            title=job_data['title'],
            defaults={
                'description': job_data['description'],
                'origin': job_data['origin'],
                'destination': job_data['destination'],
                'cargo_type': created_categories[job_data['cargo_type']],
                'weight_kg': job_data['weight_kg'],
                'pickup_date': job_data['pickup_date'],
                'created_by': user,
                'likes': 0
            }
        )
        if created:
            print(f"Created job: {job_data['title']}")
    
    print(f"\nSample data added successfully!")
    print(f"Created {len(created_categories)} job categories")
    print(f"Created {len(sample_jobs)} job posts")
    print(f"User: freight_manager (password: password123)")

if __name__ == '__main__':
    add_sample_data() 