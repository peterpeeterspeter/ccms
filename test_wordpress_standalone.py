"""
🚀 Standalone WordPress Publishing Test - CrashCasino.io
======================================================

Simple standalone test for WordPress publishing functionality without
complex import dependencies. Tests core WordPress API integration
with the provided CrashCasino.io credentials.

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Task: Phase 4 Testing - WordPress Publishing Standalone
Version: 1.0.0
"""

import requests
import base64
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleWordPressClient:
    """Simple WordPress REST API client for testing"""
    
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip('/')
        self.base_url = f"{self.site_url}/wp-json/wp/v2"
        
        # Create Basic Auth header
        auth_string = f"{username}:{app_password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'User-Agent': 'WordPress-Test-Client/1.0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> bool:
        """Test WordPress API connection"""
        try:
            logger.info(f"Testing connection to: {self.base_url}")
            response = self.session.get(f"{self.base_url}/users/me", timeout=30)
            logger.info(f"Connection response: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Connected as user: {user_data.get('name', 'Unknown')}")
                return True
            else:
                logger.error(f"Connection failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def create_test_post(self) -> Optional[Tuple[int, str]]:
        """Create a test WordPress post"""
        try:
            post_data = {
                'title': f'WordPress API Test Post - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'content': '''
                <h2>WordPress Publishing Test</h2>
                <p>This is a test post created via the WordPress REST API to verify the publishing integration is working correctly.</p>
                
                <h3>Test Details</h3>
                <ul>
                    <li>Created: {}</li>
                    <li>Method: WordPress REST API</li>
                    <li>Authentication: Application Password</li>
                    <li>Status: Draft (for safety)</li>
                </ul>
                
                <p><strong>Note:</strong> This is an automated test post and can be deleted.</p>
                '''.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                'status': 'draft',  # Create as draft for safety
                'excerpt': 'Test post created via WordPress REST API to verify publishing integration.',
                'categories': [],  # Will be assigned based on available categories
                'tags': []  # Will be assigned based on available tags
            }
            
            logger.info("Creating test post...")
            response = self.session.post(f"{self.base_url}/posts", json=post_data, timeout=30)
            
            if response.status_code == 201:
                post_response = response.json()
                post_id = post_response['id']
                post_url = post_response['link']
                
                logger.info(f"✅ Test post created successfully!")
                logger.info(f"   Post ID: {post_id}")
                logger.info(f"   Post URL: {post_url}")
                logger.info(f"   Status: {post_response.get('status', 'unknown')}")
                
                return post_id, post_url
            else:
                logger.error(f"❌ Post creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Post creation error: {str(e)}")
            return None
    
    def get_site_info(self) -> Dict[str, Any]:
        """Get WordPress site information"""
        try:
            response = self.session.get(f"{self.site_url}/wp-json", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


def test_crashcasino_wordpress_publishing():
    """Test WordPress publishing with CrashCasino.io credentials"""
    
    print("\n" + "="*70)
    print("🚀 WORDPRESS PUBLISHING TEST - CRASHCASINO.IO")
    print("="*70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # CrashCasino.io credentials
    site_url = "https://crashcasino.io"
    username = "nmlwh"
    app_password = "KFKz bo6B ZXOS 7VOA rHWb oxdC"
    
    print(f"🌐 Site URL: {site_url}")
    print(f"👤 Username: {username}")
    print("🔐 Using provided application password")
    
    try:
        # Create WordPress client
        client = SimpleWordPressClient(site_url, username, app_password)
        
        # Test 1: Connection Test
        print(f"\n{'─'*50}")
        print("🔗 STEP 1: Testing WordPress API Connection")
        print(f"{'─'*50}")
        
        if not client.test_connection():
            print("❌ Connection test failed - aborting test")
            return False
        
        # Test 2: Get Site Info
        print(f"\n{'─'*50}")
        print("ℹ️  STEP 2: Getting WordPress Site Information")
        print(f"{'─'*50}")
        
        site_info = client.get_site_info()
        if "error" not in site_info:
            print("✅ Site information retrieved:")
            print(f"   📛 Name: {site_info.get('name', 'Unknown')}")
            print(f"   📝 Description: {site_info.get('description', 'No description')}")
            print(f"   🏠 Home URL: {site_info.get('home', 'Unknown')}")
            print(f"   ⚙️  Namespaces: {', '.join(site_info.get('namespaces', []))}")
        else:
            print(f"⚠️  Could not retrieve site info: {site_info['error']}")
        
        # Test 3: Create Test Post
        print(f"\n{'─'*50}")
        print("📝 STEP 3: Creating Test WordPress Post")
        print(f"{'─'*50}")
        
        post_result = client.create_test_post()
        if post_result:
            post_id, post_url = post_result
            print("🎉 WordPress Publishing Test SUCCESSFUL!")
            print(f"   📄 Created post with ID: {post_id}")
            print(f"   🔗 Post URL: {post_url}")
            print("   📋 Status: Draft (ready for review)")
            
            print(f"\n💡 Next Steps:")
            print(f"   1. Visit {site_url}/wp-admin/edit.php to see the draft post")
            print(f"   2. Review and edit the post if needed")
            print(f"   3. Publish when ready or delete if it's just a test")
            
            return True
        else:
            print("❌ Test post creation failed")
            return False
            
    except Exception as e:
        print(f"\n❌ WordPress publishing test failed: {str(e)}")
        logger.error(f"Test execution error: {str(e)}", exc_info=True)
        return False
    
    finally:
        print(f"\n{'='*70}")
        print("🏁 WORDPRESS PUBLISHING TEST COMPLETED")
        print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)


def main():
    """Main test execution"""
    print("🧪 Starting WordPress Publishing Standalone Test...")
    
    try:
        success = test_crashcasino_wordpress_publishing()
        
        if success:
            print("\n✅ All tests passed successfully!")
            print("🎯 WordPress publishing integration is working correctly")
            print("🚀 Ready to proceed with Phase 4 implementation")
        else:
            print("\n❌ Test failed - check logs for details")
            print("🔧 Please verify credentials and WordPress configuration")
            
        return success
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test startup error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)