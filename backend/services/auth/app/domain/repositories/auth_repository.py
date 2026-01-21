
# Repository Interface (Port)
# - Định nghĩa contract cho data access
# - Không chứa implementation
# - Infrastructure layer sẽ implement
# ============================================

from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User, AuthResult


class AuthRepositoryInterface(ABC):
    """
    Abstract Repository cho Authentication
    
    Đây là "Port" trong Hexagonal Architecture
    - Định nghĩa các method cần có
    - Không quan tâm implementation cụ thể
    - Có thể swap giữa Supabase, Firebase, custom DB...
    """
    
    @abstractmethod
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None
    ) -> AuthResult:
        """
        Đăng ký user mới
        
        Args:
            email: Email đăng ký
            password: Mật khẩu
            full_name: Họ tên
            phone: Số điện thoại (optional)
            
        Returns:
            AuthResult với tokens và user info
            
        Raises:
            ValueError: Email đã tồn tại
        """
        pass
    
    @abstractmethod
    async def login(
        self,
        email: str,
        password: str
    ) -> AuthResult:
        """
        Đăng nhập
        
        Args:
            email: Email
            password: Mật khẩu
            
        Returns:
            AuthResult với tokens và user info
            
        Raises:
            ValueError: Sai email hoặc password
        """
        pass
    
    @abstractmethod
    async def logout(self, access_token: str) -> bool:
        """
        Đăng xuất - invalidate session
        
        Args:
            access_token: JWT token
            
        Returns:
            True nếu thành công
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """
        Làm mới access token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            AuthResult với tokens mới
            
        Raises:
            ValueError: Token không hợp lệ
        """
        pass
    
    @abstractmethod
    async def get_user_by_token(self, access_token: str) -> User:
        """
        Lấy user từ access token
        
        Args:
            access_token: JWT token
            
        Returns:
            User entity
            
        Raises:
            ValueError: Token không hợp lệ
        """
        pass
    
    @abstractmethod
    async def update_user(
        self,
        access_token: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """
        Cập nhật thông tin user
        
        Args:
            access_token: JWT token
            full_name: Tên mới (optional)
            phone: SĐT mới (optional)
            avatar_url: Avatar URL (optional)
            
        Returns:
            User đã cập nhật
        """
        pass
    
    @abstractmethod
    async def reset_password_request(self, email: str) -> bool:
        """
        Gửi email reset password
        
        Args:
            email: Email cần reset
            
        Returns:
            True (luôn trả về True để bảo mật)
        """
        pass