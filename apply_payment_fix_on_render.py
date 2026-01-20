#!/usr/bin/env python
"""
Script to download and apply the payment calculation fix on Render
Run this on Render: python apply_payment_fix_on_render.py
"""

import urllib.request
import os
import shutil
from datetime import datetime

def download_and_apply_fix():
    """Download updated views.py and apply the fix"""
    
    # Path to views.py on Render
    views_path = '/doccano/backend/patches/monlam_ui/views.py'
    backup_path = f'/doccano/backend/patches/monlam_ui/views.py.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print("="*80)
    print("PAYMENT CALCULATION FIX - Download and Apply")
    print("="*80)
    
    # Step 1: Backup existing file
    if os.path.exists(views_path):
        print(f"\n1. Backing up existing file...")
        shutil.copy2(views_path, backup_path)
        print(f"   ✅ Backup created: {backup_path}")
    else:
        print(f"   ⚠️  File not found at {views_path}")
        return False
    
    # Step 2: Download updated file from GitHub
    print(f"\n2. Downloading updated views.py from GitHub...")
    url = 'https://raw.githubusercontent.com/MonlamAI/Monlam-Annotation-Tools/main/patches/monlam_ui/views.py'
    
    try:
        urllib.request.urlretrieve(url, views_path)
        print(f"   ✅ File downloaded successfully")
    except Exception as e:
        print(f"   ❌ Error downloading file: {e}")
        print(f"   🔄 Restoring backup...")
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, views_path)
        return False
    
    # Step 3: Verify the fix is present
    print(f"\n3. Verifying fix is applied...")
    try:
        with open(views_path, 'r') as f:
            content = f.read()
            
        # Check if the fix is present
        if "t.status in ['submitted', 'reviewed', 'rejected']" in content:
            print(f"   ✅ Fix verified: Payment calculation includes reviewed/rejected examples")
            return True
        else:
            print(f"   ⚠️  Fix not found in downloaded file")
            print(f"   🔄 Restoring backup...")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, views_path)
            return False
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False

if __name__ == '__main__':
    success = download_and_apply_fix()
    
    if success:
        print("\n" + "="*80)
        print("✅ FIX APPLIED SUCCESSFULLY!")
        print("="*80)
        print("\nNext steps:")
        print("1. Restart your Render service (or wait for auto-restart)")
        print("2. Check the analytics dashboard to verify payments are calculated correctly")
        print("3. Verify tgonpo's payment now shows a value instead of '-'")
    else:
        print("\n" + "="*80)
        print("❌ FIX FAILED - Backup restored")
        print("="*80)
        print("\nPlease check the error messages above and try again.")

