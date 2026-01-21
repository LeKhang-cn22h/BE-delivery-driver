
# Concrete Implementation của AuthRepositoryInterface
# - Sử dụng Supabase làm backend
# ============================================

from typing import Optional
import logging

from domain.entities.user import User, AuthTokens, AuthResult
from domain.repositories.auth_repository import AuthRepositoryInterface
from supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SupabaseAuthRepository(AuthRepositoryInterface):
    """
    Supabase implementation của AuthRepository
    
    Đây là "Adapter" trong Hexagonal Architecture
    - Implement interface đã định nghĩa ở domain
    - Chứa code cụ thể cho Supabase
    """
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # ========================================
    # HELPER: Convert Supabase user → Entity
    # ========================================
    def _to_user_entity(self, supabase_user) -> User:
        """Convert Supabase user object thành User entity"""
        metadata = supabase_user.user_metadata or {}
        
        return User(
            id=supabase_user.id,
            email=supabase_user.email,
            full_name=metadata.get("full_name"),
            phone=metadata.get("phone"),
            avatar_url=metadata.get("avatar_url"),
            created_at=supabase_user.created_at
        )
    
    def _to_auth_result(self, response) -> AuthResult:
        """Convert Supabase response thành AuthResult"""
        tokens = AuthTokens(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            expires_in=response.session.expires_in
        )
        user = self._to_user_entity(response.user)
        
        return AuthResult(tokens=tokens, user=user)
    
    # ========================================
    # REGISTER
    # ========================================
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None
    ) -> AuthResult:
        """Đăng ký với Supabase Auth"""
        try:
            logger.info(f"Registering user: {email}")
            
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "phone": phone
                    }
                }
            })
            
            if response.user is None:
                raise ValueError("Đăng ký thất bại. Email có thể đã tồn tại.")
            
            if response.session is None:
                # Cần confirm email
                raise ValueError("Vui lòng kiểm tra email để xác nhận tài khoản.")
            
            logger.info(f"User registered: {response.user.id}")
            return self._to_auth_result(response)
            
        except Exception as e:
            logger.error(f"Register error: {e}")
            raise ValueError(f"Đăng ký thất bại: {str(e)}")
    
    # ========================================
    # LOGIN
    # ========================================
    async def login(self, email: str, password: str) -> AuthResult:
        """Đăng nhập với Supabase Auth"""
        try:
            logger.info(f"Login attempt: {email}")
            
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user is None or response.session is None:
                raise ValueError("Email hoặc mật khẩu không đúng")
            
            logger.info(f"User logged in: {response.user.id}")
            return self._to_auth_result(response)
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise ValueError("Email hoặc mật khẩu không đúng")
    
    # ========================================
    # LOGOUT
    # ========================================
    async def logout(self, access_token: str) -> bool:
        """Đăng xuất"""
        try:
            self.supabase.auth.sign_out()
            logger.info("User logged out")
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return True  # Vẫn return True vì client sẽ xóa token
    
    # ========================================
    # REFRESH TOKEN
    # ========================================
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Làm mới access token"""
        try:
            logger.info("Refreshing token")
            
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.user is None or response.session is None:
                raise ValueError("Refresh token không hợp lệ")
            
            return self._to_auth_result(response)
            
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            raise ValueError("Không thể refresh token")
    
    # ========================================
    # GET USER BY TOKEN
    # ========================================
    async def get_user_by_token(self, access_token: str) -> User:
        """Lấy user từ access token"""
        try:
            response = self.supabase.auth.get_user(access_token)
            
            if response.user is None:
                raise ValueError("Token không hợp lệ")
            
            return self._to_user_entity(response.user)
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            raise ValueError("Token không hợp lệ hoặc đã hết hạn")
    
    # ========================================
    # UPDATE USER
    # ========================================
    async def update_user(
        self,
        access_token: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Cập nhật thông tin user"""
        try:
            update_data = {}
            if full_name is not None:
                update_data["full_name"] = full_name
            if phone is not None:
                update_data["phone"] = phone
            if avatar_url is not None:
                update_data["avatar_url"] = avatar_url
            
            if not update_data:
                raise ValueError("Không có dữ liệu để cập nhật")
            
            response = self.supabase.auth.update_user({
                "data": update_data
            })
            
            if response.user is None:
                raise ValueError("Cập nhật thất bại")
            
            logger.info(f"User updated: {response.user.id}")
            return self._to_user_entity(response.user)
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            raise ValueError(f"Cập nhật thất bại: {str(e)}")
    
    # ========================================
    # RESET PASSWORD
    # ========================================
    async def reset_password_request(self, email: str) -> bool:
        """Gửi email reset password"""
        try:
            logger.info(f"Password reset request: {email}")
            self.supabase.auth.reset_password_email(email)
            return True
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return True  # Không tiết lộ email có tồn tại không