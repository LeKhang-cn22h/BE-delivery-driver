from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
keyadmin = os.getenv("SUPABASE_KEY_ADMIN")
keyuser = os.getenv("SUPABASE_KEY_USER")

supabaseUser = create_client(url, keyuser)
supabaseAdmin = create_client(url, keyadmin)