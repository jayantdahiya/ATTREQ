"""User management endpoints for ATTREQ API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from attreq_api.config.database import get_db
from attreq_api.config.security import oauth2_scheme
from attreq_api.crud.user import user_crud
from attreq_api.schemas.user import LocationUpdate, PasswordChange, UserResponse, UserUpdate

router = APIRouter()


async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Get current authenticated user.

    Args:
        db: Database session
        token: JWT token from Authorization header

    Returns:
        User: User object

    Raises:
        HTTPException: If user not found or inactive
    """
    from attreq_api.config.security import verify_token

    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        )

    user = await user_crud.get_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user information
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update current user profile.

    Args:
        user_update: User update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Updated user information
    """
    updated_user = await user_crud.update(db, current_user, user_update)
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Change user password.

    Args:
        password_data: Password change data
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    from attreq_api.config.security import get_password_hash, verify_password
    from attreq_api.models.user import User

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )

    # Update password
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(password_hash=get_password_hash(password_data.new_password))
    )
    await db.commit()

    return {"message": "Password updated successfully"}


@router.patch("/me/location", response_model=UserResponse)
async def update_user_location(
    location_data: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update user's saved location.

    Args:
        location_data: Location update data (lat, lon, city)
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Updated user information
    """
    updated_user = await user_crud.update_user_location(db, current_user, location_data)
    return UserResponse.model_validate(updated_user)


@router.delete("/me", status_code=status.HTTP_200_OK)
async def deactivate_account(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Deactivate current user account.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    await user_crud.deactivate_user(db, current_user)

    return {"message": "Account deactivated successfully"}
