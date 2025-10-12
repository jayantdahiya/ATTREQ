"""Authentication endpoints for ATTREQ API."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_tokens, verify_token
from app.crud.user import user_crud
from app.schemas.token import LoginResponse, TokenRefresh, TokenRefreshResponse
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        user = await user_crud.create(db, obj_in=user_in)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return tokens.

    Args:
        form_data: OAuth2 password form data (username=email, password)
        db: Database session

    Returns:
        LoginResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await user_crud.authenticate(db, email=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Update last login
    await user_crud.update_last_login(db, user)

    # Create tokens
    tokens = create_tokens(subject=user.id)

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=UserResponse.model_validate(user).model_dump(),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token data
        db: Database session

    Returns:
        TokenRefreshResponse: New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Check if user still exists and is active
        user = await user_crud.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Create new access token
        from app.core.security import create_access_token

        access_token = create_access_token(subject=user_id)

        return TokenRefreshResponse(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from e


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    Logout user (client-side token removal).

    Note: Since we're using stateless JWT tokens, logout is handled
    client-side by removing tokens from storage. This endpoint
    exists for API completeness.
    """
    return {"message": "Successfully logged out"}
