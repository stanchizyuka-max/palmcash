#!/usr/bin/env python3
"""
LoanVista Template Update Script
This script updates all HTML templates to use the consistent Tailwind design system.
"""

import os
import re
from pathlib import Path

# Define the template directory
TEMPLATE_DIR = Path("templates")

# Color mapping from Bootstrap to Tailwind classes
COLOR_MAPPINGS = {
    # Bootstrap to Tailwind status badges
    'badge bg-success': 'status-approved',
    'badge bg-warning': 'status-pending', 
    'badge bg-danger': 'status-rejected',
    'badge bg-primary': 'status-active',
    'badge bg-secondary': 'status-completed',
    'badge bg-info': 'status-disbursed',
    
    # Bootstrap buttons to Tailwind buttons
    'btn btn-primary': 'btn-primary',
    'btn btn-success': 'btn-success',
    'btn btn-warning': 'btn-warning',
    'btn btn-danger': 'btn-danger',
    'btn btn-info': 'btn-info',
    'btn btn-secondary': 'btn-secondary',
    
    # Bootstrap outline buttons
    'btn btn-outline-primary': 'btn-outline-primary',
    'btn btn-outline-success': 'btn-outline-success',
    'btn btn-outline-warning': 'btn-outline-warning',
    'btn btn-outline-danger': 'btn-outline-danger',
    'btn btn-outline-info': 'btn-outline-info',
    'btn btn-outline-secondary': 'btn-outline-secondary',
    
    # Bootstrap colors to Tailwind colors
    'text-primary': 'text-primary-600',
    'text-success': 'text-success-600',
    'text-warning': 'text-warning-600',
    'text-danger': 'text-danger-600',
    'text-info': 'text-info-600',
    'text-secondary': 'text-secondary-600',
    'text-muted': 'text-secondary-500',
    
    # Background colors
    'bg-primary': 'bg-primary-600',
    'bg-success': 'bg-success-600',
    'bg-warning': 'bg-warning-600',
    'bg-danger': 'bg-danger-600',
    'bg-info': 'bg-info-600',
    'bg-secondary': 'bg-secondary-600',
}

# Templates that should extend base_tailwind.html
TEMPLATES_TO_UPDATE = [
    'accounts/login.html',
    'accounts/register.html', 
    'accounts/profile.html',
    'accounts/edit_profile.html',
    'clients/list.html',
    'clients/detail.html',
    'clients/edit.html',
    'clients/complete_profile.html',
    'dashboard/home.html',
    'documents/list.html',
    'documents/detail.html',
    'documents/upload.html',
    'documents/review_dashboard.html',
    'loans/list.html',
    'loans/apply.html',
    'loans/calculator.html',
    'loans/document_list.html',
    'loans/document_review_dashboard.html',
    'loans/status_dashboard.html',
    'loans/upload_document.html',
    'notifications/list.html',
    'pages/contact.html',
    'pages/terms.html',
    'payments/list.html',
    'payments/detail.html',
    'payments/make.html',
    'payments/schedule.html',
    'reports/list.html',
    'reports/financial.html',
    'reports/financial_report.html',
    'reports/payment_report.html',
    'reports/payments.html',
    'reports/monthly_collection_trend.html',
    'reports/loan_report.html',
]

def update_template_extends(file_path):
    """Update template to extend base_tailwind.html instead of base.html"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace base.html with base_tailwind.html
    content = content.replace("{% extends 'base.html' %}", "{% extends 'base_tailwind.html' %}")
    
    return content

def update_bootstrap_classes(content):
    """Replace Bootstrap classes with Tailwind equivalents"""
    
    # Replace color mappings
    for bootstrap_class, tailwind_class in COLOR_MAPPINGS.items():
        content = content.replace(bootstrap_class, tailwind_class)
    
    # Replace common Bootstrap layout classes
    bootstrap_to_tailwind = {
        'container': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
        'row': 'grid grid-cols-1 md:grid-cols-12 gap-6',
        'col-12': 'col-span-12',
        'col-md-6': 'col-span-12 md:col-span-6',
        'col-md-4': 'col-span-12 md:col-span-4',
        'col-md-8': 'col-span-12 md:col-span-8',
        'col-md-3': 'col-span-12 md:col-span-3',
        'col-md-9': 'col-span-12 md:col-span-9',
        
        # Bootstrap utilities
        'mb-4': 'mb-6',
        'mt-4': 'mt-6',
        'p-4': 'p-6',
        'text-center': 'text-center',
        'd-flex': 'flex',
        'justify-content-between': 'justify-between',
        'align-items-center': 'items-center',
        
        # Cards
        'card': 'bg-white rounded-xl shadow-lg overflow-hidden card-hover',
        'card-header': 'bg-gradient-to-r from-primary-500 to-primary-600 px-6 py-4',
        'card-body': 'p-6',
        'card-title': 'text-lg font-semibold text-white',
        
        # Tables
        'table': 'min-w-full divide-y divide-secondary-200',
        'table-striped': 'bg-white divide-y divide-secondary-200',
        'table-responsive': 'overflow-x-auto',
    }
    
    for bootstrap, tailwind in bootstrap_to_tailwind.items():
        content = re.sub(rf'\b{re.escape(bootstrap)}\b', tailwind, content)
    
    return content

def wrap_content_with_layout(content):
    """Wrap content with consistent layout structure"""
    
    # Check if content already has the layout wrapper
    if 'min-h-screen bg-secondary-50' in content:
        return content
    
    # Find the content block
    content_match = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL)
    if content_match:
        original_content = content_match.group(1).strip()
        
        # Create new wrapped content
        new_content = f'''{% block content %}
<div class="min-h-screen bg-secondary-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
{original_content}
    </div>
</div>
{% endblock %}'''
        
        # Replace the content block
        content = content.replace(content_match.group(0), new_content)
    
    return content

def update_template_file(file_path):
    """Update a single template file"""
    try:
        print(f"Updating {file_path}...")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply updates
        content = update_template_extends(content)
        content = update_bootstrap_classes(content)
        content = wrap_content_with_layout(content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully updated {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all templates"""
    print("🎨 Starting LoanVista Template Update...")
    print("=" * 50)
    
    updated_count = 0
    error_count = 0
    
    # Update specific templates
    for template_path in TEMPLATES_TO_UPDATE:
        full_path = TEMPLATE_DIR / template_path
        
        if full_path.exists():
            if update_template_file(full_path):
                updated_count += 1
            else:
                error_count += 1
        else:
            print(f"⚠️  Template not found: {full_path}")
    
    print("=" * 50)
    print(f"📊 Update Summary:")
    print(f"   ✅ Successfully updated: {updated_count} files")
    print(f"   ❌ Errors: {error_count} files")
    print(f"🎉 Template update complete!")

if __name__ == "__main__":
    main()
