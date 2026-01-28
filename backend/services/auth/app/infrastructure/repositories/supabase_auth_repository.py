from typing import Optional
import logging

from domain.entities.user import User, AuthTokens, AuthResult
from domain.repositories.auth_repository import AuthRepositoryInterface
from supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SupabaseAuthRepository(AuthRepositoryInterface):
    """
    Supabase implementation với DUAL TABLE strategy:
    - auth.users: Authentication (Supabase Auth)
    - public.users: Profile data (Custom table)
    """
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # ========================================
    # HELPER: Convert DB row → Entity
    # ========================================
    def _to_user_entity(self, user_row: dict) -> User:
        """
        Convert database row từ public.users thành User
        
        THAY ĐỔI: Không dùng user_metadata nữa, dùng public.users
        """
        return User(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row.get("full_name", ""),
            phone=user_row.get("phone"),
            avatar_url=user_row.get("avatar_url"),
            role=user_row.get("role", "customer"),
            created_at=user_row.get("created_at")
        )
    
    def _to_auth_result(self, auth_response, user_row: dict) -> AuthResult:
        """
        Convert Supabase auth response + user row thành AuthResult
        """
        tokens = AuthTokens(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in
        )
        user = self._to_user_entity(user_row)
        
        return AuthResult(tokens=tokens, user=user)
    
    # ========================================
    # REGISTER - QUAN TRỌNG: Tạo trong CẢ 2 BẢNG
    # ========================================
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None
    ) -> AuthResult:
        """
        Đăng ký user mới
        
        Flow:
        1. Tạo user trong auth.users (Supabase Auth)
        2. Tạo profile trong public.users (Custom table)
        """
        try:
            logger.info(f"Registering user: {email}")
            
            # ========================================
            # BƯỚC 1: Tạo trong auth.users
            # ========================================
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                # Không cần options.data nữa vì sẽ lưu vào public.users
            })
            
            if auth_response.user is None:
                raise ValueError("Đăng ký thất bại. Email có thể đã tồn tại.")
            
            user_id = auth_response.user.id
            logger.info(f"✓ Created user in auth.users: {user_id}")
            
            # ========================================
            # BƯỚC 2: Tạo profile trong public.users
            # ========================================
            user_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "role": "customer"  # Default role
            }
            
            try:
                db_response = self.supabase.table("users")\
                    .insert(user_data)\
                    .execute()
                
                if not db_response.data:
                    # Nếu không tạo được public.users, rollback auth.users
                    logger.error(f"✗ Failed to create profile in public.users")
                    # TODO: Implement rollback logic
                    raise ValueError("Không thể tạo profile")
                
                logger.info(f"✓ Created profile in public.users: {user_id}")
                
            except Exception as e:
                logger.error(f"✗ Error creating profile: {e}")
                # TODO: Rollback auth.users
                raise ValueError(f"Không thể tạo profile: {str(e)}")
            
            # ========================================
            # BƯỚC 3: Return AuthResult
            # ========================================
            if auth_response.session is None:
                # Cần confirm email
                raise ValueError("Vui lòng kiểm tra email để xác nhận tài khoản.")
            
            return self._to_auth_result(auth_response, db_response.data[0])
            
        except Exception as e:
            logger.error(f"Register error: {e}")
            raise ValueError(f"Đăng ký thất bại: {str(e)}")
    
    # ========================================
    # LOGIN - Get data từ public.users
    # ========================================
    async def login(self, email: str, password: str) -> AuthResult:
        """
        Đăng nhập
        
        Flow:
        1. Verify credentials với auth.users (Supabase Auth)
        2. Get profile từ public.users
        """
        try:
            logger.info(f"Login attempt: {email}")
            
            # ========================================
            # BƯỚC 1: Authenticate với auth.users
            # ========================================
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Email hoặc mật khẩu không đúng")
            
            user_id = auth_response.user.id
            logger.info(f"✓ User authenticated: {user_id}")
            
            # ========================================
            # BƯỚC 2: Get profile từ public.users
            # ========================================
            try:
                user_data = self.supabase.table("users")\
                    .select("*")\
                    .eq("id", user_id)\
                    .single()\
                    .execute()
                
                if not user_data.data:
                    # Nếu không có trong public.users, tạo mới
                    logger.warning(f"⚠ User exists in auth but not in public.users: {user_id}")
                    
                    # Auto-create profile
                    user_row = {
                        "id": user_id,
                        "email": email,
                        "full_name": "",
                        "role": "customer"
                    }
                    
                    create_response = self.supabase.table("users")\
                        .insert(user_row)\
                        .execute()
                    
                    user_data.data = create_response.data[0] if create_response.data else user_row
                
                logger.info(f"✓ Profile loaded from public.users")
                
            except Exception as e:
                logger.error(f"✗ Error loading profile: {e}")
                # Fallback data
                user_data.data = {
                    "id": user_id,
                    "email": email,
                    "full_name": "",
                    "role": "customer"
                }
            
            # ========================================
            # BƯỚC 3: Return AuthResult
            # ========================================
            return self._to_auth_result(auth_response, user_data.data)
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise ValueError("Email hoặc mật khẩu không đúng")
    
    # ========================================
    # GET USER BY TOKEN - Get từ public.users
    # ========================================
    async def get_user_by_token(self, access_token: str) -> User:
        """
        Lấy user từ access token
        
        Flow:
        1. Verify token với auth.users
        2. Get full profile từ public.users
        """
        try:
            # ========================================
            # BƯỚC 1: Verify token
            # ========================================
            auth_response = self.supabase.auth.get_user(access_token)
            
            if auth_response.user is None:
                raise ValueError("Token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # ========================================
            # BƯỚC 2: Get profile từ public.users
            # ========================================
            user_data = self.supabase.table("users")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if not user_data.data:
                raise ValueError("User profile không tồn tại")
            
            return self._to_user_entity(user_data.data)
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            raise ValueError("Token không hợp lệ hoặc đã hết hạn")
    
    # ========================================
    # UPDATE USER - Update public.users
    # ========================================
    async def update_user(
        self,
        access_token: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """
        Cập nhật profile
        
        THAY ĐỔI: Update public.users thay vì user_metadata
        """
        try:
            # ========================================
            # BƯỚC 1: Verify token
            # ========================================
            auth_response = self.supabase.auth.get_user(access_token)
            
            if auth_response.user is None:
                raise ValueError("Token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # ========================================
            # BƯỚC 2: Build update data
            # ========================================
            update_data = {}
            if full_name is not None:
                update_data["full_name"] = full_name
            if phone is not None:
                update_data["phone"] = phone
            if avatar_url is not None:
                update_data["avatar_url"] = avatar_url
            
            if not update_data:
                raise ValueError("Không có dữ liệu để cập nhật")
            
            # ========================================
            # BƯỚC 3: Update public.users
            # ========================================
            response = self.supabase.table("users")\
                .update(update_data)\
                .eq("id", user_id)\
                .execute()
            
            if not response.data:
                raise ValueError("Cập nhật thất bại")
            
            logger.info(f"✓ User profile updated: {user_id}")
            return self._to_user_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            raise ValueError(f"Cập nhật thất bại: {str(e)}")
    
    # ========================================
    # LOGOUT - Không thay đổi
    # ========================================
    async def logout(self, access_token: str) -> bool:
        """Đăng xuất"""
        try:
            self.supabase.auth.sign_out()
            logger.info("User logged out")
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return True
    
    # ========================================
    # REFRESH TOKEN - Không thay đổi
    # ========================================
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """
        Làm mới access token
        
        Flow:
        1. Refresh token với auth.users
        2. Get profile từ public.users
        """
        try:
            logger.info("Refreshing token")
            
            # ========================================
            # BƯỚC 1: Refresh token
            # ========================================
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Refresh token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # ========================================
            # BƯỚC 2: Get profile từ public.users
            # ========================================
            user_data = self.supabase.table("users")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if not user_data.data:
                raise ValueError("User profile không tồn tại")
            
            return self._to_auth_result(auth_response, user_data.data)
            
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            raise ValueError("Không thể refresh token")
    
    # ========================================
    # RESET PASSWORD - Không thay đổi
    # ========================================
    async def reset_password_request(self, email: str) -> bool:
        """Gửi email reset password"""
        try:
            logger.info(f"Password reset request: {email}")
            self.supabase.auth.reset_password_email(email)
            return True
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return True