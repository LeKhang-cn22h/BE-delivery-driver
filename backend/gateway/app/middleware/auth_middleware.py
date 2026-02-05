

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
import os
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):

    # ===== WHITELIST - Routes KHÔNG cần authentication =====
    PUBLIC_PATHS: Set[str] = {
        # System endpoints
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        
        # Auth endpoints - PUBLIC
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/reset-password",
        "/api/data/route-analysis",  # ← Add
        "/api/data/area-stats",  # ← Add
        "/api/data/health",
    }
    
    def __init__(self, app, auth_service_url: Optional[str] = None):
        super().__init__(app)
        # URL của Auth Service để verify token
        self.auth_service_url = auth_service_url or os.getenv(
            "AUTH_SERVICE_URL", 
            "http://auth_service:7000"
        )
        
        logger.info(f" Auth Middleware initialized with Auth Service: {self.auth_service_url}")
    
    # async def dispatch(self, request: Request, call_next):
    #     """
    #     Main middleware logic - intercept mọi request
    #     """
    #     path = request.url.path
    #     method = request.method
    #
    #     # Log request
    #     logger.info(f"→ {method} {path} from {request.client.host if request.client else 'unknown'}")
    #
    #     # ===== 1. CHECK PUBLIC ROUTES =====
    #     if self._is_public_route(path):
    #         logger.debug(f" Public route: {path} - skipping auth")
    #         return await call_next(request)
    #
    #     # ===== 2. EXTRACT TOKEN =====
    #     token = self._extract_token(request)
    #
    #     if not token:
    #         logger.warning(f" Missing token for protected route: {path}")
    #         return self._unauthorized_response(
    #             detail="Missing Authorization header",
    #             hint="Use: Authorization: Bearer <token>"
    #         )
    #
    #     # ===== 3. VERIFY TOKEN =====
    #     user_info = await self._verify_token(token)
    #
    #     if not user_info:
    #         logger.warning(f" Invalid token for route: {path}")
    #         return self._unauthorized_response(
    #             detail="Invalid or expired token"
    #         )
    #
    #     # ===== 4. ADD USER INFO TO REQUEST =====
    #     # Backend services có thể access qua request.state hoặc headers
    #     request.state.user_id = user_info["user_id"]
    #     request.state.user_email = user_info.get("email", "")
    #     request.state.user_role = user_info.get("role", "user")
    #
    #     logger.info(
    #         f"✓ Authenticated: {user_info.get('email')} "
    #         f"(Role: {user_info.get('role', 'user')})"
    #     )
    #
    #     # ===== 5. CONTINUE TO ROUTE =====
    #     response = await call_next(request)
    #
    #     # Log response
    #     logger.info(f"← {method} {path} Status: {response.status_code}")
    #
    #     return response
    #
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # ===== 0. SKIP CORS PREFLIGHT =====
        if method == "OPTIONS":
            return await call_next(request)

        # ===== 1. CHECK PUBLIC ROUTES =====
        if self._is_public_route(path):
            return await call_next(request)

        # ===== 2. AUTH LOGIC =====
        token = self._extract_token(request)
        if not token:
            return self._unauthorized_response(
                detail="Missing Authorization header",
                hint="Use: Authorization: Bearer <token>"
            )

        user_info = await self._verify_token(token)
        if not user_info:
            return self._unauthorized_response(
                detail="Invalid or expired token"
            )

        request.state.user_id = user_info["user_id"]
        request.state.user_email = user_info.get("email", "")
        request.state.user_role = user_info.get("role", "user")

        return await call_next(request)

    def _is_public_route(self, path: str) -> bool:
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True
        
        # Prefix match (cho static files, etc)
        public_prefixes = ["/static", "/assets","/api/data/",]
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:

        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return None
        
        # Check format: "Bearer <token>"
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization header format: {auth_header[:20]}...")
            return None
        
        return parts[1]
    
    async def _verify_token(self, token: str) -> Optional[dict]:
        """
        Verify token với Auth Service
        
        Args:
            token: JWT token string
        
        Returns:
            dict: {user_id, email, role, full_name} nếu valid
            None: Nếu invalid/expired
        """
        try:
            # Call Auth Service để verify
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.auth_service_url}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Token verified for: {data.get('email')}")
                    return data
                
                logger.warning(f"Token verification failed: Status {response.status_code}")
                return None
                
        except httpx.TimeoutException:
            logger.error(f"Auth Service timeout: {self.auth_service_url}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error calling Auth Service: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            return None
    
    def _unauthorized_response(
        self, 
        detail: str, 
        hint: Optional[str] = None
    ) -> JSONResponse:
        """
        Trả về 401 Unauthorized response
        """
        content = {"detail": detail}
        if hint:
            content["hint"] = hint
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=content,
            headers={"WWW-Authenticate": "Bearer"}
        )


# ===== Role-based Access Control Middleware =====

class RoleCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware check role của user
    Dùng sau AuthMiddleware
    
    Example config trong main.py:
    ROLE_REQUIREMENTS = {
        "/api/v1/admin/*": ["admin"],
        "/api/v1/orders/assign": ["admin", "dispatcher"],
    }
    """
    
    def __init__(self, app, role_requirements: dict = None):
        super().__init__(app)
        self.role_requirements = role_requirements or {}
        
        if self.role_requirements:
            logger.info(f" Role Check Middleware initialized with {len(self.role_requirements)} rules")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Check if this route has role requirements
        required_roles = self._get_required_roles(path)
        
        if required_roles:
            # Get user role from request state (set by AuthMiddleware)
            user_role = getattr(request.state, "user_role", None)
            user_email = getattr(request.state, "user_email", "unknown")
            
            if not user_role or user_role not in required_roles:
                logger.warning(
                    f"✗ Access denied: User '{user_email}' with role '{user_role}' "
                    f"not in {required_roles} for path {path}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Insufficient permissions",
                        "required_roles": required_roles,
                        "your_role": user_role
                    }
                )
            
            logger.debug(f"✓ Role check passed: {user_role} in {required_roles}")
        
        return await call_next(request)
    
    def _get_required_roles(self, path: str) -> list:
        """Get required roles for a path"""
        # Exact match
        if path in self.role_requirements:
            return self.role_requirements[path]
        
        # Wildcard match
        for pattern, roles in self.role_requirements.items():
            if pattern.endswith("/*") and path.startswith(pattern[:-2]):
                return roles
        
        return []   