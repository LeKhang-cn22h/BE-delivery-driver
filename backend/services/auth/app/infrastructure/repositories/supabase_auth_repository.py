from typing import Optional
import logging

from domain.entities.user import SearchUser, User, AuthTokens, AuthResult, GeoPoint
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
        Convert database row từ public.users thành User Entity
        """
        # Parse location nếu có
        location = None
        if user_row.get("location"):
            try:
                location = GeoPoint.from_point_string(user_row["location"])
            except Exception as e:
                logger.warning(f"Failed to parse location: {e}")
        
        return User(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row.get("full_name"),
            phone=user_row.get("phone"),
            avatar_url=user_row.get("avatar_url"),
            address_detail=user_row.get("address_detail"),
            area_code=user_row.get("area_code"),
            location=location,
            role=user_row.get("role", "customer"),
            is_active=user_row.get("is_active", True),
            created_at=user_row.get("created_at"),
            updated_at=user_row.get("updated_at"),
            fcm_token=user_row.get("fcm_token"),
            post_office_id=user_row.get("post_office_id")
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
    # REGISTER - Tạo trong CẢ 2 BẢNG
    # ========================================
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        address_detail: Optional[str] = None,
        area_code: Optional[str] = None,
        location: Optional[GeoPoint] = None,
        role: str = "customer"
    ) -> AuthResult:
        """Đăng ký user mới"""
        try:
            logger.info(f"Registering user: {email}")
            
            # BƯỚC 1: Tạo trong auth.users
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
            })
            
            if auth_response.user is None:
                raise ValueError("Đăng ký thất bại. Email có thể đã tồn tại.")
            
            user_id = auth_response.user.id
            logger.info(f"✓ Created user in auth.users: {user_id}")
            
            # BƯỚC 2: Tạo profile trong public.users
            user_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "address_detail": address_detail,
                "area_code": area_code,
                "role": role
            }
            
            # Thêm location nếu có
            if location:
                user_data["location"] = location.to_point_string()
            
            try:
                db_response = self.supabase.table("users")\
                    .insert(user_data)\
                    .execute()
                
                if not db_response.data:
                    logger.error(f"✗ Failed to create profile in public.users")
                    raise ValueError("Không thể tạo profile")
                
                logger.info(f"✓ Created profile in public.users: {user_id}")
                
            except Exception as e:
                logger.error(f"✗ Error creating profile: {e}")
                raise ValueError(f"Không thể tạo profile: {str(e)}")
            
            # BƯỚC 3: Return AuthResult
            if auth_response.session is None:
                raise ValueError("Vui lòng kiểm tra email để xác nhận tài khoản.")
            
            return self._to_auth_result(auth_response, db_response.data[0])
            
        except Exception as e:
            logger.error(f"Register error: {e}")
            raise ValueError(f"Đăng ký thất bại: {str(e)}")
    
    # ========================================
    # LOGIN - Get data từ public.users và update FCM token
    # ========================================
    async def login(
        self,
        email: str,
        password: str,
        fcm_token: Optional[str] = None
    ) -> AuthResult:
        """Đăng nhập"""
        try:
            logger.info(f"Login attempt: {email}")
            
            # BƯỚC 1: Authenticate với auth.users
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Email hoặc mật khẩu không đúng")
            
            user_id = auth_response.user.id
            logger.info(f"✓ User authenticated: {user_id}")
            
            # BƯỚC 2: Get profile từ public.users
            try:
                user_data = self.supabase.table("users")\
                    .select("*")\
                    .eq("id", user_id)\
                    .single()\
                    .execute()
                
                if not user_data.data:
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
                
                # BƯỚC 3: Update FCM token nếu có
                if fcm_token:
                    self.supabase.table("users")\
                        .update({"fcm_token": fcm_token})\
                        .eq("id", user_id)\
                        .execute()
                    user_data.data["fcm_token"] = fcm_token
                    logger.info(f"✓ FCM token updated for user: {user_id}")
                
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
            
            return self._to_auth_result(auth_response, user_data.data)
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise ValueError("Email hoặc mật khẩu không đúng")
    
    # ========================================
    # GET USER BY TOKEN
    # ========================================
    async def get_user_by_token(self, access_token: str) -> User:
        """Lấy user từ access token"""
        try:
            # Verify token
            auth_response = self.supabase.auth.get_user(access_token)
            
            if auth_response.user is None:
                raise ValueError("Token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # Get profile từ public.users
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
    
    async def search_user_by_phone_or_mail(self, data: str) -> SearchUser:
        result = (
            self.supabase
            .table("users")
            .select("id,address_detail,area_code,location")
            .or_(f"phone.eq.{data},email.eq.{data}")
            .execute()
        )

        if not result.data:
            raise ValueError("User không tồn tại")

        row = result.data[0]

        return SearchUser(
            id=row["id"],
            address_detail=row.get("address_detail"),
            area_code=row.get("area_code"),
            location=row.get("location"),
        )

    
    # ========================================
    # UPDATE USER - Update public.users với các trường mới
    # ========================================
    async def update_user(
        self,
        access_token: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None,
        address_detail: Optional[str] = None,
        area_code: Optional[str] = None,
        location: Optional[GeoPoint] = None,
        fcm_token: Optional[str] = None
    ) -> User:
        """Cập nhật profile"""
        try:
            # BƯỚC 1: Verify token
            auth_response = self.supabase.auth.get_user(access_token)
            
            if auth_response.user is None:
                raise ValueError("Token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # BƯỚC 2: Build update data
            update_data = {}
            if full_name is not None:
                update_data["full_name"] = full_name
            if phone is not None:
                update_data["phone"] = phone
            if avatar_url is not None:
                update_data["avatar_url"] = avatar_url
            if address_detail is not None:
                update_data["address_detail"] = address_detail
            if area_code is not None:
                update_data["area_code"] = area_code
            if location is not None:
                update_data["location"] = location.to_point_string()
            if fcm_token is not None:
                update_data["fcm_token"] = fcm_token
            
            if not update_data:
                raise ValueError("Không có dữ liệu để cập nhật")
            
            # Thêm timestamp
            update_data["updated_at"] = "now()"
            
            # BƯỚC 3: Update public.users
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
            return True
    
    # ========================================
    # REFRESH TOKEN
    # ========================================
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Làm mới access token"""
        try:
            logger.info("Refreshing token")
            
            auth_response = self.supabase.auth.refresh_session(refresh_token)
            
            if auth_response.user is None or auth_response.session is None:
                raise ValueError("Refresh token không hợp lệ")
            
            user_id = auth_response.user.id
            
            # Get profile từ public.users
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
            return True