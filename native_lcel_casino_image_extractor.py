#!/usr/bin/env python3
"""
🎰 Native LangChain LCEL Casino Image Extractor
==============================================

Pure native LangChain solution using only RunnableLambda and standard library.
Extracts actual casino images from Google Images (not screenshots of interface).

LCEL Chain Architecture:
fetch_html | parse_urls | download_images | upload_to_wp | update_post
"""

import requests
import json
import re
import base64
import logging
from typing import Dict, List, Any
from pathlib import Path
from urllib.parse import unquote
import time

from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# WordPress Configuration  
WORDPRESS_BASE_URL = "https://www.crashcasino.io/wp-json/wp/v2"
WORDPRESS_USERNAME = "nmlwh"
WORDPRESS_APP_PASSWORD = "G4Vd TiTf k1Yn CCII j24L F4Ls"
MR_VEGAS_POST_ID = 51817

def fetch_google_images_search(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Fetch Google Images search HTML using native requests
    """
    try:
        search_query = inputs.get("search_query", "mr vegas casino interface screenshots")
        google_url = f"https://images.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"🔍 Fetching Google Images for: {search_query}")
        response = requests.get(google_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return {
            **inputs,
            "html_content": response.text,
            "search_success": True,
            "search_url": google_url
        }
        
    except Exception as e:
        logger.error(f"❌ Google Images fetch failed: {e}")
        return {
            **inputs, 
            "search_success": False,
            "error": str(e)
        }

def extract_image_urls_from_html(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Parse actual image URLs from Google Images HTML
    """
    if not inputs.get("search_success", False):
        return {**inputs, "parse_success": False}
    
    try:
        html_content = inputs.get("html_content", "")
        image_urls = []
        
        # Multiple extraction patterns for Google Images
        
        # Pattern 1: "ou":"<url>" (original URL)
        ou_pattern = r'"ou":"([^"]+)"'
        ou_matches = re.findall(ou_pattern, html_content)
        
        for match in ou_matches:
            decoded_url = unquote(match)
            if (decoded_url.startswith('http') and 
                any(ext in decoded_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and
                'casino' in decoded_url.lower() or 'vegas' in decoded_url.lower()):
                image_urls.append(decoded_url)
        
        # Pattern 2: ["<url>", width, height, ...] arrays
        array_pattern = r'\["(https://[^"]+\.(jpg|jpeg|png|webp)[^"]*)",\d+,\d+'
        array_matches = re.findall(array_pattern, html_content, re.IGNORECASE)
        
        for match_tuple in array_matches:
            url = match_tuple[0]
            if (url not in image_urls and 
                ('casino' in url.lower() or 'vegas' in url.lower() or len(url) > 100)):
                image_urls.append(url)
        
        # Pattern 3: JavaScript object with image data
        js_pattern = r'"(https://[^"]+\.(?:jpg|jpeg|png|webp))"[^}]*"casino|vegas"'
        js_matches = re.findall(js_pattern, html_content, re.IGNORECASE)
        
        for match in js_matches:
            if match not in image_urls:
                image_urls.append(match)
        
        # Pattern 4: Any large image URLs (fallback)
        if len(image_urls) < 2:
            large_image_pattern = r'"(https://[^"]+\.(jpg|jpeg|png|webp)[^"]*)"'
            large_matches = re.findall(large_image_pattern, html_content, re.IGNORECASE)
            
            for match in large_matches:
                if (match not in image_urls and 
                    len(match) > 80 and  # Longer URLs likely to be actual images
                    'gstatic.com' not in match and  # Skip Google static assets
                    'googleapis.com' not in match):
                    image_urls.append(match)
        
        # Filter and validate URLs
        valid_urls = []
        for url in image_urls:
            # Skip obvious non-casino images
            if any(skip in url.lower() for skip in ['icon', 'logo', 'button', 'arrow', 'gstatic']):
                continue
            # Prefer URLs that might contain casino content
            valid_urls.append(url)
        
        # Limit to max images
        max_images = inputs.get("max_images", 4)
        filtered_urls = valid_urls[:max_images]
        
        logger.info(f"📸 Extracted {len(filtered_urls)} image URLs")
        for i, url in enumerate(filtered_urls):
            logger.info(f"  {i+1}. {url[:100]}...")
        
        return {
            **inputs,
            "image_urls": filtered_urls,
            "parse_success": len(filtered_urls) > 0,
            "total_found": len(image_urls),
            "valid_found": len(valid_urls)
        }
        
    except Exception as e:
        logger.error(f"❌ URL extraction failed: {e}")
        return {**inputs, "parse_success": False, "error": str(e)}

def download_actual_casino_images(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Download the actual casino images from their source URLs
    """
    if not inputs.get("parse_success", False):
        return {**inputs, "download_success": False}
    
    try:
        image_urls = inputs.get("image_urls", [])
        downloaded_images = []
        
        # Create temp directory
        temp_dir = Path("temp_casino_images")
        temp_dir.mkdir(exist_ok=True)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        
        for i, url in enumerate(image_urls):
            try:
                logger.info(f"⬇️ Downloading image {i+1}/{len(image_urls)}")
                
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    logger.warning(f"⚠️ Not an image: {content_type}")
                    continue
                
                # Determine file extension
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default
                
                # Save image
                filename = temp_dir / f"mr_vegas_casino_{i+1}{ext}"
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Check file size (filter out small logos/icons)
                file_size = filename.stat().st_size
                if file_size < 10000:  # Less than 10KB
                    logger.warning(f"⚠️ Image {i+1} too small: {file_size} bytes")
                    filename.unlink()
                    continue
                
                downloaded_images.append({
                    "file_path": str(filename),
                    "original_url": url,
                    "file_size": file_size,
                    "content_type": content_type,
                    "index": i+1
                })
                
                logger.info(f"✅ Downloaded: {filename.name} ({file_size:,} bytes)")
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to download image {i+1}: {e}")
                continue
        
        return {
            **inputs,
            "downloaded_images": downloaded_images,
            "download_success": len(downloaded_images) > 0,
            "total_downloaded": len(downloaded_images)
        }
        
    except Exception as e:
        logger.error(f"❌ Download process failed: {e}")
        return {**inputs, "download_success": False, "error": str(e)}

def upload_images_to_wordpress(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4: Upload downloaded images to WordPress media library
    """
    if not inputs.get("download_success", False):
        return {**inputs, "upload_success": False}
    
    try:
        downloaded_images = inputs.get("downloaded_images", [])
        media_ids = []
        
        credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode('utf-8')
        
        for img_data in downloaded_images:
            try:
                file_path = img_data["file_path"]
                content_type = img_data["content_type"]
                index = img_data["index"]
                
                logger.info(f"📤 Uploading to WordPress: {Path(file_path).name}")
                
                # Read image data
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # Upload headers
                headers = {
                    'Authorization': f'Basic {credentials}',
                    'Content-Type': content_type,
                    'Content-Disposition': f'attachment; filename="{Path(file_path).name}"'
                }
                
                # Upload to WordPress
                response = requests.post(
                    f"{WORDPRESS_BASE_URL}/media",
                    headers=headers,
                    data=image_data,
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    media_data = response.json()
                    media_id = media_data['id']
                    media_ids.append({
                        "media_id": media_id,
                        "url": media_data.get('source_url', ''),
                        "title": f"Mr Vegas Casino Interface {index}",
                        "index": index
                    })
                    
                    # Update metadata
                    metadata_update = {
                        'title': f"Mr Vegas Casino Interface {index}",
                        'alt_text': f"Mr Vegas Casino interface screenshot {index}",
                        'caption': f"Mr Vegas Casino - Interface View {index}"
                    }
                    
                    requests.post(
                        f"{WORDPRESS_BASE_URL}/media/{media_id}",
                        headers={'Authorization': f'Basic {credentials}'},
                        json=metadata_update
                    )
                    
                    logger.info(f"✅ Uploaded: Media ID {media_id}")
                else:
                    logger.warning(f"⚠️ Upload failed: {response.status_code} - {response.text}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to upload {img_data.get('file_path', 'unknown')}: {e}")
                continue
        
        return {
            **inputs,
            "media_ids": media_ids,
            "upload_success": len(media_ids) > 0,
            "total_uploaded": len(media_ids)
        }
        
    except Exception as e:
        logger.error(f"❌ WordPress upload failed: {e}")
        return {**inputs, "upload_success": False, "error": str(e)}

def update_wordpress_post_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 5: Update WordPress post content with actual images
    """
    if not inputs.get("upload_success", False):
        return {**inputs, "post_update_success": False}
    
    try:
        media_ids = inputs.get("media_ids", [])
        
        # Get current post content
        credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode('utf-8')
        headers = {'Authorization': f'Basic {credentials}'}
        
        logger.info(f"📝 Updating WordPress post {MR_VEGAS_POST_ID}")
        
        # Fetch current post
        response = requests.get(
            f"{WORDPRESS_BASE_URL}/posts/{MR_VEGAS_POST_ID}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch post: {response.status_code}")
        
        post_data = response.json()
        current_content = post_data.get('content', {})
        
        # Handle different content formats
        if isinstance(current_content, dict):
            content_text = current_content.get('raw', current_content.get('rendered', ''))
        else:
            content_text = str(current_content)
        
        # Create image HTML from uploaded media
        image_html_parts = []
        for media_info in media_ids:
            media_id = media_info["media_id"]
            title = media_info["title"]
            url = media_info["url"]
            
            img_html = f'<figure class="wp-block-image size-large"><img src="{url}" alt="{title}" class="wp-image-{media_id}"/><figcaption>{title}</figcaption></figure>'
            image_html_parts.append(img_html)
        
        # Insert images into content (replace placeholders or add to specific sections)
        images_section = "\n\n".join(image_html_parts)
        
        # Look for existing image placeholders or add to end
        if "[casino-images]" in content_text:
            updated_content = content_text.replace("[casino-images]", images_section)
        else:
            # Add images before conclusion or at end
            if "</div>" in content_text:
                # Insert before last closing div
                updated_content = content_text.replace("</div>", f"\n\n{images_section}\n\n</div>")
            else:
                updated_content = f"{content_text}\n\n{images_section}"
        
        # Update post
        update_data = {
            'content': updated_content
        }
        
        response = requests.post(
            f"{WORDPRESS_BASE_URL}/posts/{MR_VEGAS_POST_ID}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            logger.info("✅ WordPress post updated successfully")
            return {
                **inputs,
                "post_update_success": True,
                "updated_content_length": len(updated_content)
            }
        else:
            logger.error(f"❌ Post update failed: {response.status_code}")
            return {**inputs, "post_update_success": False}
        
    except Exception as e:
        logger.error(f"❌ Post update failed: {e}")
        return {**inputs, "post_update_success": False, "error": str(e)}

def create_casino_image_chain():
    """
    🎰 Create the complete native LangChain LCEL chain
    """
    return (
        RunnablePassthrough() |
        RunnableLambda(fetch_google_images_search) |
        RunnableLambda(extract_image_urls_from_html) |
        RunnableLambda(download_actual_casino_images) |
        RunnableLambda(upload_images_to_wordpress) |
        RunnableLambda(update_wordpress_post_content)
    )

def main():
    """
    Execute the native LangChain casino image extraction chain
    """
    logger.info("🎰 Starting Native LangChain Casino Image Extraction")
    
    # Input configuration
    config = {
        "search_query": "mr vegas casino screenshots website interface",
        "max_images": 6
    }
    
    # Create and execute LCEL chain
    chain = create_casino_image_chain()
    
    try:
        result = chain.invoke(config)
        
        # Log final results
        logger.info("🎊 Casino Image Extraction Complete!")
        logger.info(f"✅ Search Success: {result.get('search_success', False)}")
        logger.info(f"📸 Parse Success: {result.get('parse_success', False)}")
        logger.info(f"⬇️ Download Success: {result.get('download_success', False)}")
        logger.info(f"📤 Upload Success: {result.get('upload_success', False)}")
        logger.info(f"📝 Post Update Success: {result.get('post_update_success', False)}")
        
        if result.get("media_ids"):
            logger.info("📋 WordPress Media IDs:")
            for media_info in result["media_ids"]:
                logger.info(f"  - {media_info['title']}: {media_info['media_id']}")
        
        # Cleanup temp files
        import shutil
        temp_dir = Path("temp_casino_images")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info("🧹 Cleaned up temporary files")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Chain execution failed: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    main()