#!/usr/bin/env python3
"""
🎰 Extract Real Casino Images from Google Images

Direct extraction of image URLs from Google Images search results
for Mr Vegas Casino, then download and upload to WordPress.

Native LangChain approach using requests and BeautifulSoup.
"""

import requests
import json
import re
import base64
from urllib.parse import unquote, urlparse
from pathlib import Path
import time
from typing import List, Dict, Any
import logging

# WordPress configuration
WORDPRESS_BASE_URL = "https://www.crashcasino.io/wp-json/wp/v2"
WORDPRESS_USERNAME = "peterjpetrich"
WORDPRESS_APP_PASSWORD = "BUpX VLgF MRc1 9oVW pkrH TuTm"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_image_urls_from_google(query: str, max_images: int = 10) -> List[str]:
    """
    Extract actual image URLs from Google Images search results
    """
    try:
        # Google Images search URL
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"🔍 Searching Google Images for: {query}")
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extract image URLs from the HTML
        image_urls = []
        
        # Look for JSON data containing image URLs
        json_pattern = r'"ou":"([^"]+)"'
        matches = re.findall(json_pattern, response.text)
        
        for match in matches[:max_images]:
            # Decode URL
            decoded_url = unquote(match)
            if decoded_url.startswith('http') and any(ext in decoded_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                image_urls.append(decoded_url)
                logger.info(f"📸 Found image URL: {decoded_url}")
        
        # Alternative pattern for image URLs
        if not image_urls:
            img_pattern = r'"https://[^"]+\.(jpg|jpeg|png|webp)[^"]*"'
            img_matches = re.findall(img_pattern, response.text, re.IGNORECASE)
            
            for match in img_matches[:max_images]:
                clean_url = match.strip('"')
                image_urls.append(clean_url)
                logger.info(f"📸 Found alternative image URL: {clean_url}")
        
        logger.info(f"✅ Extracted {len(image_urls)} image URLs")
        return image_urls
        
    except Exception as e:
        logger.error(f"❌ Failed to extract image URLs: {e}")
        return []

def download_image(url: str, filename: str) -> bool:
    """
    Download an image from URL and save locally
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        
        logger.info(f"⬇️ Downloading: {url}")
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"⚠️ URL doesn't return image content: {content_type}")
            return False
        
        # Save the image
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Check file size
        file_size = Path(filename).stat().st_size
        if file_size < 10000:  # Less than 10KB
            logger.warning(f"⚠️ Image too small: {file_size} bytes")
            Path(filename).unlink()  # Delete small file
            return False
        
        logger.info(f"✅ Downloaded: {filename} ({file_size} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {url}: {e}")
        return False

def upload_to_wordpress(image_path: str, title: str, alt_text: str) -> int:
    """
    Upload image to WordPress media library
    """
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Prepare headers
        credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode('utf-8')
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Disposition': f'attachment; filename="{Path(image_path).name}"',
            'Content-Type': 'image/jpeg' if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') else 'image/png'
        }
        
        # Upload to WordPress
        logger.info(f"📤 Uploading to WordPress: {image_path}")
        response = requests.post(
            f"{WORDPRESS_BASE_URL}/media",
            headers=headers,
            data=image_data,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            media_data = response.json()
            media_id = media_data['id']
            
            # Update media metadata
            metadata_update = {
                'title': title,
                'alt_text': alt_text,
                'caption': f"Mr Vegas Casino - {title}"
            }
            
            requests.post(
                f"{WORDPRESS_BASE_URL}/media/{media_id}",
                headers={'Authorization': f'Basic {credentials}'},
                json=metadata_update
            )
            
            logger.info(f"✅ Uploaded to WordPress: Media ID {media_id}")
            return media_id
        else:
            logger.error(f"❌ WordPress upload failed: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Failed to upload {image_path}: {e}")
        return 0

def main():
    """
    Main function to extract, download, and upload casino images
    """
    logger.info("🎰 Starting Mr Vegas Casino Image Extraction")
    
    # Search queries for different casino aspects
    search_queries = [
        "mr vegas casino homepage interface",
        "mr vegas casino games lobby",
        "mr vegas casino slots interface", 
        "mr vegas casino mobile app"
    ]
    
    downloaded_images = []
    upload_results = []
    
    # Create downloads directory
    downloads_dir = Path("casino_images")
    downloads_dir.mkdir(exist_ok=True)
    
    for i, query in enumerate(search_queries):
        logger.info(f"🔍 Processing query {i+1}/{len(search_queries)}: {query}")
        
        # Extract image URLs
        image_urls = extract_image_urls_from_google(query, max_images=5)
        
        # Download first successful image from each query
        for j, url in enumerate(image_urls):
            # Determine file extension
            parsed_url = urlparse(url)
            path_lower = parsed_url.path.lower()
            
            if '.jpg' in path_lower or '.jpeg' in path_lower:
                ext = '.jpg'
            elif '.png' in path_lower:
                ext = '.png'
            elif '.webp' in path_lower:
                ext = '.webp'
            else:
                ext = '.jpg'  # Default
            
            filename = downloads_dir / f"mr_vegas_casino_{i+1}_{j+1}{ext}"
            
            if download_image(url, str(filename)):
                downloaded_images.append({
                    'file': str(filename),
                    'title': f"Mr Vegas Casino Interface {i+1}",
                    'query': query
                })
                break  # Got one good image for this query
            
            time.sleep(2)  # Be respectful with requests
    
    # Upload to WordPress
    logger.info(f"📤 Uploading {len(downloaded_images)} images to WordPress")
    
    for img_data in downloaded_images:
        media_id = upload_to_wordpress(
            img_data['file'],
            img_data['title'],
            f"Mr Vegas Casino interface screenshot - {img_data['query']}"
        )
        
        if media_id > 0:
            upload_results.append({
                'media_id': media_id,
                'title': img_data['title'],
                'file': img_data['file']
            })
        
        time.sleep(3)  # Rate limiting
    
    # Results summary
    logger.info("🎊 Image Extraction Complete!")
    logger.info(f"✅ Downloaded: {len(downloaded_images)} images")
    logger.info(f"📤 Uploaded: {len(upload_results)} images")
    
    if upload_results:
        logger.info("📋 WordPress Media IDs:")
        for result in upload_results:
            logger.info(f"  - {result['title']}: Media ID {result['media_id']}")
    
    return upload_results

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n🎰 Successfully processed {len(results)} casino images!")
        
        if results:
            print("\n📋 Media IDs for WordPress:")
            for result in results:
                print(f"  - {result['title']}: {result['media_id']}")
        
    except KeyboardInterrupt:
        print("\n⛔ Process interrupted by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()