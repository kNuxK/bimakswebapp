import requests
import json
from PIL import Image

def get_linkedin_user_urn(access_token):
    access_token = str(access_token).strip()
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        resp_info = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
        if resp_info.status_code == 200: return resp_info.json().get('sub') 
    except: pass
    try:
        resp_me = requests.get("https://api.linkedin.com/v2/me", headers=headers)
        if resp_me.status_code == 200: return resp_me.json().get('id')
    except: pass
    return None

def register_upload_image(access_token, person_urn):
    access_token = str(access_token).strip()
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{person_urn}",
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = data['value']['asset']
            return upload_url, asset
        return None, None
    except: return None, None

def post_to_linkedin_real(text, media_bytes, media_type, access_token):
    if not access_token: return "❌ HATA: LinkedIn Token girilmemiş."
    access_token = str(access_token).strip()
    person_id = get_linkedin_user_urn(access_token)
    if not person_id: return "❌ HATA: Token geçersiz veya erişim izni yok."
    person_urn = f"urn:li:person:{person_id}"
    asset_urn = None
    if media_bytes and "image" in media_type:
        upload_url, asset = register_upload_image(access_token, person_id)
        if upload_url:
            try:
                put_headers = {'Authorization': f'Bearer {access_token}'}
                put_resp = requests.put(upload_url, data=media_bytes, headers=put_headers)
                if put_resp.status_code in [200, 201]: asset_urn = asset
                else: return f"❌ HATA: Resim yüklenemedi. Kod: {put_resp.status_code}"
            except Exception as e: return f"❌ HATA: Resim upload sorunu: {str(e)}"
        else: return "❌ HATA: Resim kaydı başarısız."
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'X-Restli-Protocol-Version': '2.0.0'}
    share_content = {"shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}
    if asset_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [{"status": "READY", "description": {"text": "Bimaks App Auto Post"}, "media": asset_urn, "title": {"text": "Bimaks Visual"}}]
    payload = {
        "author": person_urn, "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    try:
        response = requests.post(post_url, headers=headers, json=payload)
        if response.status_code in [200, 201]: return "✅ BAŞARILI: Paylaşım LinkedIn'de yayında!"
        else: return f"❌ HATA: LinkedIn reddetti. Kod: {response.status_code} - Mesaj: {response.text}"
    except Exception as e: return f"❌ HATA: Bağlantı sorunu: {str(e)}"

def resize_for_instagram(image):
    base_width = 1080
    w_percent = (base_width / float(image.size[0]))
    h_size = int((float(image.size[1]) * float(w_percent)))
    img = image.resize((base_width, h_size), Image.Resampling.LANCZOS)
    if h_size > 1350: img = img.crop((0, (h_size-1350)/2, 1080, (h_size+1350)/2))
    return img